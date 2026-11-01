# M58.1: Correctness And Diagnostics

Status: Gate A passed, 2026-10-31 (revision 4, approved with no findings).
Compiler lead. Not implemented. The
independent Gate A reviewer (gpt-5.6-sol xhigh) required changes on
revision 1 (nine blocking, one should-fix), revision 2 (two blocking, three
should-fix, one nit) and revision 3 (two blocking); all are addressed below. Two tutorial-site findings (a stale field-assignment message and a
duplicated parse error for nested field assignment) were added. Base: `4d80e70`. Charter: [LANGUAGE_CHARTER.md](../LANGUAGE_CHARTER.md)
(R1 fail at check, R2 canonical forms, R9 no arbitrary asymmetry).

M58 is the charter's corrective sweep, split by size into three milestones:

| Milestone | Scope |
| --- | --- |
| **M58.1** (this contract) | Make accepted programs mean what they say and diagnostics honest: missing-return analysis, initializer scope, one exhaustiveness rule, every reachable stage1-limitation path, let-else exits, diagnostics and driver defects, specification drift |
| M58.2 | Small language additions the charter lists for v1: integer `%`, `i64` and `bool` patterns, a real pattern-coverage check replacing the D047 fallback rule, range and indexed `for`, the R9 position matrix |
| M58.3 | Source rewrite tooling for the M60/M61 migrations: token-span edit engine, batch rename, guarded write |

No new syntax in M58.1. Every change rejects a program that is wrong today,
makes a diagnostic truthful, fixes a miscompile, or makes the compiler accept
what SPEC already promises (let-else loop exits, per-operand `?` inside
`try`); the Migration section lists each. Closing evidence goes to AUDIT_REMEDIATION.

## Problem

Probed and traced against `4d80e70` (code-site survey 2026-10-31):

1. A function body that can end without `return` compiles. The C function
   returns a zero-initialized value (`c_emit.nq` emits `T ret = {0};` and the
   final cleanup returns it). `main` that falls off the end exits 0. No check
   exists.
2. `let mut x = x + 1;` in an inner scope reads the new, zero-initialized `x`,
   not the outer one: the binding becomes visible at its name token, before
   its initializer (`parser.nq` pushes it at `name.start`; every lookup
   selects bindings with `at < ref.at`). Let-else already binds at the `;`.
3. Statement and expression `match` use different exhaustiveness rules and
   codes: expressions report NQ-TYPE-042 with no missing list and restrict the
   scrutinee; statements report NQ-TYPE-051 with a list, accept any scrutinee,
   and accept a zero-arm `match` on `i32`, `bool` or `str` (empty required
   variant list).
4. Ordinary source reaches "stage1 limitation" diagnostics (charter R1):
   `.5`, `1.`, `1e5`; struct literals without `name: value` fields; unknown
   constructor patterns (`Nope(x) =>`, `m::Nope =>`); `true =>`, `"s" =>`,
   `-x =>` patterns; constants that reference names, call functions or build
   lists; `?` outside statement position (`return f()?;`, `g(f()?);`,
   `if f()? {`). Handoff, borrow, IR and C-emitter invariant failures also
   say "stage1 limitation".
5. SPEC says `break`/`continue` may exit a let-else `else` block; the parser
   requires `return`.
