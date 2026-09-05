#include "runtime.c"
#include <assert.h>

static void size_error(NQIoErr* err, const char* op) {
    assert(err->code == 0 && err->os_code == 0);
    assert(nq_str_eq(err->text, nq_str("size limit exceeded")));
    assert(nq_str_eq(err->kind, nq_str("invalid_input")));
    assert(nq_str_eq(err->operation, nq_str(op)));
    assert(!err->has_path && !err->has_other_path);
    assert(!err->text.owner && !err->operation.owner && !err->kind.owner);
    assert(err->path.len == 0 && err->other_path.len == 0);
}

int main(int argc, char** argv) {
    if (argc == 2 && strcmp(argv[1], "capture-child") == 0) {
        for (int i = 0; i < 129; i += 1) assert(putchar('a') != EOF);
        return 0;
    }
    char data[130];
    const char* path = "limit-input";
    const char* dir = "limit-dir";
    memset(data, 'a', 129);
    data[129] = '\0';
    for (size_t len = 127; len <= 129; len += 1) {
        FILE* f = fopen(path, "wb");
        assert(f && fwrite(data, 1, len, f) == len && fclose(f) == 0);
        NQ_Result__str__io_err s = nq_read_file(nq_str(path));
        if (len > 128 || len >= nq_allocation_limit()) {
            assert(s.tag == NQ_Result__str__io_err_Tag_Err);
            size_error(&s.data.Err._0, "read_file");
        } else { assert(s.tag == NQ_Result__str__io_err_Tag_Ok && (size_t)s.data.Ok._0.len == len); }
        nq_result__str__io_err_drop(&s);
        NQ_Result__bytes__io_err b = nq_read_file_bytes(nq_str(path));
        if (len > nq_bytes_limit()) {
            assert(b.tag == NQ_Result__bytes__io_err_Tag_Err);
            size_error(&b.data.Err._0, "read_file_bytes");
        } else { assert(b.tag == NQ_Result__bytes__io_err_Tag_Ok && (size_t)b.data.Ok._0.len == len); }
        nq_result__bytes__io_err_drop(&b);
        assert(freopen(path, "rb", stdin) != NULL);
        NQ_Result__option__str__io_err line = nq_stdin_read_line();
        if (len > 128 || len >= nq_allocation_limit()) {
            assert(line.tag == NQ_Result__option__str__io_err_Tag_Err);
            size_error(&line.data.Err._0, "stdin_read_line");
        } else { assert(line.tag == NQ_Result__option__str__io_err_Tag_Ok && (size_t)line.data.Ok._0.data.Some._0.len == len); }
        nq_result__option__str__io_err_drop(&line);
    }
    assert(unlink(path) == 0);
    assert(setenv("NQ_LIMIT_VALUE", data, 1) == 0);
    NQ_Result__option__str__io_err env = nq_env_get(nq_str("NQ_LIMIT_VALUE"));
    assert(env.tag == NQ_Result__option__str__io_err_Tag_Err);
    size_error(&env.data.Err._0, "env_get");
    nq_result__option__str__io_err_drop(&env);
    NQ_Result__str__io_err temp = nq_create_temp_file(nq_str("."), (NQStr){data, 128, NULL});
    assert(temp.tag == NQ_Result__str__io_err_Tag_Err);
    size_error(&temp.data.Err._0, "create_temp_file");
    nq_result__str__io_err_drop(&temp);
    {
        char name[129];
        memset(name, 'p', 120); name[120] = '/'; name[121] = 'f'; name[122] = '\0';
        NQBytes b = {(unsigned char*)"ok", 2, 2};
        NQ_Result__unit__io_err r = nq_atomic_write_file(nq_str(name), &b);
        assert(r.tag == NQ_Result__unit__io_err_Tag_Err);
        size_error(&r.data.Err._0, "atomic_write_file");
        nq_result__unit__io_err_drop(&r);
    }
    assert(mkdir(dir, 0700) == 0 || errno == EEXIST);
    size_t entries = nq_allocation_limit() / sizeof(NQStr) + 1;
    if (entries > 129) entries = 129;
    for (size_t i = 0; i < entries; i += 1) {
        char name[96];
        snprintf(name, sizeof(name), "%s/%zu", dir, i);
        FILE* f = fopen(name, "wb");
        assert(f && fclose(f) == 0);
    }
    NQ_Result__list__str__io_err list = nq_read_dir(nq_str(dir));
    assert(list.tag == NQ_Result__list__str__io_err_Tag_Err);
    size_error(&list.data.Err._0, "read_dir");
    nq_result__list__str__io_err_drop(&list);
    for (size_t i = 0; i < entries; i += 1) {
        char name[96];
        snprintf(name, sizeof(name), "%s/%zu", dir, i);
        assert(unlink(name) == 0);
    }
    assert(rmdir(dir) == 0);
    {
        NQStr args_data[] = {nq_str("capture-child")};
        NQ_List__str args = {args_data, 1, 1};
        NQ_Result__process_result__io_err r = nq_run_process(nq_str(argv[0]), &args, nq_str(""));
        assert(r.tag == NQ_Result__process_result__io_err_Tag_Err);
        size_error(&r.data.Err._0, "run_process");
        nq_result__process_result__io_err_drop(&r);
    }
    {
        NQIoErr err = nq_make_io_err(7, data);
        size_error(&err, "");
        nq_io_err_drop(&err);
    }
    puts("IO limits: file/bytes/line/env/temp/atomic/list/capture/error boundaries passed");
    return 0;
}
