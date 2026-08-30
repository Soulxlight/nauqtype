#ifndef NAUQ_RUNTIME_H
#define NAUQ_RUNTIME_H

#include <stdbool.h>
#include <stdint.h>
#include <stddef.h>
#include <stdlib.h>
#include <string.h>

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

static inline NQStr nq_str(const char* data) {
    return (NQStr){data, (intptr_t)strlen(data), NULL};
}

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
