#include "runtime.h"

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
