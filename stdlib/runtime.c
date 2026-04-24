#include "runtime.h"

#include <stdio.h>

#ifdef _WIN32
#include <direct.h>
#include <errno.h>
#include <windows.h>
#else
#include <errno.h>
#include <fcntl.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>
#endif

static int nq_process_argc = 0;
static char** nq_process_argv = NULL;

static char* nq_dup_cstr(const char* text) {
    size_t len = strlen(text);
    char* copy = (char*)malloc(len + 1);
    if (copy == NULL) {
        fputs("nauqtype runtime: out of memory\n", stderr);
        exit(1);
    }
    memcpy(copy, text, len + 1);
    return copy;
}

static char* nq_str_to_cstr(NQStr text) {
    char* copy = (char*)malloc((size_t)text.len + 1);
    if (copy == NULL) {
        fputs("nauqtype runtime: out of memory\n", stderr);
        exit(1);
    }
    memcpy(copy, text.data, (size_t)text.len);
    copy[text.len] = '\0';
    return copy;
}

static NQ_Result__process_result__io_err nq_process_io_err(int32_t code, const char* text) {
    return (NQ_Result__process_result__io_err){
        .tag = NQ_Result__process_result__io_err_Tag_Err,
        .data.Err = { ._0 = nq_make_io_err(code, text) },
    };
}

static NQ_Result__process_result__io_err nq_process_ok(int32_t exit_code, NQStr stdout_text, NQStr stderr_text) {
    NQ_process_result value = { exit_code, stdout_text, stderr_text };
    return (NQ_Result__process_result__io_err){
        .tag = NQ_Result__process_result__io_err_Tag_Ok,
        .data.Ok = {
            ._0 = value,
        },
    };
}

static NQStr nq_empty_str(void) {
    return (NQStr){ .data = "", .len = 0 };
}

void* nq_realloc(void* ptr, size_t size) {
    void* next = realloc(ptr, size);
    if (next == NULL && size != 0) {
        fputs("nauqtype runtime: out of memory\n", stderr);
        exit(1);
    }
    return next;
}

void nq_init_process_args(int argc, char** argv) {
    nq_process_argc = argc;
    nq_process_argv = argv;
}

NQUnit nq_print_line(NQStr text) {
    fwrite(text.data, 1, (size_t)text.len, stdout);
    fputc('\n', stdout);
    fflush(stdout);
    return NQ_UNIT;
}

NQUnit nq_eprint_line(NQStr text) {
    fwrite(text.data, 1, (size_t)text.len, stderr);
    fputc('\n', stderr);
    fflush(stderr);
    return NQ_UNIT;
}

NQIoErr nq_make_io_err(int32_t code, const char* text) {
    return (NQIoErr){
        .code = code,
        .text = {
            .data = nq_dup_cstr(text),
            .len = (intptr_t)strlen(text),
        },
    };
}

NQStr nq_io_err_text(NQIoErr err) {
    return err.text;
}

NQ_List__str nq_list__str_make(void) {
    return (NQ_List__str){
        .data = NULL,
        .len = 0,
        .cap = 0,
    };
}

NQUnit nq_list__str_push(NQ_List__str* items, NQStr value) {
    if (items->len == items->cap) {
        int32_t next_cap = items->cap == 0 ? 4 : items->cap * 2;
        items->data = (NQStr*)nq_realloc(items->data, sizeof(NQStr) * (size_t)next_cap);
        items->cap = next_cap;
    }
    items->data[items->len] = value;
    items->len += 1;
    return NQ_UNIT;
}

int32_t nq_list__str_len(const NQ_List__str* items) {
    return items->len;
}

NQ_Option__str nq_list__str_get(const NQ_List__str* items, int32_t index) {
    if (index < 0 || index >= items->len) {
        return (NQ_Option__str){
            .tag = NQ_Option__str_Tag_None,
            .data.None = NQ_UNIT,
        };
    }
    return (NQ_Option__str){
        .tag = NQ_Option__str_Tag_Some,
        .data.Some = { ._0 = items->data[index] },
    };
}

int32_t nq_str_len(NQStr text) {
    return (int32_t)text.len;
}