6. Diagnostics: each parse error is printed four times (four token walkers
   each report it); a missing `;` is reported as "unterminated block" (the
   recovery skips the block's closing brace); `help` text appears only in JSON
   output; a missing workspace lock gives NQ-IO-001 against a module name with
   no file; `try { f()? + g()? }` is checked as `(f()? + g())?` and reports
   NQ-TYPE-042; load and parse errors do not stop the pipeline, so `run`
   cascades into "missing main".
7. Driver: `nauqc run <src> -o <relative>` resolves the output against the
   source directory and fails to start the program; `build -o <exe>` writes
   its C file to `<srcdir>/build/` instead of beside the executable.
8. Documentation drift: SPEC's keyword list and statement list omit
   `for`/`in` and SPEC has no `For` section; GRAMMAR's `borrow_expr` is
   `"ref" IDENT` although field paths are legal; GRAMMAR's `named_type` omits
   `f64`; loop control is described as `while`-only although `for` supports
   it; SPEC plans `unused_mut` and discarded-`result` lints that have no
   producer; SPEC says constants are `snake_case` (the charter says
   `UPPER_SNAKE`, enforced in M60).

## Exact Semantics

### 1. Every path returns

- A function body must not be able to reach its closing brace. This applies
  to every function, including `unit` functions and `main`: `unit` functions
  end every path with `return;` (one canonical form, R2).
- A **block terminates** if any statement in it terminates; analysis of a
  block stops at its first terminating statement, and later statements are
  ignored (not diagnosed: no unreachable-code lint in M58.1).
- A statement **terminates** when it is:
  - `return ...;`;
  - an `if` with an `else` block in which both blocks terminate (the grammar
    has no `else if`; a nested `if` inside the `else` block is analysed as
    that block's statement);
  - a statement `match` (exhaustive by rule 3) in which every arm block
    terminates;
  - `while true { ... }`, where the condition is exactly the token `true`
    (`(true)` and other constant expressions do not count), and the body
    contains no `break` targeting that loop (a `break` inside a nested
    `while` or `for` targets the nested loop).
- `for`, any other `while`, `try` boundaries, assignments, `let` statements
  and expression statements never terminate.
- For let-else (rule 5) only, `break` and `continue` also end their block.
  They never make a function body terminate.
- Violation: **NQ-TYPE-053** "function `<name>` can reach the end of its body
  without returning", spanning the function's closing `}`. Help: "end every
  path with `return`; a `unit` function ends with `return;`".
- The C emitter keeps a backstop: a function whose checked body can reach the
  end without a return is NQ-C-001 "internal: function can fall off the end"
  and emits no C definition (same preflight mechanism as M57.1's statement
  match backstop). The zero-initialized return slot remains only as the
  storage for `ret`, never as an observable result.

### 2. Initializer scope

- Binding facts keep their declaration position (`at`, used for identity,
  spans and evidence, unchanged) and gain a separate **`visible_from`**
  position in `ast.nq`. Every lookup family (resolve, typecheck, handoff and
  the phases that consume handoff) selects candidates with
  `visible_from <= ref.at` instead of `at < ref.at`.
- `visible_from` per binding form:

  | Binding form | Visible from |
  | --- | --- |
  | function parameter | start of the body (unchanged) |
  | `let`, `let mut`, typed `let` | the end of its statement (`;`) |
  | `let x = f()?;` propagation local | the end of its statement |
  | `let x: T = try { ... };` local | the end of its statement |
  | let-else bindings | the end of the let-else statement (unchanged) |
  | `match` arm pattern bindings | the start of the arm body (unchanged) |
  | `for x in items` binding | the start of the loop body; the iterable expression sees only outer bindings (unchanged) |

- So `let mut x = x + 1;` reads the outer `x`. `let x = x;` with no outer
  `x` is the existing unknown-name diagnostic (newly rejected; listed under
  Migration).

### 3. One exhaustiveness rule

- Statement and expression `match` share one check and one code,
  **NQ-TYPE-051**, renamed "match must be exhaustive; missing `<cases>`".
  The expression form's NQ-TYPE-042 "match expression must be exhaustive" is
  retired (its programs now report NQ-TYPE-051 with the missing list).
- Supported scrutinee types are the same for both forms: `i32`, `i64`,
  `option<T>`, `result<T, E>` and user enums (including concrete generic
  enum instances). `bool` joins the set in M58.2 together with `bool`
  patterns. An `f64` scrutinee keeps its existing NQ-TYPE-047 diagnostic
  unchanged. Any other scrutinee type (`bool`, `str`, products, lists, ...) is
  **NQ-TYPE-054** "cannot `match` on type `<type>`" with help "match on
  `i32`, `i64`, `option`, `result` or an enum; compare other values with
  `==` and `if`". (Today a statement accepts, for example, a `str` or `bool`
  scrutinee with a `_` arm; that becomes an error, listed under Migration.)
- Closed domains (enums, `option`, `result`) need every variant covered by a
  top-level arm or a wildcard/binding fallback; the missing list names the
  variants in declaration order (`option`: `Some`, `None`; `result`: `Ok`,
  `Err`), using the variant names as written for generic enum instances.
  Open domains (`i32`, `i64`) need a wildcard or binding fallback; their
  missing list is rendered as `_`.
- **Precedence:** the scrutinee type is checked first. An `f64` scrutinee
  reports NQ-TYPE-047 and any other unsupported type NQ-TYPE-054, and no
  arm-count or exhaustiveness diagnostic follows for that `match`. The rules
  below apply only to supported scrutinee types.
- A zero-arm **statement** `match` is exhaustive only over an empty user
  enum; any other zero-arm statement `match` reports NQ-TYPE-051 with its
  full missing list. A zero-arm **expression** `match` keeps today's rule:
  an expression `match` needs at least one arm, and its existing diagnostic
  is unchanged (an expression needs an arm to give it a type).
- The D047 refined-pattern rule (literal or nested constructor arms require a
  fallback) is unchanged in M58.1; M58.2 replaces it.

### 4. No reachable stage1 limitations

"Production source" means `selfhost/*.nq` excluding test modules
(`*_tests.nq`) and probes (`*_probe.nq`). Every production diagnostic whose
text begins with one of the three legacy prefixes "stage1 limitation",
"stage1 ir error" or "stage1 c error" is either made unreachable from source
with a focused rule, or reclassified as an internal invariant. Front-end
producers reachable from source:

The Diagnostics Matrix below is authoritative for every code, span, message
and help string; this table only maps constructs to codes.

| Source construct | M58.1 diagnostic |
| --- | --- |
| `.5`, `1.`, `1e5`, `1E5`, `1e-5` | NQ-PARSE-004 |
| struct literal field that is not `name: value` | NQ-TYPE-055 |
| unknown constructor in a pattern (`Nope(x)`, `m::Nope`) | NQ-RESOLVE-010 (if a resolve diagnostic already fires first, no NQ-TYPE-042 follows it) |
| `true`/`false` pattern | NQ-TYPE-056 (removed by M58.2) |
| string literal pattern | NQ-TYPE-056 |
| negated non-literal pattern (`-x`) | NQ-TYPE-056 |
| constant initializer with a name, call or list | NQ-TYPE-057 |
| `?` outside a statement position | NQ-PROPAGATE-007 |
| a non-name callee (`(f)(1)`) | NQ-TYPE-058 |
| nested field assignment (`o.inner.value = 0;`), today a parse error printed twice | NQ-TYPE-059, reported once |

The field-assignment root message (NQ-TYPE-042, stale since M57.1) is
corrected as the matrix specifies.

- Back-end producers in handoff (NQ-HANDOFF-001, about 62 call sites),
  borrow (NQ-BORROW-008, about 37), IR (NQ-IR-012) and the C emitter
  (NQ-C-001, about 98) change their prefix to "internal compiler error:" and
  keep their codes.
- **Producer ledger.** The milestone adds `docs/M58_1_PRODUCER_LEDGER.md`:
  the frozen inventory of every producer call site at the base `4d80e70`
  whose message carried one of the three legacy prefixes. Each entry has a
  stable identifier (`<file>:<function>:<n>`, the n-th such call in that
  function at the base), the base message, and its disposition: *covered*,
  naming the earlier rule and the fixture that proves the source shape is
  rejected before this phase; *internal*, naming the invariant an earlier
  phase establishes and the phase-level test or probe that exercises the
  producer; or *removed*, when the call site no longer exists. A checked
  test verifies that every ledger identifier's disposition evidence (rule,
  fixture or probe) exists, and that no production source contains a
  legacy prefix, so a newly introduced legacy producer fails the build.
