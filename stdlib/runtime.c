#include "runtime.h"

#include <stdio.h>
#include <sys/stat.h>

#ifdef _WIN32
#include <direct.h>
#include <errno.h>
#include <windows.h>
#else
#include <dirent.h>
#include <errno.h>
#include <fcntl.h>
#include <limits.h>
#include <signal.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>
#endif

static int nq_process_argc = 0;
static char** nq_process_argv = NULL;

struct NQStrOwner {
    size_t ref_count;
    char* storage;
};

static NQStr nq_owned_str_take(char* storage, intptr_t len) {
    NQStrOwner* owner = (NQStrOwner*)malloc(sizeof(NQStrOwner));
    if (owner == NULL) {
        free(storage);
        fputs("nauqtype runtime: out of memory\n", stderr);
        exit(1);
    }
    owner->ref_count = 1;
    owner->storage = storage;
    return (NQStr){ .data = storage, .len = len, .owner = owner };
}

static NQStr nq_owned_str_copy(const char* data, intptr_t len) {
    char* storage = (char*)malloc((size_t)len + 1);
    if (storage == NULL) {
        fputs("nauqtype runtime: out of memory\n", stderr);
        exit(1);
    }
    memcpy(storage, data, (size_t)len);
    storage[len] = '\0';
    return nq_owned_str_take(storage, len);
}

#ifdef _WIN32
static char* nq_dup_cstr(const char* text) {
    size_t len = strlen(text);
    char* copy = (char*)malloc(len + 1);
    if (copy == NULL) {
        fputs("nauqtype runtime: out of memory\n", stderr);
        exit(1);
    }
    memcpy(copy, text, len + 1);
    return copy;
}
#endif

static char* nq_str_to_cstr(NQStr text) {
    char* copy = (char*)malloc((size_t)text.len + 1);
    if (copy == NULL) {
        fputs("nauqtype runtime: out of memory\n", stderr);
        exit(1);
    }
    memcpy(copy, text.data, (size_t)text.len);
    copy[text.len] = '\0';
    return copy;
}

static const char* nq_io_kind_for_code(int code);
static NQIoErr nq_make_io_err_details(
    int32_t os_code,
    const char* kind,
    const char* operation,
    const NQStr* path,
    const NQStr* other_path,
    const char* detail
);

