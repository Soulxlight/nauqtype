# Nauqtype Deferred Features

This file records features intentionally excluded from v0.1 so that omissions are deliberate rather than forgotten.

## Language Features

- Cross-file imports and package resolution
- User-defined generics
- Methods and `impl` blocks
- Traits or interfaces
- Loops
- Field assignment
- Stored references
- Reference returns
- Literal patterns
- Nested constructor patterns
- Struct-like enum variants
- Propagation sugar such as `?`
- Macros
- Async / await
- Operator overloading
- Implicit conversions
- Exceptions
- Reflection
- Inheritance

## Standard Library

- File I/O
- Collections like `list`, `map`, and `set`
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
