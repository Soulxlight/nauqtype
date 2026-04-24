# Nauqtype Compiler Architecture

## Goals

The v0.1 compiler should deliver a real vertical slice:

- lex source
- parse one source file or a flat-root module graph
- resolve names
- type-check a meaningful subset
- enforce minimal move/borrow rules
- lower to a small IR
- emit readable C
- compile and run with a system C compiler
- report stable diagnostics

## Implementation Language

Active implementation language:

- Nauqtype

Frozen bootstrap/reference implementation in this workspace:

- Python

Reason:

- The first stage1-to-stage2 self-build proof is complete.
- The project now benefits more from teaching and exercising Nauqtype through its own implementation path than from continuing to grow the host-language bootstrap.
- Python remains valuable as a pinned bootstrap/reference path while the active driver and runner finish cutting over.

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

### 2. Project Loading And Parsing

Input:

- entry source file path plus transitive `use` graph

Output:

- per-module ASTs
- parse diagnostics

Responsibilities:

- load `<workspace-root>/<module>.nq` for flat-root imports
- detect missing modules and import cycles
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

Stage1 simplification:

- one workspace root only
- no re-exports or nested modules

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
- validate `while` conditions
- validate imported type and function usage across the flat-root graph
- infer AI Contract mutation/effect facts
- validate match exhaustiveness for supported patterns
- distinguish copy vs move types

v0.1 simplifications:

- no user generics
- exact type matching only
- built-in generic utility types only
- builtin `list<T>` only; no user-defined generics

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
- typed list helpers and bootstrap file/string helpers in `stdlib/`

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
- bootstrap `while` loops are checked with a conservative loop-head move analysis over bindings visible outside the loop body

Rules deferred:

- borrow lifetimes beyond a single call
- references in structs
- reference returns
- non-lexical lifetime-like refinements
- loop control beyond statement-form `while`
- transitive mutation contracts and richer effect atoms

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
- `CONTRACT`
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
- Contract errors: missing audit clauses, invalid `mutates(...)`, missing `effects(print)`, public API missing `audit`

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
- `review` JSON for representative examples

### Integration Tests

- compile example `.nq` files
- compile multi-file example graphs
- emit C
- invoke a system C compiler
- run executables and assert outputs
- run `selfhost/main.nq`

Determinism matters:

- stable symbol naming
- stable diagnostic ordering
- stable generated C formatting
- stable `review` JSON ordering

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

Current bootstrap runtime responsibilities:

- `str` representation
- printing support
- bootstrap file input helpers
- bootstrap file output helpers
- typed list allocation helpers
- process argument access for the active stage1 driver
- narrow directory creation and subprocess helpers for driver/proof orchestration
- helper constructors or tag definitions if needed

Everything else stays out unless it is required by the vertical slice.