NQStr nq_str_concat(NQStr left, NQStr right) {
    char* buffer = (char*)malloc((size_t)(left.len + right.len) + 1);
    if (buffer == NULL) {
        fputs("nauqtype runtime: out of memory\n", stderr);
        exit(1);
    }
    memcpy(buffer, left.data, (size_t)left.len);
    memcpy(buffer + left.len, right.data, (size_t)right.len);
    buffer[left.len + right.len] = '\0';
    return (NQStr){
        .data = buffer,
        .len = left.len + right.len,
    };
}

NQ_Result__str__io_err nq_read_file(NQStr path) {
    char* file_name = (char*)malloc((size_t)path.len + 1);
    FILE* handle;
    long file_size;
    char* buffer;
    size_t read_count;
    if (file_name == NULL) {
        fputs("nauqtype runtime: out of memory\n", stderr);
        exit(1);
    }
    memcpy(file_name, path.data, (size_t)path.len);
    file_name[path.len] = '\0';
    handle = fopen(file_name, "rb");
    free(file_name);
    if (handle == NULL) {
        return (NQ_Result__str__io_err){
            .tag = NQ_Result__str__io_err_Tag_Err,
            .data.Err = { ._0 = nq_make_io_err(1, "failed to open file") },
        };
    }
    if (fseek(handle, 0, SEEK_END) != 0) {
        fclose(handle);
        return (NQ_Result__str__io_err){
            .tag = NQ_Result__str__io_err_Tag_Err,
            .data.Err = { ._0 = nq_make_io_err(2, "failed to seek file") },
        };
    }
    file_size = ftell(handle);
    if (file_size < 0) {
        fclose(handle);
        return (NQ_Result__str__io_err){
            .tag = NQ_Result__str__io_err_Tag_Err,
            .data.Err = { ._0 = nq_make_io_err(3, "failed to size file") },
        };
    }
    if (fseek(handle, 0, SEEK_SET) != 0) {
        fclose(handle);
        return (NQ_Result__str__io_err){
            .tag = NQ_Result__str__io_err_Tag_Err,
            .data.Err = { ._0 = nq_make_io_err(4, "failed to rewind file") },
        };
    }
    buffer = (char*)malloc((size_t)file_size + 1);
    if (buffer == NULL) {
        fclose(handle);
        fputs("nauqtype runtime: out of memory\n", stderr);
        exit(1);
    }
    read_count = fread(buffer, 1, (size_t)file_size, handle);
    fclose(handle);
    if (read_count != (size_t)file_size) {
        free(buffer);
        return (NQ_Result__str__io_err){
            .tag = NQ_Result__str__io_err_Tag_Err,
            .data.Err = { ._0 = nq_make_io_err(5, "failed to read file") },
        };
    }
    buffer[file_size] = '\0';
    return (NQ_Result__str__io_err){
        .tag = NQ_Result__str__io_err_Tag_Ok,
        .data.Ok = {
            ._0 = {
                .data = buffer,
                .len = (intptr_t)file_size,
            },
        },
    };
}

NQ_Result__unit__io_err nq_write_file(NQStr path, NQStr text) {
    char* file_name = (char*)malloc((size_t)path.len + 1);
    FILE* handle;
    size_t written;
    if (file_name == NULL) {
        fputs("nauqtype runtime: out of memory\n", stderr);
        exit(1);
    }
    memcpy(file_name, path.data, (size_t)path.len);
    file_name[path.len] = '\0';
    handle = fopen(file_name, "wb");
    free(file_name);
    if (handle == NULL) {
        return (NQ_Result__unit__io_err){
            .tag = NQ_Result__unit__io_err_Tag_Err,
            .data.Err = { ._0 = nq_make_io_err(6, "failed to open file for write") },
        };
    }
    written = fwrite(text.data, 1, (size_t)text.len, handle);
    if (written != (size_t)text.len) {
        fclose(handle);
        return (NQ_Result__unit__io_err){
            .tag = NQ_Result__unit__io_err_Tag_Err,
            .data.Err = { ._0 = nq_make_io_err(7, "failed to write file") },
        };
    }
    if (fclose(handle) != 0) {
        return (NQ_Result__unit__io_err){
            .tag = NQ_Result__unit__io_err_Tag_Err,
            .data.Err = { ._0 = nq_make_io_err(8, "failed to close file after write") },
        };
    }
    return (NQ_Result__unit__io_err){
        .tag = NQ_Result__unit__io_err_Tag_Ok,
        .data.Ok = { ._0 = NQ_UNIT },
    };
}

