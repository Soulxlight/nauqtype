# M56.2: Scalar `f64`

Status: Gate A passed, 2026-10-31 (revision 3). Not implemented. Base:
`da7afdc`. The independent Gate A reviewer (gpt-5.6-sol xhigh) required
changes on revision 1 (six blocking, two should-fix) and on revision 2 (one
blocking, one should-fix). It required one wording fix on revision 3, then
approved revision 3 with no findings.
Sequencing approved by the owner on 2026-10-30 (ROADMAP M56.2); this scope
is proposed by the compiler lead. Closing evidence will be recorded in
AUDIT_REMEDIATION, not here.

This document is the `SYNTAX_IDENTITY.md` decision record for the feature
and the implementation contract. Section headings follow the SOP's required
record.

## Problem And Real Usage Pressure

- M57 ships deterministic JSON. JSON numbers that are not integral (or not
  in `i64` range) need a value type, and ROADMAP M57 already maps them to
  "M56.2 `f64`". Without it, a JSON reader must either reject ordinary
  documents (`{"ratio": 0.5}`) or carry numbers as unchecked text.
- Terminal tools compute ratios, percentages, averages, and human-readable
  durations and sizes (`1.5 s`, `2.3 MiB`, `87.5%`). Today they hand-roll
  fixed-point arithmetic on `i64`, which is error-prone and unreadable.
- No later milestone schedules a floating-point type, and the in-repo
  standard library planned with M57 cannot write one in Nauqtype source:
  correct decimal rendering and parsing need runtime support.

## Canonical Syntax

One new primitive type name, `f64`, usable everywhere a primitive type is
(locals, parameters, returns, fields, payloads, `list<f64>`, `option<f64>`,
`result<f64, E>`, generic arguments, `pub` signatures across modules and
dependencies).

One literal form, lexical rule:

```ebnf
FLOAT_LIT = ASCII_DIGIT { ASCII_DIGIT } "." ASCII_DIGIT { ASCII_DIGIT }
            [ "e" [ "-" ] ASCII_DIGIT { ASCII_DIGIT } ] ;
```

- Digits are required on both sides of the point: `0.5`, `1.0`, `2.5e-3`,
  `6.02e23`. The exponent marker is lowercase `e` with an optional `-` only.
- Leading-zero rules for the integer part are the `INT_LIT` rules.
- A float literal always has type `f64`. Negative values use the existing
  unary `-`.
- No suffix family (`1.0f64`, `1f`), no `.5`, `1.`, `1e5`, `1E5`, `1e+5`,
  hexadecimal floats, digit separators, or `inf`/`nan` keywords.

Lexing note: `INT_LIT` followed immediately by `.` and an ASCII digit is a
float literal. No current construct puts a digit after `.` following an
integer literal (field access requires an identifier, and there is no `..`
or tuple indexing), so no existing source changes meaning.

## Rejected Alternatives

- **Integer literals in `f64` context** (`let x: f64 = 1;`). Rejected: it is
  an implicit numeric conversion. D055 lets an unsuffixed literal pick `i64`
  only within the integer family. Write `1.0`.
- **Implicit widening** of `i32`/`i64` operands to `f64` in mixed
  arithmetic. Rejected by D055 (no implicit numeric conversion).
- **Literal suffixes** or a second literal spelling. Rejected by the
  one-canonical-spelling rule. The only literal type is `f64` until `f32`
  exists, and then the expected-context rule will be decided in its own
  record.
- **Trapping on division by zero** like integer division. Rejected: IEEE
  division yields well-defined infinities and NaN, C emission is native, and
  the M57 JSON writer has to check for non-finite values in any case.
- **Total ordering or reflexive equality for `==`** (NaN == NaN). Rejected:
  it differs from IEEE and from every reader's expectation. A total-order
  comparator can be a later standard-library function.
- **Unchecked casts** (`as`, C-style truncation). Rejected: Nauqtype has no
  casts, and out-of-range float-to-integer conversion is undefined in C.
- **Rendering through `printf("%g")`**. Rejected: it neither round-trips
  nor emits JSON-compatible output, and its output depends on the locale.
- **A math library** (`sqrt`, `floor`, `pow`, `fmod`, ...). Deferred to the
  in-repo standard library with M57+. M56.2 ships only the operations that
  cannot be written in Nauqtype source.

## Exact Semantics

### Representation and arithmetic

- `f64` is IEEE 754 binary64, emitted as C `double`. `is_copy` is true and
  `needs_drop` is false (like `i64`).
- Binary `+ - * /` and unary `-` operate on two `f64` operands (one for
  unary) and produce `f64`. Rounding is round-to-nearest-ties-to-even, with
  no contraction into fused multiply-add. Overflow yields ±infinity.
  Division by zero yields ±infinity or NaN per IEEE. None of these trap.
- Mixing `f64` with `i32` or `i64` in any binary operator is a type error,
  using the existing operand-mismatch diagnostic. The message gains a hint
  naming the explicit conversion builtins.
- Unary `-` negates the sign bit, so `-0.0` is negative zero.

### Comparison

- `==`, `!=`, `<`, `<=`, `>`, `>=` on two `f64` operands follow IEEE: every
  ordered comparison with a NaN operand is false, `==` with a NaN operand is
  false, and `!=` with a NaN operand is true. `0.0 == -0.0` is true.
- The documented NaN test is `x != x`; the documented finiteness test is
  `x - x == 0.0`. Both hold under the IEEE emission rules below and are used
  verbatim in the teaching example.

### `match`

