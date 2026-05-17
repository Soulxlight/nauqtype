# Nauqtype Deferred Features

This file records features intentionally excluded from v0.1 so that omissions are deliberate rather than forgotten.

## Language Features

- User-defined generics
- Methods and `impl` blocks
- Traits or interfaces
- Loop families beyond bootstrap `while`
- labeled or valued `break` / `continue`
- Field assignment
- Stored references
- Reference returns
- Literal patterns
- Nested constructor patterns
- Struct-like enum variants
- Broad propagation sugar beyond statement-boundary evidence-backed `?`
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
- Time / randomness APIs
- Process and environment APIs

The current stage1 driver has a deliberately narrow toolchain-only runtime surface for arguments, directory creation, and subprocess execution. Broad process/environment APIs remain deferred.

## Compiler / Tooling

- REPL
- Interpreter mode
- Bytecode backend
- LLVM backend
- Optimizer pipeline
- Full AST-preserving formatter and formatter write mode
- Language server
- Package manager

Near-term language ergonomics resume only as explicit language milestones with examples and differential or stage1-owned coverage. Top-level `const`, list literals, match expressions, let-else, formatter-lite, named function arguments, direct module-qualified function calls, direct module-qualified data names, copy-only record update, and minimal nearest-`while` `break` / `continue` have now graduated from this deferred list in deliberately narrow first forms.

The shipped `?` path is intentionally narrow rather than Rustlike: statement-boundary `let name = result_expr?;`, exact error-type propagation, explicit `propagates(...)` audit evidence, and versioned facts/review/change-report output. Expression-position `?`, `option<T>?`, `try` blocks, implicit conversions, and custom propagation protocols remain deferred.

## Why These Are Deferred

- They are not required for a real v0.1 vertical slice.
- Several would materially increase parser, type checker, or ownership complexity.
- The project should first prove the core pipeline: source -> checked IR -> C -> executable.
- Stage1 already activates the minimum bootstrap-critical additions: flat-root imports, `read_file`, `write_file`, bootstrap string helpers, and builtin `list<T>`.
