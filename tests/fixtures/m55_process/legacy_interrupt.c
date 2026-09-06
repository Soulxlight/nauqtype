#define _POSIX_C_SOURCE 200809L
#include <assert.h>
#include <errno.h>
#include <fcntl.h>
#include <signal.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/prctl.h>
#include <sys/time.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>

static int mode, reads, writes, waits, controls, probes, kills, capture_count;
static int report_fd = -1;
static pid_t owned_pid;
static char captures[2][64];
typedef struct { pid_t pid; char paths[2][64]; } CleanupReport;
static ssize_t probe_read(int fd, void* data, size_t count);
static ssize_t probe_write(int fd, const void* data, size_t count);
static pid_t probe_waitpid(pid_t pid, int* status, int options);
static int probe_fcntl(int fd, int command, ...);
static int probe_waitid(idtype_t type, id_t id, siginfo_t* info, int options);
static int probe_kill(pid_t pid, int signal);
static int probe_mkstemp(char* path);
static pid_t probe_fork(void);
#define read probe_read
#define write probe_write
#define waitpid probe_waitpid
#define fcntl probe_fcntl
#define waitid probe_waitid
#define kill probe_kill
#define mkstemp probe_mkstemp
#define fork probe_fork
#include "../../../stdlib/runtime.c"
#undef read
#undef write
#undef waitpid
#undef fcntl
#undef waitid
#undef kill
#undef mkstemp
#undef fork

