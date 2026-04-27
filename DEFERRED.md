# Nauqtype Deferred Features

This file records features intentionally excluded from v0.1 so that omissions are deliberate rather than forgotten.

## Language Features

- User-defined generics
- Methods and `impl` blocks
- Traits or interfaces
- Loop families beyond bootstrap `while`
- `break`
- `continue`
- Field assignment
- Stored references
- Reference returns
- Literal patterns
- Nested constructor patterns
- Struct-like enum variants
- Propagation sugar such as `?`
- Richer `effects(...)` atoms beyond `print`
- Typed holes / repair obligations
- Error or result contracts beyond `effects(...)`
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

Near-term language ergonomics resume only as explicit language milestones with examples and differential or stage1-owned coverage. Top-level `const`, list literals, match expressions, let-else, and formatter-lite have now graduated from this deferred list in deliberately narrow first forms. Minimal `break` / `continue` stay deferred until the Batch B design checkpoint records their exact control-flow rules.

## Why These Are Deferred

- They are not required for a real v0.1 vertical slice.
- Several would materially increase parser, type checker, or ownership complexity.
- The project should first prove the core pipeline: source -> checked IR -> C -> executable.
- Stage1 already activates the minimum bootstrap-critical additions: flat-root imports, `read_file`, `write_file`, bootstrap string helpers, and builtin `list<T>`.
