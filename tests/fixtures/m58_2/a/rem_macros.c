#include "runtime.h"

/* M58.2 slice A: the remainder constant macros are strict C11 integer constant
 * expressions, truncate like C99 `%`, and are guarded like the _DIV macros. */
_Static_assert(NQ_I32_CONST_REM(7, 2) == 1, "i32 pp");
_Static_assert(NQ_I32_CONST_REM(-7, 2) == -1, "i32 np");
_Static_assert(NQ_I32_CONST_REM(7, -2) == 1, "i32 pn");
_Static_assert(NQ_I32_CONST_REM(-7, -2) == -1, "i32 nn");
_Static_assert(NQ_I32_CONST_REM(0, 5) == 0, "i32 zero dividend");
_Static_assert(NQ_I32_CONST_REM(INT32_MIN, 3) == -2, "i32 min");
_Static_assert(NQ_I32_CONST_REM(INT32_MAX, INT32_MIN) == INT32_MAX, "i32 max by min");
_Static_assert(NQ_I32_CONST_REM(NQ_I32_CONST_ADD(INT32_MAX, 1), 3) == -2, "i32 nested");
_Static_assert(NQ_I64_CONST_REM(7, 2) == 1, "i64 pp");
_Static_assert(NQ_I64_CONST_REM(-7, 2) == -1, "i64 np");
_Static_assert(NQ_I64_CONST_REM(7, -2) == 1, "i64 pn");
_Static_assert(NQ_I64_CONST_REM(-7, -2) == -1, "i64 nn");
_Static_assert(NQ_I64_CONST_REM(0, 5) == 0, "i64 zero dividend");
_Static_assert(NQ_I64_CONST_REM(INT64_MIN, 3) == -2, "i64 min");
_Static_assert(NQ_I64_CONST_REM(INT64_MAX, INT64_MIN) == INT64_MAX, "i64 max by min");
_Static_assert(NQ_I64_CONST_REM(NQ_I64_CONST_ADD(INT64_MAX, 1), 3) == -2, "i64 nested");
_Static_assert(!(0 && NQ_I32_CONST_REM(1, 0)), "i32 dead zero");
_Static_assert(1 || NQ_I32_CONST_REM(INT32_MIN, -1), "i32 dead overflow");
_Static_assert(!(0 && NQ_I64_CONST_REM(1, 0)), "i64 dead zero");
_Static_assert(1 || NQ_I64_CONST_REM(INT64_MIN, -1), "i64 dead overflow");
