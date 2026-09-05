# Nauqtype v0.1 Specification

## Status

This document defines the locked Nauqtype v0.1 surface. It is intentionally smaller than the tentative design. Anything not described here is out of scope unless listed as a future extension.

The frozen stage0 reference includes statement-form `while`. The active stage1 compiler owns later live-in-the-language extensions.

The live-in-the-language loop surface now includes statement-form `while`, list-only `for name in list_expr { ... }`, and minimal nearest-loop `break;` / `continue;`.

## Language Philosophy

Nauqtype is designed for AI-authored code under human supervision.

Its source language priorities are:

- predictable structure
- explicit behavior
- visible mutation
- visible fallibility
- visible ownership-sensitive operations
- low syntax ambiguity
- strong compile-time checking
- readable generated code and diagnostics

## Source Files And Modules

- File extension: `.nq`
- One source file is one module.
- In legacy flat-root mode, the module name is derived from the file name and
  `use foo;` resolves to `<workspace-root>/foo.nq`.
- Manifest workspaces use one declared source root, nested `::` module paths,
  explicit module aliases, and locked local dependency roots as defined by
  `WORKSPACE_CONTRACT.md` and `WORKSPACE_LOCK.md`.
- All `use` declarations must appear before non-`use` items in a file.
- Imported `pub fn`, `pub type`, `pub enum`, and `pub const` enter the importing module scope unqualified.
- Imported public enum variants are also visible as constructor/pattern names.
- Import cycles are rejected.
- There is no registry/package manager, wildcard import, implicit re-export,
  hidden prelude, or ambient dependency search path in stage1.

## Naming And Style

These are style expectations, not parser rules:

- types and enum variants: `UpperCamel`
- functions, locals, fields, modules, constants: `snake_case`

This style is recommended because it improves human scanability and reduces type/value confusion.

## Keywords

Reserved keywords in v0.1:

- `and`
- `audit`
- `break`
- `const`
- `continue`
- `else`
- `enum`
- `false`
- `fn`
- `if`
- `let`
- `match`
- `mut`
- `mutref`
- `not`
- `or`
- `pub`
- `ref`
- `return`
- `true`
- `try`
- `type`
- `use`
- `while`

## Primitive Types

Current primitive types:

- `bool`
- `i32`
- `i64`
- `str`
- `unit`

Deferred numeric types:

- `u32`
- `u64`
- `f32`
- `f64`
- `char`

`i32` and `i64` are exact integer types. Unsuffixed literals default to `i32`
unless an expected `i64` context selects `i64`; arithmetic never performs an
implicit width conversion.

Addition, subtraction, multiplication, and unary negation wrap modulo the
operand width, interpreted as the corresponding signed two's-complement
value. Division truncates toward zero. Division by zero or the minimum value
divided by `-1` terminates with exit code 1 and, respectively,
`nauqtype runtime: integer division by zero` or
`nauqtype runtime: integer division overflow` on stderr. Fatal runtime failures
do not promise unwinding or cleanup.

Top-level constants use the same arithmetic. Evaluated invalid divisions are
rejected with `NQ-TYPE-045` at the slash token; boolean `and` and `or` still
short-circuit. Literal range checks remain independent of reachability. This
does not add casts or permit constant initializers to call functions or refer
to other names.

`str` is an immutable, length-carrying byte string. It is not guaranteed to be
valid UTF-8; length, indexing, and slicing use byte offsets. Runtime-owned
strings use reference counting so source-level copies remain safe while
generated code reclaims owned storage deterministically. OS-bound strings on
Linux preserve arbitrary non-NUL bytes and reject embedded NUL rather than
truncating at the C boundary.

String lengths, including views and imported OS text, are bounded by
`INT32_MAX`. List lengths and capacities are bounded by `INT32_MAX` and the
allocation-byte limit for their element type. Bytes are bounded by
`min(INT64_MAX, SIZE_MAX)`. Runtime allocation paths check size arithmetic
before allocation or growth. Infallible size/OOM failures terminate with exit
code 1 and `nauqtype runtime: size limit exceeded` or
`nauqtype runtime: out of memory`. Fallible IO reserve paths instead return an
allocation-free `io_err`: `invalid_input` with code/OS code 0 for a size limit,
or `other` with code/OS code `ENOMEM` for OOM. These errors preserve the
operation and omit path fields. See [M54_9_CONTRACTS.md](M54_9_CONTRACTS.md).

