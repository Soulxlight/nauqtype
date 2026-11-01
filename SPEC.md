# Nauqtype v0.1 Specification

## Status

This document defines the locked Nauqtype v0.1 surface. It is intentionally smaller than the tentative design. Anything not described here is out of scope unless listed as a future extension.

The frozen stage0 reference includes statement-form `while`. The active stage1 compiler owns later live-in-the-language extensions.

The live-in-the-language loop surface now includes statement-form `while`, list-only `for name in list_expr { ... }`, and minimal nearest-loop `break;` / `continue;`.

The M56 active-stage1 candidate extends this historical surface with explicit
function/product/enum generics. Its exact contract is
`docs/M56_CONTRACT.md`; current acceptance is recorded in ROADMAP/TODO, not
implied by this specification. No source-generics support is added to the
archived Python bootstrap.

## Explicit Generic Reuse

Declare ordered distinct type parameters with `fn identity<T>(value: T) -> T`,
`type Parcel<T> { value: T, }`, or `enum Choice<T, E> { Value(T), Failure(E), }`.
Every use supplies the complete argument vector: `identity::<i32>(7)`,
`Parcel<i32>` in annotations, `Parcel::<i32> { value: 7 }` in values, and
`Value::<i32, str>(7)` in constructor calls and patterns. Zero-payload variants
use `Empty::<i32>` without parentheses. Direct imported aliases still identify
the declaration origin; `alias::Tag` is allowed inside explicit type arguments,
not as a new general qualified annotation head.

Type parameters are not values. No defaults, inference, traits, methods,
constraints, generic constants or coercions are introduced. Borrow arguments
remain explicit (`ref value` / `mutref value`), and references cannot be stored
or supplied as generic type arguments. Generic `main` is rejected. All
templates receive structural/name checks, including unused ones; operation and
ownership compatibility are checked for demanded concrete instances only.

Instances are deterministic and declaration-owned. Same-instance recursion is
allowed; polymorphic recursion and recursive data layouts, including container
and nongeneric bridges, are rejected. Depth32,256 distinct instances, and
serialized-width/token/text/map bounds fail closed as detailed in the contract.
Existing concrete type/borrow/audit diagnostics retain their families and map
back to original source with instance context. `propagates(E)` substitutes only
when E fits the existing concrete error-name atom; no audit grammar is widened.

`check`, `emit-c`, `build`, and `run` use concrete specializations. Only
`facts --format v5` and `review --format v5` accept generic graphs; they
report templates and checked instances by source identity as specified in
`docs/M56_1_CONTRACT.md`. All other facts/review/diff/change/policy/rename
formats reject a graph containing generics, even unused templates
(`NQ-GENERIC-008`). Generic-aware diff, change, policy and rename remain
deferred. This is not a stable generic library promise.

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
- functions, locals, fields, modules: `snake_case`
- constants: `UPPER_SNAKE` per [LANGUAGE_CHARTER.md](LANGUAGE_CHARTER.md); the compiler enforces the charter's naming rules from M60, and existing `snake_case` constants are migrated then

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
- `for`
- `if`
- `in`
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
- `f64`
- `str`
- `unit`

Deferred types, reserved:

- `u32`
- `u64`
- `f32`
- `char`

These four names are reserved. Writing one in any type position (local,
parameter, return, field, enum payload, `ref`/`mutref` target, container or
`result` argument, explicit generic argument), including inside an unused
declaration, is rejected with `NQ-TYPE-049` "`<name>` is reserved and not yet
supported" (M56.2; previously some unused declarations were accepted).

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

### Scalar `f64` (M56.2)

`f64` is IEEE 754 binary64, emitted as C `double`. It is a copy type with no
drop. The decision record is D067; the full contract is
[docs/M56_2_CONTRACT.md](docs/M56_2_CONTRACT.md).