static NQ_Result__process_result__io_err nq_process_io_err(int32_t code, const char* text) {
    return (NQ_Result__process_result__io_err){
        .tag = NQ_Result__process_result__io_err_Tag_Err,
        .data.Err = { ._0 = nq_make_io_err_details(code, nq_io_kind_for_code(code), "run_process", NULL, NULL, text) },
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

static bool nq_str_has_nul(NQStr text) {
    return text.len > 0 && memchr(text.data, '\0', (size_t)text.len) != NULL;
}

static bool nq_str_storage_is_valid(NQStr text) {
    return text.len >= 0 && (text.len == 0 || text.data != NULL);
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
    size_t operation_len = strlen(actual_operation);
    size_t detail_len = strlen(actual_detail);
    size_t separator_len = operation_len == 0 ? 0 : 2;
    char* message = (char*)malloc(operation_len + separator_len + detail_len + 1);
    NQIoErr err;
    if (message == NULL) {
        fputs("nauqtype runtime: out of memory\n", stderr);
        exit(1);
    }
    if (operation_len > 0) {
        memcpy(message, actual_operation, operation_len);
        memcpy(message + operation_len, ": ", 2);
    }
    memcpy(message + operation_len + separator_len, actual_detail, detail_len);
    message[operation_len + separator_len + detail_len] = '\0';
    err = (NQIoErr){
        .code = os_code,
        .os_code = os_code,
        .text = nq_owned_str_take(message, (intptr_t)(operation_len + separator_len + detail_len)),
        .kind = nq_owned_str_copy(kind, (intptr_t)strlen(kind)),
        .operation = nq_owned_str_copy(actual_operation, (intptr_t)operation_len),
        .path = path == NULL ? nq_empty_str() : nq_owned_str_copy(path->data, path->len),
        .other_path = other_path == NULL ? nq_empty_str() : nq_owned_str_copy(other_path->data, other_path->len),
        .has_path = path != NULL,
        .has_other_path = other_path != NULL,
    };
    return err;
}

static NQIoErr nq_errno_io_err(const char* operation, const NQStr* path, const NQStr* other_path, int error_code) {
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
    const char* system_detail = strerror(error_code);
    size_t context_len = strlen(context);
    size_t system_len = system_detail == NULL ? 0 : strlen(system_detail);
    char* detail = (char*)malloc(context_len + (system_len == 0 ? 0 : 2 + system_len) + 1);
    NQIoErr err;
    if (detail == NULL) {
        fputs("nauqtype runtime: out of memory\n", stderr);
        exit(1);
    }
    memcpy(detail, context, context_len);
    if (system_len > 0) {
        memcpy(detail + context_len, ": ", 2);
        memcpy(detail + context_len + 2, system_detail, system_len);
    }
    detail[context_len + (system_len == 0 ? 0 : 2 + system_len)] = '\0';
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
    const NQStr* safe_path = path != NULL && nq_str_storage_is_valid(*path) ? path : NULL;
    const NQStr* safe_other_path = other_path != NULL && nq_str_storage_is_valid(*other_path) ? other_path : NULL;
    if (!nq_str_storage_is_valid(value)) {
        *out_err = nq_invalid_input_io_err(operation, safe_path, safe_other_path, "invalid string storage");
        return false;
    }
    if (nq_str_has_nul(value)) {
        *out_err = nq_invalid_input_io_err(operation, safe_path, safe_other_path, "embedded NUL is not allowed");
        return false;
    }
    *out = nq_str_to_cstr(value);
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
    void* next = realloc(ptr, size);
    if (next == NULL && size != 0) {
        fputs("nauqtype runtime: out of memory\n", stderr);
        exit(1);
    }
    return next;
}

void nq_init_process_args(int argc, char** argv) {
    nq_process_argc = argc;
    nq_process_argv = argv;
}

NQStr nq_str_clone(NQStr text) {
    if (text.owner != NULL) {
        text.owner->ref_count += 1;
    }
    return text;
}

NQBytes nq_bytes_from_str(NQStr text) {
    NQBytes bytes = { .data = NULL, .len = 0, .cap = 0 };
    if (text.len <= 0) {
        return bytes;
    }
    bytes.data = (unsigned char*)malloc((size_t)text.len);
    if (bytes.data == NULL) {
        fputs("nauqtype runtime: out of memory\n", stderr);
        exit(1);
    }
    memcpy(bytes.data, text.data, (size_t)text.len);
    bytes.len = (int64_t)text.len;
    bytes.cap = (int64_t)text.len;
    return bytes;
}

NQStr nq_str_from_bytes(const NQBytes* bytes) {
    if (bytes == NULL || bytes->len <= 0) {
        return nq_empty_str();
    }
    return nq_owned_str_copy((const char*)bytes->data, (intptr_t)bytes->len);
}

int64_t nq_bytes_len(const NQBytes* bytes) {
    return bytes->len;
}

NQ_Option__i32 nq_bytes_get(const NQBytes* bytes, int64_t index) {
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
    fwrite(text.data, 1, (size_t)text.len, stdout);
    fputc('\n', stdout);
    fflush(stdout);
    return NQ_UNIT;
}

NQUnit nq_eprint_line(NQStr text) {
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
    if (len > 0) {
        items.data = (NQStr*)nq_realloc(NULL, sizeof(NQStr) * (size_t)len);
        memcpy(items.data, values, sizeof(NQStr) * (size_t)len);
        items.len = len;
        items.cap = len;
    }
    return items;
}

NQUnit nq_list__str_push(NQ_List__str* items, NQStr value) {
    if (items->len == items->cap) {
        int32_t next_cap = items->cap == 0 ? 4 : items->cap * 2;
        items->data = (NQStr*)nq_realloc(items->data, sizeof(NQStr) * (size_t)next_cap);
        items->cap = next_cap;
    }
    items->data[items->len] = value;
    items->len += 1;
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
    return (int32_t)text.len;
}

NQStr nq_str_concat(NQStr left, NQStr right) {
    char* buffer = (char*)malloc((size_t)(left.len + right.len) + 1);
    if (buffer == NULL) {
        fputs("nauqtype runtime: out of memory\n", stderr);
        exit(1);
    }
    memcpy(buffer, left.data, (size_t)left.len);
    memcpy(buffer + left.len, right.data, (size_t)right.len);
    buffer[left.len + right.len] = '\0';
    return nq_owned_str_take(buffer, left.len + right.len);
}

typedef struct {
    unsigned char* data;
    size_t len;
    size_t cap;
} NQByteBuffer;

static void nq_buffer_reserve(NQByteBuffer* buffer, size_t needed) {
    size_t next_cap;
    if (needed <= buffer->cap) {
        return;
    }
    next_cap = buffer->cap == 0 ? 4096 : buffer->cap;
    while (next_cap < needed) {
        if (next_cap > SIZE_MAX / 2) {
            next_cap = needed;
            break;
        }
        next_cap *= 2;
    }
    buffer->data = (unsigned char*)nq_realloc(buffer->data, next_cap);
    buffer->cap = next_cap;
}

static void nq_buffer_push(NQByteBuffer* buffer, unsigned char value) {
    nq_buffer_reserve(buffer, buffer->len + 1);
    buffer->data[buffer->len] = value;
    buffer->len += 1;
}

static NQ_Result__bytes__io_err nq_read_stream(FILE* stream, const char* operation, const NQStr* path) {
    NQByteBuffer buffer = {0};
    unsigned char chunk[8192];
    while (true) {
        errno = 0;
        size_t count = fread(chunk, 1, sizeof(chunk), stream);
        if (count > 0) {
            nq_buffer_reserve(&buffer, buffer.len + count);
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
    if (buffer.len > (size_t)INT64_MAX) {
        free(buffer.data);
        return nq_bytes_err(nq_invalid_input_io_err(operation, path, NULL, "input exceeds the supported byte length"));
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

static NQ_Result__str__io_err nq_bytes_result_into_str(NQ_Result__bytes__io_err bytes_result) {
    NQBytes bytes;
    char* storage;
    if (bytes_result.tag == NQ_Result__bytes__io_err_Tag_Err) {
        return nq_str_err(bytes_result.data.Err._0);
    }
    bytes = bytes_result.data.Ok._0;
    storage = (char*)nq_realloc(bytes.data, (size_t)bytes.len + 1);
    storage[bytes.len] = '\0';
    return nq_str_ok(nq_owned_str_take(storage, (intptr_t)bytes.len));
}

NQ_Result__bytes__io_err nq_stdin_read_bytes(void) {
    return nq_read_stream(stdin, "stdin_read_bytes", NULL);
}

NQ_Result__str__io_err nq_stdin_read(void) {
    return nq_bytes_result_into_str(nq_read_stream(stdin, "stdin_read", NULL));
}

NQ_Result__option__str__io_err nq_stdin_read_line(void) {
    NQByteBuffer buffer = {0};
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
        nq_buffer_push(&buffer, (unsigned char)value);
    }
    nq_buffer_reserve(&buffer, buffer.len + 1);
    buffer.data[buffer.len] = '\0';
    return nq_option_str_ok((NQ_Option__str){
        .tag = NQ_Option__str_Tag_Some,
        .data.Some = { ._0 = nq_owned_str_take((char*)buffer.data, (intptr_t)buffer.len) },
    });
}

NQ_Result__unit__io_err nq_stdout_write(NQStr data) {
    if (!nq_str_storage_is_valid(data)) {
        return nq_unit_err(nq_invalid_input_io_err("stdout_write", NULL, NULL, "invalid string storage"));
    }
    return nq_write_stream(stdout, (const unsigned char*)data.data, (size_t)data.len, "stdout_write", NULL);
}

NQ_Result__unit__io_err nq_stdout_write_bytes(const NQBytes* data) {
    if (data == NULL || data->len < 0 || (data->len > 0 && data->data == NULL)) {
        return nq_unit_err(nq_invalid_input_io_err("stdout_write_bytes", NULL, NULL, "invalid bytes storage"));
    }
    return nq_write_stream(stdout, data->data, (size_t)data->len, "stdout_write_bytes", NULL);
}

NQ_Result__unit__io_err nq_stderr_write(NQStr data) {
    if (!nq_str_storage_is_valid(data)) {
        return nq_unit_err(nq_invalid_input_io_err("stderr_write", NULL, NULL, "invalid string storage"));
    }
    return nq_write_stream(stderr, (const unsigned char*)data.data, (size_t)data.len, "stderr_write", NULL);
}

NQ_Result__unit__io_err nq_stderr_write_bytes(const NQBytes* data) {
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

static NQ_Result__bytes__io_err nq_read_file_bytes_operation(NQStr path, const char* operation) {
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
    result = nq_read_stream(handle, operation, &path);
    errno = 0;
    if (fclose(handle) != 0 && result.tag == NQ_Result__bytes__io_err_Tag_Ok) {
        nq_bytes_drop(&result.data.Ok._0);
        return nq_bytes_err(nq_errno_io_err(operation, &path, NULL, errno == 0 ? EIO : errno));
    }
    return result;
}

NQ_Result__bytes__io_err nq_read_file_bytes(NQStr path) {
    return nq_read_file_bytes_operation(path, "read_file_bytes");
}

NQ_Result__str__io_err nq_read_file(NQStr path) {
    return nq_bytes_result_into_str(nq_read_file_bytes_operation(path, "read_file"));
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
    if (!nq_str_storage_is_valid(text)) {
        return nq_unit_err(nq_invalid_input_io_err("write_file", &path, NULL, "invalid string storage"));
    }
    return nq_write_file_data(path, (const unsigned char*)text.data, (size_t)text.len, "write_file");
}

NQ_Result__unit__io_err nq_write_file_bytes(NQStr path, const NQBytes* data) {
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
    return nq_option_str_ok((NQ_Option__str){
        .tag = NQ_Option__str_Tag_Some,
        .data.Some = { ._0 = nq_owned_str_copy(value, (intptr_t)strlen(value)) },
    });
}

NQ_Result__str__io_err nq_current_dir(void) {
#ifdef _WIN32
    size_t cap = 256;
    while (true) {
        char* buffer = (char*)malloc(cap);
        if (buffer == NULL) {
            fputs("nauqtype runtime: out of memory\n", stderr);
            exit(1);
        }
        if (_getcwd(buffer, (int)cap) != NULL) {
            return nq_str_ok(nq_owned_str_take(buffer, (intptr_t)strlen(buffer)));
        }
        free(buffer);
        if (errno != ERANGE || cap > (size_t)INT32_MAX / 2) {
            return nq_str_err(nq_errno_io_err("current_dir", NULL, NULL, errno));
        }
        cap *= 2;
    }
#else
    size_t cap = 256;
    while (true) {
        char* buffer = (char*)malloc(cap);
        if (buffer == NULL) {
            fputs("nauqtype runtime: out of memory\n", stderr);
            exit(1);
        }
        if (getcwd(buffer, cap) != NULL) {
            return nq_str_ok(nq_owned_str_take(buffer, (intptr_t)strlen(buffer)));
        }
        free(buffer);
        if (errno != ERANGE || cap > SIZE_MAX / 2) {
            return nq_str_err(nq_errno_io_err("current_dir", NULL, NULL, errno));
        }
        cap *= 2;
    }
#endif
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
        nq_list__str_push(&entries, nq_owned_str_copy(entry->d_name, (intptr_t)strlen(entry->d_name)));
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
    value = (char*)malloc(directory_len + (needs_separator ? 1 : 0) + prefix_len + 7);
    if (value == NULL) {
        fputs("nauqtype runtime: out of memory\n", stderr);
        exit(1);
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
    if (!nq_temp_template(directory, prefix, "create_temp_file", &path_template, &err)) {
        return nq_str_err(err);
    }
    fd = mkstemp(path_template);
    if (fd < 0) {
        int error_code = errno;
        free(path_template);
        return nq_str_err(nq_errno_io_err("create_temp_file", &directory, NULL, error_code));
    }
    if (fchmod(fd, 0600) != 0) {
        int error_code = errno;
        close(fd);
        unlink(path_template);
        free(path_template);
        return nq_str_err(nq_errno_io_err("create_temp_file", &directory, NULL, error_code));
    }
    if (close(fd) != 0) {
        int error_code = errno;
        unlink(path_template);
        free(path_template);
        return nq_str_err(nq_errno_io_err("create_temp_file", &directory, NULL, error_code));
    }
    return nq_str_ok(nq_owned_str_take(path_template, (intptr_t)strlen(path_template)));
#endif
}

NQ_Result__str__io_err nq_create_temp_dir(NQStr directory, NQStr prefix) {
#ifdef _WIN32
    (void)prefix;
    return nq_str_err(nq_unsupported_io_err("create_temp_dir", &directory));
#else
    char* path_template = NULL;
    NQIoErr err;
    if (!nq_temp_template(directory, prefix, "create_temp_dir", &path_template, &err)) {
        return nq_str_err(err);
    }
    if (mkdtemp(path_template) == NULL) {
        int error_code = errno;
        free(path_template);
        return nq_str_err(nq_errno_io_err("create_temp_dir", &directory, NULL, error_code));
    }
    if (chmod(path_template, 0700) != 0) {
        int error_code = errno;
        rmdir(path_template);
        free(path_template);
        return nq_str_err(nq_errno_io_err("create_temp_dir", &directory, NULL, error_code));
    }
    return nq_str_ok(nq_owned_str_take(path_template, (intptr_t)strlen(path_template)));
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
    int fd;
    int error_code;
    size_t offset = 0;
    NQStr temp_path;
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
        directory_cstr = nq_str_to_cstr(nq_str("."));
    } else if (slash == target_cstr) {
        directory_cstr = nq_str_to_cstr(nq_str("/"));
    } else {
        directory_cstr = (char*)malloc((size_t)(slash - target_cstr) + 1);
        if (directory_cstr == NULL) {
            fputs("nauqtype runtime: out of memory\n", stderr);
            exit(1);
        }
        memcpy(directory_cstr, target_cstr, (size_t)(slash - target_cstr));
        directory_cstr[slash - target_cstr] = '\0';
    }
    directory_len = strlen(directory_cstr);
    path_template = (char*)malloc(directory_len + (directory_len == 1 && directory_cstr[0] == '/' ? 0 : 1) + 18);
    if (path_template == NULL) {
        fputs("nauqtype runtime: out of memory\n", stderr);
        exit(1);
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
    NQ_Result__str__io_err result = nq_read_file((NQStr){
        .data = path,
        .len = (intptr_t)strlen(path),
        .owner = NULL,
    });
    if (result.tag == NQ_Result__str__io_err_Tag_Ok) {
        *out_text = result.data.Ok._0;
        return true;
    }
    *out_err = result.data.Err._0;
    return false;
}

#ifdef _WIN32
static char* nq_quote_windows_arg(const char* arg) {
    bool needs_quotes = arg[0] == '\0';
    const char* cursor = arg;
    while (*cursor != '\0') {
        if (*cursor == ' ' || *cursor == '\t' || *cursor == '"') {
            needs_quotes = true;
        }
        cursor += 1;
    }
    if (!needs_quotes) {
        return nq_dup_cstr(arg);
    }

    {
        size_t len = strlen(arg);
        char* out = (char*)malloc((len * 2) + 3);
        size_t out_index = 0;
        size_t slash_count = 0;
        size_t index = 0;
        if (out == NULL) {
            fputs("nauqtype runtime: out of memory\n", stderr);
            exit(1);
        }
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

static char* nq_join_windows_command(const char* program, const NQ_List__str* args) {
    char* command = nq_quote_windows_arg(program);
    int32_t index = 0;
    while (index < args->len) {
        char* arg_cstr = nq_str_to_cstr(args->data[index]);
        char* quoted = nq_quote_windows_arg(arg_cstr);
        size_t command_len = strlen(command);
        size_t quoted_len = strlen(quoted);
        command = (char*)nq_realloc(command, command_len + quoted_len + 2);
        command[command_len] = ' ';
        memcpy(command + command_len + 1, quoted, quoted_len + 1);
        free(arg_cstr);
        free(quoted);
        index += 1;
    }
    return command;
}

static char* nq_make_windows_temp_file(const char* prefix) {
    char buffer[MAX_PATH + 1];
    char path[MAX_PATH + 1];
    DWORD len = GetTempPathA(MAX_PATH, buffer);
    if (len == 0 || len > MAX_PATH) {
        return NULL;
    }
    if (GetTempFileNameA(buffer, prefix, 0, path) == 0) {
        return NULL;
    }
    return nq_dup_cstr(path);
}
#endif

NQ_Result__process_result__io_err nq_run_process(NQStr program, const NQ_List__str* args, NQStr cwd) {
    char* program_cstr = NULL;
    char* cwd_cstr = NULL;
    NQStr stdout_text = nq_empty_str();
    NQStr stderr_text = nq_empty_str();
    NQIoErr io_err;
    int32_t validation_index = 0;
    if (args == NULL || args->len < 0 || (args->len > 0 && args->data == NULL)) {
        return nq_process_err(nq_invalid_input_io_err("run_process", &program, NULL, "argument list is missing"));
    }
    if (!nq_os_string(program, "run_process", &program, NULL, &program_cstr, &io_err)) {
        return nq_process_err(io_err);
    }
    if (!nq_os_string(cwd, "run_process", &cwd, NULL, &cwd_cstr, &io_err)) {
        free(program_cstr);
        return nq_process_err(io_err);
    }
    while (validation_index < args->len) {
        if (!nq_str_storage_is_valid(args->data[validation_index]) || nq_str_has_nul(args->data[validation_index])) {
            free(program_cstr);
            free(cwd_cstr);
            return nq_process_err(nq_invalid_input_io_err("run_process", &program, NULL, "process arguments must have valid storage and may not contain embedded NUL"));
        }
        validation_index += 1;
    }
#ifdef _WIN32
    char* command = nq_join_windows_command(program_cstr, args);
    char* stdout_path = nq_make_windows_temp_file("nqo");
    char* stderr_path = nq_make_windows_temp_file("nqe");
    SECURITY_ATTRIBUTES security = {0};
    STARTUPINFOA startup = {0};
    PROCESS_INFORMATION process = {0};
    HANDLE stdout_handle;
    HANDLE stderr_handle;
    DWORD exit_code = 0;
    BOOL created;

    if (stdout_path == NULL || stderr_path == NULL) {
        free(program_cstr);
        free(cwd_cstr);
        free(command);
        free(stdout_path);
        free(stderr_path);
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

    argv = (char**)calloc((size_t)arg_count + 2, sizeof(char*));
    if (argv == NULL) {
        close(stdout_fd);
        close(stderr_fd);
        unlink(stdout_template);
        unlink(stderr_template);
        free(program_cstr);
        free(cwd_cstr);
        fputs("nauqtype runtime: out of memory\n", stderr);
        exit(1);
    }
    argv[0] = program_cstr;
    while (index < arg_count) {
        argv[index + 1] = nq_str_to_cstr(args->data[index]);
        index += 1;
    }
    argv[arg_count + 1] = NULL;

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
    if (start < 0 || end < start || end > (int32_t)text.len) {
        return (NQ_Option__str){
            .tag = NQ_Option__str_Tag_None,
            .data.None = NQ_UNIT,
        };
    }
    slice = (NQStr){
        .data = text.data + start,
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
