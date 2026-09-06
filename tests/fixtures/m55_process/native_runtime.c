#define _GNU_SOURCE
#include <assert.h>
#include <sys/prctl.h>
#include <sys/time.h>
#include "../../../stdlib/runtime.c"

static NQ_Option__instant no_deadline(void) {
    return (NQ_Option__instant){ .tag = NQ_Option__instant_Tag_None };
}
static NQ_Option__str supplied(NQStr value) {
    return (NQ_Option__str){ .tag = NQ_Option__str_Tag_Some, .data.Some._0 = value };
}
static int64_t now_ns(void) {
    NQ_Result__instant__io_err result = nq_monotonic_now();
    assert(result.tag == NQ_Result__instant__io_err_Tag_Ok);
    return result.data.Ok._0._ns;
}
static NQ_Option__instant after(int64_t ns) {
    NQ_Result__instant__io_err result = nq_deadline_after((NQ_duration){ns});
    assert(result.tag == NQ_Result__instant__io_err_Tag_Ok);
    return (NQ_Option__instant){ .tag = NQ_Option__instant_Tag_Some, .data.Some._0 = result.data.Ok._0 };
}
static void no_child(void) {
    int status;
    assert(waitpid(-1, &status, WNOHANG) == -1 && errno == ECHILD);
}
static int fd_count(void) {
    DIR* directory = opendir("/proc/self/fd");
    assert(directory != NULL);
    int count = 0;
    while (readdir(directory) != NULL) count++;
    assert(closedir(directory) == 0);
    return count;
}
static void write_all(int fd, const void* bytes, size_t len) {
    const char* data = bytes;
    while (len > 0) {
        ssize_t count = write(fd, data, len);
        if (count < 0 && errno == EINTR) continue;
        assert(count > 0);
        data += count; len -= (size_t)count;
    }
}
static NQ_process launch(const char* mode, NQ_Option__str input, bool capture, int64_t cap) {
    NQStr argument = nq_str(mode);
    NQ_List__str args = { &argument, 1, 1 }, env = {0};
    NQ_Result__process__io_err result = nq_process_start(nq_str("/proc/self/exe"), &args, nq_str("."), &env, input, capture, cap);
    if (result.tag != NQ_Result__process__io_err_Tag_Ok) {
        fprintf(stderr, "launch %s: %.*s\n", mode, (int)result.data.Err._0.text.len, result.data.Err._0.text.data);
        abort();
    }
    return result.data.Ok._0;
}
static NQ_process_outcome waited(NQ_process child, NQ_Option__instant deadline) {
    NQ_Result__process_outcome__io_err result = nq_process_wait(child, deadline);
    if (result.tag != NQ_Result__process_outcome__io_err_Tag_Ok) {
        fprintf(stderr, "wait: %.*s\n", (int)result.data.Err._0.text.len, result.data.Err._0.text.data);
        abort();
    }
    return result.data.Ok._0;
}
static void observe_exit(NQ_process child) {
    int64_t end = now_ns() + INT64_C(3000000000);
    while (true) {
        bool exited;
        assert(nq_process_probe(child._state, &exited) == 0);
        if (exited) return;
        assert(now_ns() < end);
        struct timespec delay = {0, 1000000};
        nanosleep(&delay, NULL);
    }
}
static int child_main(int argc, char** argv) {
    if (strcmp(argv[1], "block") == 0) { for (;;) pause(); }
    if (strcmp(argv[1], "flood") == 0) {
        char bytes[4096]; memset(bytes, 'x', sizeof(bytes));
        for (;;) { write_all(1, bytes, sizeof(bytes)); write_all(2, bytes, sizeof(bytes)); }
    }
    if (strcmp(argv[1], "signal") == 0) { raise(SIGTERM); return 90; }
    if (strcmp(argv[1], "natural") == 0) { write_all(1, "natural", 7); return 23; }
    if (strcmp(argv[1], "closed") == 0) {
        close(0); write_all(1, "closed", 6);
        struct timespec delay = {0, 30000000}; nanosleep(&delay, NULL);
        return 0;
    }
    if (strcmp(argv[1], "env") == 0) {
        const char* value = getenv("NQ_M55_VALUE");
        assert(value != NULL && strcmp(value, "override=ok") == 0);
        assert(getenv("NQ_M55_INHERITED") != NULL && strcmp(getenv("NQ_M55_INHERITED"), "kept") == 0);
        char directory[4096]; assert(getcwd(directory, sizeof(directory)) != NULL);
        write_all(1, directory, strlen(directory));
        return 0;
    }
    if (strcmp(argv[1], "tree") == 0 || strcmp(argv[1], "escape") == 0) {
        assert(argc == 4);
        pid_t descendant = fork(); assert(descendant >= 0);
        if (descendant == 0) {
            if (strcmp(argv[1], "escape") == 0) assert(setsid() >= 0);
            for (;;) pause();
        }
        if (strcmp(argv[1], "escape") == 0) {
            while (getpgid(descendant) != descendant) {
                struct timespec delay = {0, 1000000}; nanosleep(&delay, NULL);
            }
            write_all(1, "queued", 6);
        }
        int fd = atoi(argv[2]);
        write_all(fd, &descendant, sizeof(descendant)); close(fd);
        if (strcmp(argv[3], "natural") == 0) return 19;
        for (;;) pause();
    }
    unsigned char buffer[4096];
    if (strcmp(argv[1], "duplex") == 0) {
        for (int index = 0; index < 16; index++) {
            memset(buffer, 'O', sizeof(buffer)); write_all(1, buffer, sizeof(buffer));
            memset(buffer, 'E', sizeof(buffer)); write_all(2, buffer, sizeof(buffer));
        }
    }
    while (true) {
        ssize_t count = read(0, buffer, sizeof(buffer));
        if (count < 0 && errno == EINTR) continue;
        assert(count >= 0);
        if (count == 0) return 0;
        write_all(1, buffer, (size_t)count);
    }
}
static volatile sig_atomic_t alarms;
static void tick(int signal) { (void)signal; alarms++; }