- Acceptance: no production source string begins with a legacy prefix; the
  corpus and every negative fixture produce no "internal compiler error".

### 5. let-else exits

- A let-else `else` block must terminate by rule 1 or end with `break` or
  `continue` that targets an enclosing loop. This matches SPEC; the parser's
  "must exit explicitly with `return`" rule and its message are replaced by
  the shared termination predicate. Violation: the existing let-else code
  with message "let-else `else` block must exit with `return`, `break` or
  `continue`".

### 6. Diagnostics

- **Once per error.** Each parse diagnostic is reported once: the three
  secondary token walkers (`collect_typecheck_facts`,
  `collect_value_type_facts`, `collect_stmt_facts`) report into a discarded
  list; `parse_file` is the single reporter. Acceptance proves no secondary
  walker emits a diagnostic that `parse_file` does not.
- **Stop after load and parse errors.** If loading the module graph or
  parsing any module reports an error, the command stops before resolution,
  reports exactly those diagnostics in its existing diagnostic envelope, and
  exits non-zero, so no cascade (for example "missing main") follows:

  | Command | Behaviour on load/parse error |
  | --- | --- |
  | `check`, `build`, `run`, `emit-c` | diagnostics only; no C, executable or run |
  | `facts`, `review`, `policy-check`, `refactor-rename` | diagnostics only, in the same envelope those commands use today when `check` fails; no evidence document or edit plan |
  | `review-diff`, `change-report` | each side is loaded and parsed independently; if either side fails, that side's diagnostics are reported with the side label these commands already use, and no comparison is produced |
  | no-argument legacy/default invocation (`run_pipeline`) | same stop: diagnostics only |
  | `fmt`, `test`, `prove*`, `version`, `help` | unchanged (they do not load a module graph through this path) |

  Evidence schemas are unchanged: no command emits a new document shape.
