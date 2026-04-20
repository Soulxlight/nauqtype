#include "runtime.h"

void nq_print_line(NQStr text) {
    fwrite(text.data, 1, (size_t)text.len, stdout);
    fputc('\n', stdout);
}