int32_t nq_arg_count(void) {
    return (int32_t)nq_process_argc;
}

NQ_Option__str nq_arg_get(int32_t index) {
    if (index < 0 || index >= (int32_t)nq_process_argc || nq_process_argv == NULL) {
        return (NQ_Option__str){
            .tag = NQ_Option__str_Tag_None,
            .data.None = NQ_UNIT,
        };
    }
    return (NQ_Option__str){
        .tag = NQ_Option__str_Tag_Some,
        .data.Some = {
            ._0 = nq_str(nq_process_argv[index]),
        },
    };
}

static int nq_mkdir_single(const char* path) {
#ifdef _WIN32
    return _mkdir(path);
#else
    return mkdir(path, 0777);
#endif
}

NQ_Result__unit__io_err nq_create_dir_all(NQStr path) {
    char* value;
    size_t index;
    size_t start_index = 0;
    if (path.len == 0) {
        return (NQ_Result__unit__io_err){
            .tag = NQ_Result__unit__io_err_Tag_Ok,
            .data.Ok = { ._0 = NQ_UNIT },
        };
    }
    value = (char*)malloc((size_t)path.len + 1);
    if (value == NULL) {
        fputs("nauqtype runtime: out of memory\n", stderr);
        exit(1);
    }
    memcpy(value, path.data, (size_t)path.len);
    value[path.len] = '\0';
    if (path.len >= 3 && value[1] == ':' && (value[2] == '\\' || value[2] == '/')) {
        start_index = 3;
    } else if (path.len >= 1 && (value[0] == '\\' || value[0] == '/')) {
        start_index = 1;
    }
    for (index = start_index; index < (size_t)path.len; index += 1) {
        if (value[index] != '\\' && value[index] != '/') {
            continue;
        }
        if (index == 0) {
            continue;
        }
        {
            char saved = value[index];
            value[index] = '\0';
            if (strlen(value) > 0 && nq_mkdir_single(value) != 0 && errno != EEXIST) {
                free(value);
                return (NQ_Result__unit__io_err){
                    .tag = NQ_Result__unit__io_err_Tag_Err,
                    .data.Err = { ._0 = nq_make_io_err(9, "failed to create directory") },
                };
            }
            value[index] = saved;
        }
    }
    if (nq_mkdir_single(value) != 0 && errno != EEXIST) {
        free(value);
        return (NQ_Result__unit__io_err){
            .tag = NQ_Result__unit__io_err_Tag_Err,
            .data.Err = { ._0 = nq_make_io_err(9, "failed to create directory") },
        };
    }
    free(value);
    return (NQ_Result__unit__io_err){
        .tag = NQ_Result__unit__io_err_Tag_Ok,
        .data.Ok = { ._0 = NQ_UNIT },
    };
}

static bool nq_try_read_text_file(const char* path, NQStr* out_text, NQIoErr* out_err) {
    NQ_Result__str__io_err result = nq_read_file((NQStr){
        .data = path,
        .len = (intptr_t)strlen(path),
    });
    if (result.tag == NQ_Result__str__io_err_Tag_Ok) {
        *out_text = result.data.Ok._0;
        return true;
    }
    *out_err = result.data.Err._0;
    return false;
}

#ifdef _WIN32
static char* nq_quote_windows_arg(const char* arg) {
    bool needs_quotes = arg[0] == '\0';
    const char* cursor = arg;
    while (*cursor != '\0') {
        if (*cursor == ' ' || *cursor == '\t' || *cursor == '"') {
            needs_quotes = true;
        }
        cursor += 1;
    }
    if (!needs_quotes) {
        return nq_dup_cstr(arg);
    }

    {
        size_t len = strlen(arg);
        char* out = (char*)malloc((len * 2) + 3);
        size_t out_index = 0;
        size_t slash_count = 0;
        size_t index = 0;
        if (out == NULL) {
            fputs("nauqtype runtime: out of memory\n", stderr);
            exit(1);
        }
        out[out_index++] = '"';
        while (arg[index] != '\0') {
            char ch = arg[index];
            if (ch == '\\') {
                slash_count += 1;
            } else if (ch == '"') {
                size_t slash_index = 0;
                while (slash_index < (slash_count * 2) + 1) {
                    out[out_index++] = '\\';
                    slash_index += 1;
                }
                out[out_index++] = '"';
                slash_count = 0;
            } else {
                while (slash_count > 0) {
                    out[out_index++] = '\\';
                    slash_count -= 1;
                }
                out[out_index++] = ch;
            }
            index += 1;
        }
        while (slash_count > 0) {
            out[out_index++] = '\\';
            out[out_index++] = '\\';
            slash_count -= 1;
        }
        out[out_index++] = '"';
        out[out_index] = '\0';
        return out;
    }
}

