#include "runtime.h"

#include <stdio.h>
#include <sys/stat.h>
#include <limits.h>

#ifdef _WIN32
#include <direct.h>
#include <errno.h>
#include <windows.h>
#else
#include <dirent.h>
#include <errno.h>
#include <fcntl.h>
#include <signal.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>
#endif

static int nq_process_argc = 0;
static char** nq_process_argv = NULL;

/* Test limits must still represent fixed allocation-free IO error metadata. */
#if defined(NQ_TEST_MAX_SEQUENCE_LENGTH) && NQ_TEST_MAX_SEQUENCE_LENGTH < 128
#error NQ_TEST_MAX_SEQUENCE_LENGTH must be at least 128
#endif

typedef enum { NQ_ALLOC_OK, NQ_ALLOC_SIZE, NQ_ALLOC_OOM } NQAllocStatus;

static _Noreturn void nq_size_fail(void) {
    fputs("nauqtype runtime: size limit exceeded\n", stderr);
    exit(1);
}

static _Noreturn void nq_alloc_fail(NQAllocStatus status) {
    if (status == NQ_ALLOC_SIZE) nq_size_fail();
    fputs("nauqtype runtime: out of memory\n", stderr);
    exit(1);
}

static size_t nq_allocation_limit(void) {
    size_t limit = SIZE_MAX;
#ifdef NQ_TEST_MAX_ALLOCATION_BYTES
    if ((uintmax_t)NQ_TEST_MAX_ALLOCATION_BYTES < (uintmax_t)limit)
        limit = (size_t)NQ_TEST_MAX_ALLOCATION_BYTES;
#endif
    return limit;
}

static size_t nq_sequence_limit(uintmax_t maximum) {
    if (maximum > SIZE_MAX) maximum = SIZE_MAX;
#ifdef NQ_TEST_MAX_SEQUENCE_LENGTH
    if ((uintmax_t)NQ_TEST_MAX_SEQUENCE_LENGTH < maximum)
        maximum = (uintmax_t)NQ_TEST_MAX_SEQUENCE_LENGTH;
#endif
    return (size_t)maximum;
}

static size_t nq_str_limit(void) { return nq_sequence_limit(INT32_MAX); }
static size_t nq_bytes_limit(void) {
    size_t limit = nq_sequence_limit(INT64_MAX);
    return limit < nq_allocation_limit() ? limit : nq_allocation_limit();
}

static bool nq_size_add(size_t a, size_t b, size_t limit, size_t* out) {
    if (a > limit || b > limit - a) return false;
    *out = a + b;
    return true;
}

static bool nq_size_mul(size_t count, size_t size, size_t* out) {
    if (size != 0 && count > nq_allocation_limit() / size) return false;
    *out = count * size;
    return true;
}

static size_t nq_growth(size_t cap, size_t needed, size_t limit, size_t initial) {
    if (needed <= cap) return cap;
    size_t next = cap == 0 ? (initial < limit ? initial : limit) : cap;
    while (next < needed) next = next > limit - next ? limit : next * 2;
    return next;
}

static NQAllocStatus nq_list_capacity(int32_t cap, int32_t len, size_t extra,
                                     size_t item_size, int32_t* out) {
    size_t needed;
    size_t limit = nq_sequence_limit(INT32_MAX);
    if (item_size == 0) return NQ_ALLOC_SIZE;
    if (limit > nq_allocation_limit() / item_size) limit = nq_allocation_limit() / item_size;
    if (len < 0 || cap < len || (uintmax_t)cap > limit ||
        !nq_size_add((size_t)len, extra, limit, &needed)) return NQ_ALLOC_SIZE;
    *out = (int32_t)nq_growth((size_t)cap, needed, limit, 4);
    return NQ_ALLOC_OK;
}

size_t nq_allocation_size(size_t count, size_t item_size) {
    size_t size;
    if (!nq_size_mul(count, item_size, &size)) nq_size_fail();
    return size;
}

int32_t nq_list_grow_capacity(int32_t cap, int32_t len, size_t extra, size_t item_size) {
    int32_t next;
    if (nq_list_capacity(cap, len, extra, item_size, &next) != NQ_ALLOC_OK) nq_size_fail();
    return next;
}

#ifdef NQ_TEST_ALLOC_FAIL_AFTER
static uintmax_t nq_test_allocation_count = 0;
#endif

/* The sole runtime allocator entrypoint. Rejection never changes ptr or the
 * successful-allocation counter; zero-size requests only release storage. */
static void* nq_try_realloc(void* ptr, size_t size, NQAllocStatus* status) {
    void* next;
    *status = NQ_ALLOC_OK;
    if (size > nq_allocation_limit()) { *status = NQ_ALLOC_SIZE; return NULL; }
    if (size == 0) { free(ptr); return NULL; }
#ifdef NQ_TEST_ALLOC_FAIL_AFTER
    if (nq_test_allocation_count == (uintmax_t)NQ_TEST_ALLOC_FAIL_AFTER) {
        *status = NQ_ALLOC_OOM;
        return NULL;
    }
#endif
    next = ptr == NULL ? malloc(size) : realloc(ptr, size);
    if (next == NULL) { *status = NQ_ALLOC_OOM; return NULL; }
#ifdef NQ_TEST_ALLOC_FAIL_AFTER
    nq_test_allocation_count += 1;
#endif
    return next;
}

static bool nq_str_size(intmax_t len) {
    return len >= 0 && (uintmax_t)len <= nq_str_limit();
}

static bool nq_cstr_length(const char* text, size_t* len) {
    size_t n = 0;
    size_t limit = nq_str_limit();
    while (text[n] != '\0') {
        if (n == limit) return false;
        n += 1;
    }
    *len = n;
    return true;
}

NQStr nq_str(const char* data) {
    size_t len;
    if (!nq_cstr_length(data, &len)) nq_size_fail();
    return (NQStr){data, (intptr_t)len, NULL};
}

_Noreturn void nq_integer_division_fail(bool zero) {
    fputs(zero ? "nauqtype runtime: integer division by zero\n" :
                 "nauqtype runtime: integer division overflow\n", stderr);
    exit(1);
}

struct NQStrOwner {
    size_t ref_count;
    char* storage;
};

/* try_take consumes storage on both success and failure. */
static NQAllocStatus nq_try_str_take(char* storage, size_t len, NQStr* out) {
    NQAllocStatus status;
    NQStrOwner* owner;
    if (len > nq_str_limit() || len >= nq_allocation_limit()) { free(storage); return NQ_ALLOC_SIZE; }
    owner = (NQStrOwner*)nq_try_realloc(NULL, sizeof(NQStrOwner), &status);
    if (status != NQ_ALLOC_OK) { free(storage); return status; }
    owner->ref_count = 1;
    owner->storage = storage;
    *out = (NQStr){ .data = storage, .len = (intptr_t)len, .owner = owner };
    return NQ_ALLOC_OK;
}

static NQAllocStatus nq_try_cstr_copy(const char* data, size_t len, char** out) {
    NQAllocStatus status;
    size_t size;
    if (len > nq_str_limit() || !nq_size_add(len, 1, nq_allocation_limit(), &size)) return NQ_ALLOC_SIZE;
    *out = (char*)nq_try_realloc(NULL, size, &status);
    if (status != NQ_ALLOC_OK) return status;
    if (len != 0) memcpy(*out, data, len);
    (*out)[len] = '\0';
    return NQ_ALLOC_OK;
}

static NQAllocStatus nq_try_str_copy(const char* data, size_t len, NQStr* out) {
    char* storage = NULL;
    NQAllocStatus status;
    if (sizeof(NQStrOwner) > nq_allocation_limit()) return NQ_ALLOC_SIZE;
    status = nq_try_cstr_copy(data, len, &storage);
    if (status != NQ_ALLOC_OK) return status;
    return nq_try_str_take(storage, len, out);
}

static NQStr nq_owned_str_copy(const char* data, intptr_t len) {
    NQStr out;
    NQAllocStatus status;
    if (!nq_str_size(len)) nq_size_fail();
    status = nq_try_str_copy(data, (size_t)len, &out);
    if (status != NQ_ALLOC_OK) nq_alloc_fail(status);
    return out;
}

static const char* nq_io_kind_for_code(int code);
static NQIoErr nq_allocation_io_err(const char* operation, NQAllocStatus status);
static NQIoErr nq_make_io_err_details(
    int32_t os_code,
    const char* kind,
    const char* operation,
    const NQStr* path,
    const NQStr* other_path,
    const char* detail
);

static NQ_Result__process_result__io_err nq_process_io_err(int32_t code, const char* text) {
#ifdef _WIN32
    bool out_of_memory = code == ERROR_NOT_ENOUGH_MEMORY || code == ERROR_OUTOFMEMORY;
#else
    bool out_of_memory = code == ENOMEM;
#endif
    return (NQ_Result__process_result__io_err){
        .tag = NQ_Result__process_result__io_err_Tag_Err,
        .data.Err = { ._0 = out_of_memory ? nq_allocation_io_err("run_process", NQ_ALLOC_OOM) :
                     nq_make_io_err_details(code, nq_io_kind_for_code(code), "run_process", NULL, NULL, text) },
    };
}

static NQ_Result__process_result__io_err nq_process_err(NQIoErr err) {
    return (NQ_Result__process_result__io_err){
        .tag = NQ_Result__process_result__io_err_Tag_Err,
        .data.Err = { ._0 = err },
    };
}

static NQ_Result__process_result__io_err nq_process_ok(int32_t exit_code, NQStr stdout_text, NQStr stderr_text) {
    NQ_process_result value = { exit_code, stdout_text, stderr_text };
    return (NQ_Result__process_result__io_err){
        .tag = NQ_Result__process_result__io_err_Tag_Ok,
        .data.Ok = {
            ._0 = value,
        },
    };
}

static NQStr nq_empty_str(void) {
    return (NQStr){ .data = "", .len = 0, .owner = NULL };
}

/* operation is a runtime-owned static label, never caller-owned storage.
 * This fallback deliberately has no paths and performs no allocation. */
static NQIoErr nq_allocation_io_err(const char* operation, NQAllocStatus status) {
    bool size = status == NQ_ALLOC_SIZE;
    return (NQIoErr){
        .code = size ? 0 : ENOMEM, .os_code = size ? 0 : ENOMEM,
        .text = nq_str(size ? "size limit exceeded" : "out of memory"),
        .kind = nq_str(size ? "invalid_input" : "other"),
        .operation = nq_str(operation == NULL ? "" : operation),
        .path = nq_empty_str(), .other_path = nq_empty_str(),
        .has_path = false, .has_other_path = false,
    };
}

static bool nq_str_has_nul(NQStr text) {
    return text.len > 0 && memchr(text.data, '\0', (size_t)text.len) != NULL;
}

static bool nq_str_storage_is_valid(NQStr text) {
    return nq_str_size(text.len) && (text.len == 0 || text.data != NULL);
}

static const char* nq_io_kind_for_code(int code) {
    switch (code) {
        case ENOENT: return "not_found";
        case EACCES:
#ifdef EPERM
        case EPERM:
#endif
            return "permission_denied";
        case EEXIST: return "already_exists";
        case EINTR: return "interrupted";
#ifdef EXDEV
        case EXDEV: return "cross_device";
#endif
#ifdef ENOTSUP
        case ENOTSUP: return "unsupported";
#endif
#if defined(EOPNOTSUPP) && (!defined(ENOTSUP) || EOPNOTSUPP != ENOTSUP)
        case EOPNOTSUPP: return "unsupported";
#endif
        case EINVAL: return "invalid_input";
#ifdef ENOTDIR
        case ENOTDIR: return "not_directory";
#endif
#ifdef EISDIR
        case EISDIR: return "is_directory";
#endif
#ifdef ENOTEMPTY
        case ENOTEMPTY: return "directory_not_empty";
#endif
#ifdef EPIPE
        case EPIPE: return "broken_pipe";
#endif
        default: return "other";
    }
}

