#ifndef NAUQ_RUNTIME_H
#define NAUQ_RUNTIME_H

#include <stdbool.h>
#include <stdint.h>
#include <stddef.h>
#include <stdlib.h>
#include <string.h>

/* Constant-only operands: these remain strict C11 integer constant expressions.
 * Reconstruct the signed value using only representable casts and signed sums. */
#define NQ_I32_CONST_BITS(x) \
    ((int32_t)((uint32_t)(x) & (uint32_t)INT32_MAX) + \
     (((uint32_t)(x) > (uint32_t)INT32_MAX) ? INT32_MIN : INT32_C(0)))
#define NQ_I64_CONST_BITS(x) \
    ((int64_t)((uint64_t)(x) & (uint64_t)INT64_MAX) + \
     (((uint64_t)(x) > (uint64_t)INT64_MAX) ? INT64_MIN : INT64_C(0)))
#define NQ_I32_CONST_ADD(a, b) NQ_I32_CONST_BITS((uint32_t)(a) + (uint32_t)(b))
#define NQ_I32_CONST_SUB(a, b) NQ_I32_CONST_BITS((uint32_t)(a) - (uint32_t)(b))
#define NQ_I32_CONST_MUL(a, b) NQ_I32_CONST_BITS((uint32_t)((uint64_t)(uint32_t)(a) * (uint64_t)(uint32_t)(b)))
#define NQ_I32_CONST_NEG(a) NQ_I32_CONST_BITS(UINT32_C(0) - (uint32_t)(a))
#define NQ_I64_CONST_ADD(a, b) NQ_I64_CONST_BITS((uint64_t)(a) + (uint64_t)(b))
#define NQ_I64_CONST_SUB(a, b) NQ_I64_CONST_BITS((uint64_t)(a) - (uint64_t)(b))
#define NQ_I64_CONST_MUL(a, b) NQ_I64_CONST_BITS((uint64_t)(a) * (uint64_t)(b))
#define NQ_I64_CONST_NEG(a) NQ_I64_CONST_BITS(UINT64_C(0) - (uint64_t)(a))
/* Invalid evaluated divisions are rejected by the frontend. Guard even the
 * denominator so unreachable invalid expressions never form C division UB. */
#define NQ_I32_CONST_DIV(a, b) \
    ((int32_t)(a) / (((b) == 0 || ((a) == INT32_MIN && (b) == -1)) ? INT32_C(1) : (int32_t)(b)))
#define NQ_I64_CONST_DIV(a, b) \
    ((int64_t)(a) / (((b) == 0 || ((a) == INT64_MIN && (b) == -1)) ? INT64_C(1) : (int64_t)(b)))

_Noreturn void nq_integer_division_fail(bool zero);

static inline int32_t nq_i32_add(int32_t a, int32_t b) { return NQ_I32_CONST_ADD(a, b); }
static inline int32_t nq_i32_sub(int32_t a, int32_t b) { return NQ_I32_CONST_SUB(a, b); }
static inline int32_t nq_i32_mul(int32_t a, int32_t b) { return NQ_I32_CONST_MUL(a, b); }
static inline int32_t nq_i32_neg(int32_t a) { return NQ_I32_CONST_NEG(a); }
static inline int64_t nq_i64_add(int64_t a, int64_t b) { return NQ_I64_CONST_ADD(a, b); }
static inline int64_t nq_i64_sub(int64_t a, int64_t b) { return NQ_I64_CONST_SUB(a, b); }
static inline int64_t nq_i64_mul(int64_t a, int64_t b) { return NQ_I64_CONST_MUL(a, b); }
static inline int64_t nq_i64_neg(int64_t a) { return NQ_I64_CONST_NEG(a); }

static inline int32_t nq_i32_div(int32_t a, int32_t b) {
    if (b == 0 || (a == INT32_MIN && b == -1)) nq_integer_division_fail(b == 0);
    return a / b;
}

static inline int64_t nq_i64_div(int64_t a, int64_t b) {
    if (b == 0 || (a == INT64_MIN && b == -1)) nq_integer_division_fail(b == 0);
    return a / b;
}

