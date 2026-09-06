#define _POSIX_C_SOURCE 200809L
#include <assert.h>
#include <errno.h>
#include <fcntl.h>
#include <poll.h>
#include <signal.h>
#include <stdarg.h>
#include <stddef.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/prctl.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>

enum { READ, WRITE, POLL, WAITID, WAITPID, KILL, FCNTL, PIPE, FORK, GROUP, DUP,
       CHDIR, EXEC, CLOCK, SLEEP, QUEUED, MASK, PENDING, CALLS };
static int remaining[CALLS], failures[CALLS], calls[CALLS];
static int short_io, partial_message, descriptor_fail_at, lost_anchor, lost_after, bad_clock;
static int signals, group_signals, reaped;
static int terminal_observed, terminal_groups, terminal_success, skip_initial_group;
static int terminal_failures, terminal_error;
static int lost_terminal, lost_reap, signals_at_loss;
static pid_t owned_pid;
static int inject(int slot) {
    calls[slot]++;
    if (slot == FCNTL && descriptor_fail_at == calls[slot]) { errno = EMFILE; return 1; }
    if (remaining[slot] == 0) return 0;
    remaining[slot]--; errno = failures[slot]; return 1;
}
static ssize_t probe_read(int fd, void* data, size_t len);
static ssize_t probe_write(int fd, const void* data, size_t len);
static int probe_poll(struct pollfd* fds, nfds_t count, int timeout);
static int probe_waitid(idtype_t type, id_t id, siginfo_t* info, int options);
static pid_t probe_waitpid(pid_t pid, int* status, int options);
static int probe_kill(pid_t pid, int signal);
static int probe_fcntl(int fd, int operation, ...);
static int probe_pipe(int fds[2]);
static pid_t probe_fork(void);
static int probe_setpgid(pid_t pid, pid_t group);
static int probe_dup2(int oldfd, int newfd);
static int probe_chdir(const char* path);
static int probe_execve(const char* path, char* const argv[], char* const env[]);
static int probe_clock(clockid_t clock, struct timespec* ts);
static int probe_sleep(clockid_t clock, int flags, const struct timespec* ts, struct timespec* rest);
static int probe_ioctl(int fd, unsigned long request, ...);
static int probe_mask(int how, const sigset_t* set, sigset_t* old);
static int probe_pending(sigset_t* set);
#define read probe_read
#define write probe_write
#define poll probe_poll
#define waitid probe_waitid
#define waitpid probe_waitpid
#define kill probe_kill
#define fcntl probe_fcntl
#define pipe probe_pipe
#define fork probe_fork
#define setpgid probe_setpgid
#define dup2 probe_dup2
#define chdir probe_chdir
#define execve probe_execve
#define clock_gettime probe_clock
#define clock_nanosleep probe_sleep
#define ioctl probe_ioctl
#define sigprocmask probe_mask
#define sigpending probe_pending
#include "../../../stdlib/runtime.c"
#undef read
#undef write
#undef poll
#undef waitid
#undef waitpid
#undef kill
#undef fcntl
#undef pipe
#undef fork
#undef setpgid
#undef dup2
#undef chdir
#undef execve
#undef clock_gettime
#undef clock_nanosleep
#undef ioctl
#undef sigprocmask
#undef sigpending