An `f64` value cannot be a `match` scrutinee, and float literals cannot be
patterns (NQ-TYPE-047). The diagnostic tells the author to use `if` with
comparisons, because literal matching of floating values hides NaN and
rounding behavior. This matches the current rule that only `i32` admits
literal patterns. Binding an `f64` payload in a pattern is unaffected:
`some(x)`, `ok(x)`, and enum payloads work as for any copy type.

### Constants

The complete `f64` constant-expression grammar is:

```ebnf
f64_const_expr = FLOAT_LIT | "-" FLOAT_LIT ;
```

That is a single float literal, optionally preceded by exactly one unary
minus token. Everything else in an `f64` constant initializer is rejected
with NQ-TYPE-048:

- parentheses in any position: `(1.0)`, `-(1.0)`, `((1.0))`;
- repeated or nested unary minus: `--1.0`, `-(-1.0)`;
- arithmetic;
- references to other constants.

Any `const` initializer of type `bool` or `i32`/`i64` that contains an
`f64` operand (e.g. `const B: bool = 1.0 < 2.0;`) is also rejected with
NQ-TYPE-048. The selfhost compiler does no floating-point folding, so a
constant's value is exactly what the C compiler derives from the literal
text.

### Literal range

A float literal whose decimal value is at least
2^1024 − 2^970 (the smallest magnitude that rounds to infinity) is rejected
at compile time with a new diagnostic. The compiler decides this exactly, by
comparing normalized decimal digits against the fixed 309-digit decimal
expansion of that bound, with no floating-point arithmetic. Literals that
round to a subnormal or to zero are accepted; rounding is ordinary literal
behavior. The emitted C literal is the source literal text, which C
compilers convert with correct rounding.

### Builtins

Six builtin functions, chosen to cover what source code cannot express:

| Builtin | Result | Meaning |
| --- | --- | --- |
| `f64_from_i32(value: i32)` | `f64` | Exact (every `i32` is representable). |
| `f64_from_i64(value: i64)` | `option<f64>` | `some` only if the value is exactly representable; otherwise `none`. No silent rounding. |
| `f64_trunc_i32(value: f64)` | `option<i32>` | Truncates toward zero; `none` for NaN, ±infinity, or a truncated value outside `i32`. |
| `f64_trunc_i64(value: f64)` | `option<i64>` | Same, for `i64`. The range check is done without undefined C conversion. |
| `str_from_f64(value: f64)` | `str` | Deterministic rendering, below. |
| `f64_from_str(text: str)` | `option<f64>` | Strict parsing, below. |

Names follow the existing `<result>_from_<input>` pattern (`str_from_bytes`,
`bytes_from_str`, `duration_from_ns`), and the truncating conversions name
their rounding. The builtins are pure: they have no effect atoms and return
no error values. `str_from_f64` and `f64_from_str` can hit the existing
fatal runtime failures for size, out-of-memory, and locale-capability
problems (defined below). `none` from `f64_from_str` means only "outside the
grammar" or "rounds to infinity", never a resource failure.

**No libm.** The toolchain links without `-lm` (`selfhost/host_c.nq`, the
fixture allowlist in `selfhost/fixture_c.nq`), and that stays unchanged, so
no builtin may call a `<math.h>` function. Each conversion is a bound check
followed by a C conversion that C11 defines (C11 6.3.1.4 truncates toward
zero when the truncated value is representable):

- `f64_trunc_i64(v)`: `some((int64_t)v)` iff `v >= -0x1p63 && v < 0x1p63`,
  else `none`. Every `double` in that half-open interval truncates into
  `[INT64_MIN, INT64_MAX]`. NaN fails both comparisons.
- `f64_trunc_i32(v)`: `some((int32_t)v)` iff
  `v > -2147483649.0 && v < 2147483648.0` (an open interval, so
  `-2147483648.9` truncates to `INT32_MIN` and `-2147483649.0` is `none`),
  else `none`.
- `f64_from_i64(x)`: `d = (double)x`. The result is `none` when
  `d >= 0x1p63` (only values near `INT64_MAX` round up there), otherwise
  `some(d)` iff `(int64_t)d == x`. No out-of-range conversion is
  evaluated.
- `str_from_f64` and `f64_from_str` use only `<stdio.h>`, `<stdlib.h>`,
  `<string.h>`, and `<locale.h>` facilities (`snprintf`, `strtod`,
  `newlocale`/`uselocale`), all in libc.

**Option ABI.** `f64_from_i64`, `f64_trunc_i64`, and `f64_from_str` return
`option<f64>` or `option<i64>`. Runtime functions can return only
runtime-native carriers, and `runtime.h` is emitted before any generated
option declaration. `stdlib/runtime.h` therefore gains `NQ_Option__f64` and
`NQ_Option__i64` in the existing `NQ_Option__i32` shape (tag enum
`NQ_Option__<t>_Tag_Some/_None`, union `Some._0`/`None`). C emission's
`is_runtime_native_option` returns true for `checked_type_f64` and
`checked_type_i64`.

`option<i64>` is already usable in programs today, and the emitter
currently declares it per program. Afterwards the runtime declares it and
the emitter does not. The emitted name, tag spelling, and layout are
identical, so no Nauqtype-visible behavior changes. Any checked-in emitted-C
golden that contains a generated `NQ_Option__i64` declaration loses that
declaration. The implementation lists each such golden in the candidate
notes (the lead found none under `tests/golden/` at `da7afdc`). A program
using `option<i64>` must still compile with no duplicate or incomplete
type. A focused test compiles one that also calls `f64_trunc_i64`.

### Text rendering (`str_from_f64`)

