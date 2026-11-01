# Nauqtype Deferred Features

This file records current deliberate exclusions. Earlier milestone exclusions
that have since shipped are historical, not current limitations.

## Language Features

- Generic inference/defaults/constraints, generic constants, higher-kinded
  parameters, and generic-aware `review-diff`/`change-report`/`policy-check`/
  refactor exports. M56's explicit function/product/enum foundation is
  specified in `docs/M56_CONTRACT.md`; generic-aware `facts`/`review` v5 are
  specified in `docs/M56_1_CONTRACT.md`.
- Numeric types beyond `i32`/`i64`/`f64`: `f32`, unsigned integers, and
  `char` remain deferred (their names are reserved, `NQ-TYPE-049`). Scalar
  `f64` shipped in M56.2 (`docs/M56_2_CONTRACT.md`) without float literal
  patterns, compile-time float folding, total-order comparison, math functions
  (`sqrt`, `floor`, `pow`, ...), or fixed-precision rendering (`1.50`); the
  math functions and fixed-precision rendering belong to M57+ standard-library
  planning.
- M57.1 deliberate exclusions (`docs/M57_1_CONTRACT.md`): recursive data
  layouts through containers (`type Json { items: list<Json> }` is
  `NQ-TYPE-052`; M57 uses arena indexes); field-disjoint borrow checking
  (`f(mutref b.a, ref b.b)` is still one conflicting root); moving fields out
  of owned products (destructuring); the `%` operator (M58.2) and bitwise
  operators; and comparisons of `bool`, `str` or enums inside `const`
  initializers (constant comparisons stay integer-only). Missing-return
  analysis shipped in M58.1.
- M58.1 deliberate exclusions (`docs/M58_1_CONTRACT.md`): unreachable-code
  diagnostics after a terminating statement; splitting the shared
  `NQ-TYPE-042` code into per-message codes; loop conditions other than the
  exact token `true` (such as `(true)`) counting toward termination; `bool`
  and string patterns (`bool` and `str` patterns arrive in M58.3); nested field
  assignment (`o.inner.value = v`, `NQ-TYPE-059`); expression-position `?`
  outside `try`.
- Lints without a producer: `unused_mut` and discarded `result` values. SPEC
  lists only lints the compiler reports.
- Methods and `impl` blocks
- Traits or interfaces
- Loop families beyond `while` and list-only `for`, including iterator protocols
- labeled or valued `break` / `continue`
- Stored references
- Reference returns
- Struct-like enum variants
- Broad propagation sugar beyond statement-boundary `?` and explicit local `try` boundaries
- Richer or user-defined `effects(...)` atoms beyond fixed compiler atoms
- Typed holes / repair obligations
- Error or result contracts beyond `propagates(...)` propagation evidence
- Macros
- Async / await
- Operator overloading
- Implicit conversions
- Exceptions
- Reflection
- Inheritance

## Standard Library

- Collections beyond builtin `list<T>`, such as `map` and `set`
- Formatting machinery beyond formatter-lite
- Mutable strings
- Networking
- Randomness/entropy APIs and general calendar/timezone facilities
- Background process pumping, async scheduling, and task/executor APIs

M54 provides checked arguments, environment lookup, cwd, streams, and
filesystem authority as narrow builtins. Reusable UTF-8, lexical-path, sorting,
and CLI composition remain library-owned. M55 implements structured owned
process control and nominal time/deadlines under `M55_CONTRACTS.md`; acceptance
status remains in `ROADMAP.md`. These clocks are not entropy sources.

Focused M55 authoring exposed existing boundaries, not new supported forms:
nested constructor patterns in `let-else` still require separate bindings;
repeating `let Ok(_)` in one scope is diagnosed as a duplicate binding. Use
distinct explicit payload names pending a separately scoped wildcard fix.

## Compiler / Tooling

- REPL
- Interpreter mode
- Bytecode backend
- LLVM backend
- Optimizer pipeline
- Full AST-preserving formatter and formatter write mode
- Language server
- Package manager

Near-term language ergonomics resume only after the corrective prerequisites in
[AUDIT_REMEDIATION.md](AUDIT_REMEDIATION.md), as explicit language milestones
with stage1-owned coverage. Top-level `const`, list literals, match expressions,
let-else, formatter-lite, named arguments, qualified function/data names,
copy-only record update, owned-local field assignment, nested patterns,
manifest-governed nested modules, list-only `for`, and nearest-loop
`break`/`continue` have already shipped in deliberately narrow forms.

The shipped `?` path is intentionally narrow rather than Rustlike: statement-boundary `let name = result_expr?;` forwards exact errors with explicit `propagates(...)`, while an annotated local `try { expression }` captures expression-position propagation without returning from the function. Both forms emit versioned evidence. Function-scoped expression `?`, multi-statement `try`, short-circuit/match propagation inside a boundary, `option<T>?`, implicit conversions, and custom propagation protocols remain deferred.

## Why These Are Deferred

- They require demonstrated pressure from Linux tools or applications.
- Several would materially increase parser, type checker, or ownership complexity.
- The existing source -> checked IR -> C -> executable path must remain
  trustworthy while correcting the independently audited gaps.
- Stage1 already self-builds and runs workspace projects with narrow Linux
  input/filesystem authority. Those capabilities do not imply a package
  manager, broad OS APIs, or complete numeric/resource contracts.