static ssize_t probe_read(int fd, void* data, size_t len) {
    if (inject(READ)) return -1;
    if (partial_message && calls[READ] > 1) return 0;
    if ((short_io || partial_message) && len > 1) len = 1;
    return read(fd, data, len);
}
static ssize_t probe_write(int fd, const void* data, size_t len) {
    if (inject(WRITE)) return -1;
    if (short_io && len > 1) len = 1;
    return write(fd, data, len);
}
static int probe_poll(struct pollfd* fds, nfds_t count, int timeout) {
    if (inject(POLL)) return -1;
    return poll(fds, count, timeout);
}
static int probe_waitid(idtype_t type, id_t id, siginfo_t* info, int options) {
    assert(type == P_PID && (options & WNOWAIT) && (options & WEXITED));
    if ((lost_anchor && calls[WAITID] >= lost_after) || (lost_terminal && !(options & WNOHANG))) {
        assert(owned_pid == (pid_t)id);
        assert(kill(-owned_pid, SIGKILL) == 0);
        int status; assert(waitpid(owned_pid, &status, 0) == owned_pid);
        lost_anchor = lost_terminal = 0; signals_at_loss = signals;
        errno = ECHILD; return -1;
    }
    if (inject(WAITID)) return -1;
    int result = waitid(type, id, info, options);
    if (result == 0 && info->si_pid == (pid_t)id) terminal_observed = 1;
    return result;
}
static pid_t probe_waitpid(pid_t pid, int* status, int options) {
    assert(pid > 0 && options == 0);
    assert(terminal_observed && terminal_success);
    if (lost_reap) {
        assert(waitpid(pid, status, options) == pid);
        lost_reap = 0; signals_at_loss = signals;
        errno = ECHILD; return -1;
    }
    if (inject(WAITPID)) return -1;
    pid_t result = waitpid(pid, status, options);
    if (result == pid) { assert(signals > 0); reaped++; }
    return result;
}
static int probe_kill(pid_t pid, int signal) {
    siginfo_t info = {0};
    pid_t anchor = pid < 0 ? -pid : pid;
    assert(waitid(P_PID, (id_t)anchor, &info, WEXITED | WNOWAIT | WNOHANG) == 0);
    assert(reaped == 0);
    signals++; if (pid < 0) group_signals++;
    if (inject(KILL)) return -1;
    if (pid < 0 && !terminal_observed && skip_initial_group) {
        /* Model a racing member missed by the first group signal. The direct
         * child is still killed normally; only the final signal cleans it. */
        skip_initial_group = 0;
        return 0;
    }
    if (pid < 0 && terminal_observed) {
        terminal_groups++;
        if (terminal_failures > 0) { terminal_failures--; errno = terminal_error; return -1; }
    }
    int result = kill(pid, signal);
    if (pid < 0 && terminal_observed && (result == 0 || errno == ESRCH)) terminal_success = 1;
    return result;
}
static int probe_fcntl(int fd, int operation, ...) {
    va_list args; va_start(args, operation); int value = va_arg(args, int); va_end(args);
    if (inject(FCNTL)) return -1;
    return fcntl(fd, operation, value);
}
static int probe_pipe(int fds[2]) { if (inject(PIPE)) return -1; return pipe(fds); }
static pid_t probe_fork(void) { if (inject(FORK)) return -1; return fork(); }
static int probe_setpgid(pid_t pid, pid_t group) { if (inject(GROUP)) return -1; return setpgid(pid, group); }
static int probe_dup2(int oldfd, int newfd) { if (inject(DUP)) return -1; return dup2(oldfd, newfd); }
static int probe_chdir(const char* path) { if (inject(CHDIR)) return -1; return chdir(path); }
static int probe_execve(const char* path, char* const argv[], char* const env[]) {
    if (inject(EXEC)) return -1;
    return execve(path, argv, env);
}
static int probe_clock(clockid_t clock, struct timespec* ts) {
    if (inject(CLOCK)) return -1;
    if (bad_clock) {
        *ts = (struct timespec){ .tv_sec = (time_t)(INT64_MAX / INT64_C(1000000000)) + 1, .tv_nsec = 0 };
        return 0;
    }
    return clock_gettime(clock, ts);
}
static int probe_sleep(clockid_t clock, int flags, const struct timespec* ts, struct timespec* rest) {
    if (inject(SLEEP)) return errno;
    return clock_nanosleep(clock, flags, ts, rest);
}
static int probe_ioctl(int fd, unsigned long request, ...) {
    assert(terminal_observed && terminal_success);
    va_list args; va_start(args, request); int* count = va_arg(args, int*); va_end(args);
    if (inject(QUEUED)) return -1;
    return ioctl(fd, request, count);
}
static int probe_mask(int how, const sigset_t* set, sigset_t* old) {
    if (inject(MASK)) return -1;
    return sigprocmask(how, set, old);
}
static int probe_pending(sigset_t* set) { if (inject(PENDING)) return -1; return sigpending(set); }
static void reset(void) {
    memset(remaining, 0, sizeof(remaining)); memset(failures, 0, sizeof(failures)); memset(calls, 0, sizeof(calls));
    short_io = partial_message = descriptor_fail_at = lost_anchor = lost_after = bad_clock = 0;
    signals = group_signals = reaped = 0; owned_pid = 0;
    terminal_observed = terminal_groups = terminal_success = skip_initial_group = 0;
    terminal_failures = terminal_error = 0;
    lost_terminal = lost_reap = 0; signals_at_loss = -1;
}
static void once(int slot, int error) { remaining[slot] = 1; failures[slot] = error; calls[slot] = 0; }
static void no_child(void) {
    int status; assert(waitpid(-1, &status, WNOHANG) == -1 && errno == ECHILD);
}
static int fd_count(void) {
    DIR* dir = opendir("/proc/self/fd"); assert(dir != NULL);
    int count = 0; while (readdir(dir) != NULL) count++;
    assert(closedir(dir) == 0); return count;
}
static NQ_Result__process__io_err start(const char* mode, const char* path) {
    NQStr value = nq_str(mode); NQ_List__str args = {&value, 1, 1}, env = {0};
    return nq_process_start(nq_str(path), &args, nq_str("."), &env,
        (NQ_Option__str){ .tag = NQ_Option__str_Tag_Some, .data.Some._0 = {"payload", 7, NULL} }, true, 100);
}
static NQ_Result__process__io_err start_tree(pid_t* descendant) {
    int fds[2]; assert(pipe(fds) == 0);
    char descriptor[32]; snprintf(descriptor, sizeof(descriptor), "%d", fds[1]);
    NQStr values[] = {nq_str("tree"), nq_str(descriptor)};
    NQ_List__str args = {values, 2, 2}, env = {0};
    NQ_Result__process__io_err result = nq_process_start(nq_str("/proc/self/exe"), &args, nq_str("."), &env,
        (NQ_Option__str){ .tag = NQ_Option__str_Tag_Some, .data.Some._0 = {"", 0, NULL} }, true, 100);
    assert(result.tag == NQ_Result__process__io_err_Tag_Ok); close(fds[1]);
    assert(read(fds[0], descendant, sizeof(*descendant)) == sizeof(*descendant)); close(fds[0]);
    return result;
}
static NQ_Option__instant deadline(void) {
    struct timespec ts; assert(clock_gettime(CLOCK_MONOTONIC, &ts) == 0);
    int64_t ns = (int64_t)ts.tv_sec * 1000000000 + ts.tv_nsec + 2000000000;
    return (NQ_Option__instant){ .tag = NQ_Option__instant_Tag_Some, .data.Some._0 = {ns} };
}
static void success(NQ_Result__process__io_err launched) {
    assert(launched.tag == NQ_Result__process__io_err_Tag_Ok);
    NQ_Result__process_outcome__io_err result = nq_process_wait(launched.data.Ok._0, deadline());
    assert(result.tag == NQ_Result__process_outcome__io_err_Tag_Ok && result.data.Ok._0.exit_code == 0);
    assert(nq_str_eq(result.data.Ok._0.stdout, nq_str("payload")));
    nq_result__process_outcome__io_err_drop(&result);
    assert(group_signals > 0 && reaped == 1); no_child();
}

