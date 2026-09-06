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

## D036: `?` propagation must be evidence-and-contract, not invisible desugaring

- Decision: when `?` is implemented, start with statement-boundary `let name = result_expr?;` over exact `result<T, E>` propagation, and require the feature to surface checked propagation evidence plus a `propagates(E)` audit contract.
- Alternatives considered: cloning Rust-style expression `?`, pure desugaring to `let-else`, optional context labels only, or deferring propagation sugar indefinitely.
- Reason chosen: Nauqtype needs less wordy fallible code, but a hidden early return that does not appear in facts/review/policy surfaces would contradict the language's AI-supervision mission. Treating propagation as evidence and contract makes the source shorter while making failure paths more reviewable.
- Consequences: the initial form has no implicit error conversion, no traits, no expression-position `?`, no `option<T>?`, and no custom propagation protocols. Machine-readable propagation data must use an explicit versioned surface rather than silently changing locked JSON schemas.
- Reversible later: extensible; optional context labels, `try` blocks, `option<T>?`, and expression-position `?` can grow through separate decisions once the statement-boundary form is proven.

## D037: M23 declares the v0.1 surface stable

- Decision: after M23, the current language and stage1-owned tooling surface is the v0.1 stable baseline.
- Alternatives considered: keep accumulating syntax before declaring stability, or wait until `effects(io)` and evidence-backed `?` land before calling the current surface stable.
- Reason chosen: the compiler is self-hosted, the stage1-to-stage2 proof is standing, active workflows are Nauqtype-owned, recent syntax has evidence/refactor coverage, and the locked corpus now covers the highest-risk v0.1 ergonomics. That is enough to stabilize the baseline before the next explicit feature milestones.
- Consequences: future source-language or machine-readable contract changes should land through named milestones, examples, proof/corpus coverage, and decision records. v0.1 stability is not a package-manager, distro, or broad platform-support promise.
- Reversible later: partially; individual features can evolve through versioned contracts, but the project should treat this point as the compatibility baseline for ordinary users and future model-teaching examples.

## D038: Linux foundation before more sugar

- Decision: pause additional source-language sugar while the Linux alpha foundation is made usable from a normal shell.
- Alternatives considered: continue directly into the remaining propagation evidence surface and next syntax features, or jump straight to distro packaging.
- Reason chosen: the compiler is self-hosted and Linux-proven, but daily use should not require invoking an internal stage1 driver path directly or remembering repo-root path assumptions. A small launcher/install/checkpoint layer gives us a stable Linux workflow without pretending the project is distro-packaged.
- Consequences: `bin/nauqc`, `scripts/install_nauqtype.sh`, `scripts/make_linux_release.sh`, `scripts/check_linux_alpha.sh`, and the Linux alpha CI workflow are accepted as alpha foundation scaffolding. They do not add language semantics, runtime APIs, or packaging guarantees. Linux-facing outputs use `selfhost/build/nauqc` in the repo and `lib/nauqtype/nauqc-stage1` in copied layouts rather than the misleading `.exe` artifact name.
- Reversible later: the symlink install can be replaced by a copied install layout, tarball, `.deb`, or NauqOS integration once the release manifest is locked.

## D039: Periodic leg tests are required milestone hygiene

- Decision: add dense multi-module "leg tests" as a recurring engineering gate after every three completed milestones and before stable-surface, release-layout, or v0.x declarations.
- Alternatives considered: rely only on focused unit/golden tests, immediately add every stress program to the permanent corpus, or defer stress testing until a release candidate.
- Reason chosen: focused tests prove known behavior, but dense temporary programs expose feature-composition failures across parser, resolver, typechecker, handoff, borrow, IR, C emission, facts/review/fmt, and runtime execution. The first Linux leg test found concrete edge cases that normal coverage had not forced together.
- Consequences: stress programs should intentionally combine imports, records, enums, lists, named args, qualified calls/data, `let-else`, `?`, loops, C emission, build, and direct execution. Exposed issues should become focused regression fixtures before the stress checkpoint is closed. Temporary stress programs do not become canonical teaching corpus until the resulting edges are understood. `STRESS_LEG.md` and `scripts/run_stress_leg.sh` are the accepted M27 operating shape.
- Reversible later: the cadence can be tightened or automated once the runner has first-class stress-test support, but it should not be removed while source-language and tooling surfaces are still growing.