static NQIoErr nq_make_io_err_details(
    int32_t os_code,
    const char* kind,
    const char* operation,
    const NQStr* path,
    const NQStr* other_path,
    const char* detail
) {
    const char* actual_operation = operation == NULL ? "" : operation;
    const char* actual_detail = detail == NULL ? "I/O operation failed" : detail;
    size_t operation_len, detail_len, kind_len, message_len, size;
    size_t separator_len;
    char* message;
    NQAllocStatus status;
    NQIoErr err = {0};
    if (!nq_cstr_length(actual_operation, &operation_len) ||
        !nq_cstr_length(actual_detail, &detail_len) || !nq_cstr_length(kind, &kind_len))
        return nq_allocation_io_err(actual_operation, NQ_ALLOC_SIZE);
    separator_len = operation_len == 0 ? 0 : 2;
    if (!nq_size_add(operation_len, separator_len, nq_str_limit(), &message_len) ||
        !nq_size_add(message_len, detail_len, nq_str_limit(), &message_len) ||
        !nq_size_add(message_len, 1, nq_allocation_limit(), &size) ||
        sizeof(NQStrOwner) > nq_allocation_limit() ||
        (path != NULL && !nq_str_storage_is_valid(*path)) ||
        (other_path != NULL && !nq_str_storage_is_valid(*other_path)))
        return nq_allocation_io_err(actual_operation, NQ_ALLOC_SIZE);
    if ((path != NULL && (size_t)path->len >= nq_allocation_limit()) ||
        (other_path != NULL && (size_t)other_path->len >= nq_allocation_limit()) ||
        kind_len >= nq_allocation_limit())
        return nq_allocation_io_err(actual_operation, NQ_ALLOC_SIZE);
    message = (char*)nq_try_realloc(NULL, size, &status);
    if (status != NQ_ALLOC_OK) return nq_allocation_io_err(actual_operation, status);
    if (operation_len > 0) {
        memcpy(message, actual_operation, operation_len);
        memcpy(message + operation_len, ": ", 2);
    }
    memcpy(message + operation_len + separator_len, actual_detail, detail_len);
    message[message_len] = '\0';
    status = nq_try_str_take(message, message_len, &err.text);
    if (status == NQ_ALLOC_OK) status = nq_try_str_copy(kind, kind_len, &err.kind);
    if (status == NQ_ALLOC_OK) status = nq_try_str_copy(actual_operation, operation_len, &err.operation);
    if (status == NQ_ALLOC_OK && path != NULL) status = nq_try_str_copy(path->data, (size_t)path->len, &err.path);
    if (status == NQ_ALLOC_OK && other_path != NULL) status = nq_try_str_copy(other_path->data, (size_t)other_path->len, &err.other_path);
    if (status != NQ_ALLOC_OK) {
        nq_io_err_drop(&err);
        return nq_allocation_io_err(actual_operation, status);
    }
    err.code = os_code;
    err.os_code = os_code;
    err.has_path = path != NULL;
    err.has_other_path = other_path != NULL;
    if (path == NULL) err.path = nq_empty_str();
    if (other_path == NULL) err.other_path = nq_empty_str();
    return err;
}

static NQIoErr nq_errno_io_err(const char* operation, const NQStr* path, const NQStr* other_path, int error_code) {
    if (error_code == ENOMEM) return nq_allocation_io_err(operation, NQ_ALLOC_OOM);
    const char* detail = strerror(error_code);
    return nq_make_io_err_details(
        (int32_t)error_code,
        nq_io_kind_for_code(error_code),
        operation,
        path,
        other_path,
        detail == NULL ? "I/O operation failed" : detail
    );
}

static NQIoErr nq_errno_io_err_with_detail(
    const char* operation,
    const NQStr* path,
    const NQStr* other_path,
    int error_code,
    const char* context
) {
    if (error_code == ENOMEM) return nq_allocation_io_err(operation, NQ_ALLOC_OOM);
    const char* system_detail = strerror(error_code);
    size_t context_len, system_len = 0, detail_len, size;
    char* detail;
    NQAllocStatus status;
    NQIoErr err;
    if (!nq_cstr_length(context, &context_len) ||
        (system_detail != NULL && !nq_cstr_length(system_detail, &system_len)) ||
        !nq_size_add(context_len, system_len == 0 ? 0 : 2, nq_str_limit(), &detail_len) ||
        !nq_size_add(detail_len, system_len, nq_str_limit(), &detail_len) ||
        !nq_size_add(detail_len, 1, nq_allocation_limit(), &size))
        return nq_allocation_io_err(operation, NQ_ALLOC_SIZE);
    detail = (char*)nq_try_realloc(NULL, size, &status);
    if (status != NQ_ALLOC_OK) return nq_allocation_io_err(operation, status);
    memcpy(detail, context, context_len);
    if (system_len > 0) {
        memcpy(detail + context_len, ": ", 2);
        memcpy(detail + context_len + 2, system_detail, system_len);
    }
    detail[detail_len] = '\0';
    err = nq_make_io_err_details(
        (int32_t)error_code,
        nq_io_kind_for_code(error_code),
        operation,
        path,
        other_path,
        detail
    );
    free(detail);
    return err;
}

static NQIoErr nq_invalid_input_io_err(const char* operation, const NQStr* path, const NQStr* other_path, const char* detail) {
    return nq_make_io_err_details(0, "invalid_input", operation, path, other_path, detail);
}

static NQIoErr nq_invalid_data_io_err(const char* operation, const NQStr* path, const char* detail) {
    return nq_make_io_err_details(0, "invalid_data", operation, path, NULL, detail);
}

#ifdef _WIN32
static NQIoErr nq_unsupported_io_err(const char* operation, const NQStr* path) {
    return nq_make_io_err_details(0, "unsupported", operation, path, NULL, "operation is unsupported on this platform");
}
#endif

static bool nq_os_string(NQStr value, const char* operation, const NQStr* path, const NQStr* other_path, char** out, NQIoErr* out_err) {
    NQAllocStatus status;
    const NQStr* safe_path = path != NULL && nq_str_storage_is_valid(*path) ? path : NULL;
    const NQStr* safe_other_path = other_path != NULL && nq_str_storage_is_valid(*other_path) ? other_path : NULL;
    if (!nq_str_size(value.len) || (uintmax_t)value.len >= nq_allocation_limit()) {
        *out_err = nq_allocation_io_err(operation, NQ_ALLOC_SIZE);
        return false;
    }
    if (!nq_str_storage_is_valid(value)) {
        *out_err = nq_invalid_input_io_err(operation, safe_path, safe_other_path, "invalid string storage");
        return false;
    }
    if (nq_str_has_nul(value)) {
        *out_err = nq_invalid_input_io_err(operation, safe_path, safe_other_path, "embedded NUL is not allowed");
        return false;
    }
    status = nq_try_cstr_copy(value.data, (size_t)value.len, out);
    if (status != NQ_ALLOC_OK) {
        *out_err = nq_allocation_io_err(operation, status);
        return false;
    }
    return true;
}

#ifndef _WIN32
static bool nq_timestamp_to_i64_ns(time_t seconds, long nanoseconds, int64_t* out) {
    const intmax_t billion = INTMAX_C(1000000000);
    const intmax_t seconds_value = (intmax_t)seconds;
    const intmax_t nanoseconds_value = (intmax_t)nanoseconds;
    const intmax_t maximum_seconds = (intmax_t)(INT64_MAX / INT64_C(1000000000));
    const intmax_t minimum_seconds = (intmax_t)(INT64_MIN / INT64_C(1000000000)) - 1;
    const intmax_t minimum_nanoseconds = billion + (intmax_t)(INT64_MIN % INT64_C(1000000000));

    if (out == NULL || nanoseconds_value < 0 || nanoseconds_value >= billion) {
        return false;
    }
    if (seconds_value < minimum_seconds || seconds_value > maximum_seconds) {
        return false;
    }
    if (seconds_value == maximum_seconds && nanoseconds_value > (intmax_t)(INT64_MAX % INT64_C(1000000000))) {
        return false;
    }
    if (seconds_value == minimum_seconds) {
        if (nanoseconds_value < minimum_nanoseconds) {
            return false;
        }
        *out = INT64_MIN + (int64_t)(nanoseconds_value - minimum_nanoseconds);
        return true;
    }
    *out = ((int64_t)seconds_value * INT64_C(1000000000)) + (int64_t)nanoseconds_value;
    return true;
}
#endif

static NQ_Result__unit__io_err nq_unit_ok(void) {
    return (NQ_Result__unit__io_err){
        .tag = NQ_Result__unit__io_err_Tag_Ok,
        .data.Ok = { ._0 = NQ_UNIT },
    };
}

static NQ_Result__unit__io_err nq_unit_err(NQIoErr err) {
    return (NQ_Result__unit__io_err){
        .tag = NQ_Result__unit__io_err_Tag_Err,
        .data.Err = { ._0 = err },
    };
}

static NQ_Result__str__io_err nq_str_ok(NQStr value) {
    return (NQ_Result__str__io_err){
        .tag = NQ_Result__str__io_err_Tag_Ok,
        .data.Ok = { ._0 = value },
    };
}

static NQ_Result__str__io_err nq_str_err(NQIoErr err) {
    return (NQ_Result__str__io_err){
        .tag = NQ_Result__str__io_err_Tag_Err,
        .data.Err = { ._0 = err },
    };
}

static NQ_Result__bytes__io_err nq_bytes_ok(NQBytes value) {
    return (NQ_Result__bytes__io_err){
        .tag = NQ_Result__bytes__io_err_Tag_Ok,
        .data.Ok = { ._0 = value },
    };
}

static NQ_Result__bytes__io_err nq_bytes_err(NQIoErr err) {
    return (NQ_Result__bytes__io_err){
        .tag = NQ_Result__bytes__io_err_Tag_Err,
        .data.Err = { ._0 = err },
    };
}

static NQ_Result__option__str__io_err nq_option_str_ok(NQ_Option__str value) {
    return (NQ_Result__option__str__io_err){
        .tag = NQ_Result__option__str__io_err_Tag_Ok,
        .data.Ok = { ._0 = value },
    };
}

static NQ_Result__option__str__io_err nq_option_str_err(NQIoErr err) {
    return (NQ_Result__option__str__io_err){
        .tag = NQ_Result__option__str__io_err_Tag_Err,
        .data.Err = { ._0 = err },
    };
}

void* nq_realloc(void* ptr, size_t size) {
    NQAllocStatus status;
    void* next = nq_try_realloc(ptr, size, &status);
    if (status != NQ_ALLOC_OK) nq_alloc_fail(status);
    return next;
}

void nq_init_process_args(int argc, char** argv) {
    if (argc < 0 || (uintmax_t)argc > nq_sequence_limit(INT32_MAX)) nq_size_fail();
    nq_process_argc = argc;
    nq_process_argv = argv;
}

NQStr nq_str_clone(NQStr text) {
    if (!nq_str_size(text.len)) nq_size_fail();
    if (text.owner != NULL) {
        if (text.owner->ref_count == SIZE_MAX) nq_size_fail();
        text.owner->ref_count += 1;
    }
    return text;
}

NQBytes nq_bytes_from_str(NQStr text) {
    NQBytes bytes = { .data = NULL, .len = 0, .cap = 0 };
    if (!nq_str_size(text.len) || (uintmax_t)text.len > nq_bytes_limit()) nq_size_fail();
    if (text.len <= 0) {
        return bytes;
    }
    bytes.data = (unsigned char*)nq_realloc(NULL, (size_t)text.len);
    memcpy(bytes.data, text.data, (size_t)text.len);
    bytes.len = (int64_t)text.len;
    bytes.cap = (int64_t)text.len;
    return bytes;
}

NQStr nq_str_from_bytes(const NQBytes* bytes) {
    if (bytes != NULL && (!nq_str_size(bytes->len) || (uintmax_t)bytes->len > nq_bytes_limit())) nq_size_fail();
    if (bytes == NULL || bytes->len <= 0) {
        return nq_empty_str();
    }
    return nq_owned_str_copy((const char*)bytes->data, (intptr_t)bytes->len);
}

