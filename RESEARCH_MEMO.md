# Nauqtype Research Memo

## Purpose

This memo hardens Nauqtype v0.1 before implementation. The goal is not novelty. The goal is a small compiled language that an AI can generate reliably, a human can audit quickly, and a Rust bootstrap compiler can realistically ship.

## Starting Constraints

- Compiled-first identity
- Compile-to-C bootstrap backend unless disproven
- Small v0.1 surface area
- AI-friendly by structural regularity, not by terseness at any cost
- Human auditability matters as much as expressiveness
- Static correctness preferred over runtime apology
- Rust compiler implementation bias
- Single-file module bias
- Any feature that endangers a working v0.1 must be cut

## Executive Recommendation

Lock Nauqtype v0.1 to a compact hybrid syntax with explicit statement terminators, explicit function boundary types, explicit `result` and `option` handling, nominal structs and enums, and a minimal but real ownership model based on:

- move checking for non-copy locals
- explicit `ref` and `mutref` call-site borrows
- no stored references
- no field borrows
- no lifetime syntax

This is enough to make ownership real in v0.1 without recreating Rust's hardest parts.

## Review Outcome

### Keep

- Compile-to-C bootstrap strategy
- Rust implementation bias
- Statically typed compiled language identity
- `fn`, `type`, `enum`, `match`, `pub`
- Explicit `result`/`option` style error handling
- Immutable-by-default semantics
- Pattern matching
- Product types and enums
- Explicit ownership-sensitive forms

### Simplify

- Local bindings: use only `let` and `let mut`
- Return: use only `return`
- Modules: one source file is one module; cross-file imports deferred
- Generics: built-in `option<T>` and `result<T, E>` only
- Borrowing: only temporary call-site borrows in v0.1
- Mutation: local reassignment plus `mutref` call arguments only

### Rename

- `res<T, E>` -> `result<T, E>`
- `opt<T>` -> `option<T>`
- `out` -> `return`

### Defer

- User-defined generics
- Methods / `impl`
- Traits / interfaces
- Loops
- Stored references
- Field assignment
- File I/O
- Collections beyond future design placeholders
- Propagation sugar like `?`
- Cross-file import resolution
- Optimizer pipeline beyond trivial cleanup

### Reject For v0.1

- LLVM-first backend
- Bytecode-first runtime
- Exceptions
- Macros
- Async
- Operator overloading
- Implicit conversions
- Null values
- Full Rust-style lifetime syntax

## Required Comparisons

### A. Syntax Style Comparison

| Style | AI generation reliability | Token efficiency | Readability | Parser simplicity | Long-term maintainability | AI error proneness | Verdict |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Keyword-heavy | High | Medium-low | High | High | High | Low | Strong candidate |
| Hybrid keyword/symbol | High | Medium | High | High | High | Low-medium | Best overall |
| More symbolic compact syntax | Medium-low | High | Medium-low | Medium | Medium | High | Reject for v0.1 |

Recommendation:

- Choose hybrid keyword/symbol syntax.
- Keep symbols where they are universal and low-risk: `()`, `{}`, `,`, `;`, `:`, `.`, `->`, arithmetic/comparison operators.
- Use keywords for semantics that matter in review: `let`, `mut`, `match`, `return`, `ref`, `mutref`, `and`, `or`, `not`.

Reason:

- Fully keyword-heavy syntax would inflate tokens for little gain.
- Symbol-heavy syntax is compact but increases AI punctuation mistakes, visual density, and recovery difficulty.
- Hybrid syntax gives clear structural anchors while staying practical.

### B. Borrowing Syntax Comparison

| Form | Readability | Token cost | Novice auditability | Parser simplicity | Future ownership complexity | AI consistency | Verdict |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `ref` / `mutref` | High | Medium | High | High | Medium | High | Best for v0.1 |
| `&` / `&mut` | Medium | Low | Medium | High | Medium | Medium | Viable but less audit-friendly |
| Partially inferred borrowing | Medium-low | High when debugging mistakes | Low | Medium-low | High | Low | Reject for v0.1 |

Recommendation:

- Use `ref T` and `mutref T` in parameter positions.
- Use `ref value` and `mutref value` at call sites.