## D040: Evidence parity must precede the next syntax batch

- Decision: after M27, lock a combined evidence-parity fixture before adding more language syntax.
- Alternatives considered: move directly into propagation labels or field assignment, rely on the existing per-feature goldens, or treat review/facts drift as acceptable while the language is still alpha.
- Reason chosen: Nauqtype's AI-first value depends on deterministic compiler evidence. If facts, review, review-diff, change-report, policy-check, or refactor plans disagree about shipped syntax, agent-pair supervision gets false confidence even when `check` and `run` succeed.
- Consequences: M28 may fix evidence-surface bugs, but it must not introduce source syntax, runtime helpers, schema breaks, refactor apply mode, or broader policy enforcement. New evidence expectations should be added through existing versioned surfaces and locked goldens.
- Reversible later: no for the alpha path; evidence parity should remain a gate before large syntax batches.

## D041: Proof summaries are versioned evidence, not incidental logs

- Decision: upgrade the active proof summary to v2 instead of mutating the locked v1 shape in place.
- Alternatives considered: keep v1 minimal, add ad hoc log text beside the summary, or add a new proof command for detailed output.
- Reason chosen: humans and agents need faster failure triage without changing the quiet proof command stdout. A versioned JSON summary can carry phase metadata, corpus IDs, artifact paths, and deterministic content hashes while preserving the command surface.
- Consequences: `build/proof/summary.json` is now a machine-readable proof artifact, not a casual log. v1 remains documented historically, while v2 is the active summary schema. This does not add a stage4 proof chain, source-language syntax, runtime helpers, or new public commands.
- Reversible later: extensible through proof-summary v3 if the proof matrix grows, but the active shape should only change through a schema/version update.

## D042: Linux Alpha RC1 release identity is explicit and verified

- Decision: the copied Linux alpha layout carries explicit release identity through repository `VERSION`, copied `share/nauqtype/VERSION`, and generated `share/nauqtype/release.json`.
- Alternatives considered: leave version identity implicit in git history, rely only on the release directory name, or jump directly to distro package metadata.
- Reason chosen: a copied alpha layout needs enough identity for humans, agents, and future packaging checks to know what artifact they are testing without pretending the project is already a distro package.
- Consequences: `scripts/make_linux_release.sh` owns release metadata generation, `scripts/verify_linux_release.sh` validates the copied manifest, and `scripts/check_linux_alpha.sh` must smoke-test a copied release from outside the repository root. This adds no source-language syntax, runtime helper, public compiler command, or package-manager guarantee.
- Reversible later: yes; tarballs, `.deb` metadata, NauqOS integration, or richer release manifests can replace this alpha shape once packaging becomes the milestone.

## D043: Propagation labels are evidence-only provenance

- Decision: permit an optional bare identifier after an existing statement-boundary propagation operator, written `result_expr?[context_label]`.
- Alternatives considered: string labels, mandatory labels, audit-block label declarations, expression-position propagation labels, or no labels at all.
- Reason chosen: a short local label lets a reviewer see why an error is forwarded without duplicating the error contract or adding hidden control flow. Bare identifiers are deterministic, formatter-friendly, and keep provenance visible in source diffs.
- Consequences: labels are emitted as optional `context` fields on facts v2 and review v2 propagation sites. A label-only change alters the checked function signature used by review-diff and change-report. Labels do not alter `result` typing, `propagates(E)` inference, IR lowering, C emission, or runtime behavior.
- Reversible later: labels can gain policy requirements or broader text forms in a separately versioned evidence milestone; expression-position `?`, implicit conversion, and custom propagation protocols remain separate decisions.