int64_t nq_bytes_len(const NQBytes* bytes) {
    if (bytes->len < 0 || (uintmax_t)bytes->len > nq_bytes_limit()) nq_size_fail();
    return bytes->len;
}

NQ_Option__i32 nq_bytes_get(const NQBytes* bytes, int64_t index) {
    if (bytes->len < 0 || (uintmax_t)bytes->len > nq_bytes_limit()) nq_size_fail();
    if (index < 0 || index >= bytes->len) {
        return (NQ_Option__i32){
            .tag = NQ_Option__i32_Tag_None,
            .data.None = NQ_UNIT,
        };
    }
    return (NQ_Option__i32){
        .tag = NQ_Option__i32_Tag_Some,
        .data.Some = { ._0 = (int32_t)bytes->data[index] },
    };
}

void nq_bytes_drop(NQBytes* bytes) {
    if (bytes == NULL) {
        return;
    }
    free(bytes->data);
    bytes->data = NULL;
    bytes->len = 0;
    bytes->cap = 0;
}

void nq_str_drop(NQStr* text) {
    if (text == NULL) {
        return;
    }
    if (text->owner != NULL) {
        if (text->owner->ref_count == 0) {
            fputs("nauqtype runtime: invalid string reference count\n", stderr);
            abort();
        }
        text->owner->ref_count -= 1;
        if (text->owner->ref_count == 0) {
            free(text->owner->storage);
            free(text->owner);
        }
    }
    *text = nq_empty_str();
}

NQIoErr nq_io_err_clone(NQIoErr err) {
    err.text = nq_str_clone(err.text);
    err.kind = nq_str_clone(err.kind);
    err.operation = nq_str_clone(err.operation);
    err.path = nq_str_clone(err.path);
    err.other_path = nq_str_clone(err.other_path);
    return err;
}

void nq_io_err_drop(NQIoErr* err) {
    if (err == NULL) {
        return;
    }
    nq_str_drop(&err->text);
    nq_str_drop(&err->kind);
    nq_str_drop(&err->operation);
    nq_str_drop(&err->path);
    nq_str_drop(&err->other_path);
    err->code = 0;
    err->os_code = 0;
    err->has_path = false;
    err->has_other_path = false;
}

NQ_process_result nq_process_result_clone(NQ_process_result value) {
    value.stdout = nq_str_clone(value.stdout);
    value.stderr = nq_str_clone(value.stderr);
    return value;
}

void nq_process_result_drop(NQ_process_result* value) {
    if (value == NULL) {
        return;
    }
    nq_str_drop(&value->stdout);
    nq_str_drop(&value->stderr);
    value->exit_code = 0;
}

NQ_Option__str nq_option__str_clone(NQ_Option__str value) {
    if (value.tag == NQ_Option__str_Tag_Some) {
        value.data.Some._0 = nq_str_clone(value.data.Some._0);
    }
    return value;
}

void nq_option__str_drop(NQ_Option__str* value) {
    if (value == NULL) {
        return;
    }
    if (value->tag == NQ_Option__str_Tag_Some) {
        nq_str_drop(&value->data.Some._0);
    }
    memset(value, 0, sizeof(*value));
}

NQ_Result__str__io_err nq_result__str__io_err_clone(NQ_Result__str__io_err value) {
    if (value.tag == NQ_Result__str__io_err_Tag_Ok) {
        value.data.Ok._0 = nq_str_clone(value.data.Ok._0);
    } else {
        value.data.Err._0 = nq_io_err_clone(value.data.Err._0);
    }
    return value;
}

void nq_result__str__io_err_drop(NQ_Result__str__io_err* value) {
    if (value == NULL) {
        return;
    }
    if (value->tag == NQ_Result__str__io_err_Tag_Ok) {
        nq_str_drop(&value->data.Ok._0);
    } else {
        nq_io_err_drop(&value->data.Err._0);
    }
    memset(value, 0, sizeof(*value));
}

NQ_Result__unit__io_err nq_result__unit__io_err_clone(NQ_Result__unit__io_err value) {
    if (value.tag == NQ_Result__unit__io_err_Tag_Err) {
        value.data.Err._0 = nq_io_err_clone(value.data.Err._0);
    }
    return value;
}

void nq_result__unit__io_err_drop(NQ_Result__unit__io_err* value) {
    if (value == NULL) {
        return;
    }
    if (value->tag == NQ_Result__unit__io_err_Tag_Err) {
        nq_io_err_drop(&value->data.Err._0);
    }
    memset(value, 0, sizeof(*value));
}

void nq_result__bytes__io_err_drop(NQ_Result__bytes__io_err* value) {
    if (value == NULL) {
        return;
    }
    if (value->tag == NQ_Result__bytes__io_err_Tag_Ok) {
        nq_bytes_drop(&value->data.Ok._0);
    } else {
        nq_io_err_drop(&value->data.Err._0);
    }
    memset(value, 0, sizeof(*value));
}

NQ_Result__option__str__io_err nq_result__option__str__io_err_clone(NQ_Result__option__str__io_err value) {
    if (value.tag == NQ_Result__option__str__io_err_Tag_Ok) {
        value.data.Ok._0 = nq_option__str_clone(value.data.Ok._0);
    } else {
        value.data.Err._0 = nq_io_err_clone(value.data.Err._0);
    }
    return value;
}

void nq_result__option__str__io_err_drop(NQ_Result__option__str__io_err* value) {
    if (value == NULL) {
        return;
    }
    if (value->tag == NQ_Result__option__str__io_err_Tag_Ok) {
        nq_option__str_drop(&value->data.Ok._0);
    } else {
        nq_io_err_drop(&value->data.Err._0);
    }
    memset(value, 0, sizeof(*value));
}

NQ_Result__path_metadata__io_err nq_result__path_metadata__io_err_clone(NQ_Result__path_metadata__io_err value) {
    if (value.tag == NQ_Result__path_metadata__io_err_Tag_Err) {
        value.data.Err._0 = nq_io_err_clone(value.data.Err._0);
    }
    return value;
}

void nq_result__path_metadata__io_err_drop(NQ_Result__path_metadata__io_err* value) {
    if (value == NULL) {
        return;
    }
    if (value->tag == NQ_Result__path_metadata__io_err_Tag_Err) {
        nq_io_err_drop(&value->data.Err._0);
    }
    memset(value, 0, sizeof(*value));
}

void nq_result__list__str__io_err_drop(NQ_Result__list__str__io_err* value) {
    if (value == NULL) {
        return;
    }
    if (value->tag == NQ_Result__list__str__io_err_Tag_Ok) {
        nq_list__str_drop(&value->data.Ok._0);
    } else {
        nq_io_err_drop(&value->data.Err._0);
    }
    memset(value, 0, sizeof(*value));
}

NQ_Result__process_result__io_err nq_result__process_result__io_err_clone(NQ_Result__process_result__io_err value) {
    if (value.tag == NQ_Result__process_result__io_err_Tag_Ok) {
        value.data.Ok._0 = nq_process_result_clone(value.data.Ok._0);
    } else {
        value.data.Err._0 = nq_io_err_clone(value.data.Err._0);
    }
    return value;
}

void nq_result__process_result__io_err_drop(NQ_Result__process_result__io_err* value) {
    if (value == NULL) {
        return;
    }
    if (value->tag == NQ_Result__process_result__io_err_Tag_Ok) {
        nq_process_result_drop(&value->data.Ok._0);
    } else {
        nq_io_err_drop(&value->data.Err._0);
    }
    memset(value, 0, sizeof(*value));
}

NQUnit nq_print_line(NQStr text) {
    if (!nq_str_size(text.len)) nq_size_fail();
    fwrite(text.data, 1, (size_t)text.len, stdout);
    fputc('\n', stdout);
    fflush(stdout);
    return NQ_UNIT;
}

NQUnit nq_eprint_line(NQStr text) {
    if (!nq_str_size(text.len)) nq_size_fail();
    fwrite(text.data, 1, (size_t)text.len, stderr);
    fputc('\n', stderr);
    fflush(stderr);
    return NQ_UNIT;
}

NQIoErr nq_make_io_err(int32_t code, const char* text) {
    return nq_make_io_err_details(code, "other", "", NULL, NULL, text);
}

NQStr nq_io_err_text(NQIoErr err) {
    return nq_str_clone(err.text);
}

NQStr nq_io_err_kind(const NQIoErr* err) {
    return err == NULL ? nq_empty_str() : nq_str_clone(err->kind);
}

NQStr nq_io_err_operation(const NQIoErr* err) {
    return err == NULL ? nq_empty_str() : nq_str_clone(err->operation);
}

NQ_Option__str nq_io_err_path(const NQIoErr* err) {
    if (err == NULL || !err->has_path) {
        return (NQ_Option__str){
            .tag = NQ_Option__str_Tag_None,
            .data.None = NQ_UNIT,
        };
    }
    return (NQ_Option__str){
        .tag = NQ_Option__str_Tag_Some,
        .data.Some = { ._0 = nq_str_clone(err->path) },
    };
}

NQ_Option__str nq_io_err_other_path(const NQIoErr* err) {
    if (err == NULL || !err->has_other_path) {
        return (NQ_Option__str){
            .tag = NQ_Option__str_Tag_None,
            .data.None = NQ_UNIT,
        };
    }
    return (NQ_Option__str){
        .tag = NQ_Option__str_Tag_Some,
        .data.Some = { ._0 = nq_str_clone(err->other_path) },
    };
}

int32_t nq_io_err_os_code(const NQIoErr* err) {
    return err == NULL ? 0 : err->os_code;
}

NQ_List__str nq_list__str_make(void) {
    return (NQ_List__str){
        .data = NULL,
        .len = 0,
        .cap = 0,
    };
}

NQ_List__str nq_list__str_from_array(const NQStr* values, int32_t len) {
    NQ_List__str items = nq_list__str_make();
    (void)nq_list_grow_capacity(len, len, 0, sizeof(NQStr));
    if (len > 0) {
        size_t size = nq_allocation_size((size_t)len, sizeof(NQStr));
        for (int32_t i = 0; i < len; i += 1)
            if (!nq_str_size(values[i].len)) nq_size_fail();
        items.data = (NQStr*)nq_realloc(NULL, size);
        memcpy(items.data, values, size);
        items.len = len;
        items.cap = len;
    }
    return items;
}

static NQAllocStatus nq_try_list_str_push(NQ_List__str* items, NQStr value) {
    int32_t next_cap;
    NQAllocStatus status = nq_list_capacity(items->cap, items->len, 1, sizeof(NQStr), &next_cap);
    if (status != NQ_ALLOC_OK || !nq_str_size(value.len)) return NQ_ALLOC_SIZE;
    if (next_cap != items->cap) {
        NQStr* next = (NQStr*)nq_try_realloc(items->data, (size_t)next_cap * sizeof(NQStr), &status);
        if (status != NQ_ALLOC_OK) return status;
        items->data = next;
        items->cap = next_cap;
    }
    items->data[items->len] = value;
    items->len += 1;
    return NQ_ALLOC_OK;
}

NQUnit nq_list__str_push(NQ_List__str* items, NQStr value) {
    NQAllocStatus status = nq_try_list_str_push(items, value);
    if (status != NQ_ALLOC_OK) nq_alloc_fail(status);
    return NQ_UNIT;
}

int32_t nq_list__str_len(const NQ_List__str* items) {
    return items->len;
}

NQ_Option__str nq_list__str_get(const NQ_List__str* items, int32_t index) {
    if (index < 0 || index >= items->len) {
        return (NQ_Option__str){
            .tag = NQ_Option__str_Tag_None,
            .data.None = NQ_UNIT,
        };
    }
    return (NQ_Option__str){
        .tag = NQ_Option__str_Tag_Some,
        .data.Some = { ._0 = nq_str_clone(items->data[index]) },
    };
}

