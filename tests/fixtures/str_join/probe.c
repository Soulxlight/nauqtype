#include "runtime.c" /* runtime source is selected through the isolated include path */
#include <assert.h>

static NQStr joined(const NQStr* values, int32_t len) {
    NQ_List__str parts = { (NQStr*)values, len, len };
    return nq_str_join(&parts);
}

int main(int argc, char** argv) {
    const char* mode = argc > 1 ? argv[1] : "semantics";
    if (strcmp(mode, "semantics") == 0) {
        NQStr empty = joined(NULL, 0);
        assert(empty.owner != NULL && empty.len == 0 && empty.data[0] == '\0');
        assert(nq_test_allocation_count == 2);
        nq_str_drop(&empty);

        NQStr one_input = nq_str("singleton");
        nq_test_allocation_count = 0;
        NQStr one = joined(&one_input, 1);
        assert(one.owner != NULL && one.data != one_input.data && one.len == 9);
        assert(memcmp(one.data, "singleton", 9) == 0 && one.data[9] == '\0');
        assert(nq_test_allocation_count == 2);
        nq_str_drop(&one);

        NQStr root = nq_str_concat(nq_str("alpha"), nq_str("beta"));
        NQ_Option__str slice = nq_str_slice(root, 1, 5);
        assert(slice.tag == NQ_Option__str_Tag_Some);
        NQStr values[] = { root, slice.data.Some._0, nq_str("!") };
        NQ_List__str parts = { values, 3, 3 };
        NQStr before[3];
        memcpy(before, values, sizeof(values));
        nq_test_allocation_count = 0;
        NQStr result = nq_str_join(&parts);
        assert(nq_test_allocation_count == 2);
        assert(memcmp(before, values, sizeof(values)) == 0);
        assert(result.len == 14 && memcmp(result.data, "alphabetalpha!", 14) == 0);
        assert(result.data[14] == '\0');
        nq_option__str_drop(&slice);
        nq_str_drop(&root);
        assert(memcmp(result.data, "alphabetalpha!", 14) == 0);
        nq_str_drop(&result);

        {
            const char bytes[] = { 'A', '\0', 'B' };
            NQStr nul_parts[] = { { bytes, 3, NULL }, nq_str("Z") };
            NQStr nul = joined(nul_parts, 2);
            assert(nul.len == 4 && memcmp(nul.data, "A\0BZ", 4) == 0);
            assert(nul.data[4] == '\0');
            nq_str_drop(&nul);
        }
        puts("str_join runtime semantics passed");
        return 0;
    }
    if (strcmp(mode, "sequence") == 0) {
        NQStr values[128];
        for (int32_t i = 0; i < 128; ++i) values[i] = nq_str("");
        nq_test_allocation_count = 0;
        NQStr result = joined(values, 128);
        assert(result.len == 0 && nq_test_allocation_count == 2);
        nq_str_drop(&result);
        puts("str_join sequence boundary passed");
        return 0;
    }
    if (strcmp(mode, "sequence-limit") == 0) {
        NQ_List__str parts = { NULL, 129, 129 };
        (void)nq_str_join(&parts);
        return 7;
    }
    if (strcmp(mode, "payload-limit") == 0) {
        char a[65], b[65];
        memset(a, 'a', 64); a[64] = '\0';
        memset(b, 'b', 64); b[64] = '\0';
        NQStr values[] = { { a, 64, NULL }, { b, 64, NULL } };
        (void)joined(values, 2);
        return 7;
    }
    if (strcmp(mode, "oom") == 0) {
        NQStr values[] = { nq_str("a"), nq_str("b") };
        (void)joined(values, 2);
        return 7;
    }
    return 8;
}