## D044: IO subkinds are checked evidence, not effects

- Decision: expose the fixed IO subkinds `read`, `write`, `create_dir`, and `process` in versioned semantic evidence while retaining `io` as the only source-level IO audit atom.
- Alternatives considered: separate `effects(read, write, ...)` declarations, user-defined effect atoms, subkind policy enforcement, or no subkind evidence.
- Reason chosen: supervisors benefit from knowing how an `effects(io)` function touches the outside world, but splitting the declaration surface would make contracts noisier and less stable before real policy needs prove it worthwhile.
- Consequences: facts v2 annotates direct IO builtin call edges; review v2 annotates direct calls and reports transitive `inferred.io_kinds` in canonical order. Review-diff and change-report surface subkind-only behavior through existing changed-function evidence. Policy remains intentionally keyed to stable semantic IDs and coarse `effects(io)` facts.
- Reversible later: a separately versioned policy/effects milestone may add opt-in rules over these fixed subkinds, but no user-defined atoms, implicit capabilities, or effect subtyping are implied by this decision.

## D045: Milestone verification reuses fresh artifacts, final gates remain independent

- Decision: ordinary milestone closeouts run a composed verification gate that builds stage1 once, proves it once, creates one Linux release, and reuses that release for the stress leg; M37 and release candidates retain independent standalone gates plus the full suite.
- Alternatives considered: keep every closeout command fully independent, add persistent cross-run compiler caches, or reduce the final Alpha gate to the fast tier.
- Reason chosen: repeated proof and release assembly consume most milestone-closeout time, while persistent caching would make freshness harder to audit. In-process dependency-ordered reuse keeps the evidence honest and makes failures faster to locate.
- Consequences: `scripts/check_fast.sh` is not a release gate; `scripts/check_milestone.sh` writes ignored timing/failure evidence and reuses only artifacts it just produced. Standalone `check_linux_alpha.sh` and `run_stress_leg.sh` remain complete by default.
- Reversible later: the phase list can gain parallel-safe checks or artifact hashing, but persistent reuse must require an explicit freshness contract.

## D046: Field assignment is owned-local product update, not general lvalue syntax

- Decision: permit `binding.field = value;` only when `binding` is a direct owned `let mut` local of a user-defined product type.
- Alternatives considered: retain immutable record update only, permit writes through `mutref` parameters, add arbitrary nested lvalues, or wait for a broader mutable-place model.
- Reason chosen: direct owned-local updates reduce repetitive reconstruction in practical compiler/tooling code while preserving visible mutation authority and avoiding hidden aliasing or lifetime machinery.
- Consequences: field writes reject enum values, list elements, `mutref` parameters, nested paths, and arbitrary expression targets. The value still passes through ordinary type and move checks; this does not add field borrows, stored references, methods, or general assignment semantics.
- Reversible later: a future explicit mutable-place design can widen this boundary, but it must make aliasing and evidence consequences explicit rather than treating this syntax as precedent for arbitrary lvalues.

## D047: Refined patterns require an explicit fallback

- Decision: support integer literal patterns and recursively nested constructor patterns, but require any match using either form to include a wildcard or binding fallback arm.
- Alternatives considered: defer both forms, infer exhaustiveness over every refined pattern, or add guards, ranges, strings, booleans, and or-patterns together.
- Reason chosen: literal and nested cases make ordinary classification code clearer for people and agents, while a visible fallback prevents the first refined-pattern slice from claiming exhaustiveness it cannot yet prove mechanically.
- Consequences: `INT` and `-INT` patterns apply only to `i32`; nested constructors preserve their full checked pattern tree through IR and C lowering. Guards, ranges, non-integer literal patterns, and or-patterns remain deferred.
- Reversible later: a richer exhaustiveness analysis can relax the fallback rule only with explicit proof and evidence updates.