static ssize_t probe_read(int fd, void* data, size_t count) {
    reads++;
    if (mode == 1 && reads == 1) { errno = EINTR; return -1; }
    if (mode == 2) count = 1;
    if (mode == 3 && reads == 1) { errno = EIO; return -1; }
    if ((mode == 8 || mode == 11 || mode == 12 || mode == 14 || mode == 15) && reads == 1) { errno = EIO; return -1; }
    if (mode == 4) { if (reads > 1) return 0; count = 1; }
    return read(fd, data, count);
}
static ssize_t probe_write(int fd, const void* data, size_t count) {
    writes++;
    if (mode == 1 && writes == 1) { errno = EINTR; return -1; }
    if (mode == 2) count = 1;
    return write(fd, data, count);
}
static pid_t probe_waitpid(pid_t pid, int* status, int options) {
    assert(pid == owned_pid && pid > 0 && options == 0);
    waits++;
    if (mode == 1 && waits == 1) { errno = EINTR; return -1; }
    if (mode == 5 && waits == 1) { errno = EIO; return -1; }
    if (mode == 9 || (mode == 13 && waits <= 2)) { errno = EIO; return -1; }
    if (mode == 10 && waits == 1) {
        assert(kill(pid, SIGKILL) == 0);
        assert(waitpid(pid, status, 0) == pid); owned_pid = 0;
        errno = ECHILD; return -1;
    }
    pid_t result = waitpid(pid, status, options);
    if (result == pid || (result < 0 && errno == ECHILD)) owned_pid = 0;
    return result;
}
static int probe_waitid(idtype_t type, id_t id, siginfo_t* info, int options) {
    assert(type == P_PID && (pid_t)id == owned_pid && (options & WNOWAIT));
    probes++;
    if (mode == 11 && probes == 1) {
        int status; assert(kill(owned_pid, SIGKILL) == 0);
        assert(waitpid(owned_pid, &status, 0) == owned_pid); owned_pid = 0;
        errno = ECHILD; return -1;
    }
    return waitid(type, id, info, options);
}
static int probe_kill(pid_t pid, int signal) {
    assert(pid > 0 && pid == owned_pid);
    siginfo_t info = {0};
    assert(waitid(P_PID, (id_t)pid, &info, WEXITED | WNOWAIT | WNOHANG) == 0);
    kills++;
    if (mode == 15) {
        assert(waitid(P_PID, (id_t)pid, &info, WEXITED | WNOWAIT) == 0);
        errno = EPERM; return -1;
    }
    if (mode == 8) { errno = EPERM; return -1; }
    if (mode == 12 && kills == 1) { errno = EIO; return -1; }
    if (mode == 14 && kills == 1) { errno = EINTR; return -1; }
    return kill(pid, signal);
}
static int probe_mkstemp(char* path) {
    int fd = mkstemp(path);
    if (fd >= 0) {
        assert(capture_count < 2 && strlen(path) < sizeof(captures[0]));
        strcpy(captures[capture_count++], path);
    }
    return fd;
}
static pid_t probe_fork(void) {
    pid_t pid = fork();
    if (pid > 0) {
        owned_pid = pid;
        if (report_fd >= 0) {
            CleanupReport report = { .pid = pid };
            memcpy(report.paths, captures, sizeof(captures));
            assert(write(report_fd, &report, sizeof(report)) == sizeof(report));
        }
    }
    return pid;
}
static int probe_fcntl(int fd, int command, ...) {
    va_list args;
    va_start(args, command);
    int value = va_arg(args, int);
    va_end(args);
    controls++;
    if (mode == 6 && controls == 1) { errno = EMFILE; return -1; }
    if (mode == 7 && controls == 1) { errno = EINTR; return -1; }
    return fcntl(fd, command, value);
}
static NQStr literal(const char* text) { return (NQStr){text, (int32_t)strlen(text), NULL}; }
static void no_child(void) {
    int status;
    assert(waitpid(-1, &status, WNOHANG) == -1 && errno == ECHILD);
}
static void check(int fault, const char* program, const char* arg, int expected) {
    mode = fault; reads = writes = waits = controls = probes = kills = capture_count = 0; owned_pid = 0;
    NQStr arguments[] = {literal(arg)};
    NQ_List__str args = {arguments, 1, 1};
    NQ_Result__process_result__io_err result = nq_run_process(literal(program), &args, literal("."));
    if (expected < 0) {
        assert(result.tag == NQ_Result__process_result__io_err_Tag_Err);
        nq_io_err_drop(&result.data.Err._0);
    } else {
        assert(result.tag == NQ_Result__process_result__io_err_Tag_Ok);
        assert(result.data.Ok._0.exit_code == expected);
        assert(nq_str_eq(result.data.Ok._0.stdout, literal("stdout\n")));
        assert(nq_str_eq(result.data.Ok._0.stderr, literal("stderr\n")));
        nq_process_result_drop(&result.data.Ok._0);
    }
    no_child();
    assert(owned_pid == 0);
    if (mode == 10 || mode == 11) assert(kills == 0);
    for (int index = 0; index < capture_count; index++) assert(access(captures[index], F_OK) == -1 && errno == ENOENT);
}
static void fatal_checks(void) {
    assert(prctl(PR_SET_CHILD_SUBREAPER, 1) == 0);
    for (int fault = 8; fault <= 9; fault++) {
        int report[2], output[2]; assert(pipe(report) == 0 && pipe(output) == 0);
        pid_t worker = fork(); assert(worker >= 0);
        if (worker == 0) {
            close(report[0]); close(output[0]); assert(dup2(output[1], 2) == 2); close(output[1]);
            report_fd = report[1]; assert(fcntl(report_fd, F_SETFD, FD_CLOEXEC) == 0);
            check(fault, "/proc/self/exe", "blocked", -1);
            _exit(99);
        }
        close(report[1]); close(output[1]);
        CleanupReport child; assert(read(report[0], &child, sizeof(child)) == sizeof(child)); close(report[0]);
        int status; assert(waitpid(worker, &status, 0) == worker);
        bool fatal = WIFEXITED(status) && WEXITSTATUS(status) == 1;
        bool unlinked = access(child.paths[0], F_OK) == -1 && errno == ENOENT;
        unlinked = unlinked && access(child.paths[1], F_OK) == -1 && errno == ENOENT;
        siginfo_t info = {0};
        bool anchored = waitid(P_PID, (id_t)child.pid, &info, WEXITED | WNOWAIT | WNOHANG) == 0;
        if (anchored) {
            assert(kill(child.pid, SIGKILL) == 0);
            assert(waitpid(child.pid, &status, 0) == child.pid);
        }
        char message[128]; ssize_t count = read(output[0], message, sizeof(message)); close(output[0]);
        const char* expected = "nauqtype runtime: process cleanup failed\n";
        assert(fatal && anchored && unlinked);
        assert(count == (ssize_t)strlen(expected) && memcmp(message, expected, (size_t)count) == 0);
        no_child();
    }
    assert(prctl(PR_SET_CHILD_SUBREAPER, 0) == 0);
}
static volatile sig_atomic_t alarms;
static void tick(int signal) { (void)signal; alarms++; }
int main(int argc, char** argv) {
    if (argc > 1) {
        if (strcmp(argv[1], "blocked") == 0) { for (;;) pause(); }
        struct timespec delay = {0, 60000000};
        while (nanosleep(&delay, &delay) != 0 && errno == EINTR) {}
        puts("stdout"); fputs("stderr\n", stderr);
        fflush(stdout); fflush(stderr);
        if (strcmp(argv[1], "signal") == 0) raise(SIGTERM);
        return 7;
    }
    for (int fault = 0; fault <= 7; fault++) {
        if (fault == 2 || fault == 4) check(fault, "/does-not-exist/nauqtype-m55", "exit", -1);
        else check(fault, "/proc/self/exe", "exit", fault == 3 || fault == 5 || fault == 6 ? -1 : 7);
    }
    check(1, "/does-not-exist/nauqtype-m55", "exit", -1);
    check(0, "/proc/self/exe", "signal", 128 + SIGTERM);
    for (int fault = 10; fault <= 15; fault++) check(fault, "/proc/self/exe", "exit", -1);
    fatal_checks();
    struct sigaction action = {0};
    action.sa_handler = tick; sigemptyset(&action.sa_mask);
    assert(sigaction(SIGALRM, &action, NULL) == 0);
    struct itimerval timer = {{0, 1000}, {0, 1000}};
    assert(setitimer(ITIMER_REAL, &timer, NULL) == 0);
    check(0, "/proc/self/exe", "exit", 7);
    timer = (struct itimerval){{0, 0}, {0, 0}};
    assert(setitimer(ITIMER_REAL, &timer, NULL) == 0);
    assert(alarms > 1 && waits > 1);
    pid_t closed = fork(); assert(closed >= 0);
    if (closed == 0) {
        close(0); close(1); close(2);
        check(0, "/proc/self/exe", "exit", 7);
        _exit(0);
    }
    int status; assert(waitpid(closed, &status, 0) == closed && status == 0);
    no_child();
    puts("legacy process interruption ok");
    return 0;
}
