# Nauqtype Deferred Features

This file records current deliberate exclusions. Earlier milestone exclusions
that have since shipped are historical, not current limitations.

## Language Features

- User-defined generics
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