## D048: Syntax evolves through explicit authority and checked evidence

- Decision: future Nauqtype syntax follows `SYNTAX_IDENTITY.md`: local value flow stays concise, while mutation, borrowing, fallibility, effects, provenance, ownership, dependencies, and policy remain explicit and compiler-evidenced.
- Alternatives considered: grow through feature parity with established languages, accept several equivalent spellings for convenience, or postpone evidence work until after a syntax feature proves popular.
- Reason chosen: Nauqtype is intended for AI-authored software under human supervision. A feature only improves that workflow when its shorter source remains legible to people and produces deterministic facts for tools and reviewers.
- Consequences: every language proposal must document pressure, canonical spelling, semantics, authority/evidence impact, diagnostics, formatter behavior, teaching cases, migration, and acceptance evidence before implementation. Features that need hidden control flow, dependency search, conversion, or authority inference stay deferred.
- Reversible later: the SOP can be revised by a recorded decision and proof-backed examples, but not bypassed for isolated syntax additions.

## D049: Active bootstrap and testing retire Python through a C seed

- Decision: Python remains a frozen historical reference only until M38-M40 establish a Nauqtype-owned test runner and a reproducible C seed bootstrap; the active toolchain target is host `cc` plus checked-in Nauqtype and runtime sources.
- Alternatives considered: retain Python indefinitely as a convenient bootstrap, ship a platform-specific binary as the only seed, or delete Python before a replacement is proven.
- Reason chosen: an active Python dependency conflicts with Nauqtype's ownership goal, while a host-C seed keeps the unavoidable trust boundary small, reviewable, and portable on Linux.
- Consequences: no Python path may be removed until a clean checkout proves host C seed -> stage1 -> stage2 structural agreement and `nauqc test` covers active external behavior. Python implementation tests do not require one-for-one porting; their observable claims require Nauqtype cases or explicit archival rationale.
- Reversible later: a future independently verified native seed can replace the C seed, but active Python fallback must not quietly return.

## D050: Workspaces are manifest-authoritative and migration-visible

- Decision: introduce nested workspace modules only through `nauqtype.workspace.json`, absolute `::` module paths, and a manifest-derived entrypoint. Legacy flat-root projects remain a separate compatibility mode until explicitly migrated.
- Alternatives considered: infer project roots from the current directory, add relative imports, keep flat-root paths indefinitely, or add a registry/package manager first.
- Reason chosen: dependency provenance is an authority boundary in Nauqtype. A manifest-owned module graph gives people, agents, facts, policy, and locks one reproducible source of truth without adding hidden filesystem or network behavior.
- Consequences: `use` paths will be absolute inside a workspace, aliases must be explicit, duplicate module identities fail closed, and multi-segment paths are rejected in legacy flat-root mode. `WORKSPACE_CONTRACT.md` defines the exact M42/M43 boundary.
- Reversible later: extensible through explicit local dependencies and locks; relative lookup, wildcard imports, implicit re-exports, registries, and cache discovery require separate decisions.

## D051: List iteration is direct, bounded, and identity-preserving

- Decision: support `for name in list_expr { ... }` only for `list<T>`, with one immutable body-scoped binding and nearest-loop `break` / `continue`.
- Alternatives considered: an iterator protocol, range syntax, parser desugaring into user-visible helper calls, mutable loop variables, or retaining only manual index loops.
- Reason chosen: daily Nauqtype tooling needs concise collection traversal, but an open iteration protocol would introduce generic and method machinery before the language has justified either. A dedicated checked statement preserves source identity and evidence without hiding ownership behavior.
- Consequences: the iterable is evaluated once, checked as `list<T>`, and lowered through a dedicated handoff/IR node to the existing list helpers. The binding has a stable semantic ID, cannot be assigned, and does not escape the loop body. Ranges, custom iterables, loop values, implicit element borrowing, and iterator methods remain out of scope.
- Reversible later: a future protocol can generalize iteration only if its dispatch, ownership, evidence, and supervision rules are explicit; this syntax does not imply such a protocol.