/* C emitter support only. Failfast on invalid sizes, before arithmetic.
 * Pass the existing length and increment separately, never len + increment.
 * Returned capacity respects both INT32_MAX and allocation bytes / item_size. */
size_t nq_allocation_size(size_t count, size_t item_size);
int32_t nq_list_grow_capacity(int32_t cap, int32_t len, size_t extra, size_t item_size);

typedef struct {
    unsigned char _unused;
} NQUnit;

typedef struct NQStrOwner NQStrOwner;

typedef struct {
    const char* data;
    intptr_t len;
    NQStrOwner* owner;
} NQStr;

typedef struct {
    unsigned char* data;
    int64_t len;
    int64_t cap;
} NQBytes;

typedef struct {
    int32_t code;
    int32_t os_code;
    NQStr text;
    NQStr kind;
    NQStr operation;
    NQStr path;
    NQStr other_path;
    bool has_path;
    bool has_other_path;
} NQIoErr;

typedef struct {
    bool is_file;
    bool is_directory;
    bool is_symlink;
    int64_t size;
    int64_t modified_ns;
    int32_t mode;
} NQ_path_metadata;

typedef struct {
    int32_t exit_code;
    NQStr stdout;
    NQStr stderr;
} NQ_process_result;

/* Opaque to Nauqtype source; the C fields are runtime ABI, not constructors. */
typedef struct { int64_t _ns; } NQ_duration;
typedef struct { int64_t _ns; } NQ_instant;
typedef struct NQProcessState NQProcessState;
typedef struct { NQProcessState* _state; } NQ_process;

typedef struct {
    int32_t exit_code;
    NQStr stdout;
    NQStr stderr;
    bool timed_out;
    bool cancelled;
} NQ_process_outcome;

#define NQ_UNIT ((NQUnit){0})

typedef enum NQ_Option__i32_Tag {
    NQ_Option__i32_Tag_Some,
    NQ_Option__i32_Tag_None,
} NQ_Option__i32_Tag;

typedef struct NQ_Option__i32 {
    NQ_Option__i32_Tag tag;
    union {
        struct { int32_t _0; } Some;
        NQUnit None;
    } data;
} NQ_Option__i32;

typedef enum NQ_Option__str_Tag {
    NQ_Option__str_Tag_Some,
    NQ_Option__str_Tag_None,
} NQ_Option__str_Tag;

typedef struct NQ_Option__str {
    NQ_Option__str_Tag tag;
    union {
        struct { NQStr _0; } Some;
        NQUnit None;
    } data;
} NQ_Option__str;

typedef enum NQ_Option__duration_Tag {
    NQ_Option__duration_Tag_Some,
    NQ_Option__duration_Tag_None,
} NQ_Option__duration_Tag;
typedef struct NQ_Option__duration {
    NQ_Option__duration_Tag tag;
    union { struct { NQ_duration _0; } Some; NQUnit None; } data;
} NQ_Option__duration;

typedef enum NQ_Option__instant_Tag {
    NQ_Option__instant_Tag_Some,
    NQ_Option__instant_Tag_None,
} NQ_Option__instant_Tag;
typedef struct NQ_Option__instant {
    NQ_Option__instant_Tag tag;
    union { struct { NQ_instant _0; } Some; NQUnit None; } data;
} NQ_Option__instant;

typedef enum NQ_Result__i64__io_err_Tag {
    NQ_Result__i64__io_err_Tag_Ok,
    NQ_Result__i64__io_err_Tag_Err,
} NQ_Result__i64__io_err_Tag;
typedef struct NQ_Result__i64__io_err {
    NQ_Result__i64__io_err_Tag tag;
    union { struct { int64_t _0; } Ok; struct { NQIoErr _0; } Err; } data;
} NQ_Result__i64__io_err;

typedef enum NQ_Result__instant__io_err_Tag {
    NQ_Result__instant__io_err_Tag_Ok,
    NQ_Result__instant__io_err_Tag_Err,
} NQ_Result__instant__io_err_Tag;
typedef struct NQ_Result__instant__io_err {
    NQ_Result__instant__io_err_Tag tag;
    union { struct { NQ_instant _0; } Ok; struct { NQIoErr _0; } Err; } data;
} NQ_Result__instant__io_err;