- Finite nonzero values render exactly as ECMAScript `Number::toString(x)`
  with radix 10 (ECMA-262, Number::toString): the shortest digit string
  that round-trips, with ties among equally short strings broken toward
  the one closest to the exact value. Notation is fixed when
  `1e-6 <= |x| < 1e21`, i.e. when the decimal exponent
  `floor(log10(|x|))` is in `[-6, 21)`. Otherwise it is scientific,
  `d[.ddd]e±n`, with an explicit `+` for positive exponents. So `1.0e-6`
  renders `0.000001`, and `1.0e-7` renders `1e-7`.
  Examples: `0.1` → `0.1`, `100.0` → `100`, `1.0e21` → `1e+21`,
  `1.0e-7` → `1e-7`, `5.0e-324` → `5e-324`,
  the maximum finite value → `1.7976931348623157e+308`.
- `+0.0` → `0` and `-0.0` → `-0`. This is the one deviation from ECMAScript,
  made so that every finite value round-trips.
- NaN → `NaN`, +infinity → `Infinity`, −infinity → `-Infinity`. These are
  diagnostic spellings that `f64_from_str` does not accept.
- Rendering never depends on the process locale or on the C library's
  `%g` formatting choices. The implementation may find the shortest digits
  with correctly rounded `%.*e` conversion (glibc's is exact). It must then
  assemble the output itself from the digit characters and exponent, never
  copying the library's decimal-point character.
- **Locale independence by construction, with per-call ownership:** each
  call to either text builtin runs its `snprintf`/`strtod` work under its
  own `"C"` locale and keeps no shared lazily initialized state, so there is
  nothing to race once M59 adds tasks. The call sequence is:
  1. `loc = newlocale(LC_NUMERIC_MASK, "C", (locale_t)0)`;
  2. `old = uselocale(loc)`;
  3. the conversion;
  4. `uselocale(old)`, then `freelocale(loc)` on every exit path, including
     `none` results.

  glibc returns its static C locale object for `"C"`, so this does not
  allocate there. This is POSIX.1-2008, which is already required by
  `-D_POSIX_C_SOURCE=200809L`. If `newlocale` returns `(locale_t)0` or
  `uselocale` returns `(locale_t)0`, the program terminates with exit code
  1 and `nauqtype runtime: numeric locale unavailable` on stderr. This
  follows the existing "fatal runtime failures do not promise unwinding"
  rule. Today no Nauqtype program can change the locale: there is no FFI
  until M58, and the runtime never calls `setlocale`. The construction
  keeps the rule true after M58 too.
- **Rendering buffer:** the digits come from `snprintf` into a fixed stack
  buffer large enough for `%.17e` of any `double`, which cannot fail. The
  only allocation is the result `str`, under the existing fatal
  size/out-of-memory contract.

**Round-trip law:** for every finite `x`,
`f64_from_str(str_from_f64(x)) == some(x)`, with the same sign of zero.

### Text parsing (`f64_from_str`)

- Accepts exactly the JSON number grammar (RFC 8259 §6) over the whole
  string: `-? (0 | [1-9][0-9]*) (\.[0-9]+)? ([eE][+-]?[0-9]+)?`. There is no
  surrounding whitespace, no leading `+`, no `inf`/`nan`, and no
  hexadecimal. `str_from_f64` output for finite values is always inside
  this grammar.
- The result is the correctly rounded binary64 value (ties to even).
  `-0` gives negative zero. Underflow to a subnormal or zero is accepted.
  Any input that rounds to ±infinity gives `none`.
- `none` for any input outside the grammar, including an embedded NUL. The
  result does not depend on the locale.
- **Length-aware validation:** `str` values are length-delimited (`NQStr`
  `data`/`len`), and `str_slice` produces views that are not terminated.
  The grammar is therefore validated over exactly `(data, len)` by runtime
  code that never reads at or past `len`. No libc function ever sees the
  original bytes. So parsing `str_slice("1.259", 0, 4)` yields `1.25`, never
  `1.259`.
- **Terminated copy:** after validation succeeds, the exact `len` bytes are
  copied and a NUL appended:
  - into a fixed 512-byte stack buffer when `len < 512`;
  - otherwise into a heap buffer of `len + 1` bytes, released on every exit
    path.

  `strtod` runs on that copy under the per-call locale. It must consume the
  whole copy. Anything else is an internal invariant failure, reported as
  `nauqtype runtime: internal float parse mismatch`, exit 1. A `len + 1`
  size overflow or heap out-of-memory uses the existing fatal contract
  (`nauqtype runtime: size limit exceeded` / `nauqtype runtime: out of
  memory`, exit 1).
- Input length is bounded only by the existing `str` bound. Exponent digits
  beyond what affects the result must not overflow internal counters
  (validation counts nothing; `strtod` handles long exponents).

### C emission and IEEE preservation

The toolchain already compiles generated programs and the runtime with
`-std=c11 -O2` (`selfhost/host_c.nq`). In ISO C mode GCC turns
floating-point contraction off. The lead checked this on the WSL host with
GCC 13.3 `-march=haswell`: `a * b + c` compiles to `vmulsd` plus an add
under `-std=c11` and to `vfmadd132sd` under `-std=gnu11`. M56.2 therefore
adds **no compiler flag**. The attested proof-options frame
(`scripts/provenance.sh` `prov_proof_flags_sha256`, pinned by the M54.10
attestation checks) and every fixture argument list stay unchanged.
Instead, `stdlib/runtime.h`, which every emitted translation unit and
`runtime.c` include first, gains a guard block:

- **binary64 shape, from `<float.h>`:** `#error` unless all of the
  following hold. These are standard C11 macros, so no
  compiler-specific macro is trusted.
  - `FLT_RADIX == 2`
  - `DBL_MANT_DIG == 53`
  - `DBL_MAX_EXP == 1024`
  - `DBL_MIN_EXP == -1021`
  - `DBL_HAS_SUBNORM == 1`
  - `FLT_EVAL_METHOD == 0`
- **storage width:** `_Static_assert(sizeof(double) == 8, ...)`.
- **IEC 60559 semantics:** `#error` unless `__STDC_IEC_559__` is defined.
  On the WSL host, glibc's `<stdc-predef.h>` defines it under GCC 13.3
  `-std=c11` (the lead checked this; the same probe printed
  `2 53 1024 -1021 1 0` for the six macros above). Infinities, NaN, signed
  zero, and subnormals are additionally proved at run time by the fixture
  below rather than trusted from the macro alone.
- **no fast math:** `#error` when `__FAST_MATH__` is defined.
- **ISO dialect:** under GCC (not Clang), `#error` when `__STRICT_ANSI__` is
  not defined. A GNU dialect enables contraction by default.
- **contraction off under Clang:** `#pragma STDC FP_CONTRACT OFF` under
  `__clang__` only. Clang honors it, and the `zig cc` fallback is Clang.
  GCC rejects the pragma under `-Wall -Werror` (the lead checked this), so
  GCC must not see it.

This changes the host compiler's capability requirements (a `cc` that
lacks binary64 or IEC 60559 now fails to build any program). Per
`VERIFICATION.md`, both focused host routes must therefore pass before the
freeze: `scripts/check_fast.sh --host-suite provenance`, then
`--host-suite attestation`. Any metadata-only compiler stub those suites
use must model the new requirement truthfully and not pretend to compile.

