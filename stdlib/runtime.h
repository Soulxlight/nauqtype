#ifndef NAUQ_RUNTIME_H
#define NAUQ_RUNTIME_H

#include <stdbool.h>
#include <stdint.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct {
    unsigned char _unused;
} NQUnit;

typedef struct {
    const char* data;
    intptr_t len;
} NQStr;

typedef struct {
    int32_t code;
    NQStr text;
} NQIoErr;

typedef struct {
    int32_t exit_code;
    NQStr stdout_text;
    NQStr stderr_text;
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

static inline NQStr nq_str(const char* data) {
    return (NQStr){data, (intptr_t)strlen(data)};
}

static inline bool nq_str_eq(NQStr left, NQStr right) {
    if (left.len != right.len) {
        return false;
    }
    return memcmp(left.data, right.data, (size_t)left.len) == 0;
}

void* nq_realloc(void* ptr, size_t size);
void nq_init_process_args(int argc, char** argv);
NQUnit nq_print_line(NQStr text);
NQUnit nq_eprint_line(NQStr text);
NQIoErr nq_make_io_err(int32_t code, const char* text);
NQStr nq_io_err_text(NQIoErr err);
int32_t nq_str_len(NQStr text);
NQStr nq_str_concat(NQStr left, NQStr right);
NQ_Result__str__io_err nq_read_file(NQStr path);
NQ_Result__unit__io_err nq_write_file(NQStr path, NQStr text);
int32_t nq_arg_count(void);
NQ_Option__str nq_arg_get(int32_t index);
NQ_Result__unit__io_err nq_create_dir_all(NQStr path);
NQ_Option__i32 nq_str_get(NQStr text, int32_t index);
NQ_Option__str nq_str_slice(NQStr text, int32_t start, int32_t end);

#endif
