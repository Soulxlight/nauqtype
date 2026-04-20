# Nauqtype Compiler Architecture

## Goals

The v0.1 compiler should deliver a real vertical slice:

- lex source
- parse a source file
- resolve names
- type-check a meaningful subset
- enforce minimal move/borrow rules
- lower to a small IR
- emit readable C
- compile and run with a system C compiler
- report stable diagnostics

## Implementation Language

Preferred long-term implementation language:

- Rust

Current bootstrap implementation in this workspace:

- Python

Reason:

- Rust remains the preferred destination for long-term compiler implementation.
- The current environment does not provide a Rust toolchain.
- The bootstrap compiler should still be built now rather than blocked on environment setup.
- Python is sufficient for a small front-end and C-emitting prototype while the language design stays backend-agnostic.

## Top-Level Module Boundaries

Planned project layout:

- `compiler/lexer/`
- `compiler/parser/`
- `compiler/ast/`
- `compiler/resolve/`
- `compiler/types/`
- `compiler/borrow/`
- `compiler/ir/`
- `compiler/codegen_c/`
- `compiler/diagnostics/`
- `stdlib/`
- `examples/`
- `tests/`

The bootstrap compiler uses `compiler/` as its package root so the project layout matches the phase boundaries directly.

## Compiler Phases

### 1. Lexing

Input:

- source text

Output:

- token stream
- trivia-stripped spans
- lex diagnostics

Responsibilities:

- tokenize keywords, identifiers, literals, punctuation
- preserve source spans
- reject malformed strings and unknown characters

### 2. Parsing

Input:

- token stream

Output:

- AST for one source file
- parse diagnostics

Responsibilities:

- build a concrete AST with explicit nodes for items, statements, expressions, patterns, and types
- recover enough after errors to continue collecting diagnostics

Strategy:

- hand-written recursive-descent parser
- Pratt-style expression parser for operator precedence

### 3. Name Resolution

Input:

- AST

Output:

- resolved symbol tables
- name-linked AST or a lightweight resolved representation
- unresolved-name diagnostics

Responsibilities:

- register top-level items
- resolve local bindings
- distinguish functions, types, enum variants, and fields where applicable
- mark built-ins such as `print_line`, `option`, and `result`

v0.1 simplification:

- one-file scope only

### 4. Type Checking

Input:

- resolved AST

Output:

- typed AST / semantic model
- type diagnostics

Responsibilities:

- validate local declarations and assignments
- validate function calls
- validate return statements
- validate match exhaustiveness for supported patterns
- distinguish copy vs move types

v0.1 simplifications:

- no user generics
- exact type matching only
- built-in generic utility types only

### 5. Borrow And Move Checking

Input:

- typed AST

Output:

- borrow/move diagnostics

Responsibilities:

- reject use after move for non-copy locals
- ensure `mutref` is only taken from mutable locals
- ensure temporary borrow rules are respected per call
- prevent aliasing combinations within a call such as two `mutref` borrows of the same local

v0.1 simplifications:

- references never become first-class values
- no stored refs
- no field borrows
- no interprocedural lifetime analysis

### 6. IR Lowering

Input:

- checked AST

Output:

- small typed IR

Responsibilities:

- linearize control flow enough for deterministic C emission
- make enum construction and match lowering explicit
- preserve source location links where practical

IR design goals:

- simple, structured, and backend-agnostic enough to survive a future backend swap
- not a giant SSA system in v0.1

### 7. C Code Generation

Input:

- IR

Output:

- `.c` translation unit
- optional `.h` or embedded runtime includes

Responsibilities:

- emit readable C
- generate runtime types for `str`, `option`, `result`, structs, and enums
- emit a simple `main` wrapper if needed
- keep naming deterministic

Codegen choices:

- tagged unions for enums
- direct C structs for `type`
- helper runtime functions in `stdlib/`

## AST Strategy

The AST should remain close to source structure.

Key node groups:

- `Item`
- `TypeExpr`
- `Stmt`
- `Expr`
- `Pattern`

Important rule:

- do not hide language semantics inside parser shortcuts

## Name Resolution Strategy

Resolver scopes:

- file scope for top-level items and constructors
- function scope
- block scope

The resolver should produce stable symbol IDs rather than depending on raw text comparisons later.

## Type-Checking Strategy

The checker operates function-by-function after top-level item collection.

Main responsibilities:

- assign types to expressions
- validate statements
- validate constructor usage
- detect mismatch errors early and precisely

The type system should classify each type as copy or move-sensitive.

## Borrow-Checking Strategy

The borrow checker is intentionally conservative.

Rules enforced in v0.1:

- move after use is illegal for non-copy locals
- `mutref` requires a mutable local binding
- a call may not borrow the same local both mutably and immutably
- a call may not take two mutable borrows of the same local

Rules deferred:

- borrow lifetimes beyond a single call
- references in structs
- reference returns
- non-lexical lifetime-like refinements

## Diagnostics Strategy

Diagnostics are emitted by every phase through a shared structure.

Required fields:

- `code`
- `category`
- `message`
- `span`
- `notes`
- `help`

Example format:

```text
error[NQ-TYPE-004]: cannot assign `bool` to `i32`
  --> examples/bad_assign.nq:4:5
  note: `count` was declared here as `i32`
  help: change the value or update the binding type
```

Categories:

- `LEX`
- `PARSE`
- `RESOLVE`
- `TYPE`
- `BORROW`
- `IR`
- `INTERNAL`
- `LINT`

## Initial Diagnostics Coverage

- Parse errors: unexpected token, missing delimiter, bad literal
- Type errors: mismatched types, wrong argument count, wrong return type, invalid field access
- Ownership errors: use after move, invalid `mutref`, aliasing in a call
- Resolve errors: unknown name, duplicate definition, unknown field or variant
- Pattern errors: non-exhaustive match, invalid constructor pattern
- Fallibility misuse: discarded `result` warning

## Testing Strategy

### Unit Tests

- lexer tokenization
- parser shapes
- resolution rules
- type rules
- borrow rules
- C emission snippets

### Golden Tests

- diagnostics
- emitted C for representative examples

### Integration Tests

- compile example `.nq` files
- emit C
- invoke a system C compiler
- run executables and assert outputs

Determinism matters:

- stable symbol naming
- stable diagnostic ordering
- stable generated C formatting

## Future Extensibility Boundaries

The architecture should make later additions possible without redoing the compiler:

- cross-file modules
- user-defined generics
- methods and traits
- richer borrow analysis
- additional backends

To preserve that option:

- keep AST, semantic typing, and IR separate
- avoid baking C syntax into earlier phases

## Runtime Boundary

The runtime in `stdlib/` should remain tiny.

v0.1 runtime responsibilities:

- `str` representation
- printing support
- helper constructors or tag definitions if needed

Everything else stays out unless it is required by the vertical slice.