**Literals.** The only float literal form is
`DIGITS "." DIGITS [ "e" [ "-" ] DIGITS ]`: `0.5`, `1.0`, `2.5e-3`,
`6.02e23`. A float literal always has type `f64`; negative values use unary
`-`. There is no suffix, no `.5`, `1.`, `1e5`, `1E5`, `1e+5`, hexadecimal
float, digit separator, or `inf`/`nan` spelling. Since M58.1, `.5`, `1.`,
`1e5`, `1E5` and `1e-5` are `NQ-PARSE-004` with help "write floats as
`<digits>.<digits>`, for example `0.5`, `1.0` or `1.0e5`"; `1.e5` and
`1.foo` stay field-access errors. A float literal
followed by a malformed exponent (`1.0E5`, `1.0e+5`, `1.0e`, `1.0e-`) is
`NQ-PARSE-004` "malformed float literal". A literal whose decimal value is at
least 2^1024 − 2^970 (it would round to infinity) is `NQ-TYPE-046`; the
compiler decides this exactly on the decimal text. Literals that round to a
subnormal or to zero are accepted. The emitted C literal is the source text;
a literal at or below 2^-1075 is emitted as `0.0`, which is the value C would
round it to.

**No implicit conversion.** An integer literal is never an `f64`
(`let x: f64 = 1;` is rejected; write `1.0`). Mixing `f64` with `i32` or `i64`
in any arithmetic or comparison is rejected with the existing operand-mismatch
diagnostic, whose help names the explicit conversion builtins. An `f64` where
an `i32` is required (list index, `main` return) is likewise rejected.

**Arithmetic.** Binary `+ - * /` and unary `-` on `f64` follow IEEE 754:
round-to-nearest-ties-to-even, no fused multiply-add contraction, overflow to
±infinity, and division by zero yielding ±infinity or NaN. Nothing traps.
Unary `-` flips the sign bit, so `-0.0` is negative zero.

**Comparison.** `== != < <= > >=` follow IEEE: every ordered comparison and
`==` with a NaN operand is false, `!=` with a NaN operand is true, and
`0.0 == -0.0` is true. The NaN test is `x != x`; the finiteness test is
`x - x == 0.0`.

