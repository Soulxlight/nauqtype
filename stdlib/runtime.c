#include "runtime.h"

#ifdef _WIN32
#include <direct.h>
#include <errno.h>
#else
#include <errno.h>
#include <sys/stat.h>
#include <sys/types.h>
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
