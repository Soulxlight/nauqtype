#include "runtime.h"

int32_t nq_fn_main() {
    nq_print_line(nq_str("Hello, Nauqtype!"));
    return 0;
}

int main(void) {
    return nq_fn_main();
}