- **Missing `;`.** Recovery stops at an unmatched `}`; the diagnostic is
  NQ-PARSE-003 "expected `;`" at the end of the statement's last token.
- **Help in text output.** The text renderer prints `help: <text>` (and
  `note: <text>`) lines after the message whenever the diagnostic has them,
  exactly as JSON already carries them.
- **Missing or stale workspace lock.** The diagnostic keeps code NQ-IO-001
  and its existing message text, but its file becomes the workspace manifest
  path as the driver resolved it (relative to the invocation directory when
  the user gave a relative path) and its span is file-level (start and end
  -1), instead of a bare module name.
- **`?` inside `try` binary expressions.** In `try { f()? + g()? }` each `?`
  applies to its own direct call operand: a trailing `?` is whole-expression
  propagation only when its operand is a direct call starting at the
  expression start. The program is accepted, each propagation lowers
  separately to the `try` boundary, and it executes (acceptance runs it).
  Whole-expression `(f() + g())?` stays rejected under SPEC's direct-call
  rule with its existing diagnostic code and message, pinned by a fixture.

### 7. Driver

- `-o` paths for `build` and `run` resolve against the invocation directory.
- `build -o <exe>` writes its C file beside `<exe>` (`<exe>.c`), never inside
  the source tree. `build -o <file>.c` behaves as today.

### 8. Documentation

- SPEC: keyword and statement lists include `for`/`in`; a `### For` section
  describes D051's list loop; loop control covers `while` and `for`; the
  let-else, initializer-scope, every-path-returns and exhaustiveness rules
  above; the patterns section names the focused diagnostics; the lints
  section lists only lints that have producers (planned lints move to
  DEFERRED); the constant naming sentence defers to the charter (M60).
- GRAMMAR: `borrow_expr` with field paths and parentheses; `named_type`
  includes `f64`.
- Stale Python driver test expectations that contradict the shipped
  messages are updated or retired with a note.

## Rejected Alternatives

- **Implicit `unit` return.** Two spellings for the same exit (R2); explicit
  `return;` is already the canonical spelling and the common one in the
  compiler's own source.
- **Treating any `while` as possibly non-terminating.** `while true` without a
  `break` is the idiom for loops that exit by `return`; requiring a dead
  trailing `return` adds noise without information.
- **Keeping two exhaustiveness codes.** Two rules for one concept (R9).
- **Unreachable-code diagnostics now.** Useful, but a separate lint with its
  own false-positive questions; deferred.
- **Splitting NQ-TYPE-042 into per-message codes now.** About 80 messages
  share it. Splitting is diagnostic polish, not correctness; recorded for a
  later milestone. New diagnostics in M58.1 get their own codes.

## Diagnostics Matrix

Every new or changed diagnostic, exactly. `<...>` are substitutions. "none"
means the diagnostic carries no help line.

