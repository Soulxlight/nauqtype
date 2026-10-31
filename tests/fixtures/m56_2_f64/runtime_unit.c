/* C-level unit test for the M56.2 scalar f64 runtime builtins.
 *
 * Build (the shipped flags; runtime.c is linked, not included):
 *   cc -std=c11 -O2 -D_POSIX_C_SOURCE=200809L -I<stdlib> -pedantic-errors \
 *      -Wall -Wextra -Werror runtime_unit.c <stdlib>/runtime.c -o runtime_unit
 * No libm is linked and no <math.h> function is used.
 *
 * Run with no argument for every group; one PASS/FAIL/SKIP line per group, exit
 * status 0 only when no group failed. Two extra modes exist for the
 * allocation-failure proof and need a build with -DNQ_TEST_ALLOC_FAIL_AFTER=2:
 *   oom-heap      a >= 512-byte f64_from_str input must die with exit 1 and
 *                 "nauqtype runtime: out of memory" on the third allocation
 *   oom-boundary  a 511-byte input (stack path) succeeds, a 512-byte input dies
 *
 * Expected values in runtime_vectors.h come from Python 3 repr()/float(); the
 * generator is not part of the tree. */
#ifndef _POSIX_C_SOURCE
#define _POSIX_C_SOURCE 200809L
#endif
#include "runtime.h"

#include <float.h>
#include <locale.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "runtime_vectors.h"

static int group_failures;
static int group_checks;
static int total_failures;
static int printed_in_group;

static void group_begin(void) {
    group_failures = 0;
    group_checks = 0;
    printed_in_group = 0;
}

static void note_fail(const char* what, const char* detail) {
    group_failures += 1;
    if (printed_in_group < 8) {
        printf("    mismatch: %s%s%s\n", what, detail[0] != '\0' ? ": " : "", detail);
        printed_in_group += 1;
    }
}

static void check(bool ok, const char* what) {
    group_checks += 1;
    if (!ok) note_fail(what, "");
}

static void group_end(const char* name) {
    if (group_failures == 0) {
        printf("PASS %s (%d checks)\n", name, group_checks);
    } else {
        printf("FAIL %s (%d of %d checks failed)\n", name, group_failures, group_checks);
        total_failures += 1;
    }
}

static uint64_t bits_of(double value) {
    uint64_t bits;
    memcpy(&bits, &value, sizeof bits);
    return bits;
}

static double double_of(uint64_t bits) {
    double value;
    memcpy(&value, &bits, sizeof value);
    return value;
}

/* A view of exactly len bytes in an exactly len-byte heap block with no
 * terminator, so any read at or past len is an AddressSanitizer error. */
typedef struct {
    NQStr view;
    char* block;
} Exact;

static Exact exact_view(const char* data, size_t len) {
    Exact e;
    e.block = (char*)malloc(len == 0 ? 1 : len);
    if (e.block == NULL) abort();
    if (len != 0) memcpy(e.block, data, len);
    e.view.data = e.block;
    e.view.len = (intptr_t)len;
    e.view.owner = NULL;
    return e;
}

static void exact_free(Exact* e) {
    free(e->block);
    e->block = NULL;
}

/* Render and compare against an expected C string. */
static bool render_equals(double value, const char* expect) {
    NQStr s = nq_str_from_f64(value);
    bool ok = s.owner != NULL && (size_t)s.len == strlen(expect) &&
              memcmp(s.data, expect, (size_t)s.len) == 0;
    if (!ok) {
        char detail[160];
        (void)snprintf(detail, sizeof detail, "bits %016llx got \"%.*s\" want \"%s\"",
                       (unsigned long long)bits_of(value), (int)s.len, s.data, expect);
        note_fail("render", detail);
    }
    nq_str_drop(&s);
    return ok;
}

static void expect_parse(const char* data, size_t len, bool ok, uint64_t bits) {
    Exact e = exact_view(data, len);
    NQ_Option__f64 r = nq_f64_from_str(e.view);
    group_checks += 1;
    if (!ok) {
        if (r.tag != NQ_Option__f64_Tag_None) {
            char detail[96];
            (void)snprintf(detail, sizeof detail, "len %zu expected none got bits %016llx", len,
                           (unsigned long long)bits_of(r.data.Some._0));
            note_fail("parse", detail);
        }
    } else if (r.tag != NQ_Option__f64_Tag_Some) {
        char detail[96];
        (void)snprintf(detail, sizeof detail, "len %zu expected bits %016llx got none", len,
                       (unsigned long long)bits);
        note_fail("parse", detail);
    } else if (bits_of(r.data.Some._0) != bits) {
        char detail[128];
        (void)snprintf(detail, sizeof detail, "len %zu want %016llx got %016llx", len,
                       (unsigned long long)bits, (unsigned long long)bits_of(r.data.Some._0));
        note_fail("parse", detail);
    }
    exact_free(&e);
}

