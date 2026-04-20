#include "runtime.h"

typedef enum NQ_Result__bool__str_Tag {
    NQ_Result__bool__str_Tag_Ok,
    NQ_Result__bool__str_Tag_Err,
} NQ_Result__bool__str_Tag;
typedef struct NQ_Result__bool__str {
    NQ_Result__bool__str_Tag tag;
    union {
        struct { bool _0; } Ok;
        struct { NQStr _0; } Err;
    } data;
} NQ_Result__bool__str;

NQ_Result__bool__str nq_fn_parse_flag(NQStr nqv_1_text) {
    if (nq_str_eq(nqv_1_text, nq_str("yes"))) {
        return (NQ_Result__bool__str){ .tag = NQ_Result__bool__str_Tag_Ok, .data.Ok = { ._0 = true } };
    } else {
        return (NQ_Result__bool__str){ .tag = NQ_Result__bool__str_Tag_Err, .data.Err = { ._0 = nq_str("expected yes") } };
    }
}

int32_t nq_fn_main() {
    NQ_Result__bool__str nqv_2_parsed = nq_fn_parse_flag(nq_str("yes"));
    NQ_Result__bool__str nq_tmp_1 = nqv_2_parsed;
    switch (nq_tmp_1.tag) {
        case NQ_Result__bool__str_Tag_Ok: {
            bool nqv_3_value = nq_tmp_1.data.Ok._0;
            if (nqv_3_value) {
                return 0;
            } else {
                return 1;
            }
            break;
        }
        case NQ_Result__bool__str_Tag_Err: {
            return 2;
            break;
        }
    }
}

int main(void) {
    return nq_fn_main();
}
