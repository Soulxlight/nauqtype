# Nauqtype v0.1 Specification

## Status

This document defines the locked Nauqtype v0.1 surface. It is intentionally smaller than the tentative design. Anything not described here is out of scope unless listed as a future extension.

One controlled bootstrap-track extension is implemented in the current stage0 compiler: statement-form `while` loops. This does not widen v0.1 to broader loop families.

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
- The module name is derived from the file name.
- `use foo;` resolves to `<workspace-root>/foo.nq`.
- All `use` declarations must appear before non-`use` items in a file.
- Imported `pub fn`, `pub type`, and `pub enum` enter the importing module scope unqualified.
- Imported public enum variants are also visible as constructor/pattern names.
- Import cycles are rejected.
- There is no package manager, nested module system, or re-export system in stage1.

## Naming And Style

These are style expectations, not parser rules:

- types and enum variants: `UpperCamel`
- functions, locals, fields, modules: `snake_case`
- constants: future work

This style is recommended because it improves human scanability and reduces type/value confusion.

## Keywords

Reserved keywords in v0.1:

- `and`
- `audit`
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
- `type`
- `use`
- `while`

## Primitive Types

Locked v0.1 primitive types:

- `bool`
- `i32`
- `str`
- `unit`

Deferred numeric types:

- `i64`
- `u32`
- `u64`
- `f32`
- `f64`
- `char`

`str` is an immutable runtime string view in v0.1.

## Built-in Utility Types

- `option<T>`
- `result<T, E>`
- `list<T>`
- `io_err`

Built-in constructors:

- `Some(value)`
- `None`
- `Ok(value)`
- `Err(value)`

These are part of the core language surface in the current bootstrap compiler.

## Declarations

### Visibility

- Items are private by default.
- `pub` may prefix `fn`, `type`, and `enum`.

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

- clause order is fixed: `intent`, then `mutates`, then `effects`
- `intent("...")` is required and must be non-empty
- `mutates(...)` may list only `mutref` parameters
- `effects(...)` currently supports only `print`
- `mutates(...)` is checked against direct write-through assignments to `mutref` parameters
- `effects(print)` is checked against direct or transitive use of `print_line` in the same source file
- duplicate clause entries are rejected
- richer effect atoms, typed repair obligations, and stronger contract inference are deferred

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
- no field assignment in v0.1

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
- variable references
- constructor references such as `Ok(value)` or `User { ... }`
- function calls
- field access
- unary operators: `-`, `not`
- binary operators

### Struct Literals

```nauq
let user = User {
    name: "Perry",
    age: 32,
};
```

### Function Calls

```nauq
let sum = add(1, 2);
```

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

- local binding
- assignment to a mutable local
- `if`
- `while`
- `match`
- `return`
- expression statement

### Assignment

```nauq
let mut count = 0;
count = count + 1;
```

Rules:

- only mutable locals may be assigned
- field assignment is deferred
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
- `break` and `continue` are not part of the bootstrap surface
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

## Patterns

Supported pattern forms:

- wildcard: `_`
- binding: `name`
- unit-like variant: `None`
- tuple-like variant: `Some(value)`

Deferred pattern forms in v0.1:

- nested constructor patterns
- literal patterns

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
- `str`
- `unit`
- `io_err`
- any user-defined `type` or `enum` whose fields/payloads are all copy

Move types in v0.1:

- `list<T>`
- `option<T>` when `T` is non-copy
- `result<T, E>` when either side is non-copy

Rules:

- using a moved non-copy value is a compile error
- passing a non-copy value to an owning parameter moves it
- assigning a non-copy value into a new binding moves it

## Ownership And Borrowing

Nauqtype v0.1 has a minimal but real ownership model.

Rules:

- non-copy values move by default
- moved values cannot be reused
- shared borrows use `ref`
- mutable borrows use `mutref`
- mutable borrows require the source binding to be mutable
- `mutref` cannot coexist with any other borrow of the same place in the same call
- bootstrap `while` analysis tracks possible moves across iterations conservatively
- no stored references
- no field borrows

This is intentionally stricter than a future version. The goal is safety and implementability, not maximum flexibility.

## Error Handling

Rules:

- fallible operations return `result<T, E>`
- absent values use `option<T>`
- errors are handled explicitly with `match`
- there are no exceptions
- there is no `?` operator in v0.1

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
```

### Out Of Scope For v0.1

- formatting machinery
- mutable strings
- environment/process APIs

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
- overdeclared `effects(print)`

These are warnings, not hard errors.

## Explicit v0.1 Omissions

- methods
- traits
- loop families beyond bootstrap `while`
- `break`
- `continue`
- field assignment
- user-defined generics
- exceptions
- async
- macros
- operator overloading
- advanced lifetimes