static void run_render_vectors(void) {
    for (size_t i = 0; i < sizeof nq_render_vectors / sizeof nq_render_vectors[0]; i += 1) {
        group_checks += 1;
        (void)render_equals(double_of(nq_render_vectors[i].bits), nq_render_vectors[i].expect);
    }
}

static void run_parse_vectors(void) {
    for (size_t i = 0; i < sizeof nq_parse_vectors / sizeof nq_parse_vectors[0]; i += 1) {
        expect_parse(nq_parse_vectors[i].data, nq_parse_vectors[i].len, nq_parse_vectors[i].ok != 0,
                     nq_parse_vectors[i].bits);
    }
}

/* ------------------------------------------------------------------ groups */

static void group_from_i32(void) {
    static const struct { int32_t v; const char* text; } cases[] = {
        { INT32_MIN, "-2147483648" }, { -1, "-1" }, { 0, "0" }, { INT32_MAX, "2147483647" },
        { 1, "1" }, { 16777217, "16777217" }, { -16777217, "-16777217" },
    };
    group_begin();
    for (size_t i = 0; i < sizeof cases / sizeof cases[0]; i += 1) {
        double d = nq_f64_from_i32(cases[i].v);
        NQ_Option__i32 back = nq_f64_trunc_i32(d);
        check(back.tag == NQ_Option__i32_Tag_Some && back.data.Some._0 == cases[i].v, "i32 -> f64 -> i32");
        check(render_equals(d, cases[i].text), "i32 render");
        check(d == (double)cases[i].v, "exact value");
    }
    group_end("f64_from_i32");
}

static bool is_some_f64(NQ_Option__f64 o, double want) {
    return o.tag == NQ_Option__f64_Tag_Some && bits_of(o.data.Some._0) == bits_of(want);
}

static void group_from_i64(void) {
    group_begin();
    check(is_some_f64(nq_f64_from_i64(0), 0.0), "0");
    check(is_some_f64(nq_f64_from_i64(-1), -1.0), "-1");
    check(is_some_f64(nq_f64_from_i64((int64_t)1 << 53), 9007199254740992.0), "2^53 some");
    check(nq_f64_from_i64(((int64_t)1 << 53) + 1).tag == NQ_Option__f64_Tag_None, "2^53+1 none");
    check(is_some_f64(nq_f64_from_i64(((int64_t)1 << 53) + 2), 9007199254740994.0), "2^53+2 some");
    check(nq_f64_from_i64(((int64_t)1 << 53) + 3).tag == NQ_Option__f64_Tag_None, "2^53+3 none");
    check(nq_f64_from_i64(INT64_MAX).tag == NQ_Option__f64_Tag_None, "INT64_MAX none");
    check(nq_f64_from_i64(INT64_MAX - 1).tag == NQ_Option__f64_Tag_None, "INT64_MAX-1 none");
    check(nq_f64_from_i64(INT64_MAX - 1024).tag == NQ_Option__f64_Tag_None, "INT64_MAX-1024 none");
    check(is_some_f64(nq_f64_from_i64(INT64_MAX - 1023), 9223372036854774784.0), "INT64_MAX-1023 some");
    check(is_some_f64(nq_f64_from_i64((int64_t)0x7FFFFFFFFFFFFC00), 9223372036854774784.0),
          "largest i64 exactly representable below 2^63 some");
    check(nq_f64_from_i64((int64_t)0x7FFFFFFFFFFFFC01).tag == NQ_Option__f64_Tag_None, "one above it none");
    check(is_some_f64(nq_f64_from_i64(INT64_MIN), -9223372036854775808.0), "INT64_MIN some(-2^63)");
    check(is_some_f64(nq_f64_from_i64(INT64_MIN + 1024), -9223372036854774784.0), "INT64_MIN+1024 some");
    check(nq_f64_from_i64(INT64_MIN + 1).tag == NQ_Option__f64_Tag_None, "INT64_MIN+1 none");
    check(is_some_f64(nq_f64_from_i64(INT32_MAX), 2147483647.0), "INT32_MAX");
    check(is_some_f64(nq_f64_from_i64((int64_t)3 << 60), 3458764513820540928.0), "3*2^60 some");
    group_end("f64_from_i64");
}