typedef enum NQ_Result__process__io_err_Tag {
    NQ_Result__process__io_err_Tag_Ok,
    NQ_Result__process__io_err_Tag_Err,
} NQ_Result__process__io_err_Tag;
typedef struct NQ_Result__process__io_err {
    NQ_Result__process__io_err_Tag tag;
    union { struct { NQ_process _0; } Ok; struct { NQIoErr _0; } Err; } data;
} NQ_Result__process__io_err;

typedef enum NQ_Result__process_outcome__io_err_Tag {
    NQ_Result__process_outcome__io_err_Tag_Ok,
    NQ_Result__process_outcome__io_err_Tag_Err,
} NQ_Result__process_outcome__io_err_Tag;
typedef struct NQ_Result__process_outcome__io_err {
    NQ_Result__process_outcome__io_err_Tag tag;
    union { struct { NQ_process_outcome _0; } Ok; struct { NQIoErr _0; } Err; } data;
} NQ_Result__process_outcome__io_err;

typedef enum NQ_Result__str__io_err_Tag {
    NQ_Result__str__io_err_Tag_Ok,
    NQ_Result__str__io_err_Tag_Err,
} NQ_Result__str__io_err_Tag;

typedef struct NQ_Result__str__io_err {
    NQ_Result__str__io_err_Tag tag;
    union {
        struct { NQStr _0; } Ok;
        struct { NQIoErr _0; } Err;
    } data;
} NQ_Result__str__io_err;

typedef enum NQ_Result__unit__io_err_Tag {
    NQ_Result__unit__io_err_Tag_Ok,
    NQ_Result__unit__io_err_Tag_Err,
} NQ_Result__unit__io_err_Tag;

typedef struct NQ_Result__unit__io_err {
    NQ_Result__unit__io_err_Tag tag;
    union {
        struct { NQUnit _0; } Ok;
        struct { NQIoErr _0; } Err;
    } data;
} NQ_Result__unit__io_err;

typedef enum NQ_Result__bytes__io_err_Tag {
    NQ_Result__bytes__io_err_Tag_Ok,
    NQ_Result__bytes__io_err_Tag_Err,
} NQ_Result__bytes__io_err_Tag;

typedef struct NQ_Result__bytes__io_err {
    NQ_Result__bytes__io_err_Tag tag;
    union {
        struct { NQBytes _0; } Ok;
        struct { NQIoErr _0; } Err;
    } data;
} NQ_Result__bytes__io_err;

typedef enum NQ_Result__option__str__io_err_Tag {
    NQ_Result__option__str__io_err_Tag_Ok,
    NQ_Result__option__str__io_err_Tag_Err,
} NQ_Result__option__str__io_err_Tag;

typedef struct NQ_Result__option__str__io_err {
    NQ_Result__option__str__io_err_Tag tag;
    union {
        struct { NQ_Option__str _0; } Ok;
        struct { NQIoErr _0; } Err;
    } data;
} NQ_Result__option__str__io_err;

typedef struct NQ_List__str {
    NQStr* data;
    int32_t len;
    int32_t cap;
} NQ_List__str;

typedef enum NQ_Result__process_result__io_err_Tag {
    NQ_Result__process_result__io_err_Tag_Ok,
    NQ_Result__process_result__io_err_Tag_Err,
} NQ_Result__process_result__io_err_Tag;

typedef struct NQ_Result__process_result__io_err {
    NQ_Result__process_result__io_err_Tag tag;
    union {
        struct { NQ_process_result _0; } Ok;
        struct { NQIoErr _0; } Err;
    } data;
} NQ_Result__process_result__io_err;

typedef enum NQ_Result__path_metadata__io_err_Tag {
    NQ_Result__path_metadata__io_err_Tag_Ok,
    NQ_Result__path_metadata__io_err_Tag_Err,
} NQ_Result__path_metadata__io_err_Tag;

typedef struct NQ_Result__path_metadata__io_err {
    NQ_Result__path_metadata__io_err_Tag tag;
    union {
        struct { NQ_path_metadata _0; } Ok;
        struct { NQIoErr _0; } Err;
    } data;
} NQ_Result__path_metadata__io_err;