static void fatal_checks(void) {
    assert(prctl(PR_SET_CHILD_SUBREAPER, 1) == 0);
    for (int fault = 0; fault < 6; fault++) {
        int report[2], output[2]; assert(pipe(report) == 0 && pipe(output) == 0);
        pid_t worker = fork(); assert(worker >= 0);
        if (worker == 0) {
            close(report[0]); close(output[0]); assert(dup2(output[1], 2) == 2); close(output[1]);
            reset();
            pid_t descendant = 0;
            NQ_Result__process__io_err launched = fault >= 3 ? start_tree(&descendant) :
                start(fault == 2 ? "natural" : "blocked", "/proc/self/exe");
            assert(launched.tag == NQ_Result__process__io_err_Tag_Ok);
            pid_t child = launched.data.Ok._0._state->pid;
            pid_t children[2] = {child, descendant};
            assert(write(report[1], children, sizeof(children)) == sizeof(children)); close(report[1]);
            if (fault == 2) {
                siginfo_t info = {0}; assert(waitid(P_PID, (id_t)child, &info, WEXITED | WNOWAIT) == 0);
            }
            if (fault < 3) {
                int slot = fault == 1 ? WAITPID : KILL;
                remaining[slot] = INT_MAX; failures[slot] = slot == KILL ? EPERM : EIO;
            } else {
                skip_initial_group = 1; terminal_failures = INT_MAX; terminal_error = EPERM;
            }
            if (fault == 3) {
                (void)nq_process_wait(launched.data.Ok._0,
                    (NQ_Option__instant){ .tag = NQ_Option__instant_Tag_Some, .data.Some._0 = {0} });
                _exit(99);
            }
            if (fault == 4) { (void)nq_process_terminate(&launched.data.Ok._0); _exit(99); }
            nq_result__process__io_err_drop(&launched);
            _exit(99);
        }
        close(report[1]); close(output[1]);
        pid_t children[2] = {0}; assert(read(report[0], children, sizeof(children)) == sizeof(children)); close(report[0]);
        pid_t child = children[0], descendant = children[1];
        int status; assert(waitpid(worker, &status, 0) == worker);
        bool fatal = WIFEXITED(status) && WEXITSTATUS(status) == 1;
        /* Fatal-runtime ownership is tested under an external subreaper. It
         * kills/reaps the adopted child even when the worker could not. */
        siginfo_t info = {0};
        bool anchored = waitid(P_PID, (id_t)child, &info, WEXITED | WNOWAIT | WNOHANG) == 0;
        if (anchored) {
            assert(kill(-child, SIGKILL) == 0 || errno == ESRCH);
            assert(kill(child, SIGKILL) == 0 || errno == ESRCH);
            assert(waitpid(child, &status, 0) == child);
        }
        if (descendant > 0) {
            assert(kill(descendant, SIGKILL) == 0);
            assert(waitpid(descendant, &status, 0) == descendant && WIFSIGNALED(status));
        }
        char message[128]; size_t used = 0;
        while (true) {
            ssize_t count = read(output[0], message + used, sizeof(message) - used);
            assert(count >= 0);
            if (count == 0) break;
            used += (size_t)count; assert(used < sizeof(message));
        }
        close(output[0]);
        const char* expected = "nauqtype runtime: process cleanup failed\n";
        assert(fatal && anchored && used == strlen(expected) && memcmp(message, expected, used) == 0); no_child();
    }
    assert(prctl(PR_SET_CHILD_SUBREAPER, 0) == 0);
    reset();
    NQ_Result__process__io_err launched = start("blocked", "/proc/self/exe");
    assert(launched.tag == NQ_Result__process__io_err_Tag_Ok);
    owned_pid = launched.data.Ok._0._state->pid;
    remaining[KILL] = INT_MAX; failures[KILL] = EPERM; lost_anchor = 1; lost_after = 2;
    nq_result__process__io_err_drop(&launched);
    assert(signals == 2 && launched.data.Ok._0._state == NULL); no_child();
}