Probes for the two `host_c.nq` compiler paths:

- **System `cc`:** a focused check compiles a generated `f64` program with
  the exact `host_c.nq` arguments and runs the runtime fixture.
- **`zig cc`:** the fallback runs only when `cc` is absent, and the WSL gate
  host has neither `.deps/ziglang/zig` nor clang (the lead checked). The
  focused check therefore runs the same compile through
  `.deps/ziglang/zig cc` when that binary exists. Otherwise it records
  "zig fallback not present on this host" in the candidate notes. Proving
  the zig path on a host that has it is an explicit M60 packaging input,
  not an M56.2 claim.

An explicit user `-ffp-contract=fast` is documented as unsupported. On the
WSL host it is in fact detected: GCC 13.3 clears `__GCC_IEC_559` under that
flag, so glibc's `<stdc-predef.h>` leaves `__STDC_IEC_559__` undefined and
the guard rejects the build (see Implementation Notes). Other compilers may
not signal it, so the runtime fixture also includes a contraction
probe (a product-plus-sum whose fused and unfused results differ) so the
gate proves the shipped flags. If any existing script compiles
`runtime.h` in a GNU dialect, the guard surfaces it during implementation.
It is fixed there by using `-std=c11`, not by weakening the guard.

- Float literals are emitted as their source text. Arithmetic and
  comparisons are emitted as plain C `double` operators (`==` is never
  routed through an integer helper). The conversion builtins follow the
  bound-then-convert rules under "Builtins", so no C undefined behavior and
  no libm call is reachable.

## Authority And Evidence Impact

`f64` crosses no authority boundary: it is a plain copy value with no
effects, mutation, borrowing, provenance, or failure flow of its own. The
fallible conversions return `option`, so any failure path is visible at the
call site through ordinary `match`/`try` rules.

Evidence:

- The type name `f64` appears wherever evidence renders a type: facts
  v1-v5, review v2-v5, review-diff, change-report, policy-check,
  refactor-rename, and generic `type_arguments`. No schema enumerates type
  names, so no schema file changes.
- M56.1 atom list: the M56.1 contract says adding an atom is a format
  change. M56.2 instead treats the atom set as the builtin type set of the
  accepting compiler (the same precedent as `i64`, which M53 added after
  facts v1-v3 already rendered type names). The justification: every
  source that mentions `f64` was a hard error before M56.2, so no output
  for any previously accepted input changes, and `f64` contains no `:`, so
  the injectivity argument in M56.1 is unchanged. M56.2 amends the M56.1
  contract's atom sentence to say exactly this. The M56.1 renderer test that
  lists `"f64"` as a rejected atom (`m56_generics_tests.nq`, around line
  720) flips to accepted, and `generic.nq` `generic_builtin_arity` moves
  `f64` from the reserved group to the arity-0 builtin group. The bytewise
  regression rule below enforces the no-output-change claim. Gate A must accept or reject this
  amendment explicitly. The rejected path is a facts v6 / review v6 bump
  only to admit one atom.
- Generic mangling (`generic_names.nq`) gains one builtin encoding for
  `f64`. No `__nqg_` name or internal key is ever emitted, as M56.1
  requires.
- Builtins appear in call evidence exactly as other builtins do, with
  origin module `__builtin__` and no effect atoms.
- The diagnostics schema is unchanged; only new codes are added.

## Diagnostics And Formatter Rule

New diagnostics (the next free codes; no central registry exists, and codes
are literals at their call sites):