## Built-in Utility Types

- `option<T>`
- `result<T, E>`
- `list<T>`
- `io_err`
- `bytes`
- `process_result`
- `path_metadata`

Built-in constructors:

- `Some(value)`
- `None`
- `Ok(value)`
- `Err(value)`

These are part of the core language surface in the current bootstrap compiler.

`bytes` is owned and move-only. `path_metadata` is copyable and exposes
`is_file`, `is_directory`, `is_symlink`, `size: i64`, `modified_ns: i64`, and
`mode: i32`; on Linux, `mode` is `st_mode & 07777` and does not duplicate the
file-kind booleans. A filesystem timestamp outside the representable `i64`
nanosecond range makes `path_metadata` return `invalid_data`; it never wraps.

### Linux Authority Builtins

M54 adds narrow fallible boundaries for standard streams, environment/cwd,
binary files, metadata, directory traversal, creation, secure temporary
entries, removal, rename, and atomic replacement. These primitives expose OS
truth; UTF-8 policy, lexical path operations, sorting, and CLI composition
remain ordinary Nauqtype library work. Exact signatures and guarantees are
locked in [NQTYPE_LIBRARIES_UPSTREAM_RESPONSE.md](NQTYPE_LIBRARIES_UPSTREAM_RESPONSE.md).

All fallible authority builtins return `result<_, io_err>`. Structured error
accessors expose stable kind, operation, primary/secondary path, and OS code.
`atomic_write_file` promises same-directory atomic visibility through rename,
not crash durability or metadata preservation.

## Declarations

### Visibility

- Items are private by default.
- `pub` may prefix `fn`, `type`, `enum`, and `const`.

### Local Bindings

Immutable binding:

```nauq
let port: i32 = 8080;
```

Mutable binding:

```nauq
let mut count: i32 = 0;
```

Type annotation on locals is optional when the initializer is sufficient.

Narrow guard binding with `let-else`:

```nauq
let Some(value) = maybe else {
    return fallback;
};

let Ok(parsed) = result else {
    return fallback;
};
```

Rules:

- V1 supports only `Some(name)` for `option<T>` and `Ok(name)` for `result<T, E>`.
- The success pattern introduces the payload binding after the statement.
- The `else` block must exit explicitly, such as with `return`.
- Pattern guards, chained `if let`, and hidden propagation are not part of `let-else` V1. Statement-boundary `?` is a separate evidence-backed propagation feature.

### Local `try` Boundaries

M50 adds one visible expression-propagation boundary:

```nauq
let measured: result<i32, io_err> = try {
    str_len(read_file(path)?[read_source])
};
```

Rules:

- V1 permits `try { value_expr }` only as the direct initializer of an explicitly annotated `result<T, E>` local.
- The success expression must have type `T`; the boundary wraps it in `Ok(...)`.
- Each postfix `?` must apply to a direct function call returning `result<U, E>` with the exact same `E`.
- A failed site stores `Err(error)` in the local boundary and skips the remaining success expression; it does not return from the function.
- Sites are evaluated depth-first and left-to-right before the final success expression, making their order deterministic and visible in evidence.
- Local-boundary sites appear in facts v2 and review v2, but do not add to function-level inferred `propagates(...)` because the error does not leave the function.
- Short-circuit `and` / `or`, match success expressions, multi-statement bodies, implicit error conversion, and `option<T>?` are not supported in V1.
- Use `let-else` or `match` when mapping, logging, recovering, or otherwise handling an error explicitly.

### Top-Level Constants

Top-level constants are a stage1-owned live-in-the-language feature for small, named configuration values:

```nauq
pub const answer: i32 = 40 + 2;
const greeting: str = "Hello";
const enabled: bool = true and not false;
```

Rules:

- constants are private by default
- `pub const` is visible through flat-root `use`
- v1 constants support only non-borrow `i32`, `i64`, `bool`, and `str`
- v1 initializers support literals, parentheses, unary `-` / `not`, arithmetic and integer comparison operators, and boolean `and` / `or`
- calls, constructors, lists, borrows, I/O, and const-to-const initializer references are intentionally rejected for now
- constants can be referenced in function bodies as values, but cannot be called, borrowed, or assigned

### Functions

Function syntax:

