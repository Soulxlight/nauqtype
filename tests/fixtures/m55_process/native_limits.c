#define _POSIX_C_SOURCE 200809L
#define NQ_TEST_MAX_SEQUENCE_LENGTH 128
#define NQ_TEST_MAX_ALLOCATION_BYTES 1024
#include <assert.h>
#include "../../../stdlib/runtime.c"

int main(int argc, char** argv) {
    (void)argv;
    if (argc > 1) {
        char bytes[129]; memset(bytes, 'x', sizeof(bytes));
        assert(write(1, bytes, sizeof(bytes)) == sizeof(bytes));
        return 0;
    }
    alarm(10);
    extern char** environ;
    char* empty_env[] = {NULL}; environ = empty_env;
    NQStr arg = nq_str("child");
    NQ_List__str args = {&arg, 1, 1}, env = {0};
    NQ_Option__str input = { .tag = NQ_Option__str_Tag_Some, .data.Some._0 = {"", 0, NULL} };
    NQ_Result__process__io_err start = nq_process_start(nq_str("/proc/self/exe"), &args, nq_str("."), &env, input, true, INT32_MAX);
    assert(start.tag == NQ_Result__process__io_err_Tag_Ok);
    NQ_Result__process_outcome__io_err result = nq_process_wait(start.data.Ok._0, (NQ_Option__instant){ .tag = NQ_Option__instant_Tag_None });
    assert(result.tag == NQ_Result__process_outcome__io_err_Tag_Err);
    assert(nq_str_eq(result.data.Err._0.kind, nq_str("invalid_input")));
    nq_result__process_outcome__io_err_drop(&result);
    args.len = args.cap = INT32_MAX;
    start = nq_process_start(nq_str("/proc/self/exe"), &args, nq_str("."), &env, input, true, 0);
    assert(start.tag == NQ_Result__process__io_err_Tag_Err);
    nq_result__process__io_err_drop(&start);
    args.len = args.cap = 1;
    input.data.Some._0 = (NQStr){"invalid", INT32_MAX, NULL};
    start = nq_process_start(nq_str("/proc/self/exe"), &args, nq_str("."), &env, input, true, 0);
    assert(start.tag == NQ_Result__process__io_err_Tag_Err);
    nq_result__process__io_err_drop(&start);
    int status; assert(waitpid(-1, &status, WNOHANG) == -1 && errno == ECHILD);
    puts("native limits ok");
    return 0;
}
