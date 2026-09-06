#define _POSIX_C_SOURCE 200809L
#include <assert.h>
#include <stdint.h>
static uintmax_t native_fail_after = UINTMAX_MAX;
#define NQ_TEST_ALLOC_FAIL_AFTER native_fail_after
#include "../../../stdlib/runtime.c"

static int fd_count(void) {
    DIR* dir = opendir("/proc/self/fd"); assert(dir != NULL);
    int count = 0; while (readdir(dir) != NULL) count++;
    assert(closedir(dir) == 0); return count;
}
static void no_child(void) {
    int status; assert(waitpid(-1, &status, WNOHANG) == -1 && errno == ECHILD);
}
static NQ_Option__instant deadline(void) {
    NQ_Result__instant__io_err result = nq_deadline_after((NQ_duration){2000000000});
    assert(result.tag == NQ_Result__instant__io_err_Tag_Ok);
    return (NQ_Option__instant){ .tag = NQ_Option__instant_Tag_Some, .data.Some._0 = result.data.Ok._0 };
}
static NQ_Result__process__io_err start(void) {
    NQStr value = nq_str("child"), override = nq_str("NQ_M55_ALLOC=test");
    NQ_List__str args = {&value, 1, 1}, env = {&override, 1, 1};
    return nq_process_start(nq_str("/proc/self/exe"), &args, nq_str("."), &env,
        (NQ_Option__str){ .tag = NQ_Option__str_Tag_Some, .data.Some._0 = {"input", 5, NULL} }, true, 10000);
}
static void oom(NQIoErr error) {
    assert(error.os_code == ENOMEM && nq_str_eq(error.kind, nq_str("other")));
}
int main(int argc, char** argv) {
    (void)argv;
    if (argc > 1) {
        unsigned char bytes[2048]; memset(bytes, 'x', sizeof(bytes));
        assert(write(1, bytes, sizeof(bytes)) == sizeof(bytes));
        assert(write(2, bytes, sizeof(bytes)) == sizeof(bytes));
        while (true) {
            ssize_t count = read(0, bytes, sizeof(bytes));
            if (count < 0 && errno == EINTR) continue;
            assert(count >= 0);
            if (count == 0) return 0;
            assert(write(1, bytes, (size_t)count) == count);
        }
    }
    alarm(30);
    int before = fd_count(), failures = 0, successes = 0;
    for (uintmax_t threshold = 0; threshold < 48; threshold++) {
        native_fail_after = threshold; nq_test_allocation_count = 0;
        NQ_Result__process__io_err launched = start();
        if (launched.tag == NQ_Result__process__io_err_Tag_Err) {
            failures++; oom(launched.data.Err._0); nq_result__process__io_err_drop(&launched);
        } else {
            NQ_Result__process_outcome__io_err result = nq_process_wait(launched.data.Ok._0, deadline());
            if (result.tag == NQ_Result__process_outcome__io_err_Tag_Err) { failures++; oom(result.data.Err._0); }
            else {
                successes++;
                assert(result.data.Ok._0.exit_code == 0 && result.data.Ok._0.stdout.len == 2053 && result.data.Ok._0.stderr.len == 2048);
                NQ_Result__process_outcome__io_err copy = nq_result__process_outcome__io_err_clone(result);
                nq_result__process_outcome__io_err_drop(&copy);
            }
            nq_result__process_outcome__io_err_drop(&result);
        }
        no_child(); assert(fd_count() == before);
    }
    assert(failures > 10 && successes > 10);
    for (uintmax_t extra = 0; extra < 8; extra++) {
        native_fail_after = UINTMAX_MAX; nq_test_allocation_count = 0;
        NQ_Result__process__io_err launched = start();
        assert(launched.tag == NQ_Result__process__io_err_Tag_Ok);
        native_fail_after = nq_test_allocation_count + extra;
        NQ_Result__unit__io_err result = nq_process_terminate(&launched.data.Ok._0);
        if (result.tag == NQ_Result__unit__io_err_Tag_Err) {
            oom(result.data.Err._0); assert(launched.data.Ok._0._state == NULL);
        } else {
            NQ_Result__process_outcome__io_err outcome = nq_process_wait(launched.data.Ok._0, deadline());
            launched.data.Ok._0 = (NQ_process){0};
            assert(outcome.tag == NQ_Result__process_outcome__io_err_Tag_Ok);
            nq_result__process_outcome__io_err_drop(&outcome);
        }
        nq_result__unit__io_err_drop(&result); nq_result__process__io_err_drop(&launched);
        no_child(); assert(fd_count() == before);
    }
    native_fail_after = UINTMAX_MAX;
    NQ_Result__process__io_err launched = start();
    assert(launched.tag == NQ_Result__process__io_err_Tag_Ok);
    native_fail_after = nq_test_allocation_count;
    nq_result__process__io_err_drop(&launched);
    assert(nq_test_allocation_count == native_fail_after); no_child(); assert(fd_count() == before);
    puts("native allocation ok");
    return 0;
}