static void time_checks(void) {
    assert(nq_duration_from_ns(-1).tag == NQ_Option__duration_Tag_None);
    assert(nq_duration_as_ns(nq_duration_from_ns(INT64_MAX).data.Some._0) == INT64_MAX);
    assert(nq_duration_between((NQ_instant){8}, (NQ_instant){7}).tag == NQ_Option__duration_Tag_None);
    assert(nq_duration_between((NQ_instant){INT64_MIN}, (NQ_instant){0}).tag == NQ_Option__duration_Tag_None);
    assert(nq_duration_between((NQ_instant){INT64_MIN}, (NQ_instant){-1}).data.Some._0._ns == INT64_MAX);
    assert(nq_duration_between((NQ_instant){5}, (NQ_instant){9}).data.Some._0._ns == 4);
    NQ_Result__i64__io_err wall = nq_wall_time_ns();
    assert(wall.tag == NQ_Result__i64__io_err_Tag_Ok && wall.data.Ok._0 > 0);
    nq_result__i64__io_err_drop(&wall);
    NQ_Result__instant__io_err overflow = nq_deadline_after((NQ_duration){INT64_MAX});
    assert(overflow.tag == NQ_Result__instant__io_err_Tag_Err);
    assert(nq_str_eq(overflow.data.Err._0.kind, nq_str("invalid_data")));
    NQ_Result__instant__io_err copied = nq_result__instant__io_err_clone(overflow);
    nq_result__instant__io_err_drop(&overflow); nq_result__instant__io_err_drop(&copied);
    NQ_Result__unit__io_err negative = nq_sleep_for((NQ_duration){-1});
    assert(negative.tag == NQ_Result__unit__io_err_Tag_Err);
    nq_result__unit__io_err_drop(&negative);
    assert(nq_sleep_for((NQ_duration){0}).tag == NQ_Result__unit__io_err_Tag_Ok);
    struct sigaction action = {0}; action.sa_handler = tick; sigemptyset(&action.sa_mask);
    assert(sigaction(SIGALRM, &action, NULL) == 0);
    struct itimerval timer = {{0, 2000}, {0, 2000}};
    assert(setitimer(ITIMER_REAL, &timer, NULL) == 0);
    int64_t start = now_ns();
    assert(nq_sleep_for((NQ_duration){40000000}).tag == NQ_Result__unit__io_err_Tag_Ok);
    assert(now_ns() - start >= 40000000 && now_ns() - start < 2000000000);
    NQ_process child = launch("natural", supplied(nq_str("")), true, 7);
    NQ_process_outcome outcome = waited(child, after(2000000000));
    assert(outcome.exit_code == 23);
    nq_process_outcome_drop(&outcome);
    timer = (struct itimerval){{0, 0}, {0, 0}};
    assert(setitimer(ITIMER_REAL, &timer, NULL) == 0 && alarms > 1);
}