static bool is_some_i64(NQ_Option__i64 o, int64_t want) {
    return o.tag == NQ_Option__i64_Tag_Some && o.data.Some._0 == want;
}

static void group_trunc_i64(void) {
    volatile double zero = 0.0;
    double inf = 1.0 / zero;
    double nan = zero / zero;
    group_begin();
    check(nq_f64_trunc_i64(0x1p63).tag == NQ_Option__i64_Tag_None, "+2^63 none");
    check(is_some_i64(nq_f64_trunc_i64(-0x1p63), INT64_MIN), "-2^63 some(INT64_MIN)");
    check(is_some_i64(nq_f64_trunc_i64(9223372036854774784.0), INT64_C(9223372036854774784)),
          "largest double below 2^63");
    check(nq_f64_trunc_i64(-9223372036854777856.0).tag == NQ_Option__i64_Tag_None, "below -2^63 none");
    check(nq_f64_trunc_i64(nan).tag == NQ_Option__i64_Tag_None, "NaN none");
    check(nq_f64_trunc_i64(-nan).tag == NQ_Option__i64_Tag_None, "-NaN none");
    check(nq_f64_trunc_i64(inf).tag == NQ_Option__i64_Tag_None, "+inf none");
    check(nq_f64_trunc_i64(-inf).tag == NQ_Option__i64_Tag_None, "-inf none");
    check(is_some_i64(nq_f64_trunc_i64(0.0), 0), "0");
    check(is_some_i64(nq_f64_trunc_i64(-0.0), 0), "-0");
    check(is_some_i64(nq_f64_trunc_i64(0.9999999999999999), 0), "0.99.. truncates to 0");
    check(is_some_i64(nq_f64_trunc_i64(-0.9999999999999999), 0), "-0.99.. truncates to 0");
    check(is_some_i64(nq_f64_trunc_i64(1.5), 1), "1.5");
    check(is_some_i64(nq_f64_trunc_i64(-1.5), -1), "-1.5");
    check(is_some_i64(nq_f64_trunc_i64(4503599627370495.5), INT64_C(4503599627370495)), "2^52-0.5");
    check(is_some_i64(nq_f64_trunc_i64(9007199254740992.0), INT64_C(9007199254740992)), "2^53");
    check(is_some_i64(nq_f64_trunc_i64(-9007199254740992.0), -INT64_C(9007199254740992)), "-2^53");
    check(is_some_i64(nq_f64_trunc_i64(5e-324), 0), "smallest subnormal");
    check(nq_f64_trunc_i64(DBL_MAX).tag == NQ_Option__i64_Tag_None, "DBL_MAX none");
    check(nq_f64_trunc_i64(-DBL_MAX).tag == NQ_Option__i64_Tag_None, "-DBL_MAX none");
    group_end("f64_trunc_i64");
}

static bool is_some_i32(NQ_Option__i32 o, int32_t want) {
    return o.tag == NQ_Option__i32_Tag_Some && o.data.Some._0 == want;
}

static void group_trunc_i32(void) {
    volatile double zero = 0.0;
    double inf = 1.0 / zero;
    double nan = zero / zero;
    group_begin();
    check(is_some_i32(nq_f64_trunc_i32(2147483647.9), INT32_MAX), "2147483647.9");
    check(nq_f64_trunc_i32(2147483648.0).tag == NQ_Option__i32_Tag_None, "2147483648.0 none");
    check(is_some_i32(nq_f64_trunc_i32(-2147483648.9), INT32_MIN), "-2147483648.9");
    check(is_some_i32(nq_f64_trunc_i32(-2147483648.0), INT32_MIN), "-2147483648.0");
    check(nq_f64_trunc_i32(-2147483649.0).tag == NQ_Option__i32_Tag_None, "-2147483649.0 none");
    check(is_some_i32(nq_f64_trunc_i32(-2147483648.99999), INT32_MIN), "-2147483648.99999");
    check(is_some_i32(nq_f64_trunc_i32(-0.5), 0), "-0.5 gives 0");
    check(is_some_i32(nq_f64_trunc_i32(0.5), 0), "0.5 gives 0");
    check(is_some_i32(nq_f64_trunc_i32(-0.0), 0), "-0.0 gives 0");
    check(is_some_i32(nq_f64_trunc_i32(-1.9), -1), "-1.9");
    check(is_some_i32(nq_f64_trunc_i32(1.9), 1), "1.9");
    check(is_some_i32(nq_f64_trunc_i32(2147483647.0), INT32_MAX), "INT32_MAX");
    check(nq_f64_trunc_i32(nan).tag == NQ_Option__i32_Tag_None, "NaN none");
    check(nq_f64_trunc_i32(inf).tag == NQ_Option__i32_Tag_None, "+inf none");
    check(nq_f64_trunc_i32(-inf).tag == NQ_Option__i32_Tag_None, "-inf none");
    check(nq_f64_trunc_i32(1e300).tag == NQ_Option__i32_Tag_None, "1e300 none");
    check(nq_f64_trunc_i32(-1e300).tag == NQ_Option__i32_Tag_None, "-1e300 none");
    check(is_some_i32(nq_f64_trunc_i32(5e-324), 0), "smallest subnormal");
    group_end("f64_trunc_i32");
}

