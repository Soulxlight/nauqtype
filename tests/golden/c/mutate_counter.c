#include "runtime.h"

NQUnit nq_fn_mutate_counter__bump(int32_t* nqv_1_counter);
int32_t nq_fn_mutate_counter__main(void);

NQUnit nq_fn_mutate_counter__bump(int32_t* nqv_1_counter) {
    *nqv_1_counter = (((*nqv_1_counter)) + (1));
    return NQ_UNIT;
}

int32_t nq_fn_mutate_counter__main(void) {
    int32_t nqv_2_value = 41;
    nq_fn_mutate_counter__bump(&nqv_2_value);
    return nqv_2_value;
}

int main(void) {
    return nq_fn_mutate_counter__main();
}