static void io_checks(void) {
    size_t len = 1024 * 1024;
    char* bytes = malloc(len); assert(bytes != NULL);
    for (size_t index = 0; index < len; index++) bytes[index] = (char)(index % 256);
    NQStr input = {bytes, (intptr_t)len, NULL};
    NQ_process child = launch("duplex", supplied(input), true, (int64_t)len + 131072);
    NQ_process_outcome outcome = waited(child, after(5000000000));
    assert(outcome.exit_code == 0 && !outcome.timed_out && !outcome.cancelled);
    assert(outcome.stdout.len == (intptr_t)len + 65536 && outcome.stderr.len == 65536);
    for (int index = 0; index < 65536; index++) assert(outcome.stdout.data[index] == 'O' && outcome.stderr.data[index] == 'E');
    assert(memcmp(outcome.stdout.data + 65536, bytes, len) == 0);
    NQ_process_outcome copy = nq_process_outcome_clone(outcome);
    nq_process_outcome_drop(&outcome);
    assert(memcmp(copy.stdout.data + 65536, bytes, len) == 0);
    nq_process_outcome_drop(&copy);
    child = launch("duplex", supplied(input), true, (int64_t)len + 131071);
    NQ_Result__process_outcome__io_err over = nq_process_wait(child, after(5000000000));
    assert(over.tag == NQ_Result__process_outcome__io_err_Tag_Err);
    assert(nq_str_eq(over.data.Err._0.kind, nq_str("invalid_data")));
    nq_result__process_outcome__io_err_drop(&over); no_child();
    child = launch("closed", supplied(input), true, 6);
    outcome = waited(child, after(3000000000));
    assert(outcome.exit_code == 0 && nq_str_eq(outcome.stdout, nq_str("closed")));
    nq_process_outcome_drop(&outcome); free(bytes);
    child = launch("echo", supplied(nq_str("")), true, 0);
    outcome = waited(child, after(3000000000));
    assert(outcome.exit_code == 0 && outcome.stdout.len == 0 && outcome.stderr.len == 0);
    nq_process_outcome_drop(&outcome);
    child = launch("natural", supplied(nq_str("")), true, 0);
    over = nq_process_wait(child, after(3000000000));
    assert(over.tag == NQ_Result__process_outcome__io_err_Tag_Err && nq_str_eq(over.data.Err._0.kind, nq_str("invalid_data")));
    nq_result__process_outcome__io_err_drop(&over);
    int saved = dup(0), fds[2]; assert(saved >= 0 && pipe(fds) == 0);
    write_all(fds[1], "inherited", 9); close(fds[1]);
    assert(dup2(fds[0], 0) == 0); close(fds[0]);
    child = launch("echo", (NQ_Option__str){ .tag = NQ_Option__str_Tag_None }, true, 9);
    assert(dup2(saved, 0) == 0); close(saved);
    outcome = waited(child, after(3000000000));
    assert(nq_str_eq(outcome.stdout, nq_str("inherited"))); nq_process_outcome_drop(&outcome);
}

