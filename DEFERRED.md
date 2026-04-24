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
- Formatting machinery
- Mutable strings
- Networking
- Time / randomness APIs
- Process and environment APIs

## Compiler / Tooling

- REPL
- Interpreter mode
- Bytecode backend
- LLVM backend
- Optimizer pipeline
- Formatter
- Language server
- Package manager

## Why These Are Deferred

- They are not required for a real v0.1 vertical slice.
- Several would materially increase parser, type checker, or ownership complexity.
- The project should first prove the core pipeline: source -> checked IR -> C -> executable.
- Stage1 already activates the minimum bootstrap-critical additions: flat-root imports, `read_file`, `write_file`, bootstrap string helpers, and builtin `list<T>`.