Reason:

- The extra letters buy clarity in code review.
- Borrowing becomes visible to humans and to the AI without punctuation fragility.
- Partially inferred borrows create hidden behavior, which conflicts with the project goals.

### C. Return Keyword Comparison

| Form | Clarity | Token cost | Familiarity | AI consistency | Visual distinctness in review | Verdict |
| --- | --- | --- | --- | --- | --- | --- |
| `out` | Medium | Low | Low-medium | Medium-low | High | Reject |
| `return` | High | Medium | High | High | High enough | Choose |

Recommendation:

- Use `return`.

Reason:

- `return` is a stable learned token for both humans and models.
- `out` is compact but ambiguous in meaning and not widely reinforced by existing language data.

### D. Result Naming Comparison

| Form | Clarity | Verbosity | Generation reliability | Visual density | Verdict |
| --- | --- | --- | --- | --- | --- |
| `res<T, E>` | Medium | Low | Medium | Dense | Reject |
| `result<T, E>` | High | Medium | High | Acceptable | Choose |

Recommendation:

- Use `result<T, E>`.

Reason:

- The longer name reduces ambiguity and improves fast human scanning.
- Error handling is important enough to justify a few more tokens.

### E. Backend Comparison

| Backend | Implementation speed | Debuggability | Runtime model complexity | Future extensibility | Bootstrap practicality | Verdict |
| --- | --- | --- | --- | --- | --- | --- |
| Compile-to-C | High | High | Low-medium | Medium | High | Choose |
| Bytecode VM first | Medium-low | Medium | High | Medium | Medium-low | Reject for v0.1 |
| LLVM first | Low | Medium | Medium | High | Low | Reject for v0.1 |

Recommendation:

- Use compile-to-C for bootstrap.

Reason:

- It minimizes backend bring-up cost.
- Generated C is inspectable when the compiler or runtime misbehaves.
- It lets the project focus on language semantics before backend ambition.

### F. Additional Comparison: Local Binding Syntax

| Form | AI reliability | Human auditability | Parser simplicity | Verdict |
| --- | --- | --- | --- | --- |
| `let x = ...` / `mut y = ...` | Medium | Medium | Medium | Reject |
| `let x = ...` / `let mut y = ...` | High | High | High | Choose |

Recommendation:

- Use `let` and `let mut`.

Reason:

- One declaration family is better than two.
- Mutation becomes an obvious modifier rather than a second declaration keyword.

## Likely Failure Points

### Syntax Design

- Risk: too many special cases between declarations, constructors, and patterns.
- Mitigation: reduce the surface to a small number of regular forms and reserve semicolons/commas for clear list boundaries.

### Parser Complexity

- Risk: newline-sensitive layout would create avoidable complexity.
- Mitigation: require semicolons for simple statements and commas inside lists.

### Type System Design

- Risk: user-defined generics and inference would balloon complexity.
- Mitigation: support only monomorphic user types and built-in generic utility types in v0.1.

### Ownership Design

- Risk: full lifetimes would consume the schedule.
- Mitigation: temporary call-site borrows only, no stored refs, no field borrows.

### Diagnostics Quality

- Risk: a small compiler can easily defer diagnostics until too late.
- Mitigation: make spans, stable diagnostic codes, and golden diagnostics part of the architecture from day one.

### Code Generation Reliability

- Risk: enum layout and match lowering can become ad hoc.
- Mitigation: choose a small typed IR and a deterministic C emission strategy with readable tagged unions.

### Future Extensibility

- Risk: v0.1 shortcuts could block v0.2.
- Mitigation: keep AST, type information, and IR separate enough to add modules, traits, and richer borrow analysis later.

### Implementation Difficulty

- Risk: trying to ship too much numeric, stdlib, and module support at once.
- Mitigation: start with a single-file compile unit and a tiny runtime boundary.

## AI Generation Reliability Evaluation

### Main Findings

- Structural regularity matters more than absolute brevity.
- The language should minimize overloaded punctuation with high semantic weight.
- Statement boundaries should be explicit.
- Function signatures should always show parameter types and return types.
- Ownership-sensitive operations must look different from ordinary argument passing.

### Concrete Heuristics