```nauq
pub fn add(a: i32, b: i32) -> i32 {
    return a + b;
}
```

Functions may also carry an optional AI Contracts block before the body:

```nauq
pub fn bump(value: mutref i32) -> unit
audit {
    intent("Increment a counter in place");
    mutates(value);
    effects();
}
{
    value = value + 1;
    return;
}
```

Rules:

- parameter types are required
- return types are required
- `return` is the only return form
- there is no implicit last-expression return
- `return;` is allowed only in functions returning `unit`
- `audit` blocks are optional in the AI Contracts alpha
- `pub fn` without `audit` emits a warning in the current compiler

### AI Contracts

An `audit` block is a fixed-shape, compiler-checked review surface for a function.

Rules:

- clause order is fixed: `intent`, then `mutates`, then `effects`, then optional `propagates`
- `intent("...")` is required and must be non-empty
- `mutates(...)` may list only `mutref` parameters
- `effects(...)` currently supports the fixed atoms `print` and `io`
- `propagates(...)` may list exact error types forwarded unchanged by statement-boundary `?`
- `mutates(...)` is checked against direct write-through assignments to `mutref` parameters
- `effects(print)` is checked against direct or transitive use of `print_line` / `eprint_line`
- `effects(io)` is checked against direct or transitive use of authority-bearing builtins; facts v2 and review v2 report the fixed checked subkinds `read`, `write`, `create_dir`, `process`, `arguments`, `environment`, `cwd`, `stdin`, `stdout`, `stderr`, `metadata`, `traversal`, `create_file`, `temporary`, `remove`, `rename`, and `atomic_replace` without widening source-level effect syntax
- `propagates(E)` is checked against direct `let name = result_expr?;` propagation sites in the function
- duplicate clause entries are rejected
- user-defined effect atoms, typed repair obligations, and stronger contract inference are deferred

### Product Types

```nauq
pub type User {
    name: str,
    age: i32,
}
```

Rules:

- fields are named
- field order is declared order
- field types are required
- no methods in v0.1
- direct field assignment is allowed only through an owned `let mut` local product binding

### Enums

```nauq
pub enum ParseErr {
    BadDigit,
    Overflow,
    MissingField(str),
}
```

Rules:

- enum variants are nominal
- a variant may be unit-like or tuple-like
- struct-like enum variants are deferred

## Expressions

Supported expression forms in v0.1:

- literals: integer, string, `true`, `false`
- variable and top-level constant references
- constructor references such as `Ok(value)` or `User { ... }`
- list literals: `[]` and `[a, b, c]`
- function calls
- direct module-qualified function and data names
- field access
- copy-only record update with `Type { from base, field: value }`
- match expressions
- unary operators: `-`, `not`
- binary operators

### Struct Literals

```nauq
let user = User {
    name: "Perry",
    age: 32,
};
```

### List Literals

```nauq
let empty: list<i32> = [];
let values = [1, 2, 3];
```

Rules:

- `[]` requires an expected `list<T>` context, such as a local annotation, return type, parameter type, or constructor payload type.
- Non-empty literals infer `list<T>` from their first element when no expected list type is available.
- All elements must have the same type.
- Spreads, comprehensions, ranges, and const list initializers are deferred.

### Function Calls

```nauq
let sum = add(1, 2);
let labeled = add(right: 2, left: 1);
let imported = math::add(left: 1, right: 2);
```

Batch B rules:

- Named arguments use `name: value` and apply only to function calls.
- A call is either all positional or all named.
- Named arguments may appear in any source order, but are matched, evaluated, borrow-checked, lowered, and emitted in callee parameter order.
- Labels must match declared parameter names exactly; missing, duplicate, and unknown labels are rejected.
- Defaults, overloading, mixed positional/named calls, and named enum constructor payloads are not supported.
- `module::function(...)` calls a public function from a directly imported flat-root module.
- Qualified calls are not member calls, methods, package paths, constructors, or qualified type syntax.

### Borrow Expressions

Borrow expressions are explicit:

```nauq
let size = length(ref text);
append(mutref buffer, item);
```

Rules:

- `ref expr` and `mutref expr` are only legal as direct call arguments in v0.1
- borrow expressions must name a mutable-capable place when `mutref` is used
- borrow values cannot be stored in locals, fields, or return values
- inside a callee, `ref T` and `mutref T` parameters act as alias parameters; reading the parameter reads the referent, and assigning to a `mutref` parameter writes the referent