| Code | Condition | Message intent |
| --- | --- | --- |
| NQ-PARSE-004 | a float literal `digits.digits` followed by a malformed exponent: `1.0E5`, `1.0e+5`, `1.0e`, `1.0e-` | "malformed float literal"; shows the canonical `1.0e5` / `1.0e-5` |
| NQ-TYPE-046 | float literal at or above the overflow bound | "f64 literal is out of range (it would round to infinity)" |
| NQ-TYPE-047 | `f64` `match` scrutinee or float literal pattern | "f64 values cannot be matched; compare with `if`" |
| NQ-TYPE-048 | `f64` constant initializer other than a literal or negated literal, or an `f64` comparison inside any constant initializer | "f64 constants must be a literal; compute the value at runtime" |
| NQ-TYPE-049 | `f32`, `u32`, `u64`, or `char` in any type position | "`<name>` is reserved and not yet supported" |

**How NQ-PARSE-004 is produced.** The lexer returns tokens only and cannot
emit diagnostics (`selfhost/lexer.nq`), so a malformed exponent becomes one
full-span token, `tk_malformed_float_lit`. The scan is fixed:

1. After `DIGITS "." DIGIT+`, if the next byte is `e` or `E`, consume it.
2. Then consume at most one sign byte, `+` or `-`.
3. Then consume the maximal run of ASCII digits.

The token is `tk_float_lit` iff the marker was `e`, the sign was absent or
`-`, and at least one exponent digit followed. Otherwise it is
`tk_malformed_float_lit`, spanning exactly the consumed bytes. Lexing
resumes after the span. For example:

- `1.0E5` → one malformed token `1.0E5`;
- `1.0e+5` → `1.0e+5`;
- `1.0e` → `1.0e`;
- `1.0e-` → `1.0e-`;
- `1.0e--5` → malformed `1.0e-`, then ordinary tokens `-` and `5`;
- `1.0ex` → malformed `1.0e`, then the identifier `x`.

Without a following `e`/`E`, the float token ends after the fraction
digits, exactly as an integer literal ends after its digits. In
`parser.nq`, every place that accepts a primary literal checks for
`tk_malformed_float_lit` before the generic NQ-PARSE-003 failure path.
There it emits NQ-PARSE-004 at the token's span and stops the parse, the
same way NQ-PARSE-003 stops it. The lexer's token API keeps its shape; only
the token enum grows. Every token scanner that switches on `tk_int_lit`
(listed in the write set) treats `tk_malformed_float_lit` like
`tk_float_lit`, but that is unreachable after parse failure.

**NQ-TYPE-049 is an intentional validation tightening.** `resolve.nq`
(`is_builtin_type_name`) accepts all five deferred numeric names today, and
`handoff.nq` lets them fall through as checked named types. Some uses
already fail incidentally: a local reports NQ-TYPE-042 "annotated local
initializer does not match declared type". Others are accepted today:
unused functions or types whose signatures or fields name them, and
possibly borrows or containers of them. M56.2 rejects every occurrence in
every type position:

- local, parameter, and return types;
- fields and enum payloads;
- `ref`/`mutref` targets;
- nested containers (`list<option<u64>>`);
- `result` arguments;
- explicit generic arguments (`Bag<char>`).

This applies in reachable and unused declarations alike. No accepted
program can construct a value of these types, but some previously accepted
programs stop compiling. That change is recorded in D067 and the release
notes, not hidden as "no migration".

Forms that do not begin with `digits.digit` (`1.`, `1.e5`, `.5`, `1e5`) are
not float literals. They keep their current lexing and their current
rejection: today `1.5` reports NQ-TYPE-042 "unsupported expression shape",
and the same path rejects `1.e5`. Tests pin their exact current codes. A
dedicated diagnostic for them is deferred, because detecting them in the
lexer would need lookahead into what is otherwise ordinary member syntax.

Existing diagnostics are reused, with a hint naming the explicit builtins,
for an integer literal in `f64` context, mixed-type arithmetic or
comparison, and `f64` in contexts that require `i32`, such as list indices
and the `main` return value.

Formatter: float literals are reproduced byte-for-byte. Only one spelling
is accepted, so there is nothing to normalize. All other formatting is
unchanged.

## Teaching Positive And Negative Cases

- Positive example `examples/f64_basics.nq` (added to TEACHING_CORPUS.md),
  which:
  - averages a list of `i64` samples through `f64_from_i64`;
  - renders a percentage with `str_from_f64`;
  - parses user text with `f64_from_str`;
  - converts back with `f64_trunc_i64`;
  - shows the NaN (`x != x`) and finiteness (`x - x == 0.0`) idioms.
- Negative teaching case (corpus negative, exact code):
  `let total: f64 = count;` with `count: i64`. The expected output is the
  mismatch diagnostic with the hint "use `f64_from_i64(count)` — Nauqtype
  never converts numbers implicitly". The documented alternative is
  explicit conversion with handling of the `none` case.

## Compiler Phases And Schema Effects

Every phase changes, from lexer through C emission:

- lexer, parser and AST: the float literal token and node;
- resolve: the primitive name `f64`;
- typecheck: type identity, literal typing, operators, comparisons,
  `match` patterns, constants, builtin signatures, literal range check;
- borrow and use plan: copy, no drop;
- IR and C emission: type text, literals, operators, builtins, prelude
  guard;
- handoff and workspace exports: type contexts and origin `__builtin__`;
- facts, review, generic names and generic evidence: the type atom;
- runtime C: the six builtins and the `runtime.h` IEEE guard;
- toolchain: no flag change (see C emission);
- formatter: no change. `fmt.nq` re-indents lines without tokenizing, so
  literals are already reproduced byte-for-byte.

The full write set is listed under "Write Set And Audit Classification".

No evidence schema version changes. `schemas/*.json` are unchanged. All
existing goldens must stay byte-identical, since no existing fixture uses
`f64`.