static void group_render_oracle(void) {
    group_begin();
    check(sizeof nq_render_vectors / sizeof nq_render_vectors[0] >= 60, "at least 60 render vectors");
    run_render_vectors();
    /* Every example in the contract, by literal. */
    check(render_equals(0.1, "0.1"), "0.1");
    check(render_equals(100.0, "100"), "100.0");
    check(render_equals(1.0e21, "1e+21"), "1.0e21");
    check(render_equals(1.0e-7, "1e-7"), "1.0e-7");
    check(render_equals(5.0e-324, "5e-324"), "5.0e-324");
    check(render_equals(DBL_MAX, "1.7976931348623157e+308"), "max finite");
    check(render_equals(1.0e-6, "0.000001"), "1.0e-6");
    check(render_equals(1.0e20, "100000000000000000000"), "1.0e20");
    check(render_equals(0.0, "0"), "+0");
    check(render_equals(-0.0, "-0"), "-0");
    check(render_equals(double_of(UINT64_C(0x000FFFFFFFFFFFFF)), "2.225073858507201e-308"), "largest subnormal");
    check(render_equals(DBL_MIN, "2.2250738585072014e-308"), "smallest normal");
    {
        volatile double a = 0.1, b = 0.2;
        check(render_equals(a + b, "0.30000000000000004"), "0.1 + 0.2");
    }
    check(render_equals(9007199254740994.0, "9007199254740994"), "2^53+2");
    check(render_equals(18446744073709551616.0, "18446744073709552000"), "2^64");
    check(render_equals(123456789012345680000.0, "123456789012345680000"), "1.2345678901234568e20");
    group_end("render_oracle");
}

static void group_parse_oracle(void) {
    group_begin();
    check(sizeof nq_parse_vectors / sizeof nq_parse_vectors[0] >= 60, "at least 60 parse vectors");
    run_parse_vectors();
    group_end("parse_oracle");
}

