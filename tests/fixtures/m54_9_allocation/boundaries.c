#include "runtime.c"
#include <assert.h>

static void check_error(NQIoErr err, const char* op, NQAllocStatus status) {
    assert(err.code == (status == NQ_ALLOC_SIZE ? 0 : ENOMEM));
    assert(err.os_code == err.code);
    assert(nq_str_eq(err.text, nq_str(status == NQ_ALLOC_SIZE ? "size limit exceeded" : "out of memory")));
    assert(nq_str_eq(err.kind, nq_str(status == NQ_ALLOC_SIZE ? "invalid_input" : "other")));
    assert(nq_str_eq(err.operation, nq_str(op)));
    assert(!err.has_path && !err.has_other_path && err.path.len == 0 && err.other_path.len == 0);
    assert(!err.text.owner && !err.operation.owner && !err.kind.owner);
    nq_io_err_drop(&err);
}

int main(int argc, char** argv) {
    const char* mode = argc > 1 ? argv[1] : "ok";
    char input[130];
    NQAllocStatus status;
    size_t size;
    int32_t cap;
    memset(input, 'a', sizeof(input));
    input[128] = '\0';
    if (strcmp(mode, "str") == 0) { input[128] = 'a'; input[129] = '\0'; (void)nq_str(input); return 7; }
    if (strcmp(mode, "concat") == 0) { (void)nq_str_concat(nq_str(input), nq_str("x")); return 7; }
    if (strcmp(mode, "nul") == 0) { (void)nq_str_concat(nq_str(input), nq_str("")); return 7; }
    if (strcmp(mode, "product") == 0) { (void)nq_allocation_size(SIZE_MAX, 2); return 7; }
    if (strcmp(mode, "list") == 0) { NQ_List__str list = {NULL, INT32_MAX, INT32_MAX}; nq_list__str_push(&list, nq_str("x")); return 7; }
    if (strcmp(mode, "bytes") == 0) { NQBytes b = {NULL, INT64_MAX, INT64_MAX}; (void)nq_str_from_bytes(&b); return 7; }
    if (strcmp(mode, "view") == 0) { (void)nq_str_slice((NQStr){NULL, INTPTR_MAX, NULL}, 0, 1); return 7; }
    if (strcmp(mode, "refcount") == 0) { NQStrOwner owner = {SIZE_MAX, NULL}; (void)nq_str_clone((NQStr){"x", 1, &owner}); return 7; }
    if (strcmp(mode, "argv") == 0) { nq_init_process_args(129, NULL); return 7; }
    if (strcmp(mode, "oom") == 0) { (void)nq_realloc(NULL, 1); return 7; }
    if (strcmp(mode, "array") == 0) { (void)nq_list__str_from_array(NULL, INT32_MAX); return 7; }
    if (strcmp(mode, "arg-get") == 0) { char* args[] = {input}; input[128] = 'a'; input[129] = '\0'; nq_init_process_args(1, args); (void)nq_arg_get(0); return 7; }
    assert(nq_str_len(nq_str(input)) == 128);
    assert(!nq_size_add(SIZE_MAX, 1, SIZE_MAX, &size));
    assert(!nq_size_add(127, 2, 128, &size));
    assert(nq_size_add(127, 1, 128, &size) && size == 128);
    assert(!nq_size_mul(SIZE_MAX, 2, &size));
    assert(nq_list_capacity(0, 0, SIZE_MAX, 1, &cap) == NQ_ALLOC_SIZE);
    assert(nq_list_capacity(64, 64, 1, 1, &cap) == NQ_ALLOC_OK && cap == 128);
    assert(nq_list_capacity(128, 128, 1, 1, &cap) == NQ_ALLOC_SIZE);
    assert(nq_list_capacity(0, 0, 1, SIZE_MAX, &cap) == NQ_ALLOC_SIZE);
    assert(nq_allocation_size(4, sizeof(NQStr)) == 4 * sizeof(NQStr));
    {
        NQ_List__str list = nq_list__str_make();
        size_t max = nq_allocation_limit() / sizeof(NQStr);
        if (max > 128) max = 128;
        for (size_t i = 0; i < max; i += 1) nq_list__str_push(&list, nq_str("a"));
        assert((size_t)list.len == max && (size_t)list.cap == max);
        NQStr* saved = list.data;
        assert(nq_try_list_str_push(&list, nq_str("a")) == NQ_ALLOC_SIZE);
        assert(list.data == saved && (size_t)list.len == max && (size_t)list.cap == max);
        nq_list__str_drop(&list);
    }
    {
        NQBytes b = nq_bytes_from_str(nq_str(input));
        assert(b.len == 128 && nq_bytes_get(&b, 127).data.Some._0 == 'a');
        assert(nq_bytes_get(&b, 128).tag == NQ_Option__i32_Tag_None);
        nq_bytes_drop(&b);
    }
    {
        NQStr values[] = {nq_str("a"), nq_str("b")};
        NQ_List__str list = nq_list__str_from_array(values, 2);
        NQ_Option__str value = nq_list__str_get(&list, 1);
        assert(value.tag == NQ_Option__str_Tag_Some && nq_str_eq(value.data.Some._0, nq_str("b")));
        nq_option__str_drop(&value);
        nq_list__str_drop(&list);
    }
    {
        NQBytes b = {(unsigned char*)input, 127, 127};
        NQStr text = nq_str_from_bytes(&b);
        NQ_Option__str slice = nq_str_slice(text, 1, 127);
        assert(slice.tag == NQ_Option__str_Tag_Some && slice.data.Some._0.len == 126);
        assert(text.owner->ref_count == 2);
        nq_str_drop(&text);
        assert(nq_str_get(slice.data.Some._0, 125).data.Some._0 == 'a');
        nq_option__str_drop(&slice);
    }
    {
        NQByteBuffer b = {0};
        assert(nq_buffer_reserve(&b, 128, 128) == NQ_ALLOC_OK && b.cap == 128);
        b.len = 128;
        b.data[0] = 'x';
        unsigned char* saved = b.data;
        assert(nq_buffer_reserve(&b, 1, 128) == NQ_ALLOC_SIZE);
        assert(b.data == saved && b.len == 128 && b.cap == 128 && b.data[0] == 'x');
        free(b.data);
    }
    {
        char* out = NULL;
        NQIoErr err;
        assert(!nq_os_string((NQStr){NULL, INTPTR_MAX, NULL}, "read_file", NULL, NULL, &out, &err));
        check_error(err, "read_file", NQ_ALLOC_SIZE);
        assert(!nq_temp_template(nq_str(input), nq_str("x"), "create_temp_file", &out, &err));
        check_error(err, "create_temp_file", NQ_ALLOC_SIZE);
    }
    {
        NQ_Result__unit__io_err r = nq_stdout_write_bytes(&(NQBytes){NULL, INT64_MAX, INT64_MAX});
        assert(r.tag == NQ_Result__unit__io_err_Tag_Err);
        check_error(r.data.Err._0, "stdout_write_bytes", NQ_ALLOC_SIZE);
    }
    status = NQ_ALLOC_OK;
    assert(nq_try_realloc(NULL, nq_allocation_limit() + 1, &status) == NULL && status == NQ_ALLOC_SIZE);
    puts("boundary checks passed");
    return 0;
}
