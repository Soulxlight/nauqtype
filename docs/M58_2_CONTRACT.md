# M58.2: Remainder And Counting Loops

Status: Gate A passed, 2026-11-01 (revision 3, approved; two nits applied).
Compiler lead. Not implemented. The independent Gate A reviewer
(`gpt-5.6-sol` xhigh) required changes on revision 1 (six blocking, four
should-fix; the split below) and revision 2 (two blocking, three should-fix,
one nit). Base: `e038ed1` (M58.1 complete). Charter:
[LANGUAGE_CHARTER.md](../LANGUAGE_CHARTER.md) (R1 fail at check, R2 canonical
forms, R7 explicit abstraction; "New v1 additions" scheduled in M58).

Revision 1 covered `%`, counting loops, literal patterns and coverage,
`match` positions, nested field assignment, constants and the R9 position
matrix. The Gate A reviewer (`gpt-5.6-sol` xhigh) required changes and judged
it too broad for one frozen candidate. The corrective sweep is therefore
split:

| Milestone | Scope |
| --- | --- |
| **M58.2** (this contract) | Integer `%`; range `for i in a..b` and indexed `for i, item in items` |
| M58.3 | `i64`, `bool` and `str` literal patterns; an exact coverage check replacing D047; unreachable-arm errors; `match` expression positions |
| M58.4 | Nested field assignment; constant comparisons (and, if specified fully, constants naming constants); the R9 position matrix in SPEC |
| M58.5 | Source rewrite tooling for the M60/M61 migrations (formerly M58.3) |

Revision 1's findings on coverage determinism, constant dependency graphs,
nested-assignment aliasing, the dead-arm migration inventory and the matrix's
completeness carry to the M58.3 and M58.4 contracts.

Owner decisions (2026-11-01): indexed `for` is `for i, item in items`;
ranges are half-open `a..b` only and exist only in a `for` header; `%` is the
truncated remainder and fails exactly where `/` fails.

## Problem

Probed and traced against `e038ed1`:

1. There is no remainder operator. `%` lexes as an unknown token and reports
   NQ-PARSE-005 "malformed expression".
2. `for` iterates only a `list<T>` (D051). Counting loops and loops that need
   the element's index are written with `while` and a manual counter, which is
   where off-by-one and missing-increment mistakes live.
3. `0..10` lexes as `0`, `.`, and the malformed float `.10`
   (`lexer.nq` `scan_leading_dot_number`), so a range written by habit gets a
   float diagnostic.

## Exact Semantics

### 1. Remainder `%`

- **Token.** `%` is a new single-character token.
- **Grammar.** `multiplicative = unary { ( "*" | "/" | "%" ) unary } ;`
  `%` has the precedence of `*` and `/` and is left associative with them:
  `a / b % c` is `(a / b) % c`, `a % b * c` is `(a % b) * c`. Every pass that
  splits expressions on the root multiplicative operator treats `%` exactly
  like `/` (typecheck, constant typing and folding, handoff, generic
  projection, parser fact classification).
- **Types.** Operands are both `i32` or both `i64`; the result has the
  operand type. `f64 % f64` is NQ-TYPE-050 "operator `%` is not defined for
  type `f64`". Any other operand type, and mismatched operand types, report
  exactly what `/` reports for the same operands today.
- **Value.** `a % b` is the truncated remainder (C99): the result has the
  sign of `a` (or is zero), and `a == (a / b) * b + a % b` whenever `a / b`
  is defined.