static char* nq_join_windows_command(const char* program, const NQ_List__str* args) {
    char* command = nq_quote_windows_arg(program);
    int32_t index = 0;
    while (index < args->len) {
        char* arg_cstr = nq_str_to_cstr(args->data[index]);
        char* quoted = nq_quote_windows_arg(arg_cstr);
        size_t command_len = strlen(command);
        size_t quoted_len = strlen(quoted);
        command = (char*)nq_realloc(command, command_len + quoted_len + 2);
        command[command_len] = ' ';
        memcpy(command + command_len + 1, quoted, quoted_len + 1);
        free(arg_cstr);
        free(quoted);
        index += 1;
    }
    return command;
}

static char* nq_make_windows_temp_file(const char* prefix) {
    char buffer[MAX_PATH + 1];
    char path[MAX_PATH + 1];
    DWORD len = GetTempPathA(MAX_PATH, buffer);
    if (len == 0 || len > MAX_PATH) {
        return NULL;
    }
    if (GetTempFileNameA(buffer, prefix, 0, path) == 0) {
        return NULL;
    }
    return nq_dup_cstr(path);
}
#endif

NQ_Result__process_result__io_err nq_run_process(NQStr program, const NQ_List__str* args, NQStr cwd) {
    char* program_cstr = nq_str_to_cstr(program);
    char* cwd_cstr = nq_str_to_cstr(cwd);
    NQStr stdout_text = nq_empty_str();
    NQStr stderr_text = nq_empty_str();
    NQIoErr io_err;
#ifdef _WIN32
    char* command = nq_join_windows_command(program_cstr, args);
    char* stdout_path = nq_make_windows_temp_file("nqo");
    char* stderr_path = nq_make_windows_temp_file("nqe");
    SECURITY_ATTRIBUTES security = {0};
    STARTUPINFOA startup = {0};
    PROCESS_INFORMATION process = {0};
    HANDLE stdout_handle;
    HANDLE stderr_handle;
    DWORD exit_code = 0;
    BOOL created;

    if (stdout_path == NULL || stderr_path == NULL) {
        free(program_cstr);
        free(cwd_cstr);
        free(command);
        free(stdout_path);
        free(stderr_path);
        return nq_process_io_err(10, "failed to allocate temporary output files");
    }

    security.nLength = sizeof(security);
    security.bInheritHandle = TRUE;
    stdout_handle = CreateFileA(stdout_path, GENERIC_WRITE, FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE, &security, CREATE_ALWAYS, FILE_ATTRIBUTE_TEMPORARY, NULL);
    if (stdout_handle == INVALID_HANDLE_VALUE) {
        free(program_cstr);
        free(cwd_cstr);
        free(command);
        DeleteFileA(stdout_path);
        DeleteFileA(stderr_path);
        free(stdout_path);
        free(stderr_path);
        return nq_process_io_err((int32_t)GetLastError(), "failed to open temporary stdout capture");
    }
    stderr_handle = CreateFileA(stderr_path, GENERIC_WRITE, FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE, &security, CREATE_ALWAYS, FILE_ATTRIBUTE_TEMPORARY, NULL);
    if (stderr_handle == INVALID_HANDLE_VALUE) {
        CloseHandle(stdout_handle);
        free(program_cstr);
        free(cwd_cstr);
        free(command);
        DeleteFileA(stdout_path);
        DeleteFileA(stderr_path);
        free(stdout_path);
        free(stderr_path);
        return nq_process_io_err((int32_t)GetLastError(), "failed to open temporary stderr capture");
    }

    startup.cb = sizeof(startup);
    startup.dwFlags = STARTF_USESTDHANDLES;
    startup.hStdInput = GetStdHandle(STD_INPUT_HANDLE);
    startup.hStdOutput = stdout_handle;
    startup.hStdError = stderr_handle;
    created = CreateProcessA(
        NULL,
        command,
        NULL,
        NULL,
        TRUE,
        0,
        NULL,
        cwd_cstr[0] == '\0' ? NULL : cwd_cstr,
        &startup,
        &process
    );
    CloseHandle(stdout_handle);
    CloseHandle(stderr_handle);
    if (!created) {
        int32_t error_code = (int32_t)GetLastError();
        free(program_cstr);
        free(cwd_cstr);
        free(command);
        DeleteFileA(stdout_path);
        DeleteFileA(stderr_path);
        free(stdout_path);
        free(stderr_path);
        return nq_process_io_err(error_code, "failed to start process");
    }

    WaitForSingleObject(process.hProcess, INFINITE);
    GetExitCodeProcess(process.hProcess, &exit_code);
    CloseHandle(process.hProcess);
    CloseHandle(process.hThread);

    if (!nq_try_read_text_file(stdout_path, &stdout_text, &io_err)) {
        free(program_cstr);
        free(cwd_cstr);
        free(command);
        DeleteFileA(stdout_path);
        DeleteFileA(stderr_path);
        free(stdout_path);
        free(stderr_path);
        return (NQ_Result__process_result__io_err){
            .tag = NQ_Result__process_result__io_err_Tag_Err,
            .data.Err = { ._0 = io_err },
        };
    }
    if (!nq_try_read_text_file(stderr_path, &stderr_text, &io_err)) {
        free(program_cstr);
        free(cwd_cstr);
        free(command);
        DeleteFileA(stdout_path);
        DeleteFileA(stderr_path);
        free(stdout_path);
        free(stderr_path);
        return (NQ_Result__process_result__io_err){
            .tag = NQ_Result__process_result__io_err_Tag_Err,
            .data.Err = { ._0 = io_err },
        };
    }

    DeleteFileA(stdout_path);
    DeleteFileA(stderr_path);
    free(program_cstr);
    free(cwd_cstr);
    free(command);
    free(stdout_path);
    free(stderr_path);
    return nq_process_ok((int32_t)exit_code, stdout_text, stderr_text);
#else
    char stdout_template[] = "/tmp/nq-stdout-XXXXXX";
    char stderr_template[] = "/tmp/nq-stderr-XXXXXX";
    int stdout_fd = mkstemp(stdout_template);
    int stderr_fd = mkstemp(stderr_template);
    int error_pipe[2] = {-1, -1};
    char** argv = NULL;
    pid_t pid;
    int status = 0;
    ssize_t error_read = 0;
    int child_errno = 0;
    int32_t arg_count = args->len;
    int32_t index = 0;

    if (stdout_fd < 0 || stderr_fd < 0) {
        if (stdout_fd >= 0) {
            close(stdout_fd);
            unlink(stdout_template);
        }
        if (stderr_fd >= 0) {
            close(stderr_fd);
            unlink(stderr_template);
        }
        free(program_cstr);
        free(cwd_cstr);
        return nq_process_io_err(errno, "failed to allocate temporary output files");
    }

    argv = (char**)calloc((size_t)arg_count + 2, sizeof(char*));
    if (argv == NULL) {
        close(stdout_fd);
        close(stderr_fd);
        unlink(stdout_template);
        unlink(stderr_template);
        free(program_cstr);
        free(cwd_cstr);
        fputs("nauqtype runtime: out of memory\n", stderr);
        exit(1);
    }
    argv[0] = program_cstr;
    while (index < arg_count) {
        argv[index + 1] = nq_str_to_cstr(args->data[index]);
        index += 1;
    }
    argv[arg_count + 1] = NULL;

    if (pipe(error_pipe) != 0) {
        index = 0;
        while (index < arg_count) {
            free(argv[index + 1]);
            index += 1;
        }
        free(argv);
        close(stdout_fd);
        close(stderr_fd);
        unlink(stdout_template);
        unlink(stderr_template);
        free(program_cstr);
        free(cwd_cstr);
        return nq_process_io_err(errno, "failed to create process error pipe");
    }
    fcntl(error_pipe[1], F_SETFD, FD_CLOEXEC);

    pid = fork();
    if (pid < 0) {
        close(error_pipe[0]);
        close(error_pipe[1]);
        index = 0;
        while (index < arg_count) {
            free(argv[index + 1]);
            index += 1;
        }
        free(argv);
        close(stdout_fd);
        close(stderr_fd);
        unlink(stdout_template);
        unlink(stderr_template);
        free(program_cstr);
        free(cwd_cstr);
        return nq_process_io_err(errno, "failed to fork process");
    }

    if (pid == 0) {
        close(error_pipe[0]);
        if (cwd_cstr[0] != '\0' && chdir(cwd_cstr) != 0) {
            int err = errno;
            write(error_pipe[1], &err, sizeof(err));
            _exit(127);
        }
        if (dup2(stdout_fd, STDOUT_FILENO) < 0 || dup2(stderr_fd, STDERR_FILENO) < 0) {
            int err = errno;
            write(error_pipe[1], &err, sizeof(err));
            _exit(127);
        }
        close(stdout_fd);
        close(stderr_fd);
        execvp(program_cstr, argv);
        {
            int err = errno;
            write(error_pipe[1], &err, sizeof(err));
        }
        _exit(127);
    }

    close(error_pipe[1]);
    close(stdout_fd);
    close(stderr_fd);
    error_read = read(error_pipe[0], &child_errno, sizeof(child_errno));
    close(error_pipe[0]);
    waitpid(pid, &status, 0);

    index = 0;
    while (index < arg_count) {
        free(argv[index + 1]);
        index += 1;
    }
    free(argv);

    if (error_read > 0) {
        unlink(stdout_template);
        unlink(stderr_template);
        free(program_cstr);
        free(cwd_cstr);
        return nq_process_io_err(child_errno, "failed to start process");
    }

    if (!nq_try_read_text_file(stdout_template, &stdout_text, &io_err)) {
        unlink(stdout_template);
        unlink(stderr_template);
        free(program_cstr);
        free(cwd_cstr);
        return (NQ_Result__process_result__io_err){
            .tag = NQ_Result__process_result__io_err_Tag_Err,
            .data.Err = { ._0 = io_err },
        };
    }
    if (!nq_try_read_text_file(stderr_template, &stderr_text, &io_err)) {
        unlink(stdout_template);
        unlink(stderr_template);
        free(program_cstr);
        free(cwd_cstr);
        return (NQ_Result__process_result__io_err){
            .tag = NQ_Result__process_result__io_err_Tag_Err,
            .data.Err = { ._0 = io_err },
        };
    }

    unlink(stdout_template);
    unlink(stderr_template);
    free(program_cstr);
    free(cwd_cstr);
    if (WIFEXITED(status)) {
        return nq_process_ok(WEXITSTATUS(status), stdout_text, stderr_text);
    }
    if (WIFSIGNALED(status)) {
        return nq_process_ok(128 + WTERMSIG(status), stdout_text, stderr_text);
    }
    return nq_process_ok(1, stdout_text, stderr_text);
#endif
}

NQ_Option__i32 nq_str_get(NQStr text, int32_t index) {
    if (index < 0 || index >= (int32_t)text.len) {
        return (NQ_Option__i32){
            .tag = NQ_Option__i32_Tag_None,
            .data.None = NQ_UNIT,
        };
    }
    return (NQ_Option__i32){
        .tag = NQ_Option__i32_Tag_Some,
        .data.Some = { ._0 = (unsigned char)text.data[index] },
    };
}

NQ_Option__str nq_str_slice(NQStr text, int32_t start, int32_t end) {
    if (start < 0 || end < start || end > (int32_t)text.len) {
        return (NQ_Option__str){
            .tag = NQ_Option__str_Tag_None,
            .data.None = NQ_UNIT,
        };
    }
    return (NQ_Option__str){
        .tag = NQ_Option__str_Tag_Some,
        .data.Some = {
            ._0 = {
                .data = text.data + start,
                .len = (intptr_t)(end - start),
            },
        },
    };
}