The selfhost compiler source contains no source-level `f64` values or float
literals (the name `f64` appears only inside string literals), so the
checked-in seed does not need to understand it. Seed promotion is not required: the
seed gate's historical path accepts the unchanged seed.

## Migration And Deferred Extensions

- No migration: no previously valid program changes meaning, because
  `digits.digits` was always rejected before (NQ-TYPE-042, verified on the
  `da7afdc` compiler).
- Validation tightening, not silent reinterpretation: programs that merely
  declare (but never construct) values of `f32`, `u32`, `u64`, or `char` in
  any type position now fail with NQ-TYPE-049. The fix is to remove the
  declaration. D067 and the release notes say so.
- Deferred: `f32`; unsigned integers; `char`; float literal patterns;
  compile-time float folding; total-order comparison; math functions;
  formatted rendering with fixed precision (`1.50`). The math functions and
  fixed-precision rendering belong to the standard-library planning in M57.
  Fixed precision can be written in source from `f64_trunc_i64` plus
  integer formatting once the digits are known.
- M57 input: JSON numbers map to `i64` when the token has no fraction or
  exponent and fits in `i64`, and otherwise through `f64_from_str` (which
  accepts the JSON number grammar). The JSON writer must reject non-finite
  values before calling `str_from_f64`.

## Write Set And Audit Classification

This list comes from a read-only survey of every place in the compiler that
`i64` touches (M53 is the template). Line numbers are guides, not limits.

- Lexer and AST:
  - `selfhost/token.nq`: `tk_float_lit`.
  - `selfhost/lexer.nq`: the float scan after `scan_digit_end`, and
    NQ-PARSE-004.
  - `selfhost/ast.nq`: an `expr_fact_kind` for the float literal.
  - `selfhost/parser.nq`: `classify_expr_kind`.
  - Every token scanner that lists `tk_int_lit`:
    - `typecheck.nq` (`token_can_end_expr`, `pattern_span_is_refined`);
    - `handoff.nq` (`token_can_end_expr`);
    - `generic.nq` (`generic_symbol`, `generic_syntax_pattern`,
      `generic_syntax_atom`).
  - The ordinal maps that mirror the expression-kind enum:
    `propagation_truth.nq`, and `typecheck.nq` `p2_frontend_expr_kind`.
- Resolve: `selfhost/resolve.nq` (`is_builtin_name` gains the six builtins;
  `is_builtin_type_name` stays, with NQ-TYPE-049 enforcing the reserved
  names).
- Typecheck (`selfhost/typecheck.nq`):
  - copy facts;
  - builtin arity, return, and parameter tables;
  - a numeric/float split beside `is_int_like`;
  - `float_literal_ctx` with the exact range check;
  - arithmetic, comparison, and unary-minus paths;
  - field-base type checks;
  - constants (`is_const_safe_type`, `infer_const_expr_type_ctx`, and
    `evaluate_typed_const` for literal-only `f64`);
  - `match` scrutinee and pattern rules;
  - NQ-TYPE-046..049.
- Ownership:
  - `selfhost/borrow.nq`: `is_copy_type` and the builtin parameter tables.
  - `selfhost/value_plan.nq`: type properties and the exhaustive
    expression-kind match.
- Handoff (`selfhost/handoff.nq`):
  - `checked_expr_f64` and `checked_type_f64`;
  - the exhaustive equality matches;
  - `canonical_type_origin_module`, `intern_checked_type_id`, and literal
    construction;
  - the builtin parameter tables.
- IR and C (`selfhost/ir.nq`, `selfhost/c_emit.nq`):
  - `ir_expr_f64`;
  - `type_mangle` and `c_type` (`double`);
  - literal, operator, and comparison emission (no integer-helper route);
  - `builtin_call_name`;
  - const emission;
  - the exhaustive matches.
- Evidence:
  - `selfhost/facts.nq`, `selfhost/review.nq`: builtin type and function
    tables.
  - `selfhost/generic.nq`, `selfhost/generic_names.nq`: the atom and
    mangling.
  - `selfhost/propagation_truth.nq`: the scalar and builtin spellings.
  - `selfhost/builtin_evidence.nq`: the builtin rows.
- Parser: `selfhost/parser.nq` gains the `tk_malformed_float_lit` →
  NQ-PARSE-004 path at every primary-literal site.
- Runtime: `stdlib/runtime.h` (the guard block, plus the `NQ_Option__f64`
  and `NQ_Option__i64` carriers) and `stdlib/runtime.c` (six `nq_*`
  functions, the per-call `"C"` locale lifecycle). `c_emit.nq`
  `is_runtime_native_option` adds `checked_type_f64` and `checked_type_i64`.
  `bootstrap/seed/runtime.*` is untouched.
- Host routes: if `scripts/check_fast.sh --host-suite provenance` or
  `--host-suite attestation` uses a compiler stub that must model the new
  capability requirement, its fixture is in the write set. No change to
  `scripts/provenance.sh` flag frames, `host_c.nq` arguments, or the
  `fixture_c.nq` allowlist.
- Tests:
  - `selfhost/m56_generics_tests.nq` (the atom flip);
  - a new focused section in an existing test module, or the
    lexer/typecheck test tables, for every table in "Tests And Acceptance";
  - `selfhost/proof.nq` corpus registration;
  - `tests/fixtures/m56_2_f64/**`;
  - `examples/f64_basics.nq`.
