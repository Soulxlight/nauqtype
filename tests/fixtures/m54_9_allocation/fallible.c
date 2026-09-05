#include "runtime.c"
#include <assert.h>

static unsigned failures = 0, successes = 0;
static void error(NQIoErr* e, const char* op) {
    assert(e->code == ENOMEM && e->os_code == ENOMEM);
    assert(nq_str_eq(e->text, nq_str("out of memory")));
    assert(nq_str_eq(e->kind, nq_str("other")));
    assert(nq_str_eq(e->operation, nq_str(op)));
    assert(!e->has_path && !e->has_other_path);
    assert(!e->text.owner && !e->kind.owner && !e->operation.owner);
    assert(e->path.len == 0 && e->other_path.len == 0);
    assert(nq_test_allocation_count == NQ_TEST_ALLOC_FAIL_AFTER);
    failures += 1;
}
static void str_result(NQ_Result__str__io_err r, const char* op, bool file, bool dir) {
    if (r.tag == NQ_Result__str__io_err_Tag_Err) error(&r.data.Err._0, op);
    else {
        successes += 1;
        if (file) assert(unlink(r.data.Ok._0.data) == 0);
        if (dir) assert(rmdir(r.data.Ok._0.data) == 0);
    }
    nq_result__str__io_err_drop(&r);
}
static void option_result(NQ_Result__option__str__io_err r, const char* op) {
    if (r.tag == NQ_Result__option__str__io_err_Tag_Err) error(&r.data.Err._0, op);
    else { assert(r.data.Ok._0.tag == NQ_Option__str_Tag_Some); successes += 1; }
    nq_result__option__str__io_err_drop(&r);
}

int main(void) {
    const char* input = "io-input";
    const char* directory = "io-dir";
    FILE* f = fopen(input, "wb");
    assert(f != NULL && fwrite("hello\n", 1, 6, f) == 6 && fclose(f) == 0);
    assert(mkdir(directory, 0700) == 0 || errno == EEXIST);
    f = fopen("io-dir/entry", "wb");
    assert(f != NULL && fclose(f) == 0);
    assert(setenv("NQ_NATIVE_PROBE", "value", 1) == 0);
    for (unsigned budget = 0; budget <= 24; budget += 1) {
        for (unsigned which = 0; which < 13; which += 1) {
            nq_test_allocation_count = NQ_TEST_ALLOC_FAIL_AFTER - budget;
            switch (which) {
                case 0: str_result(nq_read_file(nq_str(input)), "read_file", false, false); break;
                case 1: {
                    NQ_Result__bytes__io_err r = nq_read_file_bytes(nq_str(input));
                    if (r.tag == NQ_Result__bytes__io_err_Tag_Err) error(&r.data.Err._0, "read_file_bytes");
                    else successes += 1;
                    nq_result__bytes__io_err_drop(&r); break;
                }
                case 2: option_result(nq_env_get(nq_str("NQ_NATIVE_PROBE")), "env_get"); break;
                case 3: str_result(nq_current_dir(), "current_dir", false, false); break;
                case 4: {
                    NQ_Result__list__str__io_err r = nq_read_dir(nq_str(directory));
                    if (r.tag == NQ_Result__list__str__io_err_Tag_Err) error(&r.data.Err._0, "read_dir");
                    else { assert(r.data.Ok._0.len == 1); successes += 1; }
                    nq_result__list__str__io_err_drop(&r); break;
                }
                case 5: str_result(nq_create_temp_file(nq_str(directory), nq_str("probe-")), "create_temp_file", true, false); break;
                case 6: str_result(nq_create_temp_dir(nq_str(directory), nq_str("probe-")), "create_temp_dir", false, true); break;
                case 7: {
                    NQBytes b = {(unsigned char*)"ok", 2, 2};
                    NQ_Result__unit__io_err r = nq_atomic_write_file(nq_str("atomic-output"), &b);
                    if (r.tag == NQ_Result__unit__io_err_Tag_Err) error(&r.data.Err._0, "atomic_write_file");
                    else { successes += 1; assert(unlink("atomic-output") == 0); }
                    nq_result__unit__io_err_drop(&r); break;
                }
                case 8: {
                    NQStr args_data[] = {nq_str("hello")};
                    NQ_List__str args = {args_data, 1, 1};
                    NQ_Result__process_result__io_err r = nq_run_process(nq_str("/bin/echo"), &args, nq_str(""));
                    if (r.tag == NQ_Result__process_result__io_err_Tag_Err) error(&r.data.Err._0, "run_process");
                    else { successes += 1; assert(r.data.Ok._0.exit_code == 0); assert(nq_str_eq(r.data.Ok._0.stdout, nq_str("hello\n"))); }
                    nq_result__process_result__io_err_drop(&r); break;
                }
                case 9: {
                    NQStr path = nq_str("missing");
                    NQIoErr e = nq_errno_io_err_with_detail("read_file", &path, &path, ENOENT, "failed to open file");
                    if (e.code == ENOMEM) error(&e, "read_file");
                    else { assert(e.code == ENOENT && e.has_path && e.has_other_path); successes += 1; }
                    nq_io_err_drop(&e); break;
                }
                case 10:
                    assert(freopen(input, "rb", stdin) != NULL);
                    option_result(nq_stdin_read_line(), "stdin_read_line"); break;
                case 11:
                    assert(freopen(input, "rb", stdin) != NULL);
                    str_result(nq_stdin_read(), "stdin_read", false, false); break;
                case 12: {
                    assert(freopen(input, "rb", stdin) != NULL);
                    NQ_Result__bytes__io_err r = nq_stdin_read_bytes();
                    if (r.tag == NQ_Result__bytes__io_err_Tag_Err) error(&r.data.Err._0, "stdin_read_bytes");
                    else successes += 1;
                    nq_result__bytes__io_err_drop(&r); break;
                }
            }
        }
    }
    assert(unlink(input) == 0);
    assert(unlink("io-dir/entry") == 0);
    assert(rmdir(directory) == 0);
    printf("fallible sweep: %u injected OOM errors, %u successful operations\n", failures, successes);
    assert(failures > 50 && successes > 200);
    return 0;
}
