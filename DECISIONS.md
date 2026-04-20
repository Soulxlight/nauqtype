# Nauqtype Decisions

## D001: Bootstrap backend is compile-to-C

- Decision: Nauqtype v0.1 lowers to C as its primary backend.
- Alternatives considered: bytecode VM first, LLVM first.
- Reason chosen: fastest path to a working compiler pipeline, readable generated output, simple runtime model.
- Consequences: backend optimizations are limited; generated C becomes part of the debugging story.
- Reversible later: yes.

## D002: Syntax stays hybrid keyword/symbol, not symbolic-minimalist

- Decision: keep familiar structural punctuation but use keywords for semantics that matter in review.
- Alternatives considered: keyword-heavy everywhere, compact symbolic syntax.
- Reason chosen: best balance across AI reliability, readability, and parser simplicity.
- Consequences: slightly higher token count than compact languages.
- Reversible later: partially, but syntax churn is expensive.

## D003: Local bindings use `let` and `let mut`

- Decision: all local declarations start with `let`.
- Alternatives considered: `let x` and separate `mut x`.
- Reason chosen: fewer declaration forms and better mutation visibility.
- Consequences: slightly more verbose mutable declarations.
- Reversible later: yes, but not worth changing.

## D004: Return uses `return`, not `out`

- Decision: the language uses `return`.
- Alternatives considered: `out`.
- Reason chosen: stronger model familiarity and lower AI mistake rate.
- Consequences: a few extra tokens.
- Reversible later: technically yes, practically undesirable.

## D005: Error container names are `option` and `result`

- Decision: use fully spelled names in types.
- Alternatives considered: `opt` and `res`.
- Reason chosen: clarity matters more than shaving a few characters from crucial APIs.
- Consequences: type signatures are slightly longer.
- Reversible later: yes with aliases, but core docs should stay stable.

## D006: Built-in constructors use `Some`, `None`, `Ok`, and `Err`

- Decision: built-in utility constructors are capitalized like enum variants.
- Alternatives considered: lowercase constructors.
- Reason chosen: stronger visual distinction between constructors and ordinary functions.
- Consequences: style is slightly more type-like.
- Reversible later: yes, but it would churn examples and diagnostics.

## D007: Ownership v0.1 is minimal but real

- Decision: enforce move checking and temporary call-site borrows only.
- Alternatives considered: no ownership in v0.1, full Rust-like lifetimes.
- Reason chosen: gives genuine safety value without making bootstrap infeasible.
- Consequences: v0.1 rejects some programs a richer future model could accept.
- Reversible later: yes, by extending the checker.

## D008: References cannot be stored in locals, fields, or returns in v0.1

- Decision: `ref` and `mutref` exist only as parameter types and call-site argument forms.
- Alternatives considered: general first-class references.
- Reason chosen: sharply reduces lifetime and aliasing complexity.
- Consequences: some APIs are less expressive.
- Reversible later: yes.

## D009: User-defined generics are deferred

- Decision: only built-in generic utility types are supported in v0.1.
- Alternatives considered: full generic structs, enums, and functions.
- Reason chosen: keeps parser, resolver, type checker, and codegen smaller.
- Consequences: some reusable abstractions are unavailable initially.
- Reversible later: yes.

## D010: Methods and `impl` blocks are deferred

- Decision: v0.1 uses free functions only.
- Alternatives considered: include method syntax from the start.
- Reason chosen: free functions avoid method lookup rules and hidden receiver behavior.
- Consequences: less ergonomic APIs.
- Reversible later: yes.

## D011: Pattern matching requires explicit arm blocks

- Decision: every `match` arm body is a block.
- Alternatives considered: single-expression arms.
- Reason chosen: simpler parsing, clearer control flow, and better diagnostic anchoring.
- Consequences: slightly more verbose matches.
- Reversible later: yes.

## D012: Semicolons and commas are required

- Decision: simple statements end with `;`, list-like constructs use `,`.
- Alternatives considered: newline-significant layout.
- Reason chosen: avoids parser fragility and AI formatting dependence.
- Consequences: extra punctuation.
- Reversible later: unlikely.

## D013: Single-file compile units define the v0.1 module boundary

- Decision: one source file is one module; cross-file imports are out of scope for v0.1.
- Alternatives considered: full multi-file module resolution now.
- Reason chosen: preserves the simple module bias while protecting the schedule.
- Consequences: visibility metadata exists before import wiring.
- Reversible later: yes.

## D014: `str` is an immutable runtime string view in v0.1

- Decision: `str` lowers to a small runtime view type instead of a mutable owned string abstraction.
- Alternatives considered: mutable heap-owned strings, raw C strings.
- Reason chosen: makes literals and printing easy without dragging in allocation policy.
- Consequences: string mutation and rich string APIs are deferred.
- Reversible later: yes.

## D015: The standard library boundary is intentionally tiny

- Decision: only minimal runtime support and a few intrinsics are in scope for v0.1.
- Alternatives considered: broader I/O and collection support.
- Reason chosen: compiler progress matters more than library breadth.
- Consequences: examples stay small and explicit.
- Reversible later: yes.

## D016: Diagnostics are a first-class product surface

- Decision: every compiler phase reports structured diagnostics with stable codes and spans.
- Alternatives considered: ad hoc error strings.
- Reason chosen: AI-authored code needs precise human-readable and machine-usable feedback.
- Consequences: more upfront design work.
- Reversible later: no, this should stay foundational.

## D017: The initial lint set stays small

- Decision: ship only a few warnings in v0.1, such as `unused_mut` and discarded `result` values.
- Alternatives considered: large lint catalog.
- Reason chosen: signal quality matters more than quantity.
- Consequences: some style and safety guidance remains future work.
- Reversible later: yes.

## D018: Current workspace bootstrap implementation uses Python, not Rust

- Decision: implement the current bootstrap compiler in Python while preserving the documented architecture and backend decisions.
- Alternatives considered: block the project pending Rust installation, silently install Rust into the user environment.
- Reason chosen: Rust is not available in the current workspace environment, and silently modifying the user's machine is a non-obvious consequence. A Python bootstrap keeps progress real while still targeting compiled C output.
- Consequences: the implementation language temporarily diverges from the preferred long-term choice; a future Rust port remains desirable.
- Reversible later: yes.

## D019: Bootstrap dependencies are pinned and workspace-local

- Decision: install `ziglang==0.16.0` and `tiktoken==0.12.0` into `.deps` through a repo-local setup script.
- Alternatives considered: rely on ambient global installs, float to latest package versions.
- Reason chosen: fresh clones should be reproducible and should not depend on hidden machine state.
- Consequences: the project owns a small dependency bootstrap step and may need explicit version bumps later.
- Reversible later: yes.

## D020: The AI-friendliness audit baseline is plain Python with `o200k_base`

- Decision: compare Nauqtype against plain idiomatic Python 3 using `tiktoken` `o200k_base` token counts plus a fixed structural rubric.
- Alternatives considered: Rust baseline, TypeScript baseline, token-only comparison.
- Reason chosen: Python is a common AI generation target and gives a strong baseline for token cost and structural clarity tradeoffs.
- Consequences: the audit emphasizes general-programming comparison, not systems-language parity.
- Reversible later: yes.