static void lifecycle_checks(void) {
    int64_t start = now_ns();
    NQ_process child = launch("block", supplied(nq_str("")), true, 100);
    NQ_process_outcome outcome = waited(child, after(30000000));
    assert(outcome.timed_out && !outcome.cancelled && outcome.exit_code == 128 + SIGKILL);
    assert(now_ns() - start < 2000000000); nq_process_outcome_drop(&outcome); no_child();
    child = launch("flood", supplied(nq_str("")), true, INT32_MAX);
    start = now_ns(); outcome = waited(child, after(20000000));
    assert(outcome.timed_out && !outcome.cancelled && now_ns() - start < 2000000000);
    nq_process_outcome_drop(&outcome); no_child();
    child = launch("block", supplied(nq_str("")), false, 0);
    assert(nq_process_terminate(&child).tag == NQ_Result__unit__io_err_Tag_Ok);
    assert(nq_process_terminate(&child).tag == NQ_Result__unit__io_err_Tag_Ok);
    outcome = waited(child, (NQ_Option__instant){ .tag = NQ_Option__instant_Tag_Some, .data.Some._0 = {0} });
    assert(outcome.cancelled && !outcome.timed_out && outcome.exit_code == 128 + SIGKILL);
    nq_process_outcome_drop(&outcome);
    child = launch("natural", supplied(nq_str("")), true, 7); observe_exit(child);
    outcome = waited(child, (NQ_Option__instant){ .tag = NQ_Option__instant_Tag_Some, .data.Some._0 = {0} });
    assert(outcome.exit_code == 23 && !outcome.timed_out && !outcome.cancelled);
    nq_process_outcome_drop(&outcome);
    child = launch("natural", supplied(nq_str("")), true, 7); observe_exit(child);
    assert(nq_process_terminate(&child).tag == NQ_Result__unit__io_err_Tag_Ok);
    outcome = waited(child, no_deadline());
    assert(outcome.exit_code == 23 && !outcome.cancelled); nq_process_outcome_drop(&outcome);
    child = launch("natural", supplied(nq_str("")), true, 1); observe_exit(child);
    NQ_Result__unit__io_err capped = nq_process_terminate(&child);
    assert(capped.tag == NQ_Result__unit__io_err_Tag_Err && child._state == NULL);
    assert(nq_str_eq(capped.data.Err._0.kind, nq_str("invalid_data")));
    nq_result__unit__io_err_drop(&capped); no_child();
    child = launch("signal", supplied(nq_str("")), true, 0);
    outcome = waited(child, after(3000000000));
    assert(outcome.exit_code == 128 + SIGTERM); nq_process_outcome_drop(&outcome);
    child = launch("block", supplied(nq_str("")), true, 0);
    nq_process_drop(&child); nq_process_drop(&child); assert(child._state == NULL); no_child();
    NQ_Result__unit__io_err inert = nq_process_terminate(&child);
    assert(inert.tag == NQ_Result__unit__io_err_Tag_Err && nq_str_eq(inert.data.Err._0.kind, nq_str("invalid_input")));
    nq_result__unit__io_err_drop(&inert);
    NQ_Result__process_outcome__io_err consumed = nq_process_wait(child, no_deadline());
    assert(consumed.tag == NQ_Result__process_outcome__io_err_Tag_Err); nq_result__process_outcome__io_err_drop(&consumed);
    pid_t unrelated = fork(); assert(unrelated >= 0);
    if (unrelated == 0) _exit(61);
    child = launch("block", supplied(nq_str("")), true, 0); nq_process_drop(&child);
    int status; assert(waitpid(unrelated, &status, 0) == unrelated && WEXITSTATUS(status) == 61);
}

