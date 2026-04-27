# Nauqtype v0.1 Specification

## Status

This document defines the locked Nauqtype v0.1 surface. It is intentionally smaller than the tentative design. Anything not described here is out of scope unless listed as a future extension.

One controlled bootstrap-track extension is implemented in the current stage0 compiler: statement-form `while` loops. This does not widen v0.1 to broader loop families.

The live-in-the-language Batch B surface is now implemented in narrow form: named function arguments, direct module-qualified function calls, and minimal `break;` / `continue;` for `while`.

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
- Imported `pub fn`, `pub type`, `pub enum`, and `pub const` enter the importing module scope unqualified.
- Imported public enum variants are also visible as constructor/pattern names.
- Import cycles are rejected.
- There is no package manager, nested module system, or re-export system in stage1.

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
- Pattern guards, chained `if let`, hidden propagation, and `?` are not part of V1.

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
- v1 constants support only non-borrow `i32`, `bool`, and `str`
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
- variable and top-level constant references
- constructor references such as `Ok(value)` or `User { ... }`
- list literals: `[]` and `[a, b, c]`
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
- the scrutinee must be `option<T>`, `result<T, E>`, or a user enum
- match expression arms do not fall through; V1 requires either a wildcard/binding fallback arm or coverage of every visible variant for the scrutinee type
- block expressions, implicit final-expression returns, and fallthrough are not supported

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
- errors are handled explicitly with `match` or the narrow `let Ok(value) = result else { return ...; };` guard form
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

`[]` is the literal equivalent of an empty `list<T>` and follows the same expected-context rule as `list()`.

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
- labeled or valued `break` / `continue`
- field assignment
- user-defined generics
- broader constant expressions beyond the v1 pure literal/operator subset
- exceptions
- async
- macros
- operator overloading
- advanced lifetimes