typedef enum NQ_Result__list__str__io_err_Tag {
    NQ_Result__list__str__io_err_Tag_Ok,
    NQ_Result__list__str__io_err_Tag_Err,
} NQ_Result__list__str__io_err_Tag;

typedef struct NQ_Result__list__str__io_err {
    NQ_Result__list__str__io_err_Tag tag;
    union {
        struct { NQ_List__str _0; } Ok;
        struct { NQIoErr _0; } Err;
    } data;
} NQ_Result__list__str__io_err;

NQStr nq_str(const char* data);

static inline bool nq_str_eq(NQStr left, NQStr right) {
    if (left.len != right.len) {
        return false;
    }
    return memcmp(left.data, right.data, (size_t)left.len) == 0;
}

void* nq_realloc(void* ptr, size_t size);
void nq_init_process_args(int argc, char** argv);
NQStr nq_str_clone(NQStr text);
void nq_str_drop(NQStr* text);
NQIoErr nq_io_err_clone(NQIoErr err);
void nq_io_err_drop(NQIoErr* err);
NQ_process_result nq_process_result_clone(NQ_process_result value);
void nq_process_result_drop(NQ_process_result* value);
void nq_process_drop(NQ_process* value);
NQ_process_outcome nq_process_outcome_clone(NQ_process_outcome value);
void nq_process_outcome_drop(NQ_process_outcome* value);
NQ_Option__duration nq_option__duration_clone(NQ_Option__duration value);
void nq_option__duration_drop(NQ_Option__duration* value);
NQ_Option__instant nq_option__instant_clone(NQ_Option__instant value);
void nq_option__instant_drop(NQ_Option__instant* value);
NQ_Result__i64__io_err nq_result__i64__io_err_clone(NQ_Result__i64__io_err value);
void nq_result__i64__io_err_drop(NQ_Result__i64__io_err* value);
NQ_Result__instant__io_err nq_result__instant__io_err_clone(NQ_Result__instant__io_err value);
void nq_result__instant__io_err_drop(NQ_Result__instant__io_err* value);
void nq_result__process__io_err_drop(NQ_Result__process__io_err* value);
NQ_Result__process_outcome__io_err nq_result__process_outcome__io_err_clone(NQ_Result__process_outcome__io_err value);
void nq_result__process_outcome__io_err_drop(NQ_Result__process_outcome__io_err* value);
NQ_Option__str nq_option__str_clone(NQ_Option__str value);
void nq_option__str_drop(NQ_Option__str* value);
NQ_Result__str__io_err nq_result__str__io_err_clone(NQ_Result__str__io_err value);
void nq_result__str__io_err_drop(NQ_Result__str__io_err* value);
NQ_Result__unit__io_err nq_result__unit__io_err_clone(NQ_Result__unit__io_err value);
void nq_result__unit__io_err_drop(NQ_Result__unit__io_err* value);
void nq_result__bytes__io_err_drop(NQ_Result__bytes__io_err* value);
NQ_Result__option__str__io_err nq_result__option__str__io_err_clone(NQ_Result__option__str__io_err value);
void nq_result__option__str__io_err_drop(NQ_Result__option__str__io_err* value);
NQ_Result__path_metadata__io_err nq_result__path_metadata__io_err_clone(NQ_Result__path_metadata__io_err value);
void nq_result__path_metadata__io_err_drop(NQ_Result__path_metadata__io_err* value);
void nq_result__list__str__io_err_drop(NQ_Result__list__str__io_err* value);
NQ_Result__process_result__io_err nq_result__process_result__io_err_clone(NQ_Result__process_result__io_err value);
void nq_result__process_result__io_err_drop(NQ_Result__process_result__io_err* value);
NQUnit nq_print_line(NQStr text);
NQUnit nq_eprint_line(NQStr text);
NQIoErr nq_make_io_err(int32_t code, const char* text);
NQStr nq_io_err_text(NQIoErr err);
NQStr nq_io_err_kind(const NQIoErr* err);
NQStr nq_io_err_operation(const NQIoErr* err);
NQ_Option__str nq_io_err_path(const NQIoErr* err);
NQ_Option__str nq_io_err_other_path(const NQIoErr* err);
int32_t nq_io_err_os_code(const NQIoErr* err);
NQ_List__str nq_list__str_make(void);
NQ_List__str nq_list__str_from_array(const NQStr* values, int32_t len);
NQUnit nq_list__str_push(NQ_List__str* items, NQStr value);
int32_t nq_list__str_len(const NQ_List__str* items);
NQ_Option__str nq_list__str_get(const NQ_List__str* items, int32_t index);
void nq_list__str_drop(NQ_List__str* items);
int32_t nq_str_len(NQStr text);
NQStr nq_str_concat(NQStr left, NQStr right);
NQ_Result__str__io_err nq_read_file(NQStr path);
NQ_Result__unit__io_err nq_write_file(NQStr path, NQStr text);
int32_t nq_arg_count(void);
NQ_Option__str nq_arg_get(int32_t index);
NQ_Result__unit__io_err nq_create_dir_all(NQStr path);
NQ_Result__process_result__io_err nq_run_process(NQStr program, const NQ_List__str* args, NQStr cwd);
NQ_Option__duration nq_duration_from_ns(int64_t value);
int64_t nq_duration_as_ns(NQ_duration value);
NQ_Option__duration nq_duration_between(NQ_instant start, NQ_instant end);
NQ_Result__i64__io_err nq_wall_time_ns(void);
NQ_Result__instant__io_err nq_monotonic_now(void);
NQ_Result__instant__io_err nq_deadline_after(NQ_duration delay);
NQ_Result__unit__io_err nq_sleep_for(NQ_duration delay);
NQ_Result__process__io_err nq_process_start(NQStr program, const NQ_List__str* args,
    NQStr cwd, const NQ_List__str* env, NQ_Option__str input, bool capture, int64_t max_output_bytes);