static void validate_start(void) {
    NQ_List__str empty = {0};
    NQ_Result__process__io_err no_cwd = nq_process_start(nq_str("/proc/self/exe"), &empty, nq_str(""), &empty,
        supplied(nq_str("")), true, 0);
    assert(no_cwd.tag == NQ_Result__process__io_err_Tag_Err && nq_str_eq(no_cwd.data.Err._0.kind, nq_str("invalid_input")));
    nq_result__process__io_err_drop(&no_cwd);
    const char* invalid[] = {"true", "", "/does-not-exist/nauqtype-m55"};
    for (size_t index = 0; index < sizeof(invalid) / sizeof(invalid[0]); index++) {
        NQ_Result__process__io_err result = nq_process_start(nq_str(invalid[index]), &empty, nq_str("."), &empty, supplied(nq_str("")), true, 0);
        assert(result.tag == NQ_Result__process__io_err_Tag_Err); nq_result__process__io_err_drop(&result); no_child();
    }
    NQStr arg = nq_str("env"); NQ_List__str args = {&arg, 1, 1};
    NQStr values[] = {nq_str("NQ_M55_VALUE=override=ok"), nq_str("NQ_M55_VALUE=duplicate")};
    NQ_List__str env = {values, 1, 2};
    assert(setenv("NQ_M55_VALUE", "parent", 1) == 0 && setenv("NQ_M55_INHERITED", "kept", 1) == 0);
    NQ_Result__process__io_err result = nq_process_start(nq_str("/proc/self/exe"), &args, nq_str("/tmp"), &env, supplied(nq_str("")), true, 4096);
    assert(result.tag == NQ_Result__process__io_err_Tag_Ok);
    NQ_process_outcome outcome = waited(result.data.Ok._0, after(3000000000));
    assert(nq_str_eq(outcome.stdout, nq_str("/tmp")) && strcmp(getenv("NQ_M55_VALUE"), "parent") == 0);
    nq_process_outcome_drop(&outcome);
    const char* bad[] = {"1KEY=x", "KEY", "=empty", "K-Y=x", "K.Y=x", "K Y=x", "KEY\xc3\xa9=x"};
    for (size_t index = 0; index < sizeof(bad) / sizeof(bad[0]); index++) {
        values[0] = nq_str(bad[index]);
        result = nq_process_start(nq_str("/proc/self/exe"), &args, nq_str("."), &env, supplied(nq_str("")), true, 0);
        assert(result.tag == NQ_Result__process__io_err_Tag_Err); nq_result__process__io_err_drop(&result);
    }
    values[0] = values[1]; env.len = 2;
    result = nq_process_start(nq_str("/proc/self/exe"), &args, nq_str("."), &env, supplied(nq_str("")), true, 0);
    assert(result.tag == NQ_Result__process__io_err_Tag_Err); nq_result__process__io_err_drop(&result);
    NQStr nul = {"a\0b", 3, NULL}; args.data = &nul;
    result = nq_process_start(nq_str("/proc/self/exe"), &args, nq_str("."), &empty, supplied(nq_str("")), true, 0);
    assert(result.tag == NQ_Result__process__io_err_Tag_Err); nq_result__process__io_err_drop(&result);
    args.data = &arg;
    for (int index = 0; index < 3; index++) {
        int64_t cap = index == 0 ? -1 : index == 1 ? (int64_t)INT32_MAX + 1 : 1;
        result = nq_process_start(nq_str("/proc/self/exe"), &args, nq_str("."), &empty, supplied(nq_str("")), index != 2, cap);
        assert(result.tag == NQ_Result__process__io_err_Tag_Err); nq_result__process__io_err_drop(&result);
    }
    char path[] = "/tmp/nq-m55-no-shell-XXXXXX";
    int fd = mkstemp(path); assert(fd >= 0);
    write_all(fd, "exit 0\n", 7); assert(fchmod(fd, 0700) == 0); close(fd);
    result = nq_process_start(nq_str(path), &empty, nq_str("."), &empty, supplied(nq_str("")), true, 0);
    assert(result.tag == NQ_Result__process__io_err_Tag_Err && result.data.Err._0.os_code == ENOEXEC);
    nq_result__process__io_err_drop(&result); assert(unlink(path) == 0); no_child();
}

