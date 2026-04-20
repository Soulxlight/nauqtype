#ifndef NAUQ_RUNTIME_H
#define NAUQ_RUNTIME_H

#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

typedef struct {
    unsigned char _unused;
} NQUnit;

typedef struct {
    const char* data;
    intptr_t len;
} NQStr;

#define NQ_UNIT ((NQUnit){0})

static inline NQStr nq_str(const char* data) {
    return (NQStr){data, (intptr_t)strlen(data)};
}

static inline bool nq_str_eq(NQStr left, NQStr right) {
    if (left.len != right.len) {
        return false;
    }
    return memcmp(left.data, right.data, (size_t)left.len) == 0;
}

void nq_print_line(NQStr text);

#endif