- Docs:
  - `SPEC.md` (primitive types, deferred list, builtins);
  - `GRAMMAR.md` (`FLOAT_LIT`, the `const_expr` note);
  - `FORMATTER.md` (one sentence);
  - `TEACHING_CORPUS.md`, `DEFERRED.md`, `README.md`, `AI_CONTRACTS.md`
    (type atoms);
  - `docs/M56_1_CONTRACT.md` (the atom sentence amendment);
  - `DECISIONS.md` D067, which records:
    - the compiler-relative atom rule: the atom set is the accepting
      compiler's builtin type set, and adding one changes no output for
      previously accepted input;
    - the NQ-TYPE-049 validation tightening;
    - the no-libm and no-new-flag choices;
    - the locale construction;
  - ROADMAP/TODO status lines.

No new `.nq` module, no `push_selfhost_modules` change, no seed or
bootstrap inventory change, and no compiler source uses `f64`.
Classification under AGENTS.md: routine milestone, one independent trailing
auditor. If implementation needs a new module or any inventory or bootstrap
change, stop, record it, and reclassify as a bootstrap-boundary milestone
with the mixed audit.

Suggested slices (disjoint write sets, merged in order):

- **A, front end:** token/lexer/ast/parser/resolve, the typecheck and
  handoff literal and operator paths, and NQ-PARSE-004 and
  NQ-TYPE-046..049.
- **B, back end:** ir/c_emit, the runtime builtins and guard, borrow and
  value_plan.
- **C, evidence and tests:** facts/review/generic/propagation and
  builtin_evidence, the fixture, goldens, corpus, and docs.

A goes first; B and C start from A's merged tree.

## Tests And Acceptance

Nauqtype-owned checks (run by `nauqc test` or the focused suites):

- **Lexer and parser:**
  - every legal literal shape;
  - every NQ-PARSE-004 case from the scan rule above, with its exact span;
  - `1.`, `1.e5`, `.5`, and `1e5` keep their current exact codes;
  - `x.field`, `1.foo`, and integer literals are unchanged.
- **Typecheck:**
  - positive and negative tables for each operator and comparison;
  - builtin arity and argument types;
  - an integer literal in `f64` context is rejected;
  - `match` on an `f64` scrutinee and float literal patterns
    (NQ-TYPE-047), and `some(x)` binding of an `f64` payload accepted.
- **Constant grammar:**
  - accepted: `1.0`, `-1.0`;
  - rejected with NQ-TYPE-048: `(1.0)`, `-(1.0)`, `((1.0))`, `--1.0`,
    `-(-1.0)`, `1.0 + 2.0`, a reference to another `f64` constant,
    `const B: bool = 1.0 < 2.0;`.
- **NQ-TYPE-049** for each of `f32`, `u32`, `u64`, `char` in each of these
  positions:
  - local, parameter, and return;
  - field and enum payload;
  - `ref` and `mutref` targets;
  - nested container (`list<option<u64>>`) and `result` argument;
  - explicit generic argument (`Bag<char>`);
  - inside an unused function and an unused type declaration.
- **Literal range** at the exact bound B = 2^1024 − 2^970 (309 decimal
  digits):
  - accepted: `1.7976931348623157e308` (the largest finite value);
    `1.7976931348623158e308` (below B, so it rounds to the largest finite
    value); B's full expansion with its last digit reduced by one, written
    with the required fraction as `<309 digits>.0`; the negation of each;
    a literal with 400 leading zeros in the fraction; `1.0e-400` and
    `-1.0e-400` (underflow to signed zero);
  - rejected with NQ-TYPE-046: `1.7976931348623159e308`; B's exact
    expansion written `<309 digits>.0`; `-<309 digits>.0`; `1.8e308`;
    `1.0e309`; and an exponent of 1000 digits.
- **Runtime fixture** `tests/fixtures/m56_2_f64/` (compiled with the
  `host_c.nq` arguments, and once more under
  `-fsanitize=address,undefined -fno-sanitize-recover=all` the way the
  existing `check_str_join.sh` builds) covers:
  - arithmetic: signed zero, overflow to infinity, NaN propagation,
    division by zero;
  - the full comparison truth table with NaN and ±0;
  - IEC 60559 behavior at run time: infinities, NaN self-inequality,
    `1.0 / -0.0` is −infinity, the smallest subnormal `5.0e-324` is nonzero
    and halves to zero;
  - `f64_from_i32` at `INT32_MIN`, `-1`, `0`, and `INT32_MAX`, each checked
    exactly through `f64_trunc_i32` and `str_from_f64`;
  - `f64_from_str` on slices: `str_slice("1.259", 0, 4)` gives `1.25`;
    `str_slice("12x", 0, 2)` gives `12`; a slice ending inside an exponent
    (`str_slice("1.0e5", 0, 4)`) gives `none`; and a 600-byte valid input
    takes the heap path;
  - the allocation-failure path: built with the existing
    `-DNQ_TEST_ALLOC_FAIL_AFTER=` test hook, a ≥512-byte `f64_from_str`
    input terminates with exit 1 and `nauqtype runtime: out of memory`;
  - `f64_from_i64` at 2^53 (`some`), 2^53+1 (`none`), 2^53+2 (`some`),
    `INT64_MAX` (`none`), and `INT64_MIN` (`some(-2^63)`);
  - `f64_trunc_i64` at ±2^63, the largest `double` below 2^63, −2^63, NaN,
    and ±infinity;
  - `f64_trunc_i32` at `2147483647.9`, `2147483648.0`, `-2147483648.9`,
    `-2147483649.0`, and `-0.5` (gives 0);
  - **rendering oracle:** exact expected strings for at least 60 vectors,
    including every example in this document; `1.0e-6` → `0.000001`;
    `1.0e-7` → `1e-7`; `1.0e20` → `100000000000000000000`; `1.0e21` →
    `1e+21`; the largest subnormal; the smallest normal; `0.1 + 0.2` →
    `0.30000000000000004`; and integers above 2^53;
  - **parsing oracle:** exact expected bit patterns for at least 60
    vectors, including grammar rejects (`+1`, `1.`, `.5`, ` 1`, `1 `,
    `01`, `1e`, `inf`, `NaN`, an embedded NUL); halfway ties that round to
    even in the normal range and at the subnormal/normal boundary;
    `1.7976931348623158e308` (finite) and `1.7976931348623159e308`
    (`none`); `-0` (negative zero); `1e-400` (zero); and a 1000-digit
    mantissa and exponent;
  - the round-trip law over a deterministic generated sample of at least
    10,000 bit patterns, including subnormals and both zeros;
  - a locale probe in C that sets the global locale to a comma-decimal
    locale when one is installed, then checks that both text builtins are
    unaffected. When none is installed (the WSL gate host has only
    `C`, `C.utf8`, `POSIX`), it records a skip. The `uselocale`
    construction is then additionally proved by code review in the trailing
    audit.