/* Consumes child, including on error. The emitter clears the moved source. */
NQ_Result__process_outcome__io_err nq_process_wait(NQ_process child, NQ_Option__instant deadline);
NQ_Result__unit__io_err nq_process_terminate(NQ_process* child);
NQ_Option__i32 nq_str_get(NQStr text, int32_t index);
NQ_Option__str nq_str_slice(NQStr text, int32_t start, int32_t end);
NQBytes nq_bytes_from_str(NQStr text);
NQStr nq_str_from_bytes(const NQBytes* bytes);
int64_t nq_bytes_len(const NQBytes* bytes);
NQ_Option__i32 nq_bytes_get(const NQBytes* bytes, int64_t index);
void nq_bytes_drop(NQBytes* bytes);
NQ_Result__str__io_err nq_stdin_read(void);
NQ_Result__bytes__io_err nq_stdin_read_bytes(void);
NQ_Result__option__str__io_err nq_stdin_read_line(void);
NQ_Result__unit__io_err nq_stdout_write(NQStr data);
NQ_Result__unit__io_err nq_stdout_write_bytes(const NQBytes* data);
NQ_Result__unit__io_err nq_stderr_write(NQStr data);
NQ_Result__unit__io_err nq_stderr_write_bytes(const NQBytes* data);
NQ_Result__unit__io_err nq_stdout_flush(void);
NQ_Result__unit__io_err nq_stderr_flush(void);
NQ_Result__option__str__io_err nq_env_get(NQStr name);
NQ_Result__str__io_err nq_current_dir(void);
NQ_Result__bytes__io_err nq_read_file_bytes(NQStr path);
NQ_Result__unit__io_err nq_write_file_bytes(NQStr path, const NQBytes* data);
NQ_Result__path_metadata__io_err nq_path_metadata(NQStr path, bool follow_symlinks);
NQ_Result__list__str__io_err nq_read_dir(NQStr path);
NQ_Result__unit__io_err nq_create_dir(NQStr path);
NQ_Result__unit__io_err nq_create_file_new(NQStr path);
NQ_Result__unit__io_err nq_remove_file(NQStr path);
NQ_Result__unit__io_err nq_remove_dir(NQStr path);
NQ_Result__unit__io_err nq_rename_path(NQStr source, NQStr target);
NQ_Result__str__io_err nq_create_temp_file(NQStr directory, NQStr prefix);
NQ_Result__str__io_err nq_create_temp_dir(NQStr directory, NQStr prefix);
NQ_Result__unit__io_err nq_atomic_write_file(NQStr path, const NQBytes* data);

#endif