| Code | When | Span | Message | Help |
| --- | --- | --- | --- | --- |
| NQ-TYPE-053 | body can reach its end | function's closing `}` | ``function `<name>` can reach the end of its body without returning`` | ``end every path with `return`; a `unit` function ends with `return;` `` |
| NQ-TYPE-051 | non-exhaustive `match`, both forms (renamed from "match statement must be exhaustive; missing ...") | `match` keyword | ``match must be exhaustive; missing `<C1>`, `<C2>` `` | ``add an arm for each missing case or a `_ => { ... }` fallback arm`` (unchanged) |
| NQ-TYPE-054 | unsupported scrutinee type other than `f64` | scrutinee expression | ``cannot `match` on type `<type>` `` | ``match on `i32`, `i64`, `option`, `result` or an enum; compare other values with `==` and `if` `` |
| NQ-TYPE-055 | malformed struct literal field | the field's first token | ``struct literal fields are written `name: value` `` | none |
| NQ-TYPE-056 | `true`/`false` pattern | the pattern | ``bool patterns are not supported yet`` | ``use `if`, or bind the value with a name`` |
| NQ-TYPE-056 | string literal pattern | the pattern | ``string patterns are not supported`` | ``compare strings with `==` and `if` `` |
| NQ-TYPE-056 | negated non-literal pattern | the pattern | ``only integer literals can be negated in patterns`` | none |
| NQ-TYPE-057 | non-literal constant initializer | the offending token | ``constant initializers may contain only literals and operators`` | ``compute the value in a function, or repeat the literal`` |
| NQ-TYPE-058 | non-name callee | the callee's first token | ``only named functions can be called`` | none |
| NQ-TYPE-059 | nested field assignment | the assignment target's first token | ``nested field assignment is not supported`` | ``pass `mutref <outer>.<field>` to a function that assigns the inner field`` |
| NQ-TYPE-042 (code kept) | field assignment root that is neither a `let mut` local nor a `mutref` parameter | the root name token (unchanged) | ``field assignment requires a `let mut` local or a `mutref` parameter`` (was "requires an owned mutable local product binding") | none (unchanged) |
| NQ-PROPAGATE-007 | `?` outside statement/`try` position | the `?` | ``` `?` is only allowed at statement position or inside `try` ``` | ``bind the result first: `let value = f()?;` `` |
| NQ-RESOLVE-010 (code kept) | unknown constructor in a pattern | the constructor name | ``unknown variant `<name>` in pattern`` | none |
| NQ-PARSE-003 | expected `;` | end of the statement's last token | ``expected `;` `` | none |
| NQ-PARSE-004 (code kept) | malformed float literal, now also `.5`, `1.`, `1e5` | the literal | existing text | ``write floats as `<digits>.<digits>`, for example `0.5`, `1.0` or `1.0e5` `` |
| NQ-IO-001 (code and text kept) | missing/stale workspace lock | file-level, file = manifest path | existing text | none (unchanged) |
| NQ-C-001 | backstop: fall-off reached C emission | function name | ``internal compiler error: function can fall off the end`` | none |
| let-else code (kept) | let-else `else` block that does not exit | existing span | ``let-else `else` block must exit with `return`, `break` or `continue` `` | none |

Exact strings are fixed in the tests.

## Evidence Impact

No evidence schema changes. Programs that M58.1 now rejects produce no
evidence (they fail `check`). For accepted programs, facts/review output is
unchanged except where a previously miscompiled initializer now resolves to
the outer binding (its call and mutation evidence then names the correct
binding).

## Migration

**Accepted at `4d80e70`, rejected after M58.1:**

- functions that can fall off the end, including `unit` functions without a
  final `return;`;
- a statement `match` on a `bool`, `str` or other unsupported scrutinee
  (NQ-TYPE-054); a zero-arm statement `match` on a non-empty domain;
- `let x = x;` with no outer `x` (previously read the new zero value).

**Changes meaning:** `let x = x ...` initializers in an inner scope now read
the outer binding (the miscompile this milestone fixes); call, borrow and
move evidence for such programs then names the outer binding.

**Newly accepted:** let-else `else` blocks ending in `break` or `continue`;
`try { f()? + g()? }` with per-operand propagation.

**Driver behaviour change:** `build -o <exe>` writes its C file beside the
executable (`<exe>.c`) instead of `<srcdir>/build/`.

**Diagnostic-only evidence changes (no program changes acceptance):**

- the rule-4 constructs already failed `check` with a stage1-limitation
  diagnostic; they now fail with focused codes;
- parse errors are reported once, and load/parse errors no longer cascade;
- NQ-TYPE-051's message is renamed (code kept) and now also covers
  expression matches, replacing NQ-TYPE-042 "match expression must be
  exhaustive";
- the field-assignment root message is corrected (code NQ-TYPE-042 kept);
- text-format diagnostics now print `help:` and `note:` lines (JSON is
  unchanged);
- the workspace-lock NQ-IO-001 keeps its code and text but reports the
  manifest path with a file-level span.