## D052: Internal helpers graduate only from measured repetition

- Decision: centralize repeated pure compiler helpers only when current Nauqtype tooling has multiple concrete callers; M49 promotes five/six-part concatenation and bounded line rendering into `selfhost/text.nq` and adds no runtime surface.
- Alternatives considered: create a broad standard library, add generic collection helpers speculatively, keep private copies indefinitely, or expose convenience builtins through the runtime.
- Reason chosen: the compiler, proof runner, and evidence renderers already paid maintenance and consistency costs for these exact helpers. Other proposed helpers lacked comparable usage pressure.
- Consequences: facts, review, proof, and C emission share deterministic text construction while `selfhost/files.nq` remains the existing path authority. New helpers still require real tool or corpus use; package scripts, network APIs, and prestige modules remain deferred.
- Reversible later: helper modules can grow or reorganize when usage proves a clearer boundary, but runtime widening and generic abstractions remain separate decisions.

## D053: Expression propagation exits to a visible local boundary

- Decision: add expression-position `?` only inside `let value: result<T, E> = try { expression };`, where failure populates the local boundary instead of silently returning from the function.
- Alternatives considered: Rust-style function-scoped expression propagation, general multi-statement try blocks, implicit error conversion, or retaining statement-boundary propagation only.
- Reason chosen: nested fallible expressions become materially less wordy, while the source still names the control-flow destination and facts/review preserve every propagation site for human and agent supervision.
- Consequences: V1 requires exact error matching and direct-call operands, evaluates propagation sites depth-first and left-to-right before wrapping the final value in `Ok`, and excludes short-circuit logic and match success expressions until their lowering can preserve control flow. Local sites are checked evidence but do not enlarge function-level `propagates(...)`.
- Reversible later: multi-statement boundaries or broader expression contexts may be proposed separately, but they must preserve visible authority, deterministic evaluation, and versioned evidence rather than treating this syntax as precedent for hidden returns.

## D054: Stable Linux targets terminal and native application contracts, not feature parity

- Decision: define stability through two concrete contracts: comfortable Linux terminal tooling and practical native command-line, service, library, and explicitly bound application development. A built-in GUI toolkit and parity with another general-purpose language are not v1 requirements.
- Alternatives considered: declare the organizational alpha stable now, chase syntax breadth first, copy Rust's application model, or promise arbitrary Linux application completeness without defining required operating-system boundaries.
- Reason chosen: the compiler and supervised workflow are proven, but daily programs still lack ordinary Linux input, filesystem, process, data, interop, concurrency, and development-tool surfaces. Naming those capabilities gives release work a finite evidence contract while preserving Nauqtype's visible authority and AI-first identity.
- Consequences: M52-M61 first restore CI and foundational diagnostic/value/resource truth, then proceed through terminal runtime foundations, generics, data, FFI, bounded applications/tooling, packaging, and an independent stable gate. Runtime primitives stay narrow; conveniences prefer Nauqtype modules; every authority-bearing feature requires checked evidence and real release fixtures.
- Reversible later: individual milestones may be split or reordered when real implementation pressure demands it, but no stable claim may omit an accepted terminal/application capability without recording a narrower release contract.

## D055: Stable values carry explicit backend truth and deterministic cleanup