- **Failure.** `x % 0` and `MIN % -1` (`MIN` the type's minimum) terminate the
  program exactly as `/` does in the same cases: stderr receives
  `nauqtype runtime: integer remainder by zero` or
  `nauqtype runtime: integer remainder overflow` followed by a newline, and
  the process exits with status 1. The runtime adds `nq_i32_rem` and
  `nq_i64_rem`, checked like `nq_i32_div`/`nq_i64_div`; emitted C never
  evaluates C's `%` with a zero divisor or with `MIN` and `-1`, at any
  optimization level.
- **Evaluation order and short-circuit.** As for `/`: both operands are
  evaluated left to right before the check; `%` inside the unevaluated
  operand of `and`/`or` is never evaluated.
- **Constants.** `%` folds in integer constant initializers. A constant
  remainder by zero or `MIN % -1` is NQ-TYPE-045 at the `%` token with message
  "constant integer remainder by zero" or "constant integer remainder
  overflow" and help "Change the evaluated constant remainder; a zero divisor
  and the minimum integer with divisor -1 are not defined results." The runtime adds
  `NQ_I32_CONST_REM`/`NQ_I64_CONST_REM`, guarded like the `_DIV` macros.
- **Evidence.** None (termination evidence arrives with M62).

### 2. Range `for`

- **Lexing.** `..` is one token, read before any other rule that starts with
  `.` (maximal munch, left to right: two adjacent dots always form `..`). A
  single `.` that is not part of a `..` and directly follows a `..` token is a
  plain `.` token (it never starts a leading-dot float). So:

  | Source | Tokens |
  | --- | --- |
  | `0..10` | `0`, `..`, `10` |
  | `a..b`, `a .. b` | `a`, `..`, `b` |
  | `x.len..y.len` | `x`, `.`, `len`, `..`, `y`, `.`, `len` |
  | `1...2` | `1`, `..`, `.`, `2` |
  | `1....2` | `1`, `..`, `..`, `2` |
  | `1..=2` | `1`, `..`, `=`, `2` |
  | `1.0..2.0` | `1.0`, `..`, `2.0` |

- **Grammar.**
  `for_stmt = "for" IDENT [ "," IDENT ] "in" for_iterable block ;`
  `for_iterable = expr ".." expr | expr ;`
  The range splits at the `..` token at bracket depth zero in the iterable
  span; `..` binds more loosely than every operator, so `0..n + 1` is
  `0..(n + 1)`.
- **Malformed ranges** in a `for` header are **NQ-PARSE-006**, reported once
  by `parse_file` at the `..` token; the statement contributes no other
  diagnostic:

  | Shape | Message |
  | --- | --- |
  | `..` followed by `.` or `=` (`1...2`, `1..=2`) | ``ranges are written `a..b`; there is no `...` or `..=` form`` |
  | nothing before `..` (`for i in ..n`) | ``a range needs a start bound: `a..b` `` |
  | nothing after `..` (`for i in 0..`) | ``a range needs an end bound: `a..b` `` |
  | a second `..` at depth zero (`0..1..2`) | ``a range has exactly two bounds: `a..b` `` |
  | a range inside parentheses (`for i in (0..n)`) | ``write the range without parentheses: `for i in a..b` `` |

  The rows are tested in this order, and the first that applies is reported:
  (a) `...`/`..=`, (b) a second `..` at depth zero, (c) parentheses,
  (d) missing start bound, (e) missing end bound. `1....2` is (b);
  `for i in (0..)` is (c).
- **One diagnostic per `for` header.** A malformed header reports exactly
  one diagnostic, chosen by this precedence: (1) binding syntax
  (NQ-PARSE-003 for a missing name around the `,`, or a missing `in`);
  (2) the indexed-over-range rejection (NQ-PARSE-006 at the `,`); (3) the
  malformed-range rows above, in the order (a)-(e). So `for i, in 0..n` is
  NQ-PARSE-003, `for i, x in 0..` is the indexed-over-range rejection, and
  `for i in (0..)` is the parenthesized-range row.

- **Ranges are not values.** A `..` token anywhere other than at depth zero
  of a `for` iterable is NQ-PARSE-006 ``a range `a..b` is only allowed as the
  iterable of a `for` loop`` at the `..`, reported once; the enclosing
  statement contributes no other diagnostic.
- **Types.** Both bounds are `i32` or both `i64`; the binding has that type.
  Otherwise **NQ-TYPE-062** ``range bounds must both be `i32` or both be
  `i64`; found `<A>` and `<B>` `` at the `..` token, with types spelled as in
  other type diagnostics. A bound that fails to type-check reports only its
  own diagnostic.
- **Execution.** The start bound is evaluated, then the end bound, each
  exactly once, before the first iteration (into hidden locals). The body
  runs with the binding equal to `a`, `a + 1`, ..., `b - 1`; it does not run
  when `a >= b`. The binding is incremented only after a body run with
  `i < b`, so `MAX - 1 .. MAX` runs once and never overflows. `break` and
  `continue` behave as in list loops.
- **`?`** in a bound is NQ-PROPAGATE-007, as for any other `for` iterable.
- **Scope.** The bound expressions see only bindings visible before the
  loop; the loop binding is visible from the start of the body
  (`visible_from` = body start), is immutable (existing "`for` loop bindings
  are immutable"), and does not escape the body.

### 3. Indexed `for`

- `for i, item in items { ... }`: `items` is any `list<T>` expression under
  the existing list-loop rules (D051: evaluated once, copy element types
  only, same diagnostics). `i` is an `i32` running `0, 1, ...,
  list_len(items) - 1`; `item` is the element at `i`.
- `for i, x in a..b` is NQ-PARSE-006 ``an indexed `for` iterates a list; a
  range already provides its index`` at the `,`, reported once.
- `for i, i in xs` reports the existing "duplicate local binding in one
  scope" diagnostic at the second name, exactly once.
- `for i, in xs` and `for , x in xs` are NQ-PARSE-003 "expected identifier"
  at the token after (or at) the `,`.
- Both bindings are immutable, body-scoped, and visible from the start of the
  body. Each has its own binding fact with its own declaration identity (the
  byte offset of its name), its own semantic binding ID in the checked
  handoff, and its own C local. Shadowing, mutation evidence and call
  evidence treat each exactly as a list-loop binding is treated today.

### 4. Representation (both loop forms)

Field mapping, by loop form (new fields in bold; "—" means the field keeps
its "absent" value: `""`, `-1`):

| Record | Field | List `for x in xs` | Indexed `for i, x in xs` | Range `for i in a..b` |
| --- | --- | --- | --- | --- |
| `stmt_fact` (`ast.nq`) | **`for_kind`** | `for_list` | `for_indexed` | `for_range` |
| | `name`, `at` | `x`, its byte offset | `x`, its byte offset | `i`, its byte offset |
| | **`index_name`**, **`index_at`** | — | `i`, its byte offset | — |
| | `expr_start`, `expr_end` | `xs` tokens | `xs` tokens | `a` tokens |
| | **`bound_end_start`**, **`bound_end_end`** | — | — | `b` tokens |
| checked `for` (`handoff.nq` `checked_stmt`) | **`for_kind`** | list | indexed | range |
| | `target_binding_id` | `x` | `x` | `i` |
| | **`index_binding_id`** | — | `i` | — |
| | `expr_id` | `xs` | `xs` | `a` |
| | **`end_expr_id`** | — | — | `b` |
| IR `for` (`ir.nq` `ir_stmt`) | **`for_kind`** | list | indexed | range |
| | `target_local_id` | local of `x` | local of `x` | local of `i` |
| | **`index_local_id`** | — | local of `i` | — |
| | `expr_id` | `xs` | `xs` | `a` |
| | **`end_expr_id`** | — | — | `b` |

Checked binding IDs (`*_binding_id`) and IR local IDs (`*_local_id`) are
distinct ID spaces, as today. A list loop's records and emitted C are
unchanged.
- Every consumer that matches on statement or IR kinds or copies these
  records is updated: at least `ast.nq`, `parser.nq` (all four statement
  walkers), `resolve.nq`, `typecheck.nq`, `handoff.nq`, `value_plan.nq`,
  `borrow.nq`, `ir.nq`, `c_emit.nq`, `facts.nq`, `review.nq`, `generic.nq`
  (projection reparses source), and the checked-index probes
  (`checked_index_probe.nq`, `c_emit_index_probe.nq`).
- C: every loop binding is a semantic local declared in the function
  prelude, like every other non-parameter local, and assigned at the top of
  each iteration. A range loop lowers to
  `T nq_range_lo_N = <a>; T nq_range_hi_N = <b>;`
  `for (T nq_range_i_N = nq_range_lo_N; nq_range_i_N < nq_range_hi_N; nq_range_i_N += 1) { <i> = nq_range_i_N; ... }`
  with `T` `int32_t` or `int64_t` (the increment runs only while
  `nq_range_i_N < nq_range_hi_N`, so it cannot overflow). The indexed loop is
  the list loop with `<i> = nq_for_index_N;` added before the element
  assignment at the top of each iteration.

### 5. Formatter

Formatter-lite does not reflow expressions (FORMATTER.md): it preserves
intra-line spelling. It must accept the new tokens unchanged (`fmt --check`
succeeds on canonical sources containing `%`, `..` and indexed loops). The
canonical style used by examples and docs is `a % b`, `for i in 0..n {`,
`for i, item in items {` (no spaces around `..`).

### 6. Termination and other rules

A `for` loop of any form never terminates for the every-path-returns rule
(M58.1). `facts.nq` `is_reserved_word` gains the keywords it omits (`and`,
`break`, `continue`, `for`, `in`, `not`, `or`, `try`).

## Rejected Alternatives

- **Inclusive or stepped ranges, descending ranges.** A second spelling for
  overlapping intent (R2); such loops stay `while` loops.
- **Range values or an iterator protocol.** Hidden dispatch and a new type
  family (R7); D051 rejected an iteration protocol.
- **`MIN % -1 == 0`.** Mathematically defined, but breaks the symmetry with
  `/` the owner chose.
- **Floating `%`.** Belongs with the standard library's math functions
  (M67).
- **Parenthesized ranges.** Two spellings of one header (R2).

## Diagnostics Matrix

| Code | When | Span | Message | Help |
| --- | --- | --- | --- | --- |
| NQ-TYPE-050 (code kept) | `%` on `f64` | the `%` | ``operator `%` is not defined for type `f64` `` | as for other NQ-TYPE-050 |
| (codes kept) | `%` with operands other than two `i32`, two `i64` or two `f64` | as for `/` | exactly the code, span, message and help `/` reports for the same operand types at `e038ed1` (frozen by tests that compare the `%` and `/` diagnostics byte for byte, with the operator character substituted) | as for `/` |
| NQ-TYPE-045 (code kept) | constant `%` by zero | the `%` | ``constant integer remainder by zero`` | ``Change the evaluated constant remainder; a zero divisor and the minimum integer with divisor -1 are not defined results.`` |
| NQ-TYPE-045 (code kept) | constant `MIN % -1` | the `%` | ``constant integer remainder overflow`` | same |
| NQ-TYPE-062 | range bound types | the `..` | ``range bounds must both be `i32` or both be `i64`; found `<A>` and `<B>` `` | none |
| NQ-PARSE-006 | range outside a `for` iterable | the `..` | ``a range `a..b` is only allowed as the iterable of a `for` loop`` | none |
| NQ-PARSE-006 | `...` / `..=` | the `..` | ``ranges are written `a..b`; there is no `...` or `..=` form`` | none |
| NQ-PARSE-006 | missing start bound | the `..` | ``a range needs a start bound: `a..b` `` | none |
| NQ-PARSE-006 | missing end bound | the `..` | ``a range needs an end bound: `a..b` `` | none |
| NQ-PARSE-006 | two `..` | the second `..` | ``a range has exactly two bounds: `a..b` `` | none |
| NQ-PARSE-006 | parenthesized range | the `..` | ``write the range without parentheses: `for i in a..b` `` | none |
| NQ-PARSE-006 | indexed loop over a range | the `,` | ``an indexed `for` iterates a list; a range already provides its index`` | none |
| (runtime, exit 1) | `x % 0` | — | ``nauqtype runtime: integer remainder by zero`` | — |
| (runtime, exit 1) | `MIN % -1` | — | ``nauqtype runtime: integer remainder overflow`` | — |

Exact strings are fixed in the tests. NQ-TYPE-062 and NQ-PARSE-006 are unused
at `e038ed1`.

## Evidence Impact

No schema changes. facts and review contain no loop-specific records; the
new bindings appear wherever list-loop bindings appear today (binding
identity in mutation and call evidence). For every program accepted at
`e038ed1`, facts and review output and the emitted C are byte-identical.

## Migration

No accepted program changes meaning or becomes an error. Newly accepted:
`%`, range loops, indexed loops. Diagnostic-only changes for programs that
were already rejected:

- every `%` reported NQ-PARSE-005 "malformed expression" (unknown token); a
  `%` with valid integer operands is now accepted, and an invalid one reports
  the `/`-equivalent type diagnostic, NQ-TYPE-050 for `f64`, or NQ-TYPE-045
  for an invalid constant;
- `0..10` and other `..` shapes reported a malformed-float or
  malformed-expression diagnostic; they now report NQ-PARSE-006, NQ-TYPE-062,
  or are accepted as range loops.

## Write Set And Audit Classification

- `selfhost/`: `token.nq`, `lexer.nq`, the files listed in Representation,
  `const_word.nq` (`const_word_rem`), `fmt.nq` if it must accept the new
  tokens, plus tests in existing test modules.
- `stdlib/runtime.h`/`runtime.c`: `nq_i32_rem`, `nq_i64_rem`,
  `NQ_I32_CONST_REM`, `NQ_I64_CONST_REM`, and the remainder failure messages.
  The bootstrap seed (`bootstrap/seed/**`, including its runtime copy) and the
  seed machinery are untouched; the compiler's own source does not use the
  new forms, so no seed promotion. If either assumption changes, the
  milestone is reclassified and the lead notified.
- Tests: `tests/fixtures/m58_2/**`; a teaching example using `%`, a range
  loop and an indexed loop in the locked corpus.
- Docs: SPEC (operators, For, keywords/grammar notes), GRAMMAR (tokens,
  `multiplicative`, `for_stmt`), DEFERRED, TEACHING_CORPUS, DECISIONS D071,
  FORMATTER (new tokens accepted). The M58.2-M58.5 split is recorded in
  ROADMAP, TODO, DEFERRED and NAUQTYPE_COORDINATION with this contract's
  Gate A commit, before implementation.
- **Ownership-class milestone:** new loop bindings and their checked
  binding identities feed moves, borrows and evidence; the trailing audit is
  a `gpt-5.6-sol` xhigh primary plus an independent `gpt-6.1-sol` xhigh
  adversarial auditor.

## Tests And Acceptance

- `%`: `i32` and `i64` results for all four sign combinations and zero
  dividends; `x % 0` and `MIN % -1` for both types terminate with exact stderr
  and exit status, in builds at the default flags, with the emitted C
  compiled at `-O2`, and under ASan/UBSan; operands with observable side
  effects (calls that print) show left-then-right, exactly-once evaluation,
  including when the remainder then fails; constant `MIN % -1` for both
  widths; the `/`-equivalence test for every rejected operand-type pair;
  mixed `/` and `%` associativity (`7 / 2 % 2`, `7 % 4 / 2`) and precedence
  with `+`; `%` in the unevaluated operand of `and`/`or` is not evaluated;
  constant folding (all sign combinations) and both constant errors;
  `f64 %` rejection; mismatched operands.
- Lexing: the token table above as a token-stream test, plus `1.foo`,
  `1.e5`, `.5` and `1.0` unchanged.
- Range loops: `i32` and `i64` with exact output; empty (`a == b`, `a > b`);
  bounds evaluated once each, start before end (side-effecting calls
  observed through output); `MAX - 1 .. MAX` for both types (one iteration, no
  overflow, UBSan clean); `break` and `continue`; a bound expression naming
  an outer variable that the loop binding shadows; NQ-TYPE-062 for
  `i32`/`i64`, `i32`/`bool` and `f64` bounds; every NQ-PARSE-006 row, each
  reported exactly once with no other diagnostic; `?` in a bound; assignment
  to the binding; a function ending in a range loop is NQ-TYPE-053.
- Indexed loops: exact output; both bindings immutable (assignment to each
  rejected); duplicate names; the missing-name parse errors; shadowing of
  outer names by each binding; facts and review naming each binding
  correctly in a program that passes `mutref` of a local inside the loop and
  calls with both bindings as arguments.
- Checked-handoff, IR and C-index probe assertions for each loop form: the
  kind, `target_binding_id`/`index_binding_id`, `target_local_id`/
  `index_local_id`, `expr_id`/`end_expr_id`, exactly as the Representation
  table maps them; the prelude declares every loop binding once.
- The one-diagnostic precedence cases (`for i, in 0..n`, `for i, x in 0..`,
  `for i in (0..)`, `1....2`).
- Byte-identical facts, review and emitted C for unaffected accepted
  programs (a list-loop program among them).
- `fmt --check` on the teaching example; the reserved-word list.
- Compiler self-check, full corpus, seed bootstrap, and the full milestone
  gate.

## Acceptance Gate

M58.2 is complete when all of the above pass in the single milestone gate,
both trailing audits have no open findings, SPEC and GRAMMAR describe the
shipped rules, and DECISIONS records D071.
