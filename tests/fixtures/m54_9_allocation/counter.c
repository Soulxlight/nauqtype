#include "runtime.c"
#include <assert.h>
int main(void) {
    NQAllocStatus status;
    char* ptr;
    assert(nq_test_allocation_count == 0);
    NQIoErr os = nq_errno_io_err("read_file", NULL, NULL, ENOMEM);
    assert(os.code == ENOMEM && os.os_code == ENOMEM && os.text.owner == NULL);
    assert(nq_str_eq(os.text, nq_str("out of memory")));
    nq_io_err_drop(&os);
    os = nq_errno_io_err_with_detail("read_file", NULL, NULL, ENOMEM, "failed to open");
    assert(os.code == ENOMEM && os.text.owner == NULL);
    nq_io_err_drop(&os);
    NQ_Result__process_result__io_err process = nq_process_io_err(ENOMEM, "fork failed");
    assert(process.tag == NQ_Result__process_result__io_err_Tag_Err && process.data.Err._0.text.owner == NULL);
    nq_result__process_result__io_err_drop(&process);
    assert(nq_test_allocation_count == 0);
    assert(nq_try_realloc(NULL, 129, &status) == NULL && status == NQ_ALLOC_SIZE);
    assert(nq_test_allocation_count == 0);
    assert(nq_try_realloc(NULL, 0, &status) == NULL && status == NQ_ALLOC_OK);
    assert(nq_test_allocation_count == 0);
    ptr = nq_try_realloc(NULL, 1, &status);
    assert(status == NQ_ALLOC_OK && ptr != NULL && nq_test_allocation_count == 1);
    ptr[0] = 'x';
    ptr = nq_try_realloc(ptr, 2, &status);
    assert(status == NQ_ALLOC_OK && ptr[0] == 'x' && nq_test_allocation_count == 2);
    assert(nq_try_realloc(ptr, 129, &status) == NULL && status == NQ_ALLOC_SIZE);
    assert(nq_try_realloc(ptr, 3, &status) == NULL && status == NQ_ALLOC_OOM && ptr[0] == 'x');
    NQByteBuffer buffer = {(unsigned char*)ptr, 1, 2};
    assert(nq_buffer_reserve(&buffer, 2, 128) == NQ_ALLOC_OOM);
    assert(buffer.data == (unsigned char*)ptr && buffer.len == 1 && buffer.cap == 2 && ptr[0] == 'x');
    assert(nq_test_allocation_count == 2);
    char oversized[130];
    memset(oversized, 'x', 129); oversized[129] = '\0';
    NQIoErr sized = nq_make_io_err(9, oversized);
    assert(sized.code == 0 && sized.os_code == 0 && sized.text.owner == NULL);
    assert(nq_str_eq(sized.text, nq_str("size limit exceeded")));
    nq_io_err_drop(&sized);
    NQIoErr err = nq_make_io_err(9, "error");
    assert(err.code == ENOMEM && err.os_code == ENOMEM && err.text.owner == NULL);
    assert(nq_str_eq(err.text, nq_str("out of memory")));
    nq_io_err_drop(&err);
    assert(nq_test_allocation_count == 2);
    assert(nq_try_realloc(ptr, 0, &status) == NULL && status == NQ_ALLOC_OK);
    assert(nq_test_allocation_count == 2);
    puts("counter: exactly two successful allocations, zero/size rejection uncounted, fallback allocation-free");
    return 0;
}
