#include "runtime.h"

/* A separate translation unit isolates the ICE contract from generated runtime
 * carriers, which may intentionally use extensions outside constant contexts. */
_Static_assert(NQ_I32_CONST_ADD(INT32_MAX, 1) == INT32_MIN, "i32 add");
_Static_assert(NQ_I32_CONST_SUB(INT32_MIN, 1) == INT32_MAX, "i32 sub");
_Static_assert(NQ_I32_CONST_MUL(INT32_MAX, 2) == -2, "i32 mul");
_Static_assert(NQ_I32_CONST_MUL(INT32_MAX, INT32_MAX) == 1, "i32 square");
_Static_assert(NQ_I32_CONST_MUL(INT32_MIN, 2) == 0, "i32 zero wrap");
_Static_assert(NQ_I32_CONST_NEG(INT32_MIN) == INT32_MIN, "i32 neg");
_Static_assert(NQ_I32_CONST_DIV(7, 2) == 3, "i32 pp");
_Static_assert(NQ_I32_CONST_DIV(-7, 2) == -3, "i32 np");
_Static_assert(NQ_I32_CONST_DIV(7, -2) == -3, "i32 pn");
_Static_assert(NQ_I32_CONST_DIV(-7, -2) == 3, "i32 nn");
_Static_assert(NQ_I32_CONST_DIV(-1, 2) == 0, "i32 trunczero");
_Static_assert(NQ_I32_CONST_DIV(NQ_I32_CONST_ADD(INT32_MAX, 1), 2) == -1073741824, "i32 nested");
_Static_assert(NQ_I32_CONST_DIV(7, NQ_I32_CONST_MUL(INT32_MAX, 2)) == -3, "i32 denominator");
_Static_assert(NQ_I64_CONST_ADD(INT64_MAX, 1) == INT64_MIN, "i64 add");
_Static_assert(NQ_I64_CONST_SUB(INT64_MIN, 1) == INT64_MAX, "i64 sub");
_Static_assert(NQ_I64_CONST_MUL(INT64_MAX, 2) == -2, "i64 mul");
_Static_assert(NQ_I64_CONST_MUL(INT64_MAX, INT64_MAX) == 1, "i64 square");
_Static_assert(NQ_I64_CONST_MUL(INT64_MIN, 2) == 0, "i64 zero wrap");
_Static_assert(NQ_I64_CONST_NEG(INT64_MIN) == INT64_MIN, "i64 neg");
_Static_assert(NQ_I64_CONST_DIV(7, 2) == 3, "i64 pp");
_Static_assert(NQ_I64_CONST_DIV(-7, 2) == -3, "i64 np");
_Static_assert(NQ_I64_CONST_DIV(7, -2) == -3, "i64 pn");
_Static_assert(NQ_I64_CONST_DIV(-7, -2) == 3, "i64 nn");
_Static_assert(NQ_I64_CONST_DIV(-1, 2) == 0, "i64 trunczero");
_Static_assert(NQ_I64_CONST_DIV(NQ_I64_CONST_ADD(INT64_MAX, 1), 2) == -INT64_C(4611686018427387904), "i64 nested");
_Static_assert(NQ_I64_CONST_DIV(7, NQ_I64_CONST_MUL(INT64_MAX, 2)) == -3, "i64 denominator");
_Static_assert(!(0 && NQ_I32_CONST_DIV(1, 0)), "i32 dead zero");
_Static_assert(1 || NQ_I32_CONST_DIV(INT32_MIN, -1), "i32 dead overflow");
_Static_assert(!(0 && NQ_I64_CONST_DIV(1, 0)), "i64 dead zero");
_Static_assert(1 || NQ_I64_CONST_DIV(INT64_MIN, -1), "i64 dead overflow");