- Decision: M53 adds exact `i64`, canonical `is_copy` and `needs_drop` type facts, a downstream copy/move/borrow use plan, and type-directed clone/move/drop lowering before adding move-only `bytes`. Heap-backed `str` values retain source-level copy semantics through runtime reference counting; `list<T>` and `bytes` remain move-only.
- Alternatives considered: rely on process-exit cleanup, expose manual `drop`, make `str` move-only, add lifetime syntax, use a tracing garbage collector, or add binary and time APIs before value ownership is representable.
- Reason chosen: terminal tools and long-running applications need bounded resources, but Nauqtype should not make users reconstruct backend ownership rules or import Rust-like lifetime machinery. Checked value semantics keep cleanup deterministic and inspectable while preserving the concise source model already used by the selfhost compiler.
- Consequences: integer literals remain unsuffixed and default to `i32`; expected `i64` context selects `i64`, arithmetic requires exact matching integer types, and there is no implicit numeric conversion. Literal patterns and list indices remain `i32`. M55 must use a nominal duration value over `i64` nanoseconds rather than treating arbitrary integers as durations. `bytes` V1 has no literal and exposes only the minimal exercised construction/read surface. Generated cleanup must cover assignment replacement, normal exits, returns, propagation, loop control, pattern arms, parameters, aggregates, and compiler-generated temporaries. No user-visible destructor, lifetime, trait, or garbage-collector contract is introduced.
- Reversible later: additional numeric conversions, byte operations, or ownership optimizations may be proposed with checked evidence, but deterministic cleanup and exact type identity remain stable requirements.

## D056: Stage1 diagnostics report producer truth without a schema reset

- Decision: keep diagnostics JSON v1 while replacing placeholder stage1 values with producer-supplied stable codes, categories, severities, physical source paths, and UTF-8 byte spans. Span ends are exclusive, line and column are one-based, and `-1` represents the absence of a genuine source location.
- Alternatives considered: publish diagnostics v2, infer codes from message text, keep null spans until editor work, or preserve generic `NQ-STAGE1-001` for compatibility.
- Reason chosen: the existing v1 schema already permits truthful values. Continuing to emit a fabricated generic identity would undermine the supervised evidence contract, while a version bump would add shape churn without adding a field.
- Consequences: producers own diagnostic codes; text diagnostics go to stderr and JSON diagnostics remain one deterministic stdout document. Warning-only diagnostics do not fail `check`; errors and internal failures do. Empty note/help values render as `[]` and `null`. `help`, `--help`, and `-h` share one stable output, while `version`, `--version`, and `-V` print exactly `nauqc <version>` from the checked compiler identity. The no-argument bootstrap mode remains unchanged.
- Reversible later: diagnostics v2 may add genuinely new structured fields, but locked v1 values cannot return to placeholder identity or location evidence.

## D057: M54 keeps Linux bytes and authority explicit

- Decision: retain `str` as an immutable byte-indexed value that may contain non-UTF-8 data, use explicit locked local dependencies for the first `nauqtype.std` library proof, and expose Linux input/filesystem authority through narrow fallible primitives with stable `io_err` accessors and checked IO subkinds.
- Alternatives considered: silently redefine `str` as UTF-8, add an implicit bundled `std` search path, introduce a workspace/package v2 before versions are used, represent paths as lossy text, or let filesystem errors remain message-only.
- Reason chosen: the current value model can preserve every Linux path byte except NUL, while NQType Libraries can own UTF-8 and lexical-path policy in ordinary Nauqtype. Explicit path dependencies and content hashes already provide reproducible provenance; hidden search and premature package versioning would add authority without solving the M54 runtime boundary.
- Consequences: string indexing remains byte-based, OS-bound strings reject embedded NUL, public Linux path helpers use `/` only, and UTF-8 validation remains explicit library work. `std` is a conventional declared alias for workspace `nauqtype.std`, not a prelude or reserved resolver rule. M54 keeps `io_err` as the fallible carrier but adds stable kind, operation, path, secondary-path, and OS-code accessors plus fixed evidence subkinds. Qualified type annotations remain deferred, so official library nominal types use a collision-safe `Nq` prefix in V1. `check` accepts non-entry library modules; executable commands still require `main`.
- Reversible later: a versioned package contract, bundled library resolution, qualified type annotations, validated text type, or stronger path authority may be added through separate evidence-backed decisions, but must not reinterpret these byte, error, or dependency contracts silently.