## Statements

Supported statements:

- local binding, including an explicitly typed local `try` boundary
- statement-boundary propagation binding: `let name = result_expr?;`
- `let-else` guard binding for `option` / `result` success patterns
- assignment to a mutable local
- direct field assignment through an owned mutable local product binding
- `if`
- `while`
- `match`
- `return`
- `break` and `continue` inside `while`
- expression statement

### Assignment

```nauq
let mut count = 0;
count = count + 1;
```

Rules:

- only mutable locals may be assigned
- `binding.field = value;` requires `binding` to be a direct, owned `let mut` local of a user-defined product type
- field assignment rejects `mutref` parameters, enum values, list elements, nested field paths, and arbitrary assignment targets
- assigning to a `mutref` parameter writes through the borrow

### If

```nauq
if count > 0 {
    print_line("positive");
} else {
    print_line("zero");
}
```

Rules:

- condition type must be `bool`
- there is no truthy/falsy coercion

### While

```nauq
while count < limit {
    count = count + 1;
}
```

Rules:

- `while` is a statement, not an expression
- condition type must be `bool`
- loop bodies are explicit blocks
- Batch B adds only `break;` and `continue;` for the nearest enclosing `while`
- `break;` and `continue;` are valid inside nested `if`, `match`, or `let-else` only when the nested construct is inside a `while`
- loop exits have no value, no labels, and do not make `while` an expression
- loop move checking is conservative across iterations; if a non-copy value may be moved on one iteration and reused on a later one, the compiler rejects the loop

### Match

```nauq
match value {
    Ok(n) => {
        return n;
    },
    Err(_) => {
        return 0;
    },
}
```

Rules:

- each arm body is a block
- arm patterns are matched top to bottom
- a `match` must be exhaustive for its scrutinee type
- statement `match` arms do not produce values

### Match Expressions

```nauq
let value = match maybe {
    Some(n) => n + 1,
    None => 0,
};
```

Rules:

- expression arms use `pattern => expr`, separated by commas
- all arm result types must agree exactly
- the scrutinee must be `i32`, `option<T>`, `result<T, E>`, or a user enum
- match expression arms do not fall through; V1 requires either a wildcard/binding fallback arm or coverage of every visible variant for the scrutinee type
- block expressions, implicit final-expression returns, and fallthrough are not supported

## Patterns

Supported pattern forms:

- wildcard: `_`
- binding: `name`
- unit-like variant: `None`
- tuple-like variant: `Some(value)`
- integer literal: `42` or `-1`, for `i32` scrutinees only
- nested constructor: `Some(Some(value))`

Any match containing a literal or nested constructor pattern must include a wildcard or binding fallback arm. This keeps the first refined-pattern form conservative and exhaustiveness visible. Guards, ranges, string or boolean literals, and or-patterns remain deferred.

## Operators

### Precedence

From lowest to highest:

1. `or`
2. `and`
3. `==`, `!=`
4. `<`, `<=`, `>`, `>=`
5. `+`, `-`
6. `*`, `/`
7. unary `-`, `not`
8. call and field access

### Rules

- binary operators require explicitly compatible operand types
- there are no implicit numeric promotions in v0.1

## Type Rules

### General

- variables have one static type
- function calls must match parameter types exactly
- return expressions must match the declared return type
- `if` conditions must be `bool`
- `while` conditions must be `bool`
- there are no implicit conversions

### Copy vs Move

Copy types in v0.1:

- `bool`
- `i32`
- `i64`
- `str`
- `unit`
- `io_err`
- `process_result`
- any user-defined `type` or `enum` whose fields/payloads are all copy

Move types in v0.1:

- `list<T>`
- `bytes`
- `option<T>` when `T` is non-copy
- `result<T, E>` when either side is non-copy

Rules:

- using a moved non-copy value is a compile error
- passing a non-copy value to an owning parameter moves it
- assigning a non-copy value into a new binding moves it
- every checked type carries canonical `is_copy` and `needs_drop` properties
- every checked expression carries a read/copy/move/borrow use decision before IR lowering
- generated C deterministically drops owned locals, parameters, aggregates, and temporaries on replacement and every normal control-flow exit

## Ownership And Borrowing