- One local declaration family: `let` / `let mut`
- One return form: `return`
- One fallibility container family: `option`, `result`
- Two borrow forms: `ref`, `mutref`
- No hidden conversions
- No implicit error propagation
- No multiple ways to define products or enums
- No newline-significant parsing

### Ambiguity Risk

- Low after locking semicolons, commas, and explicit borrow markers.

### Syntax Collision Risk

- Moderate if enum constructors share names with functions.
- Reduced by style guidance: `UpperCamel` for types and variants, `snake_case` for values and functions.

### Punctuation Overload Risk

- Moderate but manageable.
- Key overloaded symbols are limited to universal ones: `()`, `{}`, `.`, `:`, `,`, `;`, `->`.

### Token Cost

- Slightly higher than a compact language, but justified by clarity.
- Most token increases come from `return`, `result`, and explicit `ref` forms.

### Tendency Toward Structurally Similar Generated Code

- High in a good way.
- Regular statement shapes and explicit signatures should lead to AST-like generated code that is easy to lint and review.

## Human Auditability Evaluation

### Scanability

- Strong with fixed declaration forms and required function signatures.

### Obvious Boundaries

- Strong with braces, commas, semicolons, and explicit return types.

### Obvious Fallibility

- Strong because fallible APIs visibly return `result<T, E>` and are handled with `match`.

### Obvious Mutation

- Strong with `let mut`, assignment, and `mutref`.

### Obvious Data Shape

- Strong with nominal `type` and `enum` declarations.

### Obvious Control Flow

- Strong because there are no exceptions, no implicit truthiness, and no hidden propagation sugar.

## Compiler Practicality Evaluation

### Grammar Simplicity

- Good. A hand-written lexer plus recursive-descent or Pratt parser is sufficient.

### AST Simplicity

- Good if the language keeps statements and expressions orthogonal and avoids method-resolution complexity.

### Resolver Complexity

- Good with one-file compile units and no imports in v0.1.

### Type Checker Complexity

- Moderate but manageable with monomorphic user types plus built-in generics only.

### Ownership Checker Feasibility

- Good only if references do not escape call sites.
- Poor if stored references or field borrows are added in v0.1.

### Compile-to-C Feasibility

- Strong for structs, enums, pattern matches, and a small runtime boundary.

## Locked Recommendation Set

### Final v0.1 Syntax Direction

- Hybrid keyword/symbol syntax
- Required semicolons for simple statements
- Required commas in declaration and match lists
- `let` / `let mut`
- `return`
- `type` and `enum`
- `match` with explicit arm blocks
- `result<T, E>` and `option<T>`
- `Ok`, `Err`, `Some`, `None`
- `ref` / `mutref`
- No methods, traits, or macros

### Final Backend Decision

- Compile to readable C for bootstrap.

### Final Ownership Strategy For v0.1

- Minimal but real.
- Non-copy locals move by default.
- Primitive scalars are copy types.
- `str` is an immutable runtime string view and is copyable in v0.1.
- Borrows are explicit and temporary at call sites only.
- No stored refs.
- No field borrows.
- No lifetime syntax.

### Final Error Handling Strategy For v0.1

- Explicit `result<T, E>` plus `match`.
- No exceptions.
- No hidden unwinding.
- No `?` in v0.1.

### Final Must-Have Features

- Single-file compile units
- `pub` parsing and visibility metadata
- `let` / `let mut`
- Functions with explicit boundary types
- Structs and enums
- Pattern matching
- Built-in `option<T>` and `result<T, E>`
- Basic name resolution
- Basic type checking
- Minimal move checking
- Temporary borrow checking for `ref` / `mutref`
- Compile-to-C backend
- Minimal runtime support for `str` and printing
- Diagnostics with codes and spans
- Initial lints

### Final Explicitly Deferred Features

- Cross-file imports
- User-defined generics
- Methods and `impl`
- Traits
- Loops
- Field assignment
- Stored references
- Propagation sugar
- Dynamic collections
- File I/O
- Optimizations beyond straightforward lowering

## Scope Freeze Statement

The locked v0.1 plan is intentionally smaller than the tentative design. That is the right outcome. Nauqtype should earn additional power only after the compiler pipeline is demonstrably real.
