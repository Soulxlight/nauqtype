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

## D021: Stage0 may implement statement-form `while` as a bootstrap-track exception

- Decision: allow `while condition { ... }` in the current Python bootstrap compiler while keeping broader loop work deferred from the locked v0.1 language plan.
- Alternatives considered: keep all loops deferred until a later milestone, add a broader control-flow set (`for`, `break`, `continue`) now.
- Reason chosen: simple counter-style loops are useful for bootstrap practicality, and `while` fits the existing parser, checker, IR, and C emitter without forcing a larger control-flow design commitment.
- Consequences: docs must call out `while` explicitly as a controlled bootstrap extension; move checking across loop iterations stays conservative and may reject some loops a richer future analysis could accept.
- Reversible later: yes, either by folding `while` into a wider stabilized loop design or by tightening the bootstrap boundary again.

## D022: AI Contracts are Nauqtype's primary AI-first differentiator

- Decision: add a fixed-shape `audit` block on functions with compiler-checked `intent`, `mutates`, and `effects` clauses.
- Alternatives considered: typed holes first, free-form annotations/comments, generated review summaries only.
- Reason chosen: AI Contracts make the most review-critical API facts explicit in source and machine-readable in a stable form, without requiring speculative language complexity.
- Consequences: public APIs become slightly more verbose, but reviewability and toolability improve materially.
- Reversible later: partially; the exact syntax is reversible, but the principle of compiler-checked review metadata should remain.

## D023: Bootstrap Stage1 proceeds imports first, then file input, then builtin `list<T>`

- Decision: after AI Contracts alpha, the next language expansion sequence is acyclic imports, then file input, then builtin `list<T>`.
- Alternatives considered: add file I/O first, add collections first, widen surface more broadly.
- Reason chosen: imports are the first real blocker for a self-hosted compiler split across files; file input and one growable sequence type follow naturally after that.
- Consequences: methods, traits, user-defined generics, richer control flow, and broad stdlib growth stay behind bootstrap-critical work.
- Reversible later: yes, but reordering now would likely slow bootstrap progress.

## D024: Stage1 imports stay flat-root and unqualified

- Decision: `use foo;` resolves only to `<workspace-root>/foo.nq`, and imported public names enter scope unqualified.
- Alternatives considered: relative imports, nested modules, qualified imports.
- Reason chosen: this is the smallest real module graph that supports a self-hosted compiler without dragging in a package system.
- Consequences: module graphs stay simple, but namespace collisions are rejected eagerly.
- Reversible later: yes.

## D025: Structural copy replaces blanket move-only user types

- Decision: a user-defined `type` or `enum` is copy iff all of its fields or payloads are copy.
- Alternatives considered: keep all user types move-only, add a user-facing `copy` marker.
- Reason chosen: stage1 needs lists of tokens, spans, and small AST records without forcing a much larger borrow/container model.
- Consequences: some older move tests change because simple structs become copy.
- Reversible later: partially; explicit copy traits or annotations could refine this later.

## D026: Stage1 file/string/list support is builtin, not a broader stdlib family

- Decision: add only `read_file`, `write_file`, `io_err_text`, `str_len`, `str_concat`, `str_get`, `str_slice`, and builtin `list<T>` helpers.
- Alternatives considered: broader filesystem APIs, list literals, maps/sets, methods.
- Reason chosen: this is the minimum runtime surface needed to write a compiler front end in Nauqtype.
- Consequences: the runtime grows slightly, but the language avoids a broad library design commitment.
- Reversible later: yes.

## D027: Stage1 starts with a shallow selfhost front end, not a full second compiler immediately

- Decision: `selfhost/` first proves load + lex + parse + diagnose over its own tree before resolver/type-checker parity.
- Alternatives considered: wait to start selfhost until full semantic parity, or attempt a complete self-hosted compiler in one jump.
- Reason chosen: an early Nauqtype-written front end creates real bootstrap pressure and validates the stage1 surface sooner.
- Consequences: stage1 is near-self-hosting, not fully self-hosting yet.
- Reversible later: yes, by extending the selfhost compiler rather than replacing it.

## D028: The flat selfhost fact pipeline is accepted only as the stage1 semantic front-end path

- Decision: keep the current selfhost parser/resolve/typecheck pipeline as the trusted semantic front-end path for the current subset.
- Alternatives considered: rewrite selfhost now into a richer typed AST architecture, or keep extending flat facts indefinitely into every later phase.
- Reason chosen: the current flat fact pipeline has now earned trust for semantic front-end work, and rewriting it immediately would burn schedule without improving the next real bootstrap blocker.
- Consequences: the current selfhost front end remains the truth-producing semantic path, but its ownership boundary must stay narrow and explicit.
- Reversible later: partially; the implementation may evolve, but the checkpoint principle that semantic trust does not require an immediate rewrite should remain.