## D058: Correct source semantics before extending the Linux surface

- Decision: M54.7 repairs Astra F01/F02/F04 to the existing grammar and match
  contract. Left-associative operators select the rightmost root at each
  precedence level; equality is below relational comparison. Every match
  uses source-ordered conditions with one scrutinee evaluation, including
  fallback-first and duplicate-specific arms. Unreachable later arms are not
  a new source rejection.
- C spelling is a private backend encoding, not semantic identity. Escape
  source `_` as `_u`, `:` as `_c`, and any other non-alphanumeric byte as
  `_x<decimal>z`. Prefix user members with `nqf_`, nominal C types with
  `NQ_User__`, and nominal type-mangle leaves with `named__`. Encoded source
  atoms contain no double underscore, reserving that separator for recursive
  generic type structure. Function, constant, and binding prefixes remain
  distinct. Runtime-native records, generic carriers, and builtin members
  retain their ABI spelling.
- Alternatives considered: retain wrong output for bootstrap similarity,
  reorder/reject legal match arms, add a blacklist of C keywords, or rewrite
  the whole parser. None fixes the confirmed behavior as narrowly as restoring
  source semantics and encoding all user identities consistently.
- Consequences: add spec-derived Nauqtype execution/cleanup regressions, refresh
  the generated seed through an audited fixed point, and keep proof
  normalization unchanged. These repairs add no syntax, ownership rule,
  runtime API, or machine-readable schema. The remaining audit findings stay
  open in `AUDIT_REMEDIATION.md` ahead of M55 feature growth.
- Reversible later: a measured IR optimization may replace the condition chain
  with a switch only when it preserves first-match priority and every cleanup
  edge. Any C encoding revision requires another explicit seed transition,
  not altered comparison rules that erase semantic differences.

## D059: Source Contract Validity Is Shared By Every Checked Command

- Decision: M54.8a extracts and validates the existing fixed audit grammar once
  per analyzed input and gives review renderers those validated declarations,
  resolved propagation targets, and the validation summary. Compilation,
  facts, review, diffs, policy targets, and refactor plans share acceptance.
- Reason chosen: a source program cannot be trustworthy for `build` or
  `facts` while the same declared contract is rejected by `review`. Output
  purpose is not a different semantic policy.
- Consequences: the driver owns structured diagnostic emission. Warnings are
  nonfatal and emitted once per input; successful JSON shapes stay unchanged.
  A call-containing body's direct-only mutation analysis cannot justify a
  negative overdeclaration claim, so only call-free bodies receive that
  warning. Missing directly inferred mutation remains an error. Shared
  completeness checks reject missing value-plan coverage in tooling too.
- Compatibility boundary: fixed-grammar enforcement and previously
  review-only contract errors now apply consistently. The M54.7 seed remains
  pinned if it bootstraps the new source and the fixed point passes. M54.8b
  must separately version evidence changes for absent declarations, partial
  mutation coverage, and failed or unprovided inputs. This is not a silent
  schema correction or a claim that all audit findings are closed.

## D060: Review Coverage Is Versioned And Explicitly Partial

- Decision: opt-in review v3 distinguishes absent/declared audits and derives
  direct mutable-parameter writes from checked binding identities. Every
  function exposes the same partial lower-bound scope and ordered uncovered
  builtin/local/imported call-write categories.
- Reason: a name-only assignment can target a shadowing local, and an empty
  direct-write list cannot prove absence of call-mediated mutation. Evidence
  must not turn either limitation into a completeness claim.
- Compatibility: review v1/v2 success output and all source-contract
  acceptance remain unchanged. v3 is successful-output-only and exclusive to
  review. Missing checked identity fails with NQ-INTERNAL-012, not a guess.
- Boundary: no new syntax, ownership, effects, or runtime behavior. b1 proves
  emitter/golden coherence only. Checked call summaries, validation migration,
  standing standards-schema enforcement, and diff/change failure envelopes
  require their own reviewed follow-up; no general JSON engine is added here.