static void group_slices(void) {
    NQStr base = nq_str("1.259");
    NQ_Option__str cut;
    NQ_Option__f64 r;
    group_begin();

    /* Views produced by nq_str_slice on a static string and on an owned one. */
    cut = nq_str_slice(base, 0, 4);
    check(cut.tag == NQ_Option__str_Tag_Some, "slice(0,4) exists");
    r = nq_f64_from_str(cut.data.Some._0);
    check(is_some_f64(r, 1.25), "slice(\"1.259\", 0, 4) parses as 1.25");
    nq_str_drop(&cut.data.Some._0);

    {
        NQStr owned = nq_str_concat(nq_str("1.2"), nq_str("59"));
        cut = nq_str_slice(owned, 0, 4);
        r = nq_f64_from_str(cut.data.Some._0);
        check(is_some_f64(r, 1.25), "owned slice 1.25");
        r = nq_f64_from_str(owned);
        check(is_some_f64(r, 1.259), "borrowed owned argument still parses afterwards");
        r = nq_f64_from_str(owned);
        check(is_some_f64(r, 1.259), "and again (the callee never consumed it)");
        nq_str_drop(&cut.data.Some._0);
        nq_str_drop(&owned);
    }

    cut = nq_str_slice(nq_str("12x"), 0, 2);
    r = nq_f64_from_str(cut.data.Some._0);
    check(is_some_f64(r, 12.0), "slice(\"12x\", 0, 2) parses as 12");
    nq_str_drop(&cut.data.Some._0);

    cut = nq_str_slice(nq_str("1.0e5"), 0, 4);
    r = nq_f64_from_str(cut.data.Some._0);
    check(r.tag == NQ_Option__f64_Tag_None, "slice(\"1.0e5\", 0, 4) = \"1.0e\" is none");
    nq_str_drop(&cut.data.Some._0);

    cut = nq_str_slice(nq_str("1.0e5"), 0, 3);
    r = nq_f64_from_str(cut.data.Some._0);
    check(is_some_f64(r, 1.0), "slice(\"1.0e5\", 0, 3) parses as 1.0");
    nq_str_drop(&cut.data.Some._0);

    cut = nq_str_slice(nq_str("-12"), 1, 3);
    r = nq_f64_from_str(cut.data.Some._0);
    check(is_some_f64(r, 12.0), "slice(\"-12\", 1, 3) parses as 12");
    nq_str_drop(&cut.data.Some._0);

    cut = nq_str_slice(nq_str("xx"), 1, 1);
    r = nq_f64_from_str(cut.data.Some._0);
    check(r.tag == NQ_Option__f64_Tag_None, "empty slice is none");
    nq_str_drop(&cut.data.Some._0);

    /* Not-terminated exact-size heap views, many shapes (ASan catches overreads). */
    expect_parse("1.2599", 4, true, bits_of(1.25));
    expect_parse("0.5e", 3, true, bits_of(0.5));
    expect_parse("0.5e", 4, false, 0);
    expect_parse("1e999", 4, true, bits_of(1e99));
    expect_parse("-0", 2, true, UINT64_C(0x8000000000000000));
    expect_parse("-0123", 2, true, UINT64_C(0x8000000000000000));

    /* 600-byte valid input takes the heap path. */
    {
        char big[600];
        big[0] = '2';
        big[1] = '.';
        memset(big + 2, '0', 597);
        big[599] = '5';
        expect_parse(big, 600, true, bits_of(2.0));
        big[598] = '1';
        expect_parse(big, 600, true, bits_of(2.0)); /* still 2.0: the tail is far below one ulp */
        memset(big, '0', 600);
        big[0] = '0';
        big[1] = '.';
        big[599] = '1';
        expect_parse(big, 600, true, 0); /* 1e-599 underflows to +0 */
        memset(big, '9', 600);
        expect_parse(big, 600, false, 0); /* 600 nines: integer overflow to infinity -> none */
        big[0] = '-';
        big[1] = '1';
        big[2] = 'e';
        big[3] = '-';
        memset(big + 4, '0', 595);
        big[599] = '3';
        expect_parse(big, 600, true, bits_of(-1e-3));
    }
    group_end("slice_and_heap_path");
}

/* splitmix64: a deterministic sample generator */
static uint64_t splitmix_state = UINT64_C(0x9E3779B97F4A7C15);

static uint64_t splitmix(void) {
    uint64_t z = (splitmix_state += UINT64_C(0x9E3779B97F4A7C15));
    z = (z ^ (z >> 30)) * UINT64_C(0xBF58476D1CE4E5B9);
    z = (z ^ (z >> 27)) * UINT64_C(0x94D049BB133111EB);
    return z ^ (z >> 31);
}

static bool is_finite_bits(uint64_t bits) {
    return ((bits >> 52) & 0x7FF) != 0x7FF;
}

static void roundtrip_one(uint64_t bits) {
    double x = double_of(bits);
    NQStr s = nq_str_from_f64(x);
    NQ_Option__f64 r = nq_f64_from_str(s);
    group_checks += 1;
    if (r.tag != NQ_Option__f64_Tag_Some || bits_of(r.data.Some._0) != bits) {
        char detail[160];
        (void)snprintf(detail, sizeof detail, "bits %016llx rendered \"%.*s\"", (unsigned long long)bits,
                       (int)s.len, s.data);
        note_fail("round trip", detail);
    }
    nq_str_drop(&s);
}