## D029: Post-typecheck stage1 work must consume a structured checked handoff, not raw flat facts

- Decision: stage1 borrow checking, IR lowering, and C emission must target a downstream structured checked representation built from the trusted selfhost semantic outputs.
- Alternatives considered: add borrow/IR/codegen directly on top of the current flat parser/typecheck facts, or rewrite the entire front end before starting backend work.
- Reason chosen: backend growth directly on flat facts would turn a useful semantic front end into an accidental architecture trap, while a full rewrite now would slow genuine parity work unnecessarily.
- Consequences: a new one-way handoff layer becomes mandatory before backend parity; the flat front end remains in place and is not being replaced in this checkpoint.
- Reversible later: no for this bootstrap phase; genuine parity work should not bypass the structured checked handoff.

## D030: Nauqtype becomes the active implementation language after the first self-build proof

- Decision: after the first stage1-to-stage2 self-build comparison proof, Nauqtype becomes the active implementation language for the project, and the Python compiler remains in-repo only as a frozen bootstrap/reference path during the cutover.
- Alternatives considered: continue feature work primarily in Python, revive the older Rust preference, or defer the transition until every stage0 feature is already mirrored.
- Reason chosen: the first self-build proof means the project can finally teach, exercise, and harden the language through its own implementation path instead of continuing to invest in a throwaway host-language center of gravity.
- Consequences: new active workflows should move onto the stage1 executable driver first, while Python is limited to narrow bootstrap/reference fixes until the Nauqtype-owned driver and runner fully replace it.
- Reversible later: partially; bootstrap reference code may survive for history, but the active toolchain direction should remain Nauqtype-first.

## D031: Top-level `const` starts narrow and pure

- Decision: add top-level `const` as the first live-in-the-language ergonomics feature, with `pub const` visibility through flat-root imports and a deliberately narrow v1 initializer subset.
- Alternatives considered: defer constants until list literals and match expressions, add broad compile-time evaluation immediately, or use a different declaration word.
- Reason chosen: `const` names make configuration and repeated literals easier for humans and agents to supervise, while a pure `i32` / `bool` / `str` subset gives useful value without hidden evaluation, I/O, or dependency-order complexity.
- Consequences: constants participate in checked facts, refactor plans, policy metadata, checked handoff, IR, and C emission, but const-to-const initializer references, calls, constructors, lists, borrows, and effects remain rejected for now.
- Reversible later: extensible; the keyword and declaration form should stay stable, while the initializer subset can grow through recorded milestones.

## D032: List literals start contextual and homogeneous

- Decision: add list literals V1 with `[]` and `[a, b, c]` only.
- Alternatives considered: keep only `list()`, add spreads/ranges/comprehensions immediately, or add broad mixed-element inference.
- Reason chosen: literals improve readability and proof-corpus coverage while a contextual empty-list rule and homogeneous non-empty rule keep type inference and backend lowering small.
- Consequences: `[]` requires an expected `list<T>` context; non-empty literals infer or check one element type; const list initializers, spreads, comprehensions, and ranges remain deferred.
- Reversible later: extensible; the syntax can grow by explicit milestones without changing V1 behavior.

## D033: Named arguments are supervision syntax, not evaluation-order control

- Decision: add named function arguments as `call(name: value)` for direct function calls only.
- Alternatives considered: `name = value`, defaults, overloading, mixed positional/named calls, and named constructors.
- Reason chosen: labels make calls easier for humans and agents to review, while parameter-order normalization avoids hidden source-order semantics.
- Consequences: a call is either all positional or all named; named arguments must exactly match parameter names, may appear in any source order, and are evaluated/lowered in callee parameter order.
- Reversible later: extensible, but defaults and constructor labels should require separate decisions.

## D034: Qualified calls are direct module provenance, not methods

- Decision: add `module::function(...)` as a direct call to a public function from a directly imported flat-root module.
- Alternatives considered: member calls, package paths, qualified constructors/types, and broader namespace paths.
- Reason chosen: explicit provenance helps supervised agent work without introducing receiver lookup, methods, or package-system complexity.
- Consequences: only one module qualifier is accepted, the left side resolves in the module namespace, and plain imported names keep the existing unqualified visibility rules.
- Reversible later: yes, broader paths can grow without changing this direct-call meaning.

## D035: `break` and `continue` stay minimal and loop-local

- Decision: add only `break;` and `continue;` for the nearest enclosing `while`.
- Alternatives considered: labels, valued break, loop expressions, and broader loop families.
- Reason chosen: simple loop exits improve day-to-day Nauqtype authorship while keeping control flow explicit and non-Rustlike.
- Consequences: they are valid inside nested `if`, `match`, or `let-else` only when those constructs are inside a `while`; they have no value and do not count as a `let-else` explicit exit in V1.
- Reversible later: extensible, but labels and valued loop expressions remain separate future decisions.
