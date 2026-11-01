#include "runtime.h"

typedef struct NQ_List__i32 NQ_List__i32;

static inline NQ_List__i32 nq_value__list__i32_move(NQ_List__i32* value);
static inline void nq_value__list__i32_drop(NQ_List__i32* value);

typedef struct NQ_List__i32 {
    int32_t* data;
    int32_t len;
    int32_t cap;
} NQ_List__i32;
static inline NQ_List__i32 nq_list__i32_make(void) {
    return (NQ_List__i32){ .data = NULL, .len = 0, .cap = 0 };
}
static inline NQ_List__i32 nq_list__i32_from_array(const int32_t* values, int32_t len) {
    NQ_List__i32 items = nq_list__i32_make();
    int32_t capacity = nq_list_grow_capacity(0, 0, (size_t)len, sizeof(int32_t));
    if (len > 0) {
        items.data = (int32_t*)nq_realloc(NULL, nq_allocation_size((size_t)capacity, sizeof(int32_t)));
        memcpy(items.data, values, nq_allocation_size((size_t)len, sizeof(int32_t)));
        items.len = len;
        items.cap = capacity;
    }
    return items;
}
static inline NQUnit nq_list__i32_push(NQ_List__i32* items, int32_t value) {
    int32_t next_cap = nq_list_grow_capacity(items->cap, items->len, 1, sizeof(int32_t));
    if (next_cap != items->cap) {
        items->data = (int32_t*)nq_realloc(items->data, nq_allocation_size((size_t)next_cap, sizeof(int32_t)));
        items->cap = next_cap;
    }
    items->data[items->len] = value;
    items->len += 1;
    return NQ_UNIT;
}
static inline int32_t nq_list__i32_len(const NQ_List__i32* items) {
    return items->len;
}
static inline NQ_Option__i32 nq_list__i32_get(const NQ_List__i32* items, int32_t index) {
    if (index < 0 || index >= items->len) {
        return (NQ_Option__i32){ .tag = NQ_Option__i32_Tag_None, .data.None = NQ_UNIT };
    }
    return (NQ_Option__i32){ .tag = NQ_Option__i32_Tag_Some, .data.Some = { ._0 = items->data[index] } };
}

static inline NQ_List__i32 nq_value__list__i32_move(NQ_List__i32* value) {
    NQ_List__i32 out = *value;
    memset(value, 0, sizeof(*value));
    return out;
}
static inline void nq_value__list__i32_drop(NQ_List__i32* value) {
    free(value->data);
    memset(value, 0, sizeof(*value));
}

int32_t nq_fn_for_ulist_c_cmain(void);

int32_t nq_fn_for_ulist_c_cmain(void) {
    int32_t nq_return_value_1 = {0};
    NQ_List__i32 nqv_1_numbers = {0};
    int32_t nqv_2_total = {0};
    int32_t nqv_3_value = {0};
    NQ_List__i32 nq_value_1 = nq_list__i32_from_array((int32_t[]){ 5, 7, 11, 19 }, 4);
    nqv_1_numbers = nq_value_1;
    nqv_2_total = 0;
    NQ_List__i32 nq_for_items_2 = nqv_1_numbers;
    for (int32_t nq_for_index_2 = 0; nq_for_index_2 < nq_list__i32_len(&nq_for_items_2); nq_for_index_2 += 1) {
        nqv_3_value = nq_list__i32_get(&nq_for_items_2, nq_for_index_2).data.Some._0;
        int32_t nq_value_3 = nqv_3_value;
        bool nq_value_4 = ((nq_value_3) == (7));
        if (nq_value_4) {
            continue;
        }
        int32_t nq_value_5 = nqv_2_total;
        int32_t nq_value_6 = nqv_3_value;
        int32_t nq_value_7 = nq_i32_add(nq_value_5, nq_value_6);
        nqv_2_total = nq_value_7;
        int32_t nq_value_8 = nqv_2_total;
        bool nq_value_9 = ((nq_value_8) > (20));
        if (nq_value_9) {
            break;
        }
    }
    int32_t nq_value_10 = nqv_2_total;
    nq_return_value_1 = nq_value_10;
    goto nq_function_cleanup_1;
nq_function_cleanup_1: {
    nq_value__list__i32_drop(&nqv_1_numbers);
    return nq_return_value_1;
}
}

int main(int argc, char** argv) {
    nq_init_process_args(argc, argv);
    return nq_fn_for_ulist_c_cmain();
}

