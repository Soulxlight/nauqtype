#define _POSIX_C_SOURCE 200809L
/* Exercise non-Linux API branches on the host; not a foreign-target ABI test. */
#undef __linux__
#include <assert.h>
#include "../../../stdlib/runtime.c"

int main(void) {
    NQ_Result__i64__io_err wall = nq_wall_time_ns();
    assert(wall.tag == NQ_Result__i64__io_err_Tag_Err && nq_str_eq(wall.data.Err._0.kind, nq_str("unsupported")));
    nq_result__i64__io_err_drop(&wall);
    NQ_Result__instant__io_err instant = nq_monotonic_now();
    assert(instant.tag == NQ_Result__instant__io_err_Tag_Err && nq_str_eq(instant.data.Err._0.kind, nq_str("unsupported")));
    nq_result__instant__io_err_drop(&instant);
    instant = nq_deadline_after((NQ_duration){0});
    assert(instant.tag == NQ_Result__instant__io_err_Tag_Err && nq_str_eq(instant.data.Err._0.kind, nq_str("unsupported")));
    nq_result__instant__io_err_drop(&instant);
    NQ_Result__unit__io_err unit = nq_sleep_for((NQ_duration){0});
    assert(unit.tag == NQ_Result__unit__io_err_Tag_Err && nq_str_eq(unit.data.Err._0.kind, nq_str("unsupported")));
    nq_result__unit__io_err_drop(&unit);
    NQ_List__str list = {0};
    NQ_Result__process__io_err start = nq_process_start(nq_str("/bin/true"), &list, nq_str("."), &list,
        (NQ_Option__str){ .tag = NQ_Option__str_Tag_None }, false, 0);
    assert(start.tag == NQ_Result__process__io_err_Tag_Err && nq_str_eq(start.data.Err._0.kind, nq_str("unsupported")));
    nq_result__process__io_err_drop(&start);
    NQ_process child = {0};
    NQ_Result__process_outcome__io_err wait = nq_process_wait(child, (NQ_Option__instant){ .tag = NQ_Option__instant_Tag_None });
    assert(wait.tag == NQ_Result__process_outcome__io_err_Tag_Err && nq_str_eq(wait.data.Err._0.kind, nq_str("unsupported")));
    nq_result__process_outcome__io_err_drop(&wait);
    unit = nq_process_terminate(&child);
    assert(unit.tag == NQ_Result__unit__io_err_Tag_Err && nq_str_eq(unit.data.Err._0.kind, nq_str("unsupported")));
    nq_result__unit__io_err_drop(&unit);
    assert(nq_duration_from_ns(0).tag == NQ_Option__duration_Tag_Some);
    puts("native platform ok");
    return 0;
}