**`match`.** An `f64` value cannot be a `match` scrutinee and a float literal
cannot be a pattern (`NQ-TYPE-047` "f64 values cannot be matched; compare
with `if`"). Binding an `f64` payload (`Some(x)`, `Ok(x)`, enum payloads) is
unaffected.

**Constants.** An `f64` constant initializer is exactly a float literal or
`-` followed by a float literal. Parentheses, repeated or nested minus,
arithmetic, references to other constants, and any `f64` operand inside a
`bool`/`i32`/`i64` constant initializer are rejected with `NQ-TYPE-048`
"f64 constants must be a literal; compute the value at runtime". The compiler
performs no floating-point folding.

**Builtins.** Six pure builtins (no effect atoms, no error values):

```nauq
fn f64_from_i32(value: i32) -> f64;          // exact
fn f64_from_i64(value: i64) -> option<f64>;  // None unless exactly representable
fn f64_trunc_i32(value: f64) -> option<i32>; // toward zero; None for NaN, ±inf, out of range
fn f64_trunc_i64(value: f64) -> option<i64>; // toward zero; None for NaN, ±inf, out of range
fn str_from_f64(value: f64) -> str;
fn f64_from_str(text: str) -> option<f64>;
```

- `f64_trunc_i32(v)` is `Some` exactly when `-2147483649.0 < v < 2147483648.0`
  (so `-2147483648.9` truncates to `INT32_MIN`); `f64_trunc_i64(v)` exactly
  when `-2^63 <= v < 2^63`. No undefined C conversion and no `libm` call is
  reachable; the toolchain still links without `-lm`.
- `str_from_f64` renders finite nonzero values exactly as ECMAScript
  `Number::toString`: the shortest round-tripping digits (ties toward the
  closest), fixed notation when `1e-6 <= |x| < 1e21`, otherwise `d[.ddd]e±n`
  with an explicit `+` (`0.1`, `100`, `0.000001`, `1e-7`, `1e+21`,
  `5e-324`, `1.7976931348623157e+308`). `+0.0` renders `0` and `-0.0`
  renders `-0`. NaN, +infinity and −infinity render `NaN`, `Infinity`,
  `-Infinity`; `f64_from_str` does not accept those spellings.
- `f64_from_str` accepts exactly the JSON number grammar (RFC 8259 §6) over the
  whole string, `-? (0 | [1-9][0-9]*) (\.[0-9]+)? ([eE][+-]?[0-9]+)?`, with no
  surrounding whitespace, leading `+`, `inf`/`nan`, or hexadecimal. The result
  is the correctly rounded value; `-0` gives negative zero, underflow gives a
  subnormal or zero, and any input that rounds to ±infinity gives `None`. It
  validates exactly the string's bytes, so a `str_slice` view parses only
  its own bytes (`str_slice("1.259", 0, 4)` gives `1.25`).
- For every finite `x`, `f64_from_str(str_from_f64(x)) == Some(x)` with the
  same sign of zero.
- Both text builtins run each call under its own `"C"` numeric locale
  (`newlocale`/`uselocale`), so the process locale never changes the result.
  If that locale cannot be created, the program terminates with exit code 1 and
  `nauqtype runtime: numeric locale unavailable`. Size and out-of-memory
  failures use the fatal contract above. On Windows builds there is no
  per-call locale construction, so rendering a finite nonzero value or parsing
  grammar-valid text takes the locale failure path.

**Host compiler requirement.** `stdlib/runtime.h` rejects, at compile time, a
C compiler whose `double` is not binary64 with `FLT_EVAL_METHOD == 0`, that
does not define `__STDC_IEC_559__`, that defines `__FAST_MATH__`, or (GCC)
that compiles in a GNU dialect. Under Clang it sets `#pragma STDC FP_CONTRACT
OFF`. GCC 13.3 also clears `__STDC_IEC_559__` under `-ffp-contract=fast`, so
that flag is rejected too. The shipped `-std=c11 -O2` flags are unchanged.

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

M55 additionally provides opaque `duration`, `instant`, and owned `process`,
plus the copy product `process_outcome`. Exact signatures, failure rules, and
Linux lifecycle guarantees are locked in [M55_CONTRACTS.md](M55_CONTRACTS.md).
`duration`/`instant` are nominal nanosecond values with no source constructor,
field access, operator arithmetic, comparison, or implicit integer conversion.
`process` is move-only and cleanup-requiring; `process_wait` consumes it.

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

A `let` binding becomes visible at the end of its statement (the `;`), so its
initializer sees only bindings declared before it. `let mut x = x + 1;` in an
inner scope reads the outer `x`; `let x = x;` with no outer `x` is the
unknown-name diagnostic `NQ-RESOLVE-010`. The same holds for typed `let`,
`let name = f()?;` and `let name: result<T, E> = try { ... };` locals. Other
binding forms: parameters are visible from the start of the body, let-else
bindings after the let-else statement, `match` arm bindings from the start of
the arm body, and a `for` binding from the start of the loop body (the
iterable sees only outer bindings).

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
- The `else` block must exit: it must terminate (see Functions, "Every path returns") or end with `break;` or `continue;` targeting an enclosing loop. Otherwise `check` reports `NQ-PARSE-003` "let-else `else` block must exit with `return`, `break` or `continue`" at the `else` token.
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
- Each postfix `?` must apply to a direct function call returning `result<U, E>` with the exact same `E`. In a binary expression each `?` applies to its own call operand, so `try { f()? + g()? }` propagates from each call separately; `(f() + g())?` is not a direct call and stays rejected.
- `?` anywhere else (`return f()?;`, `g(f()?);`, `if f()? { ... }`, `f()?;`) is `NQ-PROPAGATE-007` "`?` is only allowed in a `let name = expr?;` statement or inside `try`".
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
- v1 constants support only non-borrow `i32`, `i64`, `f64`, `bool`, and `str`; an `f64` constant is a single float literal, optionally negated (see Scalar `f64`)
- v1 initializers support literals, parentheses, unary `-` / `not`, arithmetic and integer comparison operators, and boolean `and` / `or`
- calls, constructors, lists, borrows, I/O, and const-to-const initializer references are intentionally rejected for now: `NQ-TYPE-057` "constant initializers may contain only literals and operators" at the offending token
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
- every path returns: a function body, including a `unit` function's and `main`'s, must not be able to reach its closing `}`; a `unit` function ends every path with `return;` (see below)
- `audit` blocks are optional in the AI Contracts alpha
- `pub fn` without `audit` emits a warning in the current compiler

Every path returns:

- A block terminates if any statement in it terminates; analysis stops at the
  first terminating statement (later statements are not diagnosed).
- A statement terminates when it is `return ...;`; an `if` with an `else`
  where both blocks terminate (there is no `else if`; a nested `if` inside
  the `else` block is that block's statement); a statement `match` whose arm
  blocks all terminate; or `while true { ... }` whose condition is exactly
  the token `true` and whose body has no `break` targeting that loop (a
  `break` inside a nested `while` or `for` targets the nested loop).
- `for`, any other `while`, assignments, `let` statements and expression
  statements never terminate.
- Violation: `NQ-TYPE-053` "function `<name>` can reach the end of its body
  without returning" at the function's closing `}`, with help "end every path
  with `return`; a `unit` function ends with `return;`".

### AI Contracts

An `audit` block is a fixed-shape, compiler-checked review surface for a function.

Rules:

- clause order is fixed: `intent`, then `mutates`, then `effects`, then optional `propagates`
- `intent("...")` is required and must be non-empty
- `mutates(...)` may list only `mutref` parameters
- `effects(...)` currently supports the fixed atoms `print` and `io`
- `propagates(...)` may list exact error types forwarded unchanged by statement-boundary `?`
- `mutates(...)` is checked against write-through to `mutref` parameters: direct assignments (`p = value;`), field assignments through the parameter (`p.field = value;`), and call-mediated writes (passing `mutref p` or `mutref p.field...` to a mutating parameter or to `list_push`, `list_replace`, or `list_pop`)
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
- direct field assignment is allowed through an owned `let mut` local product binding or a `mutref` parameter of a user-defined product type (M57.1)
- a product or enum may not contain itself by value, directly or through `list`, `option`, or `result` arguments at any depth; `check` rejects each such cycle once with `NQ-TYPE-052`, naming the shortest cycle (for example `Tree -> Branch -> Tree`) at its first-declared member. Store related values in a separate list and refer to them by index. Graphs with generic declarations keep reporting `NQ-GENERIC-005`

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

- literals: integer, float (`f64`), string, `true`, `false`
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

Each field is written `name: value`; anything else is `NQ-TYPE-055` "struct
literal fields are written `name: value`" at the field's first token.

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
- The callee is a function name (`f` or `module::f`); any other callee, such as `(f)(1)` or `f(1)(2)`, is `NQ-TYPE-058` "only named functions can be called".

### Borrow Expressions

Borrow expressions are explicit:

```nauq
let size = length(ref text);
append(mutref buffer, item);
```

Rules:

- `ref expr` and `mutref expr` are only legal as direct call arguments in v0.1
- both may name a binding or a product field path `root.f1.f2...` (including fields of a concrete generic product instance)
- `mutref` requires a mutable-capable root: the nearest visible binding of `root` must be a `let mut` owned local or a `mutref` parameter; any other root (`ref` or owned parameter, immutable local, `for`, pattern, or `let-else` binding) is `NQ-TYPE-012` "cannot take `mutref` of immutable binding `<root>`"
- borrow values cannot be stored in locals, fields, or return values
- inside a callee, `ref T` and `mutref T` parameters act as alias parameters; reading the parameter reads the referent, and assigning to a `mutref` parameter writes the referent

## Statements

Supported statements:

- local binding, including an explicitly typed local `try` boundary
- statement-boundary propagation binding: `let name = result_expr?;`
- `let-else` guard binding for `option` / `result` success patterns
- assignment to a mutable local or a `mutref` parameter
- direct field assignment through a `let mut` local or a `mutref` product parameter
- `if`
- `while`
- `for`
- `match`
- `return`
- `break` and `continue` inside `while` or `for`
- expression statement

### Assignment

```nauq
let mut count = 0;
count = count + 1;
```

Rules:

- `name = value;` requires the nearest visible binding of `name` to be a `let mut` local or a `mutref` parameter; plain `let`, `let-else` and pattern bindings and `ref` or owned parameters are `NQ-TYPE-007` "cannot assign to immutable binding `<name>`" (shadowing is respected in both directions; `for` bindings keep their existing `NQ-TYPE-042` message)
- `binding.field = value;` requires the nearest visible binding to be an owned `let mut` local or a `mutref` parameter of a user-defined product type, including a concrete generic product instance
- field assignment through a `mutref` parameter writes through the borrow (C `(*p).member`); the overwritten field value is dropped exactly once, as for an owned local
- any other root is `NQ-TYPE-042` "field assignment requires a `let mut` local or a `mutref` parameter" at the root name
- field assignment rejects `ref` parameters, owned non-`mut` locals and parameters, enum values, list elements, and arbitrary assignment targets; a nested field path (`p.a.b = v`) is `NQ-TYPE-059` "nested field assignment is not supported" (help: pass `mutref p.a` to a function that assigns the inner field)
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
- `while true { ... }` with no `break` targeting it terminates for the every-path-returns rule; the condition must be exactly the token `true`

### For

```nauq
for item in items {
    print_line(item);
}
```

Rules (D051):

- the iterable must be a `list<T>` expression; it is evaluated once
- the loop binding is immutable, scoped to the body, and cannot be assigned or escape the body
- the iterable expression sees only bindings declared before the loop, not the loop binding
- ranges, custom iterables, loop values and implicit element borrowing are not supported

### Loop Control

- `break;` and `continue;` apply to the nearest enclosing `while` or `for`
- they are valid inside nested `if`, `match`, or `let-else` only when the nested construct is inside a loop
- loop exits have no value, no labels, and do not make loops expressions
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
- statement and expression `match` share one scrutinee rule and one exhaustiveness rule:
  - the scrutinee must be `i32`, `i64`, `option<T>`, `result<T, E>`, or a user enum (including a concrete generic enum instance); an `f64` scrutinee is `NQ-TYPE-047`, any other type is `NQ-TYPE-054` "cannot `match` on type `<type>`", and no other diagnostic follows for that `match`
  - an enum, `option` or `result` scrutinee needs every variant covered by a top-level arm or a wildcard/binding fallback; `i32` and `i64` need a fallback
  - otherwise `check` reports `NQ-TYPE-051` "match must be exhaustive; missing `<C1>`, `<C2>`" at the `match` keyword (variants in declaration order; `Some`, `None`; `Ok`, `Err`; `_` for integers)
  - a zero-arm statement `match` is exhaustive only over an empty enum; a zero-arm expression `match` is rejected because an expression needs an arm
  - literal or nested-constructor arms keep the refined-pattern fallback rule (see Patterns)
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
- the scrutinee and exhaustiveness rules are the statement `match` rules above
- match expression arms do not fall through
- block expressions, implicit final-expression returns, and fallthrough are not supported

## Patterns

Supported pattern forms:

- wildcard: `_`
- binding: `name`
- unit-like variant: `None`
- tuple-like variant: `Some(value)`
- integer literal: `42` or `-1`, for `i32` scrutinees only (float literals are never patterns, and `f64` is never a scrutinee)
- nested constructor: `Some(Some(value))`

Any match containing a literal or nested constructor pattern must include a wildcard or binding fallback arm. This keeps the first refined-pattern form conservative and exhaustiveness visible. Guards, ranges, string or boolean literals, and or-patterns remain deferred.

Unsupported pattern forms have focused diagnostics:

- an unknown constructor (`Nope(x)`, `m::Nope`): `NQ-RESOLVE-010` "unknown variant `<name>` in pattern"
- `true` / `false`: `NQ-TYPE-056` "bool patterns are not supported yet" (M58.2 adds them)
- a string literal: `NQ-TYPE-056` "string patterns are not supported"
- a negated non-literal (`-x`): `NQ-TYPE-056` "only integer literals can be negated in patterns"
- any other unsupported shape (for example `1 | 2`): `NQ-TYPE-056` "this pattern form is not supported"

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

Runtime comparison operands (both sides must have the identical type):

| Operators | Operand type |
| --- | --- |
| `==`, `!=` | `i32`, `i64`, `f64`, `bool`, `str`, payload-free enums |
| `<`, `<=`, `>`, `>=` | `i32`, `i64`, `f64` |

- A payload-free enum is a user enum, or a concrete instance of a generic user enum, whose declared variants all have no payload; `==` compares variants.
- Any other identical operand type (`str` ordering, `bool` ordering, enums with payloads, products, `option`, `result`, `list`, `unit`, ...) is `NQ-TYPE-050` "operator `<op>` is not defined for type `<type>`", with the type spelled as in source (for example `Pair<i32>`). Mismatched operands keep `NQ-TYPE-042` "comparison operands must have matching types", and process/time types keep their `NQ-TYPE-042` message.
- `const` initializers keep their integer-only comparison rule.

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
- `f64`
- `str`
- `unit`
- `io_err`
- `process_result`
- `duration`, `instant`, and `process_outcome` (M55)
- any user-defined `type` or `enum` whose fields/payloads are all copy

Move types in v0.1:

- `list<T>`
- `bytes`
- `process` (M55)
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
- `mutref` cannot coexist with any other borrow of the same root in the same call (`NQ-BORROW-006`). Every argument under root `r` borrows `r`: `ref r...`, `mutref r...`, and a borrow parameter `r` forwarded by name, whose kind is the receiving parameter's kind. So `f(mutref b.items, ref b.count)` and `f(p, mutref p.items)` are rejected, while two shared borrows never conflict; field-disjoint checking is deferred
- consuming a non-copy pointee through a borrowed binding is rejected; copy values may be read from a borrow and are copied according to their checked value plan
- bootstrap `while` analysis tracks possible moves across iterations conservatively
- no stored references
- `ref binding.field...` and `mutref binding.field...` paths are supported for
  direct call arguments, including the shipped runtime product fields; a
  `mutref` path needs a `let mut` owned local or `mutref` parameter root, and
  writes through a `mutref` parameter root reach the caller's value in place
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
fn str_join(parts: ref list<str>) -> str;
fn str_get(text: str, index: i32) -> option<i32>;
fn str_slice(text: str, start: i32, end: i32) -> option<str>;
fn list() -> list<T>;            // requires expected context
fn list_push(items: mutref list<T>, value: T) -> unit;
fn list_len(items: ref list<T>) -> i32;
fn list_get(items: ref list<T>, index: i32) -> option<T>;
fn list_replace(items: mutref list<T>, index: i32, value: T) -> option<T>;
fn list_pop(items: mutref list<T>) -> option<T>;
fn i64_from_i32(value: i32) -> i64;
fn i32_from_i64(value: i64) -> option<i32>;
fn bytes_from_str(text: str) -> bytes;
fn bytes_len(value: ref bytes) -> i64;
fn bytes_get(value: ref bytes, index: i64) -> option<i32>;
```

`[]` is the literal equivalent of an empty `list<T>` and follows the same expected-context rule as `list()`.

M57.1 in-place list updates and integer conversions:

- `list_replace` stores `value` at `index` when `0 <= index < list_len` and
  returns `Some(old)`, moving the old element out to the caller; otherwise the
  list is unchanged, `value` is dropped once, and the result is `None`.
- `list_pop` removes the last element and returns it as `Some`, moving it out
  (dropping the list later does not drop it again), or returns `None` when the
  list is empty.
- Unlike `list_get`, neither needs a copy element type. Both mutate argument 0
  for `mutates(...)` like `list_push`, have no effects, run in O(1), and never
  shrink capacity.
- `i64_from_i32` is exact. `i32_from_i64` returns `None` outside
  `[-2147483648, 2147483647]`. There is still no implicit numeric conversion.
- Builtin callable names (every builtin function plus `list`, `Some`, `None`,
  `Ok`, `Err`) cannot name an enum variant (`NQ-RESOLVE-010` "builtin callable
  names cannot be redeclared"). Top-level functions, types, enums and
  constants with such names remain accepted; an unqualified call still reaches
  the builtin.

`str_join` concatenates borrowed text parts in list order, with no separator
or conversion, into independently owned text. Empty input returns empty text;
embedded NUL is preserved. No input mutation/consumption or effect atom occurs.
Owned lists require an explicit `ref` argument; existing `ref list<str>`
parameters can be forwarded directly, positionally or with `parts:`, under
the existing checked borrow rules.
Size/OOM failures use the existing fatal string allocation contract. Empty and
singleton calls also allocate a fresh payload and owner. See
`PERFORMANCE_ENABLEMENT.md` for PRE-M56 E1 acceptance.

The active compiler driver also uses a deliberately narrow tooling runtime
surface for arguments, directory creation, and captured process execution.
Those builtins are toolchain-enabling authority, not a general OS API.

M55 adds explicit process environment overrides, stdin, capture limits,
monotonic deadlines, consuming wait, cancellation, and automatic owned-child
cleanup, plus checked wall/monotonic time and sleep. It does not add background
pumping, threads, async tasks, implicit shell execution, or PATH search to the
new launch API. Legacy `run_process` retains its existing PATH behavior.

Owned process-containing parameters, locals, temporary values, and return
types conservatively contribute `effects(io)` and checked `process` evidence.
This rule is recursive through checked product/enum/container type identities;
merely borrowing such values does not contribute cleanup authority. Review
reports this may-authority without inventing source call sites in facts.
Clock/deadline reads use IO kind `read`; sleep uses current-process `process`
authority. See the exact boundary in [M55_CONTRACTS.md](M55_CONTRACTS.md).

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

- Text output prints `note:` and `help:` lines after the message whenever the
  diagnostic carries them; JSON output carries the same fields.
- Each parse error is reported once.
- If loading the module graph or parsing any module reports an error, the
  command stops before name resolution and reports only those diagnostics in
  its usual envelope (for `review-diff` and `change-report`, per side). No
  cascade such as "missing main" follows.
- A malformed expression the parser cannot read (for example `1 2` or
  `+1`) is `NQ-PARSE-005` "malformed expression"; a missing statement
  terminator is `NQ-PARSE-003` "expected `;`" at the end of the statement's
  last token.
- Diagnostics whose message begins "internal compiler error:" report a
  compiler invariant failure, never a property of the source; every source
  shape the compiler does not support has a focused diagnostic
  (docs/M58_1_PRODUCER_LEDGER.md records the inventory).

The compiler also supports:

```text
nauqc review <file>
```

`review` emits deterministic JSON summarizing each function's declared `audit` data and compiler-inferred mutation/effect facts.

## Initial Lints

Current lints, all warnings:

- public function missing `audit` (`NQ-CONTRACT-001`)
- overdeclared `mutates(...)` (`NQ-CONTRACT-006`)
- overdeclared `effects(print)` / `effects(io)` (`NQ-CONTRACT-009`)

Planned lints without a producer (`unused_mut`, discarded `result` value) are
listed in DEFERRED.md. The charter makes `pub` contracts required from M62.

## Explicit v0.1 Omissions

- methods
- traits
- loop families beyond bootstrap `while` and list-only `for`
- labeled or valued `break` / `continue`
- inference, constraints and other generic facilities beyond explicit M56 reuse
- broader constant expressions beyond the v1 pure literal/operator subset
- exceptions
- async
- macros
- operator overloading
- advanced lifetimes