static void group_roundtrip(void) {
    group_begin();
    for (int sign = 0; sign < 2; sign += 1) {
        uint64_t s = (uint64_t)sign << 63;
        roundtrip_one(s | 0);
        roundtrip_one(s | 1);
        roundtrip_one(s | 2);
        roundtrip_one(s | UINT64_C(0x000FFFFFFFFFFFFF));
        roundtrip_one(s | UINT64_C(0x0010000000000000));
        roundtrip_one(s | UINT64_C(0x0010000000000001));
        roundtrip_one(s | UINT64_C(0x7FEFFFFFFFFFFFFF));
        roundtrip_one(s | UINT64_C(0x7FEFFFFFFFFFFFFE));
        /* every power of two, with its neighbours (the asymmetric intervals) */
        for (uint64_t e = 0; e < 2047; e += 1) {
            uint64_t p = s | (e << 52);
            roundtrip_one(p);
            roundtrip_one(p + 1);
            if (e != 0) roundtrip_one(p - 1);
        }
        /* subnormal ramp */
        for (uint64_t m = 1; m < 700; m += 1) roundtrip_one(s | m);
    }
    for (int i = 0; i < 16000; i += 1) {
        uint64_t bits = splitmix();
        if (is_finite_bits(bits)) roundtrip_one(bits);
        /* a second family: small integers scaled, and short decimals */
        bits = (splitmix() & UINT64_C(0x800FFFFFFFFFFFFF)) | ((uint64_t)(900 + (int)(splitmix() % 300)) << 52);
        roundtrip_one(bits);
    }
    check(group_checks >= 10000, "at least 10000 patterns");
    /* non-finite values render as diagnostics and never parse */
    {
        NQStr nan_text = nq_str_from_f64(double_of(UINT64_C(0x7FF8000000000000)));
        check(nq_f64_from_str(nan_text).tag == NQ_Option__f64_Tag_None, "NaN text does not parse");
        nq_str_drop(&nan_text);
    }
    check(nq_f64_from_str(nq_str("Infinity")).tag == NQ_Option__f64_Tag_None, "Infinity does not parse");
    group_end("round_trip_law");
}

static void group_iec(void) {
    volatile double zero = 0.0;
    volatile double one = 1.0;
    volatile double negzero = -0.0;
    volatile double tiny = 5e-324;
    volatile double dmax = DBL_MAX;
    volatile double dmin = DBL_MIN;
    double inf = one / zero;
    double ninf = -one / zero;
    double nan = zero / zero;
    group_begin();
    check(inf > dmax, "1/0 is +infinity");
    check(ninf < -dmax, "-1/0 is -infinity");
    check(inf == inf && inf != ninf, "infinities compare");
    check(inf - inf != inf - inf, "inf - inf is NaN");
    check(nan != nan, "NaN != NaN");
    check(!(nan == nan), "NaN == NaN is false");
    check(!(nan < one) && !(nan > one) && !(nan <= one) && !(nan >= one), "NaN ordered compares false");
    check(zero == negzero, "0.0 == -0.0");
    check(one / negzero == ninf, "1.0 / -0.0 is -infinity");
    check(one / zero == inf, "1.0 / 0.0 is +infinity");
    check(bits_of(negzero) == UINT64_C(0x8000000000000000), "-0.0 has the sign bit");
    check(bits_of(-zero) == UINT64_C(0x8000000000000000), "negating +0 gives -0");
    check(bits_of(tiny) == 1, "5.0e-324 literal is the smallest subnormal");
    check(tiny != 0.0, "smallest subnormal is nonzero");
    check(tiny / 2.0 == 0.0, "smallest subnormal halves to zero");
    check(bits_of(tiny * 0.5) == 0, "smallest subnormal times 0.5 is +0");
    check(dmin / 2.0 != 0.0 && dmin / 2.0 < dmin, "DBL_MIN halves to a subnormal");
    check(dmax * 2.0 == inf, "overflow gives infinity");
    check(dmax + dmax == inf && -dmax - dmax == ninf, "overflow on addition");
    check(bits_of(dmax * 1.0000000000000002) == bits_of(inf), "DBL_MAX*(1+ulp) overflows");
    check(one + 0x1p-53 == one, "1 + 2^-53 rounds to even (1)");
    check(one + 0x1p-52 > one, "1 + 2^-52 is above 1");
    check(one + (0x1p-53 + 0x1p-105) > one, "1 + (2^-53 + 2^-105) rounds up");
    check(nan - nan != nan - nan, "NaN propagates");
    check(inf - inf != 0.0, "inf - inf is not zero");
    group_end("iec_60559_runtime");
}

static void group_contraction(void) {
    /* a*b rounds to 1 + 2^-29 (losing 2^-60); the sum with c is then exactly 0
     * unless the compiler fused the multiply-add, which keeps 2^-60. */
    volatile double a = 1.0 + 0x1p-30;
    volatile double b = 1.0 + 0x1p-30;
    volatile double c = -(1.0 + 0x1p-29);
    double r = a * b + c;
    double fused_would_be = 0x1p-60;
    group_begin();
    check(r == 0.0, "a*b+c is the unfused result (0)");
    check(r != fused_would_be, "a*b+c is not the fused result (2^-60)");
    group_end("contraction_probe");
}