Nauqtype v0.1 has a minimal but real ownership model.

Rules:

- non-copy values move by default
- moved values cannot be reused
- shared borrows use `ref`
- mutable borrows use `mutref`
- mutable borrows require the source binding to be mutable
- `mutref` cannot coexist with any other borrow of the same place in the same call
- consuming a non-copy pointee through a borrowed binding is rejected; copy values may be read from a borrow and are copied according to their checked value plan
- bootstrap `while` analysis tracks possible moves across iterations conservatively
- no stored references
- read-only `ref binding.field` paths are supported for direct call arguments,
  including the shipped runtime product fields; `mutref` still targets a
  binding rather than a field
- borrow-prefixed arithmetic is not a place and is rejected, not silently
  lowered as pointer arithmetic

This is intentionally stricter than a future version. The goal is safety and implementability, not maximum flexibility.

## Error Handling

Rules:

- fallible operations return `result<T, E>`
- absent values use `option<T>`
- errors are handled explicitly with `match`, the narrow `let Ok(value) = result else { return ...; };` guard form, or a visible local `try` boundary
- unchanged `result<T, E>` errors may be forwarded with statement-boundary `let value = result_expr?;` when the enclosing function returns `result<_, E>` and declares `propagates(E)`
- `?` performs no implicit error conversion; use `let-else` or `match` when mapping one error type into another
- there are no exceptions
- function-scoped expression `?`, multi-statement `try` blocks, `option<T>?`, implicit error conversion, and custom propagation protocols are not supported

Example:

```nauq
fn parse_flag(text: str) -> result<bool, str> {
    if text == "yes" {
        return Ok(true);
    } else {
        return Err("expected yes");
    }
}
```

## Standard Library Boundary

### In Scope

- `str`
- `option<T>`
- `result<T, E>`
- `list<T>`
- `io_err`
- `bytes`
- `process_result`
- minimal printing intrinsic:

```nauq
fn print_line(text: str) -> unit;
```

- bootstrap file/string helpers:

```nauq
fn read_file(path: str) -> result<str, io_err>;
fn write_file(path: str, text: str) -> result<unit, io_err>;
fn io_err_text(err: io_err) -> str;
fn str_len(text: str) -> i32;
fn str_concat(left: str, right: str) -> str;
fn str_get(text: str, index: i32) -> option<i32>;
fn str_slice(text: str, start: i32, end: i32) -> option<str>;
fn list() -> list<T>;            // requires expected context
fn list_push(items: mutref list<T>, value: T) -> unit;
fn list_len(items: ref list<T>) -> i32;
fn list_get(items: ref list<T>, index: i32) -> option<T>;
fn bytes_from_str(text: str) -> bytes;
fn bytes_len(value: ref bytes) -> i64;
fn bytes_get(value: ref bytes, index: i64) -> option<i32>;
```

`[]` is the literal equivalent of an empty `list<T>` and follows the same expected-context rule as `list()`.

The active compiler driver also uses a deliberately narrow tooling runtime
surface for arguments, directory creation, and captured process execution.
Those builtins are toolchain-enabling authority, not a general OS API.

### Out Of Scope For The Current Surface

- formatting machinery
- mutable strings
- broad environment/process APIs beyond the narrow checked tooling surface

## Entry Point

The executable entry point is:

```nauq
fn main() -> i32
```

The compiler may later accept `-> unit`, but v0.1 keeps the C mapping simple by requiring `i32`.

## Diagnostics Model

Every diagnostic should contain:

- code
- category
- message
- primary span
- optional note list
- optional help hint

Diagnostics should be stable enough for snapshot testing and future editor integration.

The compiler also supports:

```text
nauqc review <file>
```

`review` emits deterministic JSON summarizing each function's declared `audit` data and compiler-inferred mutation/effect facts.

## Initial Lints

Planned v0.1 lints:

- `unused_mut`
- discarded `result` value
- public function missing `audit`
- overdeclared `mutates(...)`
- overdeclared `effects(print)` / `effects(io)`

These are warnings, not hard errors.

## Explicit v0.1 Omissions

- methods
- traits
- loop families beyond bootstrap `while` and list-only `for`
- labeled or valued `break` / `continue`
- user-defined generics
- broader constant expressions beyond the v1 pure literal/operator subset
- exceptions
- async
- macros
- operator overloading
- advanced lifetimes