## D061: Checked Mutation And Versioned Failure Evidence

- Decision: source-contract validity uses one checked-ID direct/builtin/call
  may-write analysis after handoff, with canonical parameter mapping and a
  finite recursive fixed point. Known omissions are errors; absence warnings
  require complete coverage. Failed source or checked phases do not feed
  invalid data into later compiler passes.
- Evidence: opt-in review v4 reports the precise checked-parameter scope;
  legacy review v3 remains an explicitly partial direct-write lower bound.
  Complete does not mean pure, reachable, or ownership-complete.
- Compatibility: keep earlier successful schemas unchanged. Change-report v3
  distinguishes absent/checked/failed policy and malformed policy. Source
  failures in all supported diff/change formats deliberately migrate to the
  seven-field evidence-error v1 envelope with requested-format identity.
- Verification: an owned bounded schema profile checks all repository schemas
  and negative coherence fixtures. Unsupported JSON/profile features reject;
  this is not a general JSON library or full standards-conformance claim.
- Diagnostics: producer deduplication uses the complete diagnostic identity.
  Distinct same-span errors survive, and unsupported non-copy list_get uses
  NQ-TYPE-044 with its full builtin token span and actionable help.
- Boundary: no syntax, ownership, effect, runtime, or Python feature growth.
  M54.9 integer/allocation semantics and M54.10 provenance remain separate.

## D062: Defined Integer And Allocation Boundaries

- Decision: both exact integer widths wrap for addition, subtraction,
  multiplication, and negation. Division truncates toward zero and fails
  deterministically for zero or minimum-value divided by `-1`. Constant
  evaluation obeys the same rules and boolean short-circuiting, with source
  diagnostics for evaluated invalid division.
- Lowering: dynamic operands are materialized in order once before unsigned
  C arithmetic helpers. Constants fold typed IR into bounded-size strict C11
  literals using bounded-limb arithmetic, not host signed overflow or nested
  duplicating macros.
- Allocation: validate size, growth, terminators, and element products before
  arithmetic can overflow. Infallible paths fail with fixed stderr/exit status;
  fallible IO reserve paths return allocation-free existing `io_err` values.
  Imported strings and generated lists obey the same limits as native ones.
- Evidence: exercise runtime-fed arithmetic at both widths under optimization
  and UBSan, constant diagnostics, generated containers, and injected size/OOM
  limits. Private test macros do not become runtime builtins or release flags.
- Boundary: no new syntax, numeric conversion, ownership, runtime builtin,
  exception, or unwinding promise. M54.10 owns provenance; M55/F14 remain open.

## D063: Captured Provenance And Derivation Evidence

- Dependency locks explicitly migrate to `workspace-lock/v2`, using framed
  sorted paths and raw captured source bytes. Parsing, routing, and evidence
  consume the validated capture. Root source loading is unchanged.
- Legacy facts/change formats retain successful shapes and compatibility
  meanings. Opt-in facts v4 and change-report v4 expose authoritative framed
  source identities. External consumers migrate their own locks explicitly.
- Seed v2 checks exact historical source inventory and pinned C/runtime;
  generator identity records are not signatures. The seed gate checks both
  historical-source reproduction and current stage1/stage2 structural C,
  reusing an emission only under explicit source/input identity equality.
- Builder-only cache v2 binds captured inputs, emitted artifacts, compiler
  identity, target, and flags. Full milestone attestations bind the reviewed
  candidate and proof/release outputs; disclosed completion deltas are
  restricted to nonpackaged status documents.
- Proof-summary v3 uses SHA-256 objects and null for unproduced artifacts or
  unperformed comparisons. Keep the existing direct structural normalizer.
- Scope is a trusted Linux host, not hostile-owner tamper resistance or an
  atomic concurrent-filesystem transaction. No new language/runtime API,
  generic JSON engine, transitive dependency solver, or stage3/stage4 chain.