/* Run the text builtins on a bounded sample; used under hostile locales. */
static void text_sample(const char* what) {
    static const struct { double value; const char* text; } samples[] = {
        { 1.5, "1.5" }, { -0.1, "-0.1" }, { 123456.789, "123456.789" }, { 1e-6, "0.000001" },
        { 1e-7, "1e-7" }, { 1e22, "1e+22" }, { 0.5, "0.5" }, { 2.5e-300, "2.5e-300" },
    };
    for (size_t i = 0; i < sizeof samples / sizeof samples[0]; i += 1) {
        char note[64];
        (void)snprintf(note, sizeof note, "%s render %zu", what, i);
        group_checks += 1;
        if (!render_equals(samples[i].value, samples[i].text)) note_fail(note, "");
        {
            Exact e = exact_view(samples[i].text, strlen(samples[i].text));
            NQ_Option__f64 r = nq_f64_from_str(e.view);
            group_checks += 1;
            if (r.tag != NQ_Option__f64_Tag_Some || bits_of(r.data.Some._0) != bits_of(samples[i].value)) {
                (void)snprintf(note, sizeof note, "%s parse %zu", what, i);
                note_fail(note, samples[i].text);
            }
            exact_free(&e);
        }
    }
    expect_parse("1,5", 3, false, 0);
    expect_parse("1.5", 3, true, bits_of(1.5));
}

static const char* const comma_locales[] = {
    "de_DE.UTF-8", "de_DE.utf8", "fr_FR.UTF-8", "fr_FR.utf8", "de_DE", "fr_FR",
    "it_IT.UTF-8", "es_ES.UTF-8", "ru_RU.UTF-8", "pt_BR.UTF-8", "nl_NL.UTF-8", "sv_SE.UTF-8",
};

static void group_locale(void) {
    const char* found = NULL;
    char saved[128];
    const char* cur = setlocale(LC_ALL, NULL);
    group_begin();
    (void)snprintf(saved, sizeof saved, "%s", cur != NULL ? cur : "C");
    /* Always: a hostile thread-local "C"-everything locale is restored. */
    {
        locale_t other = newlocale(LC_ALL_MASK, "C", (locale_t)0);
        locale_t before;
        check(other != (locale_t)0, "newlocale(C) works");
        if (other != (locale_t)0) {
            before = uselocale(other);
            text_sample("thread C locale");
            check(uselocale((locale_t)0) == other, "thread locale restored after calls");
            (void)uselocale(before);
            freelocale(other);
        }
    }
    check(uselocale((locale_t)0) == LC_GLOBAL_LOCALE, "global thread locale restored");
    for (size_t i = 0; i < sizeof comma_locales / sizeof comma_locales[0]; i += 1) {
        if (setlocale(LC_ALL, comma_locales[i]) != NULL && localeconv()->decimal_point[0] == ',') {
            found = comma_locales[i];
            break;
        }
    }
    if (found == NULL) {
        (void)setlocale(LC_ALL, saved);
        if (group_failures == 0) {
            printf("PASS locale_probe_base (%d checks)\n", group_checks);
        } else {
            printf("FAIL locale_probe_base (%d of %d checks failed)\n", group_failures, group_checks);
            total_failures += 1;
        }
        printf("SKIP locale_probe_comma: no comma-decimal locale is installed (tried %zu names)\n",
               sizeof comma_locales / sizeof comma_locales[0]);
        return;
    }
    {
        char probe[32];
        (void)snprintf(probe, sizeof probe, "%.1f", 1.5);
        check(strcmp(probe, "1,5") == 0, "the comma locale is really active for printf");
    }
    text_sample("global comma locale");
    run_render_vectors();
    run_parse_vectors();
    {
        char probe[32];
        (void)snprintf(probe, sizeof probe, "%.1f", 1.5);
        check(strcmp(probe, "1,5") == 0, "global comma locale unchanged after calls");
    }
    /* thread-local comma locale on top of a global C locale */
    (void)setlocale(LC_ALL, "C");
    {
        locale_t comma = newlocale(LC_NUMERIC_MASK, found, (locale_t)0);
        if (comma != (locale_t)0) {
            locale_t before = uselocale(comma);
            char probe[32];
            (void)snprintf(probe, sizeof probe, "%.1f", 1.5);
            check(strcmp(probe, "1,5") == 0, "the thread-local comma locale is active");
            text_sample("thread comma locale");
            check(uselocale((locale_t)0) == comma, "thread comma locale restored");
            (void)uselocale(before);
            freelocale(comma);
        }
    }
    (void)setlocale(LC_ALL, saved);
    if (group_failures == 0) {
        printf("PASS locale_probe_comma %s (%d checks)\n", found, group_checks);
    } else {
        printf("FAIL locale_probe_comma %s (%d of %d checks failed)\n", found, group_failures, group_checks);
        total_failures += 1;
    }
}