void nq_list__str_drop(NQ_List__str* items) {
    int32_t index = 0;
    if (items == NULL) {
        return;
    }
    while (index < items->len) {
        nq_str_drop(&items->data[index]);
        index += 1;
    }
    free(items->data);
    items->data = NULL;
    items->len = 0;
    items->cap = 0;
}

int32_t nq_str_len(NQStr text) {
    if (!nq_str_size(text.len)) nq_size_fail();
    return (int32_t)text.len;
}

NQStr nq_str_concat(NQStr left, NQStr right) {
    size_t len, size;
    NQStr result;
    NQAllocStatus status;
    char* buffer;
    if (!nq_str_size(left.len) || !nq_str_size(right.len) ||
        !nq_size_add((size_t)left.len, (size_t)right.len, nq_str_limit(), &len) ||
        !nq_size_add(len, 1, nq_allocation_limit(), &size) ||
        sizeof(NQStrOwner) > nq_allocation_limit()) nq_size_fail();
    buffer = (char*)nq_realloc(NULL, size);
    if (left.len != 0) memcpy(buffer, left.data, (size_t)left.len);
    if (right.len != 0) memcpy(buffer + left.len, right.data, (size_t)right.len);
    buffer[len] = '\0';
    status = nq_try_str_take(buffer, len, &result);
    if (status != NQ_ALLOC_OK) nq_alloc_fail(status);
    return result;
}

typedef struct {
    unsigned char* data;
    size_t len;
    size_t cap;
} NQByteBuffer;

static NQAllocStatus nq_buffer_reserve(NQByteBuffer* buffer, size_t extra, size_t limit) {
    size_t needed;
    size_t next_cap;
    unsigned char* next;
    NQAllocStatus status;
    if (limit > nq_allocation_limit()) limit = nq_allocation_limit();
    if (buffer->cap > limit || buffer->len > buffer->cap ||
        !nq_size_add(buffer->len, extra, limit, &needed)) return NQ_ALLOC_SIZE;
    if (needed <= buffer->cap) {
        return NQ_ALLOC_OK;
    }
    next_cap = nq_growth(buffer->cap, needed, limit, 4096);
    next = (unsigned char*)nq_try_realloc(buffer->data, next_cap, &status);
    if (status != NQ_ALLOC_OK) return status;
    buffer->data = next;
    buffer->cap = next_cap;
    return NQ_ALLOC_OK;
}

static NQAllocStatus nq_buffer_push(NQByteBuffer* buffer, unsigned char value, size_t limit) {
    NQAllocStatus status = nq_buffer_reserve(buffer, 1, limit);
    if (status != NQ_ALLOC_OK) return status;
    buffer->data[buffer->len] = value;
    buffer->len += 1;
    return NQ_ALLOC_OK;
}

static NQ_Result__bytes__io_err nq_read_stream(FILE* stream, const char* operation, const NQStr* path, size_t limit) {
    NQByteBuffer buffer = {0};
    unsigned char chunk[8192];
    while (true) {
        errno = 0;
        size_t count = fread(chunk, 1, sizeof(chunk), stream);
        if (count > 0) {
            NQAllocStatus status = nq_buffer_reserve(&buffer, count, limit);
            if (status != NQ_ALLOC_OK) {
                free(buffer.data);
                return nq_bytes_err(nq_allocation_io_err(operation, status));
            }
            memcpy(buffer.data + buffer.len, chunk, count);
            buffer.len += count;
        }
        if (count < sizeof(chunk)) {
            if (ferror(stream)) {
                int error_code = errno == 0 ? EIO : errno;
                free(buffer.data);
                return nq_bytes_err(nq_errno_io_err(operation, path, NULL, error_code));
            }
            break;
        }
    }
    return nq_bytes_ok((NQBytes){
        .data = buffer.data,
        .len = (int64_t)buffer.len,
        .cap = (int64_t)buffer.cap,
    });
}

static NQ_Result__unit__io_err nq_write_stream(FILE* stream, const unsigned char* data, size_t len, const char* operation, const NQStr* path) {
    size_t offset = 0;
#ifndef _WIN32
    void (*previous_sigpipe)(int) = signal(SIGPIPE, SIG_IGN);
#endif
    while (offset < len) {
        errno = 0;
        size_t count = fwrite(data + offset, 1, len - offset, stream);
        if (ferror(stream) || count == 0) {
            int error_code = errno == 0 ? EIO : errno;
#ifndef _WIN32
            if (previous_sigpipe != SIG_ERR) {
                signal(SIGPIPE, previous_sigpipe);
            }
#endif
            return nq_unit_err(nq_errno_io_err(operation, path, NULL, error_code));
        }
        offset += count;
    }
#ifndef _WIN32
    if (previous_sigpipe != SIG_ERR) {
        signal(SIGPIPE, previous_sigpipe);
    }
#endif
    return nq_unit_ok();
}

static NQ_Result__str__io_err nq_bytes_result_into_str(NQ_Result__bytes__io_err bytes_result, const char* operation) {
    NQBytes bytes;
    char* storage;
    size_t size;
    NQStr text;
    NQAllocStatus status;
    if (bytes_result.tag == NQ_Result__bytes__io_err_Tag_Err) {
        return nq_str_err(bytes_result.data.Err._0);
    }
    bytes = bytes_result.data.Ok._0;
    if (!nq_str_size(bytes.len) ||
        !nq_size_add((size_t)bytes.len, 1, nq_allocation_limit(), &size) ||
        sizeof(NQStrOwner) > nq_allocation_limit()) {
        free(bytes.data);
        return nq_str_err(nq_allocation_io_err(operation, NQ_ALLOC_SIZE));
    }
    storage = (char*)nq_try_realloc(bytes.data, size, &status);
    if (status != NQ_ALLOC_OK) {
        free(bytes.data);
        return nq_str_err(nq_allocation_io_err(operation, status));
    }
    storage[bytes.len] = '\0';
    status = nq_try_str_take(storage, (size_t)bytes.len, &text);
    if (status != NQ_ALLOC_OK) return nq_str_err(nq_allocation_io_err(operation, status));
    return nq_str_ok(text);
}

NQ_Result__bytes__io_err nq_stdin_read_bytes(void) {
    return nq_read_stream(stdin, "stdin_read_bytes", NULL, nq_bytes_limit());
}

NQ_Result__str__io_err nq_stdin_read(void) {
    return nq_bytes_result_into_str(nq_read_stream(stdin, "stdin_read", NULL, nq_str_limit()), "stdin_read");
}

NQ_Result__option__str__io_err nq_stdin_read_line(void) {
    NQByteBuffer buffer = {0};
    NQAllocStatus status;
    NQStr text;
    size_t terminated_limit;
    while (true) {
        errno = 0;
        int value = fgetc(stdin);
        if (value == EOF) {
            if (ferror(stdin)) {
                int error_code = errno == 0 ? EIO : errno;
                free(buffer.data);
                return nq_option_str_err(nq_errno_io_err("stdin_read_line", NULL, NULL, error_code));
            }
            if (buffer.len == 0) {
                free(buffer.data);
                return nq_option_str_ok((NQ_Option__str){
                    .tag = NQ_Option__str_Tag_None,
                    .data.None = NQ_UNIT,
                });
            }
            break;
        }
        if (value == '\n') {
            break;
        }
        status = nq_buffer_push(&buffer, (unsigned char)value, nq_str_limit());
        if (status != NQ_ALLOC_OK) {
            free(buffer.data);
            return nq_option_str_err(nq_allocation_io_err("stdin_read_line", status));
        }
    }
    if (!nq_size_add(nq_str_limit(), 1, SIZE_MAX, &terminated_limit)) terminated_limit = SIZE_MAX;
    status = nq_buffer_reserve(&buffer, 1, terminated_limit);
    if (status != NQ_ALLOC_OK) {
        free(buffer.data);
        return nq_option_str_err(nq_allocation_io_err("stdin_read_line", status));
    }
    buffer.data[buffer.len] = '\0';
    status = nq_try_str_take((char*)buffer.data, buffer.len, &text);
    if (status != NQ_ALLOC_OK) return nq_option_str_err(nq_allocation_io_err("stdin_read_line", status));
    return nq_option_str_ok((NQ_Option__str){
        .tag = NQ_Option__str_Tag_Some,
        .data.Some = { ._0 = text },
    });
}

NQ_Result__unit__io_err nq_stdout_write(NQStr data) {
    if (!nq_str_size(data.len)) return nq_unit_err(nq_allocation_io_err("stdout_write", NQ_ALLOC_SIZE));
    if (!nq_str_storage_is_valid(data)) {
        return nq_unit_err(nq_invalid_input_io_err("stdout_write", NULL, NULL, "invalid string storage"));
    }
    return nq_write_stream(stdout, (const unsigned char*)data.data, (size_t)data.len, "stdout_write", NULL);
}

NQ_Result__unit__io_err nq_stdout_write_bytes(const NQBytes* data) {
    if (data != NULL && (data->len < 0 || (uintmax_t)data->len > nq_bytes_limit()))
        return nq_unit_err(nq_allocation_io_err("stdout_write_bytes", NQ_ALLOC_SIZE));
    if (data == NULL || data->len < 0 || (data->len > 0 && data->data == NULL)) {
        return nq_unit_err(nq_invalid_input_io_err("stdout_write_bytes", NULL, NULL, "invalid bytes storage"));
    }
    return nq_write_stream(stdout, data->data, (size_t)data->len, "stdout_write_bytes", NULL);
}

NQ_Result__unit__io_err nq_stderr_write(NQStr data) {
    if (!nq_str_size(data.len)) return nq_unit_err(nq_allocation_io_err("stderr_write", NQ_ALLOC_SIZE));
    if (!nq_str_storage_is_valid(data)) {
        return nq_unit_err(nq_invalid_input_io_err("stderr_write", NULL, NULL, "invalid string storage"));
    }
    return nq_write_stream(stderr, (const unsigned char*)data.data, (size_t)data.len, "stderr_write", NULL);
}

NQ_Result__unit__io_err nq_stderr_write_bytes(const NQBytes* data) {
    if (data != NULL && (data->len < 0 || (uintmax_t)data->len > nq_bytes_limit()))
        return nq_unit_err(nq_allocation_io_err("stderr_write_bytes", NQ_ALLOC_SIZE));
    if (data == NULL || data->len < 0 || (data->len > 0 && data->data == NULL)) {
        return nq_unit_err(nq_invalid_input_io_err("stderr_write_bytes", NULL, NULL, "invalid bytes storage"));
    }
    return nq_write_stream(stderr, data->data, (size_t)data->len, "stderr_write_bytes", NULL);
}

NQ_Result__unit__io_err nq_stdout_flush(void) {
#ifndef _WIN32
    void (*previous_sigpipe)(int) = signal(SIGPIPE, SIG_IGN);
#endif
    errno = 0;
    if (fflush(stdout) != 0) {
        int error_code = errno == 0 ? EIO : errno;
#ifndef _WIN32
        if (previous_sigpipe != SIG_ERR) {
            signal(SIGPIPE, previous_sigpipe);
        }
#endif
        return nq_unit_err(nq_errno_io_err("stdout_flush", NULL, NULL, error_code));
    }
#ifndef _WIN32
    if (previous_sigpipe != SIG_ERR) {
        signal(SIGPIPE, previous_sigpipe);
    }
#endif
    return nq_unit_ok();
}

NQ_Result__unit__io_err nq_stderr_flush(void) {
#ifndef _WIN32
    void (*previous_sigpipe)(int) = signal(SIGPIPE, SIG_IGN);
#endif
    errno = 0;
    if (fflush(stderr) != 0) {
        int error_code = errno == 0 ? EIO : errno;
#ifndef _WIN32
        if (previous_sigpipe != SIG_ERR) {
            signal(SIGPIPE, previous_sigpipe);
        }
#endif
        return nq_unit_err(nq_errno_io_err("stderr_flush", NULL, NULL, error_code));
    }
#ifndef _WIN32
    if (previous_sigpipe != SIG_ERR) {
        signal(SIGPIPE, previous_sigpipe);
    }
#endif
    return nq_unit_ok();
}

