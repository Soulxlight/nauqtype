#include "runtime.h"

int32_t nq_fn_hello__main(void);

int32_t nq_fn_hello__main(void) {
    nq_print_line(nq_str("Hello, Nauqtype!"));
    return 0;
}

int main(void) {
    return nq_fn_hello__main();
}
