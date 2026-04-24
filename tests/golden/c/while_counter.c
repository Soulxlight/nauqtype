#include "runtime.h"

int32_t nq_fn_while_counter__main(void);

int32_t nq_fn_while_counter__main(void) {
    int32_t nqv_1_count = 0;
    while (((nqv_1_count) < (5))) {
        nqv_1_count = ((nqv_1_count) + (1));
    }
    return nqv_1_count;
}

int main(int argc, char** argv) {
    nq_init_process_args(argc, argv);
    return nq_fn_while_counter__main();
}