- **Option ABI:** a program that uses `option<i64>` directly and also calls
  `f64_trunc_i64` and `f64_from_str` compiles with no duplicate or
  incomplete type and runs correctly.
- **Evidence:** `f64` in a product field, an enum payload, `list<f64>`,
  `option<f64>`, `result<f64, E>`, a generic instance (`Bag<f64>`), and a
  `pub` function exported through a workspace dependency, with facts v5 /
  review v5 goldens showing `f64`.
- **The `runtime.h` guard:**
  - compiling a generated program with `-ffast-math` fails, and so does
    compiling it with `-std=gnu11` under GCC;
  - the host routes `--host-suite provenance` and `--host-suite
    attestation` pass;
  - a contraction probe in the runtime fixture (`a * b + c` with operands
    chosen so the fused and unfused results differ) yields the unfused
    result under the shipped flags. The probe is only meaningful on hosts
    with FMA in the baseline ISA, such as aarch64. On baseline x86-64 it
    passes trivially, so the WSL proof of the flag behavior is the
    assembly check recorded above.
- All existing goldens byte-identical (checked by the normal suites).
- The teaching example and negative case are in TEACHING_CORPUS.md.

Close: Gate A on this revision → implementation with focused checks → one
independent trailing audit → one full `scripts/check_milestone.sh` on the
frozen candidate → commit, then attestation close.

## Implementation Notes

Deviations from this contract that the compiler lead accepted during
implementation (also recorded in D067):

1. NQ-PARSE-004 is reported once per malformed float token and parsing
   continues, instead of stopping like NQ-PARSE-003. No cascade
   diagnostics result.
2. C emission writes any float literal whose value is at most 2^-1075
   (decided by exact textual comparison) as `0.0`, the value C rounds it
   to, to avoid GCC's default `-Woverflow` "truncated to zero" warning.
   Negation stays outside, so `-1.0e-400` is still negative zero.
3. `-ffp-contract=fast` is detected on GCC 13.3 (it clears
   `__GCC_IEC_559`, so `__STDC_IEC_559__` is undefined and the guard
   rejects it). The guard is stricter than specified above.
4. `selfhost/c_emit.nq` gained `use lexer;` for the shared
   literal-magnitude helper: an import edge, not a new module.
5. NQ-TYPE-049 is also reported for explicit generic arguments in
   `generic.nq` `generic_parse_type`.
6. The fixture-C warm-reuse scanner (`selfhost/fixture_c.nq`
   `fixture_c_directives_modeled`) now models `<float.h>` and
   `<locale.h>` and exactly one pragma line, `#pragma STDC FP_CONTRACT OFF`.
   Every other `#pragma`, and `_Pragma`, is still rejected, and unit cases
   pin both sides. Without this change the new runtime text made every
   owned fixture group compile cold (correct but slower). The compiler
   argument allowlist is unchanged.

Also as shipped: on Windows builds the runtime has no per-call locale
construction, so the two text builtins take the
`numeric locale unavailable` failure path instead of depending on the
process locale. The runtime's internal-invariant failures are
`nauqtype runtime: internal float parse mismatch` (named above) and the
analogous `internal float format mismatch` / `internal float render
mismatch` in rendering; none is reachable with a conforming C library.

Where the tests live: the end-to-end fixtures `tests/fixtures/m56_2_f64/`
`runtime.nq` and `option_abi.nq` (exact `.expected` output, run through
`nauqc run` with the `host_c.nq` arguments and again from the emitted C under
ASan/UBSan), `runtime_unit.c` (plain; ASan/UBSan with
`float-cast-overflow`; `-DNQ_TEST_ALLOC_FAIL_AFTER=0/2/3`), and the
`runtime.h` guard negatives all run in the `integer-policy` suite
(`selfhost/integer_policy_tests.nq`). The v5 evidence goldens
`tests/golden/schema_profile/facts-v5-f64.json` and `review-v5-f64.json`
(workspace `tests/fixtures/m56_2_f64/workspace/`) run in `driver-fixtures`
beside the M56.1 goldens. `examples/f64_basics.nq` is a locked corpus case.

## Acceptance Gate

M56.2 is complete when:

- all of the above pass in the single milestone gate;
- the trailing audit has no open findings;
- SPEC/GRAMMAR/FORMATTER/AI_CONTRACTS describe `f64` exactly as shipped;
- DECISIONS records D067;
- `f64` leaves SPEC's deferred numeric list.