static NQ_Result__bytes__io_err nq_read_file_bytes_operation(NQStr path, const char* operation, size_t limit) {
    char* file_name = NULL;
    FILE* handle;
    NQIoErr validation_err;
    NQ_Result__bytes__io_err result;
    if (!nq_os_string(path, operation, &path, NULL, &file_name, &validation_err)) {
        return nq_bytes_err(validation_err);
    }
    handle = fopen(file_name, "rb");
    free(file_name);
    if (handle == NULL) {
        return nq_bytes_err(nq_errno_io_err_with_detail(operation, &path, NULL, errno, "failed to open file"));
    }
    result = nq_read_stream(handle, operation, &path, limit);
    errno = 0;
    if (fclose(handle) != 0 && result.tag == NQ_Result__bytes__io_err_Tag_Ok) {
        nq_bytes_drop(&result.data.Ok._0);
        return nq_bytes_err(nq_errno_io_err(operation, &path, NULL, errno == 0 ? EIO : errno));
    }
    return result;
}

NQ_Result__bytes__io_err nq_read_file_bytes(NQStr path) {
    return nq_read_file_bytes_operation(path, "read_file_bytes", nq_bytes_limit());
}

NQ_Result__str__io_err nq_read_file(NQStr path) {
    return nq_bytes_result_into_str(nq_read_file_bytes_operation(path, "read_file", nq_str_limit()), "read_file");
}

static NQ_Result__unit__io_err nq_write_file_data(NQStr path, const unsigned char* data, size_t len, const char* operation) {
    char* file_name = NULL;
    FILE* handle;
    NQIoErr validation_err;
    NQ_Result__unit__io_err result;
    if (!nq_os_string(path, operation, &path, NULL, &file_name, &validation_err)) {
        return nq_unit_err(validation_err);
    }
    handle = fopen(file_name, "wb");
    free(file_name);
    if (handle == NULL) {
        return nq_unit_err(nq_errno_io_err_with_detail(operation, &path, NULL, errno, "failed to open file for write"));
    }
    result = nq_write_stream(handle, data, len, operation, &path);
    errno = 0;
    if (fclose(handle) != 0 && result.tag == NQ_Result__unit__io_err_Tag_Ok) {
        return nq_unit_err(nq_errno_io_err(operation, &path, NULL, errno == 0 ? EIO : errno));
    }
    return result;
}

NQ_Result__unit__io_err nq_write_file(NQStr path, NQStr text) {
    if (!nq_str_size(text.len)) return nq_unit_err(nq_allocation_io_err("write_file", NQ_ALLOC_SIZE));
    if (!nq_str_storage_is_valid(text)) {
        return nq_unit_err(nq_invalid_input_io_err("write_file", &path, NULL, "invalid string storage"));
    }
    return nq_write_file_data(path, (const unsigned char*)text.data, (size_t)text.len, "write_file");
}

NQ_Result__unit__io_err nq_write_file_bytes(NQStr path, const NQBytes* data) {
    if (data != NULL && (data->len < 0 || (uintmax_t)data->len > nq_bytes_limit()))
        return nq_unit_err(nq_allocation_io_err("write_file_bytes", NQ_ALLOC_SIZE));
    if (data == NULL || data->len < 0 || (data->len > 0 && data->data == NULL)) {
        return nq_unit_err(nq_invalid_input_io_err("write_file_bytes", &path, NULL, "invalid bytes storage"));
    }
    return nq_write_file_data(path, data->data, (size_t)data->len, "write_file_bytes");
}

int32_t nq_arg_count(void) {
    return (int32_t)nq_process_argc;
}

NQ_Option__str nq_arg_get(int32_t index) {
    if (index < 0 || index >= (int32_t)nq_process_argc || nq_process_argv == NULL) {
        return (NQ_Option__str){
            .tag = NQ_Option__str_Tag_None,
            .data.None = NQ_UNIT,
        };
    }
    return (NQ_Option__str){
        .tag = NQ_Option__str_Tag_Some,
        .data.Some = {
            ._0 = nq_str(nq_process_argv[index]),
        },
    };
}

NQ_Result__option__str__io_err nq_env_get(NQStr name) {
    char* name_cstr = NULL;
    const char* value;
    NQIoErr validation_err;
    NQAllocStatus status;
    NQStr text;
    size_t len;
    if (!nq_os_string(name, "env_get", NULL, NULL, &name_cstr, &validation_err)) {
        return nq_option_str_err(validation_err);
    }
    value = getenv(name_cstr);
    free(name_cstr);
    if (value == NULL) {
        return nq_option_str_ok((NQ_Option__str){
            .tag = NQ_Option__str_Tag_None,
            .data.None = NQ_UNIT,
        });
    }
    if (!nq_cstr_length(value, &len)) return nq_option_str_err(nq_allocation_io_err("env_get", NQ_ALLOC_SIZE));
    status = nq_try_str_copy(value, len, &text);
    if (status != NQ_ALLOC_OK) return nq_option_str_err(nq_allocation_io_err("env_get", status));
    return nq_option_str_ok((NQ_Option__str){
        .tag = NQ_Option__str_Tag_Some,
        .data.Some = { ._0 = text },
    });
}