static void ordering_checks(void) {
    assert(prctl(PR_SET_CHILD_SUBREAPER, 1) == 0);
    for (int action = 0; action < 3; action++) {
        for (int fault = 0; fault < 3; fault++) {
            reset(); pid_t descendant = 0;
            NQ_Result__process__io_err launched = start_tree(&descendant);
            skip_initial_group = 1;
            terminal_failures = fault != 0; terminal_error = fault == 1 ? EINTR : EIO;
            if (action == 2) nq_result__process__io_err_drop(&launched);
            else {
                if (action == 1) {
                    NQ_Result__unit__io_err result = nq_process_terminate(&launched.data.Ok._0);
                    assert((result.tag == NQ_Result__unit__io_err_Tag_Err) == (fault == 2));
                    nq_result__unit__io_err_drop(&result);
                }
                if (launched.data.Ok._0._state != NULL) {
                    NQ_Result__process_outcome__io_err outcome = nq_process_wait(launched.data.Ok._0,
                        (NQ_Option__instant){ .tag = NQ_Option__instant_Tag_Some, .data.Some._0 = {0} });
                    assert((outcome.tag == NQ_Result__process_outcome__io_err_Tag_Err) == (action == 0 && fault == 2));
                    if (outcome.tag == NQ_Result__process_outcome__io_err_Tag_Ok) {
                        assert(outcome.data.Ok._0.timed_out == (action == 0));
                        assert(outcome.data.Ok._0.cancelled == (action == 1));
                    }
                    nq_result__process_outcome__io_err_drop(&outcome);
                }
            }
            int status; assert(waitpid(descendant, &status, 0) == descendant);
            assert(WIFSIGNALED(status) && WTERMSIG(status) == SIGKILL);
            assert(!skip_initial_group && terminal_observed && terminal_success && terminal_groups > 0 && reaped == 1);
            no_child();
        }
    }
    assert(prctl(PR_SET_CHILD_SUBREAPER, 0) == 0);
    for (int action = 0; action < 3; action++) {
        for (int lose_reap = 0; lose_reap < 2; lose_reap++) {
            reset(); NQ_Result__process__io_err launched = start("blocked", "/proc/self/exe");
            assert(launched.tag == NQ_Result__process__io_err_Tag_Ok);
            owned_pid = launched.data.Ok._0._state->pid;
            lost_terminal = !lose_reap; lost_reap = lose_reap;
            if (action == 2) nq_result__process__io_err_drop(&launched);
            else if (action == 1) {
                NQ_Result__unit__io_err result = nq_process_terminate(&launched.data.Ok._0);
                assert(result.tag == NQ_Result__unit__io_err_Tag_Err && result.data.Err._0.os_code == ECHILD);
                assert(launched.data.Ok._0._state == NULL); nq_result__unit__io_err_drop(&result);
            } else {
                NQ_Result__process_outcome__io_err result = nq_process_wait(launched.data.Ok._0,
                    (NQ_Option__instant){ .tag = NQ_Option__instant_Tag_Some, .data.Some._0 = {0} });
                assert(result.tag == NQ_Result__process_outcome__io_err_Tag_Err && result.data.Err._0.os_code == ECHILD);
                nq_result__process_outcome__io_err_drop(&result);
            }
            assert(signals_at_loss >= 0 && signals_at_loss == signals && reaped == 0);
            assert(terminal_success == lose_reap); no_child();
        }
    }
}
int main(int argc, char** argv) {
    if (argc > 1) {
        if (strcmp(argv[1], "tree") == 0) {
            assert(argc == 3);
            pid_t descendant = fork(); assert(descendant >= 0);
            if (descendant == 0) { for (;;) pause(); }
            int fd = atoi(argv[2]); assert(write(fd, &descendant, sizeof(descendant)) == sizeof(descendant)); close(fd);
            for (;;) pause();
        }
        if (strcmp(argv[1], "blocked") == 0) { for (;;) pause(); }
        if (strcmp(argv[1], "natural") == 0) return 0;
        unsigned char bytes[64];
        while (true) {
            ssize_t count = read(0, bytes, sizeof(bytes));
            if (count < 0 && errno == EINTR) continue;
            assert(count >= 0);
            if (count == 0) return 0;
            assert(write(1, bytes, (size_t)count) == count);
        }
    }
    alarm(30);
    int before = fd_count();
    reset(); short_io = 1; success(start("echo", "/proc/self/exe"));
    reset();
    int interrupted[] = {READ, WRITE, POLL, WAITID, WAITPID, KILL, FCNTL, PIPE, FORK, GROUP, DUP, CHDIR, EXEC};
    for (size_t index = 0; index < sizeof(interrupted) / sizeof(interrupted[0]); index++) once(interrupted[index], EINTR);
    success(start("echo", "/proc/self/exe"));
    int setup[] = {READ, FCNTL, PIPE, FORK, GROUP, DUP, CHDIR, EXEC};
    for (size_t index = 0; index < sizeof(setup) / sizeof(setup[0]); index++) {
        reset(); once(setup[index], EIO);
        NQ_Result__process__io_err launched = start("echo", "/proc/self/exe");
        assert(launched.tag == NQ_Result__process__io_err_Tag_Err);
        nq_result__process__io_err_drop(&launched); no_child(); assert(fd_count() == before);
    }
    for (int index = 1; index <= 14; index++) {
        reset(); descriptor_fail_at = index;
        NQ_Result__process__io_err launched = start("echo", "/proc/self/exe");
        assert(launched.tag == NQ_Result__process__io_err_Tag_Err);
        nq_result__process__io_err_drop(&launched); no_child(); assert(fd_count() == before);
    }
    for (int mode = 0; mode < 3; mode++) {
        reset(); short_io = mode == 0; partial_message = mode == 1;
        if (mode == 2) { once(READ, EINTR); once(WRITE, EINTR); }
        NQ_Result__process__io_err launched = start("echo", "/does-not-exist/nauqtype-m55");
        assert(launched.tag == NQ_Result__process__io_err_Tag_Err);
        if (mode == 1) assert(launched.data.Err._0.os_code == EIO);
        nq_result__process__io_err_drop(&launched); no_child();
    }
    int runtime[] = {READ, WRITE, POLL, WAITID, WAITPID, KILL, CLOCK, QUEUED, MASK, PENDING};
    for (size_t index = 0; index < sizeof(runtime) / sizeof(runtime[0]); index++) {
        reset(); NQ_Result__process__io_err launched = start(runtime[index] == QUEUED ? "natural" : "echo", "/proc/self/exe");
        assert(launched.tag == NQ_Result__process__io_err_Tag_Ok);
        if (runtime[index] == QUEUED) {
            siginfo_t info = {0};
            assert(waitid(P_PID, (id_t)launched.data.Ok._0._state->pid, &info, WEXITED | WNOWAIT) == 0);
        }
        once(runtime[index], EIO);
        NQ_Result__process_outcome__io_err result = nq_process_wait(launched.data.Ok._0, deadline());
        if (result.tag != NQ_Result__process_outcome__io_err_Tag_Err)
            fprintf(stderr, "unreached fault slot %d, calls %d\n", runtime[index], calls[runtime[index]]);
        assert(result.tag == NQ_Result__process_outcome__io_err_Tag_Err);
        assert(result.data.Err._0.os_code == EIO);
        nq_result__process_outcome__io_err_drop(&result); no_child(); assert(fd_count() == before);
    }
    int cleanup[] = {WAITID, WAITPID, KILL};
    for (size_t index = 0; index < sizeof(cleanup) / sizeof(cleanup[0]); index++) {
        reset(); NQ_Result__process__io_err launched = start("blocked", "/proc/self/exe");
        assert(launched.tag == NQ_Result__process__io_err_Tag_Ok);
        once(cleanup[index], EIO);
        nq_result__process__io_err_drop(&launched); no_child(); assert(fd_count() == before);
        assert(reaped == 1 && group_signals > 0);
    }
    reset(); NQ_Result__process__io_err launched = start("blocked", "/proc/self/exe");
    assert(launched.tag == NQ_Result__process__io_err_Tag_Ok);
    owned_pid = launched.data.Ok._0._state->pid; lost_anchor = 1;
    NQ_Result__unit__io_err terminated = nq_process_terminate(&launched.data.Ok._0);
    assert(terminated.tag == NQ_Result__unit__io_err_Tag_Err && terminated.data.Err._0.os_code == ECHILD);
    assert(launched.data.Ok._0._state == NULL && signals == 0);
    nq_result__unit__io_err_drop(&terminated); nq_result__process__io_err_drop(&launched); no_child();
    reset(); bad_clock = 1;
    NQ_Result__i64__io_err wall = nq_wall_time_ns();
    assert(wall.tag == NQ_Result__i64__io_err_Tag_Err && nq_str_eq(wall.data.Err._0.kind, nq_str("invalid_data")));
    nq_result__i64__io_err_drop(&wall);
    NQ_Result__instant__io_err instant = nq_monotonic_now();
    assert(instant.tag == NQ_Result__instant__io_err_Tag_Err); nq_result__instant__io_err_drop(&instant);
    reset(); once(CLOCK, EIO);
    instant = nq_monotonic_now(); assert(instant.tag == NQ_Result__instant__io_err_Tag_Err);
    nq_result__instant__io_err_drop(&instant);
    reset(); once(CLOCK, EINTR); once(SLEEP, EINTR);
    assert(nq_sleep_for((NQ_duration){1000000}).tag == NQ_Result__unit__io_err_Tag_Ok && calls[SLEEP] >= 2);
    reset(); once(SLEEP, EIO);
    terminated = nq_sleep_for((NQ_duration){1000000});
    assert(terminated.tag == NQ_Result__unit__io_err_Tag_Err && terminated.data.Err._0.os_code == EIO);
    nq_result__unit__io_err_drop(&terminated); no_child(); assert(fd_count() == before);
    fatal_checks(); ordering_checks(); assert(fd_count() == before);
    puts("native faults ok");
    return 0;
}
