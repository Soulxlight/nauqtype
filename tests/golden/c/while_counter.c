#include "runtime.h"

int32_t nq_fn_while_counter__main(void);

int32_t nq_fn_while_counter__main(void) {
    int32_t nqv_1_count = 0;
    while (((nqv_1_count) < (5))) {
        nqv_1_count = ((nqv_1_count) + (1));
    }
    return nqv_1_count;
}

int main(void) {
    return nq_fn_while_counter__main();
}