NQ_Result__str__io_err nq_current_dir(void) {
    size_t limit, cap;
    if (!nq_size_add(nq_str_limit(), 1, nq_allocation_limit(), &limit)) limit = nq_allocation_limit();
#ifdef _WIN32
    if (limit > INT_MAX) limit = INT_MAX;
#endif
    cap = limit < 256 ? limit : 256;
    while (true) {
        NQAllocStatus status;
        NQStr text;
        size_t len;
        char* buffer;
        int error_code;
        if (cap == 0) return nq_str_err(nq_allocation_io_err("current_dir", NQ_ALLOC_SIZE));
        buffer = (char*)nq_try_realloc(NULL, cap, &status);
        if (status != NQ_ALLOC_OK) return nq_str_err(nq_allocation_io_err("current_dir", status));
#ifdef _WIN32
        if (_getcwd(buffer, (int)cap) != NULL) {
#else
        if (getcwd(buffer, cap) != NULL) {
#endif
            if (!nq_cstr_length(buffer, &len)) {
                free(buffer);
                return nq_str_err(nq_allocation_io_err("current_dir", NQ_ALLOC_SIZE));
            }
            status = nq_try_str_take(buffer, len, &text);
            if (status != NQ_ALLOC_OK) return nq_str_err(nq_allocation_io_err("current_dir", status));
            return nq_str_ok(text);
        }
        error_code = errno;
        free(buffer);
        if (error_code != ERANGE) return nq_str_err(nq_errno_io_err("current_dir", NULL, NULL, error_code));
        if (cap == limit) return nq_str_err(nq_allocation_io_err("current_dir", NQ_ALLOC_SIZE));
        cap = nq_growth(cap, cap + 1, limit, 256);
    }
}

static int nq_mkdir_single(const char* path) {
#ifdef _WIN32
    return _mkdir(path);
#else
    return mkdir(path, 0777);
#endif
}

static bool nq_cstr_is_directory(const char* path) {
#ifdef _WIN32
    struct _stat value;
    return _stat(path, &value) == 0 && (value.st_mode & _S_IFDIR) != 0;
#else
    struct stat value;
    return stat(path, &value) == 0 && S_ISDIR(value.st_mode);
#endif
}

NQ_Result__unit__io_err nq_create_dir_all(NQStr path) {
    char* value = NULL;
    NQIoErr validation_err;
    size_t index;
    size_t start_index = 0;
    if (path.len == 0) {
        return nq_unit_ok();
    }
    if (!nq_os_string(path, "create_dir_all", &path, NULL, &value, &validation_err)) {
        return nq_unit_err(validation_err);
    }
#ifdef _WIN32
    if (path.len >= 3 && value[1] == ':' && (value[2] == '\\' || value[2] == '/')) {
        start_index = 3;
    } else if (path.len >= 1 && (value[0] == '\\' || value[0] == '/')) {
        start_index = 1;
    }
#else
    if (path.len >= 1 && value[0] == '/') {
        start_index = 1;
    }
#endif
    for (index = start_index; index < (size_t)path.len; index += 1) {
#ifdef _WIN32
        if (value[index] != '\\' && value[index] != '/') {
#else
        if (value[index] != '/') {
#endif
            continue;
        }
        if (index == 0) {
            continue;
        }
        {
            char saved = value[index];
            value[index] = '\0';
            if (strlen(value) > 0 && nq_mkdir_single(value) != 0) {
                int error_code = errno;
                if (error_code != EEXIST || !nq_cstr_is_directory(value)) {
                    value[index] = saved;
                    free(value);
                    return nq_unit_err(nq_errno_io_err("create_dir_all", &path, NULL, error_code == EEXIST ? ENOTDIR : error_code));
                }
            }
            value[index] = saved;
        }
    }
    if (nq_mkdir_single(value) != 0) {
        int error_code = errno;
        if (error_code != EEXIST || !nq_cstr_is_directory(value)) {
            free(value);
            return nq_unit_err(nq_errno_io_err("create_dir_all", &path, NULL, error_code == EEXIST ? ENOTDIR : error_code));
        }
    }
    free(value);
    return nq_unit_ok();
}

NQ_Result__unit__io_err nq_create_dir(NQStr path) {
    char* path_cstr = NULL;
    NQIoErr validation_err;
    if (!nq_os_string(path, "create_dir", &path, NULL, &path_cstr, &validation_err)) {
        return nq_unit_err(validation_err);
    }
    if (nq_mkdir_single(path_cstr) != 0) {
        int error_code = errno;
        free(path_cstr);
        return nq_unit_err(nq_errno_io_err("create_dir", &path, NULL, error_code));
    }
    free(path_cstr);
    return nq_unit_ok();
}

NQ_Result__unit__io_err nq_create_file_new(NQStr path) {
    char* path_cstr = NULL;
    NQIoErr validation_err;
#ifdef _WIN32
    if (!nq_os_string(path, "create_file_new", &path, NULL, &path_cstr, &validation_err)) {
        return nq_unit_err(validation_err);
    }
    free(path_cstr);
    return nq_unit_err(nq_unsupported_io_err("create_file_new", &path));
#else
    int fd;
    if (!nq_os_string(path, "create_file_new", &path, NULL, &path_cstr, &validation_err)) {
        return nq_unit_err(validation_err);
    }
    fd = open(path_cstr, O_WRONLY | O_CREAT | O_EXCL, 0666);
    if (fd < 0) {
        int error_code = errno;
        free(path_cstr);
        return nq_unit_err(nq_errno_io_err("create_file_new", &path, NULL, error_code));
    }
    free(path_cstr);
    if (close(fd) != 0) {
        return nq_unit_err(nq_errno_io_err("create_file_new", &path, NULL, errno));
    }
    return nq_unit_ok();
#endif
}

NQ_Result__path_metadata__io_err nq_path_metadata(NQStr path, bool follow_symlinks) {
    char* path_cstr = NULL;
    NQIoErr validation_err;
#ifdef _WIN32
    if (!nq_os_string(path, "path_metadata", &path, NULL, &path_cstr, &validation_err)) {
        return (NQ_Result__path_metadata__io_err){
            .tag = NQ_Result__path_metadata__io_err_Tag_Err,
            .data.Err = { ._0 = validation_err },
        };
    }
    free(path_cstr);
    return (NQ_Result__path_metadata__io_err){
        .tag = NQ_Result__path_metadata__io_err_Tag_Err,
        .data.Err = { ._0 = nq_unsupported_io_err("path_metadata", &path) },
    };
#else
    struct stat value;
    int64_t modified_ns;
    int status;
    if (!nq_os_string(path, "path_metadata", &path, NULL, &path_cstr, &validation_err)) {
        return (NQ_Result__path_metadata__io_err){
            .tag = NQ_Result__path_metadata__io_err_Tag_Err,
            .data.Err = { ._0 = validation_err },
        };
    }
    status = follow_symlinks ? stat(path_cstr, &value) : lstat(path_cstr, &value);
    if (status != 0) {
        int error_code = errno;
        free(path_cstr);
        return (NQ_Result__path_metadata__io_err){
            .tag = NQ_Result__path_metadata__io_err_Tag_Err,
            .data.Err = { ._0 = nq_errno_io_err("path_metadata", &path, NULL, error_code) },
        };
    }
    if (!nq_timestamp_to_i64_ns(value.st_mtim.tv_sec, value.st_mtim.tv_nsec, &modified_ns)) {
        free(path_cstr);
        return (NQ_Result__path_metadata__io_err){
            .tag = NQ_Result__path_metadata__io_err_Tag_Err,
            .data.Err = { ._0 = nq_invalid_data_io_err(
                "path_metadata",
                &path,
                "modified timestamp is outside the supported i64 nanosecond range"
            ) },
        };
    }
    free(path_cstr);
    return (NQ_Result__path_metadata__io_err){
        .tag = NQ_Result__path_metadata__io_err_Tag_Ok,
        .data.Ok = { ._0 = (NQ_path_metadata){
            .is_file = S_ISREG(value.st_mode),
            .is_directory = S_ISDIR(value.st_mode),
            .is_symlink = S_ISLNK(value.st_mode),
            .size = (int64_t)value.st_size,
            .modified_ns = modified_ns,
            .mode = (int32_t)(value.st_mode & 07777),
        } },
    };
#endif
}

NQ_Result__list__str__io_err nq_read_dir(NQStr path) {
    char* path_cstr = NULL;
    NQIoErr validation_err;
#ifdef _WIN32
    if (!nq_os_string(path, "read_dir", &path, NULL, &path_cstr, &validation_err)) {
        return (NQ_Result__list__str__io_err){
            .tag = NQ_Result__list__str__io_err_Tag_Err,
            .data.Err = { ._0 = validation_err },
        };
    }
    free(path_cstr);
    return (NQ_Result__list__str__io_err){
        .tag = NQ_Result__list__str__io_err_Tag_Err,
        .data.Err = { ._0 = nq_unsupported_io_err("read_dir", &path) },
    };
#else
    DIR* directory;
    NQ_List__str entries = nq_list__str_make();
    if (!nq_os_string(path, "read_dir", &path, NULL, &path_cstr, &validation_err)) {
        return (NQ_Result__list__str__io_err){
            .tag = NQ_Result__list__str__io_err_Tag_Err,
            .data.Err = { ._0 = validation_err },
        };
    }
    directory = opendir(path_cstr);
    free(path_cstr);
    if (directory == NULL) {
        return (NQ_Result__list__str__io_err){
            .tag = NQ_Result__list__str__io_err_Tag_Err,
            .data.Err = { ._0 = nq_errno_io_err("read_dir", &path, NULL, errno) },
        };
    }
    errno = 0;
    while (true) {
        struct dirent* entry = readdir(directory);
        if (entry == NULL) {
            break;
        }
        if ((entry->d_name[0] == '.' && entry->d_name[1] == '\0') ||
            (entry->d_name[0] == '.' && entry->d_name[1] == '.' && entry->d_name[2] == '\0')) {
            continue;
        }
        {
            NQStr name = nq_empty_str();
            size_t len;
            int32_t next_cap;
            NQAllocStatus status = nq_list_capacity(entries.cap, entries.len, 1, sizeof(NQStr), &next_cap);
            if (!nq_cstr_length(entry->d_name, &len)) status = NQ_ALLOC_SIZE;
            if (status == NQ_ALLOC_OK) status = nq_try_str_copy(entry->d_name, len, &name);
            if (status == NQ_ALLOC_OK) status = nq_try_list_str_push(&entries, name);
            if (status != NQ_ALLOC_OK) {
                nq_str_drop(&name);
                closedir(directory);
                nq_list__str_drop(&entries);
                return (NQ_Result__list__str__io_err){
                    .tag = NQ_Result__list__str__io_err_Tag_Err,
                    .data.Err = { ._0 = nq_allocation_io_err("read_dir", status) },
                };
            }
        }
        errno = 0;
    }
    if (errno != 0) {
        int error_code = errno;
        closedir(directory);
        nq_list__str_drop(&entries);
        return (NQ_Result__list__str__io_err){
            .tag = NQ_Result__list__str__io_err_Tag_Err,
            .data.Err = { ._0 = nq_errno_io_err("read_dir", &path, NULL, error_code) },
        };
    }
    if (closedir(directory) != 0) {
        int error_code = errno;
        nq_list__str_drop(&entries);
        return (NQ_Result__list__str__io_err){
            .tag = NQ_Result__list__str__io_err_Tag_Err,
            .data.Err = { ._0 = nq_errno_io_err("read_dir", &path, NULL, error_code) },
        };
    }
    return (NQ_Result__list__str__io_err){
        .tag = NQ_Result__list__str__io_err_Tag_Ok,
        .data.Ok = { ._0 = entries },
    };
#endif
}

NQ_Result__unit__io_err nq_remove_file(NQStr path) {
    char* path_cstr = NULL;
    NQIoErr validation_err;
    if (!nq_os_string(path, "remove_file", &path, NULL, &path_cstr, &validation_err)) {
        return nq_unit_err(validation_err);
    }
#ifdef _WIN32
    if (remove(path_cstr) != 0) {
#else
    if (unlink(path_cstr) != 0) {
#endif
        int error_code = errno;
        free(path_cstr);
        return nq_unit_err(nq_errno_io_err("remove_file", &path, NULL, error_code));
    }
    free(path_cstr);
    return nq_unit_ok();
}

NQ_Result__unit__io_err nq_remove_dir(NQStr path) {
    char* path_cstr = NULL;
    NQIoErr validation_err;
    if (!nq_os_string(path, "remove_dir", &path, NULL, &path_cstr, &validation_err)) {
        return nq_unit_err(validation_err);
    }
#ifdef _WIN32
    if (_rmdir(path_cstr) != 0) {
#else
    if (rmdir(path_cstr) != 0) {
#endif
        int error_code = errno;
        free(path_cstr);
        return nq_unit_err(nq_errno_io_err("remove_dir", &path, NULL, error_code));
    }
    free(path_cstr);
    return nq_unit_ok();
}

NQ_Result__unit__io_err nq_rename_path(NQStr source, NQStr target) {
    char* source_cstr = NULL;
    char* target_cstr = NULL;
    NQIoErr validation_err;
    if (!nq_os_string(source, "rename_path", &source, &target, &source_cstr, &validation_err)) {
        return nq_unit_err(validation_err);
    }
    if (!nq_os_string(target, "rename_path", &source, &target, &target_cstr, &validation_err)) {
        free(source_cstr);
        return nq_unit_err(validation_err);
    }
    if (rename(source_cstr, target_cstr) != 0) {
        int error_code = errno;
        free(source_cstr);
        free(target_cstr);
        return nq_unit_err(nq_errno_io_err("rename_path", &source, &target, error_code));
    }
    free(source_cstr);
    free(target_cstr);
    return nq_unit_ok();
}

static bool nq_temp_template(NQStr directory, NQStr prefix, const char* operation, char** out_template, NQIoErr* out_err) {
    char* directory_cstr = NULL;
    char* prefix_cstr = NULL;
    size_t directory_len;
    size_t prefix_len;
    bool needs_separator;
    char* value;
    size_t len, size;
    NQAllocStatus status;
    if (!nq_os_string(directory, operation, &directory, NULL, &directory_cstr, out_err)) {
        return false;
    }
    if (!nq_os_string(prefix, operation, &directory, NULL, &prefix_cstr, out_err)) {
        free(directory_cstr);
        return false;
    }
    if (strchr(prefix_cstr, '/') != NULL
#ifdef _WIN32
        || strchr(prefix_cstr, '\\') != NULL
#endif
    ) {
        free(directory_cstr);
        free(prefix_cstr);
        *out_err = nq_invalid_input_io_err(operation, &directory, NULL, "temporary prefix must be a single path component");
        return false;
    }
    directory_len = strlen(directory_cstr);
    prefix_len = strlen(prefix_cstr);
    if (directory_len == 0) {
        free(directory_cstr);
        free(prefix_cstr);
        *out_err = nq_invalid_input_io_err(operation, &directory, NULL, "temporary directory must not be empty");
        return false;
    }
    needs_separator = directory_cstr[directory_len - 1] != '/';
    if (!nq_size_add(directory_len, needs_separator ? 1 : 0, nq_str_limit(), &len) ||
        !nq_size_add(len, prefix_len, nq_str_limit(), &len) ||
        !nq_size_add(len, 6, nq_str_limit(), &len) ||
        !nq_size_add(len, 1, nq_allocation_limit(), &size)) {
        free(directory_cstr);
        free(prefix_cstr);
        *out_err = nq_allocation_io_err(operation, NQ_ALLOC_SIZE);
        return false;
    }
    value = (char*)nq_try_realloc(NULL, size, &status);
    if (status != NQ_ALLOC_OK) {
        free(directory_cstr);
        free(prefix_cstr);
        *out_err = nq_allocation_io_err(operation, status);
        return false;
    }
    memcpy(value, directory_cstr, directory_len);
    if (needs_separator) {
        value[directory_len] = '/';
        directory_len += 1;
    }
    memcpy(value + directory_len, prefix_cstr, prefix_len);
    memcpy(value + directory_len + prefix_len, "XXXXXX", 7);
    free(directory_cstr);
    free(prefix_cstr);
    *out_template = value;
    return true;
}

NQ_Result__str__io_err nq_create_temp_file(NQStr directory, NQStr prefix) {
#ifdef _WIN32
    (void)prefix;
    return nq_str_err(nq_unsupported_io_err("create_temp_file", &directory));
#else
    char* path_template = NULL;
    NQIoErr err;
    int fd;
    NQStr result;
    NQAllocStatus status;
    if (!nq_temp_template(directory, prefix, "create_temp_file", &path_template, &err)) {
        return nq_str_err(err);
    }
    /* Reserve the owner before creating the file, so OOM cannot orphan it. */
    status = nq_try_str_take(path_template, strlen(path_template), &result);
    if (status != NQ_ALLOC_OK) return nq_str_err(nq_allocation_io_err("create_temp_file", status));
    fd = mkstemp(path_template);
    if (fd < 0) {
        int error_code = errno;
        nq_str_drop(&result);
        return nq_str_err(nq_errno_io_err("create_temp_file", &directory, NULL, error_code));
    }
    if (fchmod(fd, 0600) != 0) {
        int error_code = errno;
        close(fd);
        unlink(path_template);
        nq_str_drop(&result);
        return nq_str_err(nq_errno_io_err("create_temp_file", &directory, NULL, error_code));
    }
    if (close(fd) != 0) {
        int error_code = errno;
        unlink(path_template);
        nq_str_drop(&result);
        return nq_str_err(nq_errno_io_err("create_temp_file", &directory, NULL, error_code));
    }
    return nq_str_ok(result);
#endif
}

NQ_Result__str__io_err nq_create_temp_dir(NQStr directory, NQStr prefix) {
#ifdef _WIN32
    (void)prefix;
    return nq_str_err(nq_unsupported_io_err("create_temp_dir", &directory));
#else
    char* path_template = NULL;
    NQIoErr err;
    NQStr result;
    NQAllocStatus status;
    if (!nq_temp_template(directory, prefix, "create_temp_dir", &path_template, &err)) {
        return nq_str_err(err);
    }
    status = nq_try_str_take(path_template, strlen(path_template), &result);
    if (status != NQ_ALLOC_OK) return nq_str_err(nq_allocation_io_err("create_temp_dir", status));
    if (mkdtemp(path_template) == NULL) {
        int error_code = errno;
        nq_str_drop(&result);
        return nq_str_err(nq_errno_io_err("create_temp_dir", &directory, NULL, error_code));
    }
    if (chmod(path_template, 0700) != 0) {
        int error_code = errno;
        rmdir(path_template);
        nq_str_drop(&result);
        return nq_str_err(nq_errno_io_err("create_temp_dir", &directory, NULL, error_code));
    }
    return nq_str_ok(result);
#endif
}

NQ_Result__unit__io_err nq_atomic_write_file(NQStr path, const NQBytes* data) {
#ifdef _WIN32
    (void)data;
    return nq_unit_err(nq_unsupported_io_err("atomic_write_file", &path));
#else
    char* target_cstr = NULL;
    char* directory_cstr = NULL;
    char* slash;
    char* path_template;
    size_t directory_len;
    NQIoErr validation_err;
    NQAllocStatus allocation_status;
    size_t template_len, template_size;
    int fd;
    int error_code;
    size_t offset = 0;
    NQStr temp_path;
    if (data != NULL && (data->len < 0 || (uintmax_t)data->len > nq_bytes_limit()))
        return nq_unit_err(nq_allocation_io_err("atomic_write_file", NQ_ALLOC_SIZE));
    if (data == NULL || data->len < 0 || (data->len > 0 && data->data == NULL)) {
        return nq_unit_err(nq_invalid_input_io_err("atomic_write_file", &path, NULL, "invalid bytes storage"));
    }
    if (!nq_os_string(path, "atomic_write_file", &path, NULL, &target_cstr, &validation_err)) {
        return nq_unit_err(validation_err);
    }
    slash = strrchr(target_cstr, '/');
    if (slash != NULL && slash[1] == '\0') {
        free(target_cstr);
        return nq_unit_err(nq_invalid_input_io_err("atomic_write_file", &path, NULL, "target path must name a file"));
    }
    if (slash == NULL) {
        allocation_status = nq_try_cstr_copy(".", 1, &directory_cstr);
    } else if (slash == target_cstr) {
        allocation_status = nq_try_cstr_copy("/", 1, &directory_cstr);
    } else {
        allocation_status = nq_try_cstr_copy(target_cstr, (size_t)(slash - target_cstr), &directory_cstr);
    }
    if (allocation_status != NQ_ALLOC_OK) {
        free(target_cstr);
        return nq_unit_err(nq_allocation_io_err("atomic_write_file", allocation_status));
    }
    directory_len = strlen(directory_cstr);
    if (!nq_size_add(directory_len, directory_len == 1 && directory_cstr[0] == '/' ? 0 : 1,
                     nq_str_limit(), &template_len) ||
        !nq_size_add(template_len, 17, nq_str_limit(), &template_len) ||
        !nq_size_add(template_len, 1, nq_allocation_limit(), &template_size)) {
        free(directory_cstr);
        free(target_cstr);
        return nq_unit_err(nq_allocation_io_err("atomic_write_file", NQ_ALLOC_SIZE));
    }
    path_template = (char*)nq_try_realloc(NULL, template_size, &allocation_status);
    if (allocation_status != NQ_ALLOC_OK) {
        free(directory_cstr);
        free(target_cstr);
        return nq_unit_err(nq_allocation_io_err("atomic_write_file", allocation_status));
    }
    memcpy(path_template, directory_cstr, directory_len);
    if (!(directory_len == 1 && directory_cstr[0] == '/')) {
        path_template[directory_len] = '/';
        directory_len += 1;
    }
    memcpy(path_template + directory_len, ".nq-atomic-XXXXXX", 18);
    free(directory_cstr);
    fd = mkstemp(path_template);
    if (fd < 0) {
        error_code = errno;
        free(path_template);
        free(target_cstr);
        return nq_unit_err(nq_errno_io_err("atomic_write_file", &path, NULL, error_code));
    }
    temp_path = (NQStr){ .data = path_template, .len = (intptr_t)strlen(path_template), .owner = NULL };
    while (offset < (size_t)data->len) {
        ssize_t count = write(fd, data->data + offset, (size_t)data->len - offset);
        if (count < 0 && errno == EINTR) {
            continue;
        }
        if (count <= 0) {
            NQIoErr write_err;
            error_code = count == 0 ? EIO : errno;
            write_err = nq_errno_io_err("atomic_write_file", &path, &temp_path, error_code);
            close(fd);
            unlink(path_template);
            free(path_template);
            free(target_cstr);
            return nq_unit_err(write_err);
        }
        offset += (size_t)count;
    }
    if (close(fd) != 0) {
        NQIoErr close_err;
        error_code = errno;
        close_err = nq_errno_io_err("atomic_write_file", &path, &temp_path, error_code);
        unlink(path_template);
        free(path_template);
        free(target_cstr);
        return nq_unit_err(close_err);
    }
    if (rename(path_template, target_cstr) != 0) {
        NQIoErr rename_err;
        error_code = errno;
        rename_err = nq_errno_io_err("atomic_write_file", &path, &temp_path, error_code);
        unlink(path_template);
        free(path_template);
        free(target_cstr);
        return nq_unit_err(rename_err);
    }
    free(path_template);
    free(target_cstr);
    return nq_unit_ok();
#endif
}

static bool nq_try_read_text_file(const char* path, NQStr* out_text, NQIoErr* out_err) {
    size_t len;
    NQ_Result__str__io_err result;
    if (!nq_cstr_length(path, &len)) {
        *out_err = nq_allocation_io_err("run_process", NQ_ALLOC_SIZE);
        return false;
    }
    result = nq_bytes_result_into_str(nq_read_file_bytes_operation(
        (NQStr){path, (intptr_t)len, NULL}, "run_process", nq_str_limit()), "run_process");
    if (result.tag == NQ_Result__str__io_err_Tag_Ok) {
        *out_text = result.data.Ok._0;
        return true;
    }
    *out_err = result.data.Err._0;
    return false;
}

#ifdef _WIN32
static char* nq_quote_windows_arg(const char* arg, NQAllocStatus* status) {
    size_t len, doubled, size;
    *status = NQ_ALLOC_OK;
    if (!nq_cstr_length(arg, &len)) { *status = NQ_ALLOC_SIZE; return NULL; }
    bool needs_quotes = arg[0] == '\0';
    const char* cursor = arg;
    while (*cursor != '\0') {
        if (*cursor == ' ' || *cursor == '\t' || *cursor == '"') {
            needs_quotes = true;
        }
        cursor += 1;
    }
    if (!needs_quotes) {
        char* copy = NULL;
        *status = nq_try_cstr_copy(arg, len, &copy);
        return copy;
    }

    {
        char* out;
        size_t out_index = 0;
        size_t slash_count = 0;
        size_t index = 0;
        if (!nq_size_mul(len, 2, &doubled) || !nq_size_add(doubled, 3, nq_allocation_limit(), &size)) {
            *status = NQ_ALLOC_SIZE;
            return NULL;
        }
        out = (char*)nq_try_realloc(NULL, size, status);
        if (*status != NQ_ALLOC_OK) return NULL;
        out[out_index++] = '"';
        while (arg[index] != '\0') {
            char ch = arg[index];
            if (ch == '\\') {
                slash_count += 1;
            } else if (ch == '"') {
                size_t slash_index = 0;
                while (slash_index < (slash_count * 2) + 1) {
                    out[out_index++] = '\\';
                    slash_index += 1;
                }
                out[out_index++] = '"';
                slash_count = 0;
            } else {
                while (slash_count > 0) {
                    out[out_index++] = '\\';
                    slash_count -= 1;
                }
                out[out_index++] = ch;
            }
            index += 1;
        }
        while (slash_count > 0) {
            out[out_index++] = '\\';
            out[out_index++] = '\\';
            slash_count -= 1;
        }
        out[out_index++] = '"';
        out[out_index] = '\0';
        return out;
    }
}

static char* nq_join_windows_command(const char* program, const NQ_List__str* args, NQAllocStatus* status) {
    char* command = nq_quote_windows_arg(program, status);
    int32_t index = 0;
    if (*status != NQ_ALLOC_OK) return NULL;
    while (index < args->len) {
        char* arg_cstr = NULL;
        char* quoted;
        char* next;
        size_t command_len, quoted_len, size;
        *status = nq_try_cstr_copy(args->data[index].data, (size_t)args->data[index].len, &arg_cstr);
        if (*status != NQ_ALLOC_OK) { free(command); return NULL; }
        quoted = nq_quote_windows_arg(arg_cstr, status);
        free(arg_cstr);
        if (*status != NQ_ALLOC_OK) { free(command); return NULL; }
        command_len = strlen(command);
        quoted_len = strlen(quoted);
        if (!nq_size_add(command_len, quoted_len, nq_allocation_limit(), &size) ||
            !nq_size_add(size, 2, nq_allocation_limit(), &size)) {
            free(command);
            free(quoted);
            *status = NQ_ALLOC_SIZE;
            return NULL;
        }
        next = (char*)nq_try_realloc(command, size, status);
        if (*status != NQ_ALLOC_OK) { free(command); free(quoted); return NULL; }
        command = next;
        command[command_len] = ' ';
        memcpy(command + command_len + 1, quoted, quoted_len + 1);
        free(quoted);
        index += 1;
    }
    return command;
}

static char* nq_make_windows_temp_file(const char* prefix, NQAllocStatus* status) {
    char buffer[MAX_PATH + 1];
    char path[MAX_PATH + 1];
    char* copy = NULL;
    size_t path_len;
    *status = NQ_ALLOC_OK;
    DWORD len = GetTempPathA(MAX_PATH, buffer);
    if (len == 0 || len > MAX_PATH) {
        return NULL;
    }
    if (GetTempFileNameA(buffer, prefix, 0, path) == 0) {
        return NULL;
    }
    if (!nq_cstr_length(path, &path_len)) *status = NQ_ALLOC_SIZE;
    else *status = nq_try_cstr_copy(path, path_len, &copy);
    if (*status != NQ_ALLOC_OK) DeleteFileA(path);
    return copy;
}
#endif

NQ_Result__process_result__io_err nq_run_process(NQStr program, const NQ_List__str* args, NQStr cwd) {
    char* program_cstr = NULL;
    char* cwd_cstr = NULL;
    NQStr stdout_text = nq_empty_str();
    NQStr stderr_text = nq_empty_str();
    NQIoErr io_err;
    NQAllocStatus allocation_status;
    int32_t validation_index = 0;
    int32_t validated_cap;
    size_t argv_count, argv_size;
    if (args != NULL && nq_list_capacity(args->cap, args->len, 0, sizeof(NQStr), &validated_cap) != NQ_ALLOC_OK)
        return nq_process_err(nq_allocation_io_err("run_process", NQ_ALLOC_SIZE));
    if (args == NULL || args->len < 0 || (args->len > 0 && args->data == NULL)) {
        return nq_process_err(nq_invalid_input_io_err("run_process", &program, NULL, "argument list is missing"));
    }
    if (!nq_size_add((size_t)args->len, 2, nq_allocation_limit(), &argv_count) ||
        !nq_size_mul(argv_count, sizeof(char*), &argv_size))
        return nq_process_err(nq_allocation_io_err("run_process", NQ_ALLOC_SIZE));
    if (!nq_os_string(program, "run_process", &program, NULL, &program_cstr, &io_err)) {
        return nq_process_err(io_err);
    }
    if (!nq_os_string(cwd, "run_process", &cwd, NULL, &cwd_cstr, &io_err)) {
        free(program_cstr);
        return nq_process_err(io_err);
    }
    while (validation_index < args->len) {
        if (!nq_str_size(args->data[validation_index].len) ||
            (uintmax_t)args->data[validation_index].len >= nq_allocation_limit()) {
            free(program_cstr);
            free(cwd_cstr);
            return nq_process_err(nq_allocation_io_err("run_process", NQ_ALLOC_SIZE));
        }
        if (!nq_str_storage_is_valid(args->data[validation_index]) || nq_str_has_nul(args->data[validation_index])) {
            free(program_cstr);
            free(cwd_cstr);
            return nq_process_err(nq_invalid_input_io_err("run_process", &program, NULL, "process arguments must have valid storage and may not contain embedded NUL"));
        }
        validation_index += 1;
    }
#ifdef _WIN32
    char* command = nq_join_windows_command(program_cstr, args, &allocation_status);
    char* stdout_path = NULL;
    char* stderr_path = NULL;
    SECURITY_ATTRIBUTES security = {0};
    STARTUPINFOA startup = {0};
    PROCESS_INFORMATION process = {0};
    HANDLE stdout_handle;
    HANDLE stderr_handle;
    DWORD exit_code = 0;
    BOOL created;

    if (allocation_status == NQ_ALLOC_OK) stdout_path = nq_make_windows_temp_file("nqo", &allocation_status);
    if (allocation_status == NQ_ALLOC_OK && stdout_path != NULL) stderr_path = nq_make_windows_temp_file("nqe", &allocation_status);
    if (allocation_status != NQ_ALLOC_OK || stdout_path == NULL || stderr_path == NULL) {
        free(program_cstr);
        free(cwd_cstr);
        free(command);
        if (stdout_path != NULL) DeleteFileA(stdout_path);
        if (stderr_path != NULL) DeleteFileA(stderr_path);
        free(stdout_path);
        free(stderr_path);
        if (allocation_status != NQ_ALLOC_OK) return nq_process_err(nq_allocation_io_err("run_process", allocation_status));
        return nq_process_io_err(10, "failed to allocate temporary output files");
    }

    security.nLength = sizeof(security);
    security.bInheritHandle = TRUE;
    stdout_handle = CreateFileA(stdout_path, GENERIC_WRITE, FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE, &security, CREATE_ALWAYS, FILE_ATTRIBUTE_TEMPORARY, NULL);
    if (stdout_handle == INVALID_HANDLE_VALUE) {
        free(program_cstr);
        free(cwd_cstr);
        free(command);
        DeleteFileA(stdout_path);
        DeleteFileA(stderr_path);
        free(stdout_path);
        free(stderr_path);
        return nq_process_io_err((int32_t)GetLastError(), "failed to open temporary stdout capture");
    }
    stderr_handle = CreateFileA(stderr_path, GENERIC_WRITE, FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE, &security, CREATE_ALWAYS, FILE_ATTRIBUTE_TEMPORARY, NULL);
    if (stderr_handle == INVALID_HANDLE_VALUE) {
        CloseHandle(stdout_handle);
        free(program_cstr);
        free(cwd_cstr);
        free(command);
        DeleteFileA(stdout_path);
        DeleteFileA(stderr_path);
        free(stdout_path);
        free(stderr_path);
        return nq_process_io_err((int32_t)GetLastError(), "failed to open temporary stderr capture");
    }

    startup.cb = sizeof(startup);
    startup.dwFlags = STARTF_USESTDHANDLES;
    startup.hStdInput = GetStdHandle(STD_INPUT_HANDLE);
    startup.hStdOutput = stdout_handle;
    startup.hStdError = stderr_handle;
    created = CreateProcessA(
        NULL,
        command,
        NULL,
        NULL,
        TRUE,
        0,
        NULL,
        cwd_cstr[0] == '\0' ? NULL : cwd_cstr,
        &startup,
        &process
    );
    CloseHandle(stdout_handle);
    CloseHandle(stderr_handle);
    if (!created) {
        int32_t error_code = (int32_t)GetLastError();
        free(program_cstr);
        free(cwd_cstr);
        free(command);
        DeleteFileA(stdout_path);
        DeleteFileA(stderr_path);
        free(stdout_path);
        free(stderr_path);
        return nq_process_io_err(error_code, "failed to start process");
    }

    WaitForSingleObject(process.hProcess, INFINITE);
    GetExitCodeProcess(process.hProcess, &exit_code);
    CloseHandle(process.hProcess);
    CloseHandle(process.hThread);

    if (!nq_try_read_text_file(stdout_path, &stdout_text, &io_err)) {
        free(program_cstr);
        free(cwd_cstr);
        free(command);
        DeleteFileA(stdout_path);
        DeleteFileA(stderr_path);
        free(stdout_path);
        free(stderr_path);
        return (NQ_Result__process_result__io_err){
            .tag = NQ_Result__process_result__io_err_Tag_Err,
            .data.Err = { ._0 = io_err },
        };
    }
    if (!nq_try_read_text_file(stderr_path, &stderr_text, &io_err)) {
        nq_str_drop(&stdout_text);
        free(program_cstr);
        free(cwd_cstr);
        free(command);
        DeleteFileA(stdout_path);
        DeleteFileA(stderr_path);
        free(stdout_path);
        free(stderr_path);
        return (NQ_Result__process_result__io_err){
            .tag = NQ_Result__process_result__io_err_Tag_Err,
            .data.Err = { ._0 = io_err },
        };
    }

    DeleteFileA(stdout_path);
    DeleteFileA(stderr_path);
    free(program_cstr);
    free(cwd_cstr);
    free(command);
    free(stdout_path);
    free(stderr_path);
    return nq_process_ok((int32_t)exit_code, stdout_text, stderr_text);
#else
    char stdout_template[] = "/tmp/nq-stdout-XXXXXX";
    char stderr_template[] = "/tmp/nq-stderr-XXXXXX";
    int stdout_fd = mkstemp(stdout_template);
    int stderr_fd = mkstemp(stderr_template);
    int error_pipe[2] = {-1, -1};
    char** argv = NULL;
    pid_t pid;
    int status = 0;
    ssize_t error_read = 0;
    int child_errno = 0;
    int32_t arg_count = args->len;
    int32_t index = 0;

    if (stdout_fd < 0 || stderr_fd < 0) {
        if (stdout_fd >= 0) {
            close(stdout_fd);
            unlink(stdout_template);
        }
        if (stderr_fd >= 0) {
            close(stderr_fd);
            unlink(stderr_template);
        }
        free(program_cstr);
        free(cwd_cstr);
        return nq_process_io_err(errno, "failed to allocate temporary output files");
    }

    argv = (char**)nq_try_realloc(NULL, argv_size, &allocation_status);
    if (allocation_status != NQ_ALLOC_OK) {
        close(stdout_fd);
        close(stderr_fd);
        unlink(stdout_template);
        unlink(stderr_template);
        free(program_cstr);
        free(cwd_cstr);
        return nq_process_err(nq_allocation_io_err("run_process", allocation_status));
    }
    argv[0] = program_cstr;
    while (index < arg_count) {
        allocation_status = nq_try_cstr_copy(args->data[index].data, (size_t)args->data[index].len, &argv[(size_t)index + 1]);
        if (allocation_status != NQ_ALLOC_OK) {
            while (index > 0) { free(argv[index]); index -= 1; }
            free(argv);
            close(stdout_fd);
            close(stderr_fd);
            unlink(stdout_template);
            unlink(stderr_template);
            free(program_cstr);
            free(cwd_cstr);
            return nq_process_err(nq_allocation_io_err("run_process", allocation_status));
        }
        index += 1;
    }
    argv[(size_t)arg_count + 1] = NULL;

    if (pipe(error_pipe) != 0) {
        index = 0;
        while (index < arg_count) {
            free(argv[index + 1]);
            index += 1;
        }
        free(argv);
        close(stdout_fd);
        close(stderr_fd);
        unlink(stdout_template);
        unlink(stderr_template);
        free(program_cstr);
        free(cwd_cstr);
        return nq_process_io_err(errno, "failed to create process error pipe");
    }
    fcntl(error_pipe[1], F_SETFD, FD_CLOEXEC);

    pid = fork();
    if (pid < 0) {
        close(error_pipe[0]);
        close(error_pipe[1]);
        index = 0;
        while (index < arg_count) {
            free(argv[index + 1]);
            index += 1;
        }
        free(argv);
        close(stdout_fd);
        close(stderr_fd);
        unlink(stdout_template);
        unlink(stderr_template);
        free(program_cstr);
        free(cwd_cstr);
        return nq_process_io_err(errno, "failed to fork process");
    }

    if (pid == 0) {
        close(error_pipe[0]);
        if (cwd_cstr[0] != '\0' && chdir(cwd_cstr) != 0) {
            int err = errno;
            ssize_t ignored = write(error_pipe[1], &err, sizeof(err));
            (void)ignored;
            _exit(127);
        }
        if (dup2(stdout_fd, STDOUT_FILENO) < 0 || dup2(stderr_fd, STDERR_FILENO) < 0) {
            int err = errno;
            ssize_t ignored = write(error_pipe[1], &err, sizeof(err));
            (void)ignored;
            _exit(127);
        }
        close(stdout_fd);
        close(stderr_fd);
        execvp(program_cstr, argv);
        {
            int err = errno;
            ssize_t ignored = write(error_pipe[1], &err, sizeof(err));
            (void)ignored;
        }
        _exit(127);
    }

    close(error_pipe[1]);
    close(stdout_fd);
    close(stderr_fd);
    error_read = read(error_pipe[0], &child_errno, sizeof(child_errno));
    close(error_pipe[0]);
    waitpid(pid, &status, 0);

    index = 0;
    while (index < arg_count) {
        free(argv[index + 1]);
        index += 1;
    }
    free(argv);

    if (error_read > 0) {
        unlink(stdout_template);
        unlink(stderr_template);
        free(program_cstr);
        free(cwd_cstr);
        return nq_process_io_err(child_errno, "failed to start process");
    }

    if (!nq_try_read_text_file(stdout_template, &stdout_text, &io_err)) {
        unlink(stdout_template);
        unlink(stderr_template);
        free(program_cstr);
        free(cwd_cstr);
        return (NQ_Result__process_result__io_err){
            .tag = NQ_Result__process_result__io_err_Tag_Err,
            .data.Err = { ._0 = io_err },
        };
    }
    if (!nq_try_read_text_file(stderr_template, &stderr_text, &io_err)) {
        nq_str_drop(&stdout_text);
        unlink(stdout_template);
        unlink(stderr_template);
        free(program_cstr);
        free(cwd_cstr);
        return (NQ_Result__process_result__io_err){
            .tag = NQ_Result__process_result__io_err_Tag_Err,
            .data.Err = { ._0 = io_err },
        };
    }

    unlink(stdout_template);
    unlink(stderr_template);
    free(program_cstr);
    free(cwd_cstr);
    if (WIFEXITED(status)) {
        return nq_process_ok(WEXITSTATUS(status), stdout_text, stderr_text);
    }
    if (WIFSIGNALED(status)) {
        return nq_process_ok(128 + WTERMSIG(status), stdout_text, stderr_text);
    }
    return nq_process_ok(1, stdout_text, stderr_text);
#endif
}

NQ_Option__i32 nq_str_get(NQStr text, int32_t index) {
    if (!nq_str_size(text.len)) nq_size_fail();
    if (index < 0 || index >= (int32_t)text.len) {
        return (NQ_Option__i32){
            .tag = NQ_Option__i32_Tag_None,
            .data.None = NQ_UNIT,
        };
    }
    return (NQ_Option__i32){
        .tag = NQ_Option__i32_Tag_Some,
        .data.Some = { ._0 = (unsigned char)text.data[index] },
    };
}

NQ_Option__str nq_str_slice(NQStr text, int32_t start, int32_t end) {
    NQStr slice;
    if (!nq_str_size(text.len)) nq_size_fail();
    if (start < 0 || end < start || end > (int32_t)text.len) {
        return (NQ_Option__str){
            .tag = NQ_Option__str_Tag_None,
            .data.None = NQ_UNIT,
        };
    }
    slice = (NQStr){
        .data = start == 0 ? text.data : text.data + start,
        .len = (intptr_t)(end - start),
        .owner = text.owner,
    };
    return (NQ_Option__str){
        .tag = NQ_Option__str_Tag_Some,
        .data.Some = {
            ._0 = nq_str_clone(slice),
        },
    };
}