**Compiler and fixture migration (budgeted now).** A read-only scan at Gate A
found about 23 `unit` functions in the compiler's own source that fall
through without `return;` (for example `generic_evidence_string_array` and
neighbours in `selfhost/facts.nq`, `proof_artifact_forget` in
`selfhost/proof_artifacts.nq`) and about 3 fixtures (for example
`tests/fixtures/m56_generics/values.nq`). The milestone adds `return;` to
each; the old seed accepts that form, so no seed promotion is needed. All 43
`while true` loops in the compiler have no `break`, so the termination rule
accepts them unchanged. Acceptance includes an exact scan, using the new
check itself, that the compiler, examples and every positive fixture are
clean, with the migrated list recorded in the evidence. Compatibility
fixtures show each rejected class at the base and after. The tutorial site's
snippets are updated by its maintainer after the push.

## Write Set And Audit Classification

- `selfhost/`: `ast.nq` (`visible_from`), `lexer.nq`, `parser.nq`, `resolve.nq`, `typecheck.nq`,
  `handoff.nq`, `borrow.nq`, `ir.nq`, `c_emit.nq`, `diag.nq`, `main.nq`,
  `workspace.nq` if the lock diagnostic lives there; tests in existing test
  modules.
- Tests: `tests/fixtures/m58_1/**`, golden updates where text diagnostics now
  print help lines, corpus entry for a teaching example of let-else exits and
  `while true` termination.
- Docs: SPEC, GRAMMAR, DEFERRED, TEACHING_CORPUS, DECISIONS D070, the stale
  Python test expectations, ROADMAP/TODO status lines after the gate.
- No new `.nq` module, no seed promotion unless the compiler's own source
  needs a form the seed rejects (it should not: every change rejects or
  repairs). **Ownership-class milestone:** initializer scope changes which
  checked binding a move or borrow names, so the trailing audit is a
  `gpt-5.6-sol` xhigh primary plus an independent `gpt-6.1-sol` xhigh
  adversarial auditor, each reaching its own verdict first.
- `docs/M58_1_PRODUCER_LEDGER.md` and its checking test.

## Tests And Acceptance

- Every-path-returns: positive and negative cases for each terminating form
  (`if`/`else` nested inside `else` blocks, `match` arms, `while true` with
  and without a same-loop `break`, a `break` inside a nested `while` and a
  nested `for`, `while (true)` not counting, `return` followed by unreachable
  statements, `unit` functions, `main`); the C backstop via an IR-level
  emitter test.
- Initializer scope: `let mut x = x + 1;` shadowing in inner scopes (plain,
  typed, propagation and `try` locals), executed with exact output; `let x =
  x;` with no outer `x` rejected; a `for` iterable that names a variable
  shadowed by the loop binding; the M57.1 width-shadow fixtures still pass;
  facts and review v1-v5 for a shadowing program name the correct binding,
  and byte-identical evidence for an unaffected accepted program.
- Exhaustiveness: both forms on every supported scrutinee type, including a
  generic enum instance's missing list; zero-arm statement cases (empty enum
  accepted, others rejected) and zero-arm expression cases (existing
  diagnostic); `f64` keeps NQ-TYPE-047; other unsupported scrutinee types
  give NQ-TYPE-054; exact missing lists; the old expression-exhaustiveness
  message no longer appears anywhere.
- Each rule-4 construct with its exact diagnostic; a repository scan that no
  production source string begins with any of the three legacy prefixes
  ("stage1 limitation", "stage1 ir error", "stage1 c error"); corpus and
  negative fixtures produce no diagnostic with a legacy prefix or "internal
  compiler error".
- Zero-arm `match` on `bool`, `str` and `f64` scrutinees, statement and
  expression forms: only the scrutinee diagnostic is reported.
- The legacy/default invocation stops after load/parse errors.
- let-else exits with `return`, `break`, `continue`, and a rejected
  fall-through.
- Diagnostics: one copy of each parse error; the load/parse stop for every
  command row in the table (including each side of `review-diff` and
  `change-report`); missing `;`; help and note lines in text output; the lock
  diagnostic's file and span; `try { f()? + g()? }` accepted and executed;
  `(f() + g())?` still rejected with its pinned diagnostic; nested field
  assignment reported once as NQ-TYPE-059; the corrected field-assignment
  root message.
- The producer ledger test.
- Driver: `run -o rel/exe` and `build -o rel/exe` from a different working
  directory, with the C file location asserted.
- Full corpus, self-build (the compiler compiles under every new rule), seed
  bootstrap, and the full milestone gate.

## Acceptance Gate

M58.1 is complete when all of the above pass in the single milestone gate,
both trailing audits have no open findings, SPEC and GRAMMAR describe the
shipped rules, DECISIONS records D070, and no production source contains any
of the three legacy prefixes.