static void group_ownership(void) {
    NQStr s;
    NQStr extra;
    group_begin();
    s = nq_str_from_f64(0.25);
    check(s.owner != NULL && s.len == 4 && memcmp(s.data, "0.25", 4) == 0, "result is a fresh owned str");
    extra = nq_str_clone(s);
    nq_str_drop(&s);
    check(extra.len == 4 && memcmp(extra.data, "0.25", 4) == 0, "clone survives the original drop");
    check(is_some_f64(nq_f64_from_str(extra), 0.25), "owned result parses back");
    nq_str_drop(&extra);
    s = nq_str_from_f64(0.0);
    check(s.len == 1 && s.data[0] == '0' && s.owner != NULL, "zero is an owned str");
    nq_str_drop(&s);
    s = nq_str_from_f64(double_of(UINT64_C(0x7FF8000000000000)));
    check(s.len == 3 && memcmp(s.data, "NaN", 3) == 0 && s.owner != NULL, "NaN is an owned str");
    nq_str_drop(&s);
    /* the option carriers have the emitter's shape */
    {
        NQ_Option__i64 a = { .tag = NQ_Option__i64_Tag_Some, .data.Some = { ._0 = 7 } };
        NQ_Option__i64 b = { .tag = NQ_Option__i64_Tag_None, .data.None = NQ_UNIT };
        NQ_Option__f64 c = { .tag = NQ_Option__f64_Tag_Some, .data.Some = { ._0 = 1.5 } };
        NQ_Option__f64 d = { .tag = NQ_Option__f64_Tag_None, .data.None = NQ_UNIT };
        check(a.data.Some._0 == 7 && b.tag == NQ_Option__i64_Tag_None, "NQ_Option__i64 shape");
        check(c.data.Some._0 == 1.5 && d.tag == NQ_Option__f64_Tag_None, "NQ_Option__f64 shape");
    }
    group_end("str_ownership_and_option_abi");
}

/* Allocation-failure modes. */
static int mode_oom(bool boundary) {
    static char buf[1024];
    NQStr warm;
    Exact e;
    NQ_Option__f64 r;
    memset(buf, '0', sizeof buf);
    buf[0] = '1';
    buf[1] = '.';
    /* < 512 bytes: stack path, no allocation. */
    e = exact_view(buf, 100);
    r = nq_f64_from_str(e.view);
    exact_free(&e);
    if (!is_some_f64(r, 1.0)) { puts("short parse failed"); return 3; }
    /* One successful str_from_f64 = two runtime allocations (storage + owner). */
    warm = nq_str_from_f64(1.5);
    nq_str_drop(&warm);
    puts("warm-up ok: short parse allocated nothing, str_from_f64 used two allocations");
    fflush(stdout);
    if (boundary) {
        e = exact_view(buf, 511);
        r = nq_f64_from_str(e.view);
        exact_free(&e);
        if (!is_some_f64(r, 1.0)) { puts("511-byte parse failed"); return 3; }
        puts("511-byte input parsed on the stack path");
        fflush(stdout);
        e = exact_view(buf, 512);
    } else {
        e = exact_view(buf, 600);
    }
    r = nq_f64_from_str(e.view);
    exact_free(&e);
    puts(is_some_f64(r, 1.0) ? "heap-path parse completed" : "heap-path parse returned wrong value");
    return is_some_f64(r, 1.0) ? 0 : 3;
}

int main(int argc, char** argv) {
    if (argc > 1) {
        if (strcmp(argv[1], "oom-heap") == 0) return mode_oom(false);
        if (strcmp(argv[1], "oom-boundary") == 0) return mode_oom(true);
        fprintf(stderr, "unknown mode %s\n", argv[1]);
        return 2;
    }
    group_from_i32();
    group_from_i64();
    group_trunc_i64();
    group_trunc_i32();
    group_render_oracle();
    group_parse_oracle();
    group_slices();
    group_roundtrip();
    group_iec();
    group_contraction();
    group_ownership();
    group_locale();
    if (total_failures != 0) {
        printf("FAILED: %d group(s)\n", total_failures);
        return 1;
    }
    puts("ALL GROUPS PASSED");
    return 0;
}