static void tree_checks(void) {
    assert(prctl(PR_SET_CHILD_SUBREAPER, 1) == 0);
    for (int mode = 0; mode < 5; mode++) {
        int fds[2]; assert(pipe(fds) == 0);
        char descriptor[32]; snprintf(descriptor, sizeof(descriptor), "%d", fds[1]);
        NQStr values[] = {nq_str(mode == 4 ? "escape" : "tree"), nq_str(descriptor), nq_str(mode == 0 || mode == 4 ? "natural" : "block")};
        NQ_List__str args = {values, 3, 3}, env = {0};
        NQ_Result__process__io_err result = nq_process_start(nq_str("/proc/self/exe"), &args, nq_str("."), &env, supplied(nq_str("")), true, mode == 4 ? 6 : 0);
        assert(result.tag == NQ_Result__process__io_err_Tag_Ok); close(fds[1]);
        pid_t descendant = 0; assert(read(fds[0], &descendant, sizeof(descendant)) == sizeof(descendant)); close(fds[0]);
        NQ_process child = result.data.Ok._0;
        int64_t start = now_ns();
        if (mode == 3) {
            nq_process_drop(&child);
            assert(child._state == NULL);
        }
        else {
            if (mode == 2) {
                assert(nq_process_terminate(&child).tag == NQ_Result__unit__io_err_Tag_Ok);
                assert(child._state->ready && child._state->terminal_signalled && child._state->pid == 0);
            }
            NQ_process_outcome outcome = waited(child, mode == 1 ? after(30000000) : no_deadline());
            assert(mode != 0 || outcome.exit_code == 19);
            assert(mode != 1 || outcome.timed_out); assert(mode != 2 || outcome.cancelled);
            if (mode == 4) {
                assert(outcome.exit_code == 19 && nq_str_eq(outcome.stdout, nq_str("queued")));
                assert(kill(descendant, 0) == 0);
                assert(kill(descendant, SIGKILL) == 0);
            }
            nq_process_outcome_drop(&outcome);
        }
        assert(now_ns() - start < 2000000000);
        int status; assert(waitpid(descendant, &status, 0) == descendant);
        assert(WIFSIGNALED(status) && WTERMSIG(status) == SIGKILL); no_child();
    }
    assert(prctl(PR_SET_CHILD_SUBREAPER, 0) == 0);
}

static void stdio_and_sigpipe_checks(void) {
    pid_t pid = fork(); assert(pid >= 0);
    if (pid == 0) {
        close(0); close(1); close(2);
        NQ_process child = launch("echo", supplied((NQStr){"a\0b", 3, NULL}), true, 3);
        NQ_process_outcome outcome = waited(child, after(3000000000));
        assert(outcome.exit_code == 0 && outcome.stdout.len == 3 && memcmp(outcome.stdout.data, "a\0b", 3) == 0);
        nq_process_outcome_drop(&outcome);
        child = launch("echo", supplied(nq_str("")), false, 0);
        outcome = waited(child, after(3000000000));
        assert(outcome.exit_code == 0 && outcome.stdout.len == 0 && outcome.stderr.len == 0);
        nq_process_outcome_drop(&outcome); no_child(); _exit(0);
    }
    int status; assert(waitpid(pid, &status, 0) == pid && status == 0);
    int fds[2]; assert(pipe(fds) == 0); close(fds[0]);
    sigset_t set, old, pending;
    sigemptyset(&set); sigaddset(&set, SIGPIPE);
    assert(sigprocmask(SIG_BLOCK, &set, &old) == 0);
    assert(raise(SIGPIPE) == 0);
    assert(nq_process_write_input(fds[1], "x", 1) == -1 && errno == EPIPE);
    assert(sigpending(&pending) == 0 && sigismember(&pending, SIGPIPE) == 1);
    struct timespec zero = {0}; assert(sigtimedwait(&set, NULL, &zero) == SIGPIPE);
    assert(sigprocmask(SIG_SETMASK, &old, NULL) == 0);
    assert(nq_process_write_input(fds[1], "x", 1) == -1 && errno == EPIPE);
    assert(sigpending(&pending) == 0 && sigismember(&pending, SIGPIPE) == 0);
    close(fds[1]);
}

int main(int argc, char** argv) {
    if (argc > 1) return child_main(argc, argv);
    alarm(30);
    int before = fd_count();
    time_checks(); io_checks(); lifecycle_checks(); validate_start(); tree_checks(); stdio_and_sigpipe_checks();
    no_child(); assert(fd_count() == before);
    puts("native runtime ok");
    return 0;
}
