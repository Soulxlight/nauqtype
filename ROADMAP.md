# Nauqtype Roadmap

## MVP Definition

Nauqtype "compiles and runs code" when all of the following are true:

- a `.nq` program is lexed and parsed successfully
- names resolve
- a meaningful subset type-checks
- move/borrow rules are enforced for the supported subset
- the compiler emits readable C
- the emitted C is compiled by a system C compiler
- the produced executable runs successfully
- example programs and tests cover the path

## Bootstrap Terms

- `stage0`: the frozen Python bootstrap/reference compiler
- `stage1`: a compiler semantic front end and active executable driver written in Nauqtype and built by stage0
- `semantic near parity`: stage1 can load, parse, resolve, and type-check its own source tree for the trusted subset, with no retained limitation path used by the in-repo `selfhost/` tree
- `genuine parity`: stage1 adds borrow checking and backend work closely enough to participate in a real self-build proof chain
- `architecture checkpoint`: the current flat selfhost fact pipeline is accepted as the semantic front-end path, but backend work must target a downstream structured checked handoff instead of raw flat facts

## Working Vertical Slice

The first real success target is:

- one source file
- `fn main() -> i32`
- local bindings
- arithmetic and boolean expressions
- structs
- enums
- `result` / `option`
- `if`
- bootstrap-track `while`
- `match`
- explicit `return`
- `print_line`
- minimal move / borrow checking

## Milestones

### M0: Locked Design

- write research memo
- write spec, grammar, architecture, decisions, risks
- freeze v0.1 scope

### M1: Scaffold And Diagnostics Core

- create bootstrap compiler package layout
- add shared span and diagnostic types
- add CLI shape

### M2: Lexer And Parser

- tokenize the v0.1 grammar
- parse items, statements, expressions, patterns, and types
- add parser golden tests

### M3: Resolution And Type Checking

- resolve top-level and local names
- type-check functions, structs, enums, calls, returns, and matches
- emit stable semantic diagnostics

### M4: Minimal Ownership Enforcement

- classify copy vs move types
- detect use-after-move
- validate `ref` / `mutref` rules for calls

### M5: IR And C Emission

- lower checked programs to a small typed IR
- emit readable C
- include tiny runtime support

### M6: End-to-End Execution

- compile generated C with a detected system C compiler
- run example programs
- add integration coverage

### M7: Lints And Hardening

- `unused_mut`
- discarded `result`
- stabilize diagnostic wording

### M8: AI Contracts Alpha

- add fixed-shape `audit` blocks on functions
- infer `mutates(...)` from direct write-through `mutref` parameters
- infer `effects(print)` through the single-file call graph
- add deterministic `review` JSON output

### M9: Bootstrap Stage1

- activate acyclic imports for one workspace root
- then add file input as `result<str, io_err>`
- then add builtin `list<T>`

Status:

- done in the current bootstrap compiler
- `selfhost/` now exercises the stage1 surface by loading, lexing, shallow-parsing, resolving top-level/import facts, resolving a first body-level slice, and diagnosing its own module graph

### M10: Semantic Near Parity

- extend the Nauqtype stage1 front end beyond the first resolver and value-flow slices
- add trusted-subset stage1 body-level semantic parity
- differential-test stage0 vs stage1 by accept/reject family
- require the in-repo `selfhost/` tree to pass without `stage1 limitation` diagnostics
- keep the language core frozen unless a concrete bootstrap blocker requires otherwise

Status:

- done for the current semantic front-end milestone
- backend work has moved downstream of the structured checked handoff
- semantic near parity is now the trusted front-end checkpoint for the first self-build proof

### M11: Diagnostics JSON v1

- add `check --diagnostics json`
- ship a stable versioned JSON schema
- snapshot-test representative warning and error payloads

### M12: Flat-Architecture Checkpoint

- accept the current flat selfhost parser/resolve/typecheck pipeline as the trusted semantic front-end path
- explicitly forbid stage1 borrow/IR/codegen growth directly on raw flat facts
- define the structured checked handoff contract required for downstream genuine-parity work

Status:

- done as an architecture checkpoint
- the next parity work starts with the structured checked handoff, not direct backend work on flat facts

### M13: Genuine Parity Backend Path

- build the structured checked handoff from trusted semantic outputs
- harden the checked handoff for backend consumers
- add stage1 borrow checking
- add stage1 IR lowering
- add stage1 C emission

Status:

- done on the current trusted subset
- borrow checking now runs on the structured checked handoff
- IR lowering now runs on the structured checked handoff
- C emission now runs on the structured IR path

### M14: First Self-Build Proof

- run stage0 on a copied selfhost workspace to emit stage1 `build/main.c`
- compile the emitted stage1 C into a stage2 executable
- run the stage2 executable on the same copied workspace to emit stage2 `build/main.c`
- compare stage1-emitted vs stage2-emitted output by normalized structural C
- also require matching proof smoke behavior: success exit, expected stdout, no `stage1 limitation`, and no `stage1 c error`

Status:

- done for the first copied-selfhost target
- the proof reuses the copied-workspace smoke, emitted-C compile/run helper, and shared structural C normalization
- stage1 and stage2 now match on normalized structural C plus smoke behavior for the in-repo copied selfhost workspace
- broader proof hardening and any wider proof targets remain explicit future work, not implied by this first checkpoint

### M15: Nauqtype-Owned Driver Cutover

- freeze `compiler/`, `scripts/`, and the Python-heavy harness as bootstrap/reference code
- turn the selfhost executable into the active compiler driver
- first slice: `check` and `emit-c`
- second slice: `review`
- third slice: `build` and `run`
- keep the no-arg copied-selfhost proof path intact while the executable driver grows

Status:

- done for the active driver slice
- the stage1 executable now owns `check`, `emit-c`, `review`, `build`, and `run`
- the legacy no-arg selfhost path is preserved for the copied-selfhost proof flow
- the current `build` / `run` slice still resolves the pinned Zig toolchain and `stdlib/runtime.c` from the repo-root bootstrap layout

### M16: Nauqtype-Owned Proof And Corpus Runner

- replace the active Python proof/test orchestration with a Nauqtype-owned runner
- keep the copied-selfhost proof as a standing serial gate on Windows
- run the locked example corpus through emit/compile/run from the Nauqtype-owned runner
- preserve normalized structural C plus smoke-behavior comparison

Status:

- done for the active proof/corpus runner slice
- the Nauqtype-only transition loop is closed for active driver and proof/corpus orchestration
- the stage1 driver now owns the combined transition gate as `prove`
- the stage1 driver now owns the copied-selfhost proof gate as `prove-selfhost`
- the stage1 driver now owns the locked example corpus gate as `prove-corpus`
- `prove-corpus` runs the locked examples through `emit-c`, `build`, and `run`, compares normalized structural C across driver paths, and checks smoke behavior
- the current Python proof/corpus harness remains only as frozen bootstrap/reference coverage until a later archival cleanup pass

### M17: AI-First Review Surfaces

- extend `review` without breaking v1 consumers
- add stable semantic identities for functions and call sites
- expose call references and call graph edges for agent-pair workflows
- add a standalone semantic facts export for definitions, references, and call graph edges
- distinguish declared audit data from checked compiler inference
- add `review-diff` after the v2 identity surface is stable
- add plan-only semantic rename refactoring
- add advisory ownership/review policy sidecars

Status:

- done for the pre-language tooling spine
- `review --format v2` now emits stable function/call identities, references, call graph edges, and evidence fields
- `review-diff` now emits deterministic semantic changes over stable function identities and call graph edges, with v2 evidence metadata available without breaking v1
- `facts` now emits stable definitions, references, and call graph edges for checked programs
- `facts` v1 is now locked by a versioned schema, golden fixture, and representative selfhost-module smoke check
- `facts --format v2` preserves v1 and adds explicit `declared` / `checked` / `builtin` / `unresolved` evidence fields
- full-tree `facts selfhost/main.nq` is now bounded under the Windows 240-second gate
- named-argument labels now appear in checked facts v2 and participate in parameter `refactor-rename` plans across local and imported calls
- `change-report --format v1` now combines semantic diff evidence, optional policy status, and diagnostics for supervised review
- `refactor-rename` emits deterministic JSON edit plans and never mutates files; checked field definitions, field uses, and named-argument labels are now part of the supported rename surface
- `policy-check` validates `nauqtype.policy.json` v1 sidecars against checked semantic facts, and the root sidecar now covers high-risk selfhost compiler surfaces
- `prove` now includes the AI tooling confidence fixtures for facts, review, review-diff, change-report, refactor plans, policy-check, and formatter-lite
- no semantic language features, Rust-like lifetime expansion, or broader borrow semantics were included in this tooling milestone

### M18: Live-In-The-Language Ergonomics Batch

- add only the language features that make day-to-day Nauqtype authorship materially better
- keep control flow explicit and avoid hidden failure paths
- ship canonical Nauqtype examples as future teaching material for each feature
- differential-test every semantic widening against a concrete blocker

Status:

- in progress
- started after the completed pre-language AI tooling spine
- top-level `const` is done for the narrow stage1-owned `i32` / `bool` / `str` pure-initializer subset, with canonical example and stage1 driver coverage
- list literals are done for the narrow stage1-owned homogeneous `list<T>` subset, including empty literals in expected `list<T>` contexts
- `match` as an expression is done for exhaustive value-producing arms with exact arm-result agreement
- narrow `let-else` is done for `Some(name)` and `Ok(name)` guard bindings with explicit-return `else` blocks
- formatter-lite is done as an output-only / `--check` trusted-subset formatter, not a full AST-preserving formatter
- Batch B is done for named function arguments, direct module-qualified function calls, and minimal nearest-`while` `break` / `continue`
- named arguments normalize to parameter order, qualified calls are module-provenance function calls only, and loop control stays statement-only with no labels, values, methods, or package-path expansion
- the first tiny Batch C slice is done for direct `module::Type` struct literals and `module::Variant` enum constructors/patterns from directly imported flat-root modules
- Batch D is done for copy-only record update with explicit `Type { from base, field: value }` provenance; broad field assignment remains deferred

### M19: Alpha Stabilization And Supervised Workflow

- freeze language growth while the current self-hosted toolchain is made release-shaped
- treat machine-readable outputs as compatibility contracts: diagnostics JSON, facts v1/v2, review v2, review-diff v1/v2, change-report v1, refactor plans, policy-check, and policy sidecars
- add a canonical supervised-change fixture pair that exercises `check`, `facts`, `review`, `review-diff`, `change-report`, `policy-check`, and plan-only `refactor-rename`
- add deterministic goldens for that workflow without adding a new public command
- include the supervised workflow in the stage1-owned `prove` gate

Status:

- done for the current alpha checkpoint
- no source-language syntax, runtime helpers, CLI commands, borrow semantics, IR/C changes, or package/module expansion were added
- `prove` now checks the supervised evidence loop alongside selfhost proof, corpus proof, existing tooling goldens, policy validation, refactor plans, and formatter-lite

### M20: Proof Hardening Before Batch D

- widen proof confidence before the next semantic language batch
- add deterministic proof summaries and better failure localization where useful
- expand corpus/proof coverage around stabilized examples and evidence workflows
- keep stage3/stage4-style proof expansion separate from ordinary language-feature work

Status:

- done for proof summary v1
- `prove`, `prove-selfhost`, and `prove-corpus` keep their existing quiet success stdout
- each proof command now writes `build/proof/summary.json` using stable phase IDs and versioned proof-summary schemas
- summaries are written on success and failure, with `failed_phase` identifying the first failed proof phase
- the locked corpus is guarded so every runnable canonical example under `examples/` participates in `prove-corpus`
- no source-language syntax, runtime helpers, CLI flags, new commands, stage3/stage4 proof chain, or Batch D feature work was added

### M21: Formatter And Teaching Corpus Hardening

- harden formatter-lite as a teaching-corpus gate before adding more syntax
- keep formatter behavior output-only / `--check`; no write mode until comment preservation is safe
- make every canonical example source participate in stage1-owned proof checks, including helper-only modules that are not runnable corpus entries
- use this milestone to make future LLM training material boringly consistent instead of merely pretty

Status:

- done for the current formatter-lite teaching-corpus checkpoint
- `prove` now formatter-checks every `examples/*.nq` file, not just runnable corpus entries
- helper-only modules such as `batch_b_helper`, `multi_file_helper`, and `qualified_data_helper` are part of the active stage1 proof gate
- `FORMATTER.md` documents the canonical formatter-lite contract: output-only / `--check`, four-space brace indentation, LF output, no tabs, no file mutation, and fail-closed unsupported cases
- no parser, resolver, typechecker, borrow, IR, C emission, runtime, or source-language behavior changed

### M22: Evidence And Refactor Coverage For Recent Syntax

- extend semantic evidence and supervised refactor planning across newer syntax that already exists
- focus first on direct qualified data names and copy-only record update provenance
- keep default v1 outputs stable; add new evidence only through existing v2/versioned surfaces
- do not add mutation/apply mode for refactors

Status:

- done for the current recent-syntax evidence checkpoint
- facts v2 now distinguishes explicit record-update field overrides from inherited fields using checked `field_init` and `record_update_inherit` references
- inherited record-update fields are evidence-only and are skipped by plan-only refactor edits because no field label exists in source
- `refactor-rename` now supports stable variant constructor IDs, including direct module-qualified constructor and pattern references
- facts v1 and existing refactor output shape stayed compatible; no source-language behavior changed

### M23: Surgical Helpers And Proof Confidence

- centralize duplicated pure-Nauqtype helpers where active tooling or canonical examples already need them
- prefer ordinary Nauqtype modules over new runtime builtins
- widen proof confidence without starting a stage3/stage4 self-build chain
- keep package systems, broad OS APIs, prestige stdlib growth, and Rust-like ownership expansion deferred

Status:

- done for the v0.1 stable-surface checkpoint
- M23-A is done: shared `text.nq` helpers now own `i32_to_str`, `bool_text`, `str_starts_with`, `str_ends_with`, and string/i32 list containment
- duplicate private helper definitions were removed from active selfhost modules that needed those helpers
- the new import edges from `borrow`, `c_emit`, `facts`, `resolve`, and `review` are covered by the selfhost run and `prove`
- M23-B is done: the locked corpus now covers multi-module qualified call chains, nested `break` / `continue` inside `if` within `while`, and record update over a computed owned base value
- M23-C is done: the current v0.1 language/tooling surface is stable; future growth resumes through explicit milestones and proof-backed examples

### M24: `effects(io)` Audit Atom

- add `io` as the second fixed effect atom after `print`
- cover `read_file`, `write_file`, `create_dir_all`, and `run_process`
- extend review inference and docs without opening user-defined effect atoms
- keep this as an audit/tooling milestone before propagation sugar

Status:

- done
- `io` is now a fixed audit effect inferred from `read_file`, `write_file`, `create_dir_all`, and `run_process`
- stage1 review and the bootstrap reference both understand `effects(io)` so audited selfhost sources can carry truthful file/process effects
- user-defined effect atoms remain deferred

### M25: Evidence-Backed `?` Propagation

- add statement-boundary `let name = result_expr?;` only
- require exact `result<T, E>` to `result<U, E>` propagation with no implicit conversion
- add `propagates(E)` as an audit-contract clause inferred from `?` sites
- expose checked propagation sites through an explicit versioned facts/review/change-report surface
- keep expression-position `?`, `option<T>?`, optional context labels, and `try` blocks deferred

Status:

- done
- statement-boundary `let name = result_expr?;`, exact error typing, `propagates(E)` audit validation, diagnostics, and locked corpus coverage are implemented
- facts v2 now exports checked propagation-site references, review v2 exports propagation contracts/sites, and change-report v1 reports added/removed propagation contracts
- design direction is locked by `PROPAGATION.md` and D036

### M26: Linux Alpha Foundation

- pause additional language sugar while the compiler becomes comfortable to use from a normal Linux shell
- keep this as launcher/install/release scaffolding around the existing stage1 driver, not a source-language milestone
- add a repo-local `nauqc` launcher that hides the internal stage1 driver path from daily use
- add a conservative local install path and a Linux alpha verification gate
- document what is alpha-ready now versus what is still required for distro packaging

Status:

- done
- the active repo-local stage1 driver is now built as `selfhost/build/nauqc`; Linux-facing release/install outputs no longer use the misleading `.exe` artifact name
- `bin/nauqc` wraps the active stage1 driver and normalizes user paths while running from the repository root, or from the copied alpha layout when `lib/nauqtype/nauqc-stage1` is present
- `scripts/install_nauqtype.sh` installs a symlink into `$HOME/.local/bin` or `$PREFIX/bin`
- `scripts/make_linux_release.sh` creates a copied alpha layout with the launcher, internal stage1 driver, runtime files, schemas, examples, and docs
- `scripts/check_linux_alpha.sh` runs the bootstrap rebuild, repo-local smoke checks, the stage1-owned `prove` gate, copied-layout creation, and copied-launcher smoke checks
- `.github/workflows/linux-alpha.yml` gives clean-checkout Linux coverage for the same alpha gate

### M27: Stress-Leg Edge Cleanup

- promote periodic multi-module stress programs into the normal milestone process instead of relying only on focused unit/golden tests
- run a "leg test" after every three completed milestones, and before any stable-surface declaration, Linux release-layout checkpoint, or v0.x release
- keep these programs intentionally dense: imports, records, enums, list literals, `let-else`, `?`, loops, qualified calls/data, named args, review/facts/fmt, C emission, build, and runtime behavior
- do not treat temporary leg tests as permanent corpus additions until the exposed edges are understood and reduced to focused fixtures

Status:

- done
- the first Linux leg test compiled and ran end-to-end after reducing two edge shapes, which makes the remaining work concrete rather than speculative
- qualified enum constructors inside `match` expressions now participate in exhaustiveness the same way statement `match` already does
- nested qualified function calls used directly as call arguments now stay positional instead of being misread as named arguments
- review/facts/change-report propagation evidence is aligned with the M25 versioned evidence surface
- `STRESS_LEG.md` documents the cadence, temporary-program policy, checklist, and reduction rule
- `scripts/run_stress_leg.sh` creates a dense temporary multi-module workspace and runs check, review v2, facts v2, fmt, emit-c, build, and direct runtime execution
- the first stress-program findings were reduced into focused driver regressions; the dense runner remains periodic hygiene, not a fast-test replacement

### M28: Evidence Parity Lock For Current Syntax

- lock deterministic evidence coverage for the currently shipped syntax families before adding more language surface
- require facts v2, review v2, review-diff v2, change-report v1, policy-check, and refactor-rename to agree on stable semantic identities where each surface applies
- cover recent syntax together: top-level const, list literals, match expressions, let-else, named arguments, qualified calls/data, break/continue, copy-only record update, `effects(io)`, and statement-boundary `?`
- keep facts v1 and existing JSON schemas compatible; add only golden coverage and bug fixes where current evidence is already supposed to be known

Status:

- done
- no new source-language syntax, runtime helpers, public commands, or schema versions are part of this milestone
- combined evidence-parity fixtures and goldens now cover facts v2, review v2, review-diff v2, change-report v1, policy-check, and refactor-rename for the shipped syntax surface
- review-diff and change-report now use the same resolved builtin and variant call-edge identities as review v2/facts v2
- full suite, stage1 `prove`, Linux alpha, and stress-leg gates passed before closure

### M29: Proof Confidence Matrix v2

- improve proof summaries with richer phase IDs, artifact hashes, corpus IDs, and better failure localization
- keep `prove`, `prove-selfhost`, and `prove-corpus` stdout stable unless an explicit compatibility decision says otherwise
- add a versioned proof-summary v2 schema instead of silently changing the locked v1 contract
- keep this as proof observability only: no stage4 proof chain, source-language syntax, runtime helpers, or public command expansion

Status:

- done
- proof-summary v2 is now the active proof evidence shape, while v1 remains historical/compatible
- summaries now include richer phase metadata, first-failure localization, corpus IDs, preserved proof artifacts, and deterministic content hashes
- `prove`, `prove-selfhost`, and `prove-corpus` stdout stayed stable
- no stage4 proof chain, source-language syntax, runtime helpers, or public command expansion were added

### M30: Linux Alpha RC1

- make the copied Linux layout smoke-test outside the repository root
- lock release manifest accuracy against the copied alpha layout
- add explicit version/release identity for the alpha layout and generated artifacts
- keep this as release-readiness scaffolding, not distro packaging or language growth

Status:

- done
- the release layout now carries a repository `VERSION`, copied `share/nauqtype/VERSION`, and deterministic `share/nauqtype/release.json` identity as `nauqtype-0.1.0-alpha.1`
- `scripts/verify_linux_release.sh` validates executable placement, runtime files, docs, schemas, tracked examples, release identity, and generated-artifact exclusions against the copied layout
- `scripts/check_linux_alpha.sh` now smoke-tests a copied release from a temporary project outside the repository root, proving the launcher/runtime path does not depend on the source checkout cwd
- no distro packaging, source-language syntax, runtime helpers, public commands, or proof-chain widening were added

### M31: Stress-Leg 2

- run the next dense cross-feature leg after M28, M29, and M30
- reduce every finding into focused fixtures before closing the milestone
- update `STRESS_LEG.md`, roadmap status, and any relevant deferred-boundary notes from the findings
- keep temporary stress programs separate from canonical teaching corpus until findings are understood

Status:

- done
- the dense stress runner now replays the same cross-feature program through both the repo-local launcher and a copied Linux Alpha RC1 release launcher outside the repository root
- the leg covered check, review v2, facts v2, change-report v1, formatter-lite, C emission, build, and runtime behavior across imports, record update, qualified calls/data, list literals, `let-else`, `?`, and loop control
- no new compiler findings were exposed, so no focused regression fixtures were required for this checkpoint
- this remains milestone hygiene, not a permanent teaching-corpus entry or stage3/stage4 proof expansion

### M32: Teaching Corpus v1

- organize canonical examples into lessons, evidence demos, negative diagnostics, and runnable corpus entries
- keep formatter-lite as the gate for teaching examples
- make the corpus useful for future model training and human onboarding without growing source-language semantics
- keep runnable corpus entries connected to `prove-corpus`

Status:

- done
- the root `TEACHING_CORPUS.md` now groups runnable examples into beginner, feature, and evidence-workflow lessons
- helper-only modules are documented separately
- all `.nq` files are locked into the corpus index and verified by `tests/test_teaching_corpus.py`
- formatter-lite and `prove-corpus` integration remained unchanged and enforced

### M33: Propagation Context Labels

- add optional labels for statement-boundary `?` sites so propagation evidence can say why an error is forwarded
- keep exact error typing, `propagates(E)`, and evidence-backed supervision intact
- do not add expression-position `?`, `try` blocks, implicit error conversion, `option<T>?`, or custom propagation protocols

Status:

- done
- statement-boundary propagation now accepts an optional bare identifier label as `?[context_label]`
- labels are preserved as optional `context` evidence on facts v2 and review v2 propagation sites without changing unlabeled output shapes
- label-only changes participate in review-diff and change-report function-change detection
- exact error typing, `propagates(E)`, lowering, and runtime behavior remain unchanged
- no expression-position `?`, `try` blocks, implicit conversion, `option<T>?`, or custom propagation protocols were added

### M34: Effect Evidence Granularity

- keep source-level `effects(io)` as the declared audit atom
- expose checked IO subkinds in evidence: read, write, create-dir, and process
- keep user-defined effects deferred
- make review/facts/change-report evidence more precise without changing source-language audit syntax

Status:

- planned

### M35: Field Assignment V1

- add `binding.field = expr;` only for owned mutable local product types
- reject enum fields, list elements, mutref-param field assignment, nested field assignment, and arbitrary assignment targets
- route through parse, resolve, typecheck, handoff, borrow, IR, C emission, facts/review where relevant, and proof corpus coverage
- keep field borrows, stored refs, methods, and broader mutation semantics deferred

Status:

- planned

### M36: Literal And Nested Constructor Patterns

- add simple literal patterns and nested constructor patterns with conservative exhaustiveness rules
- cover parser, typecheck, handoff, IR, C emission, facts/review, diagnostics, and examples
- keep guards, ranges, or-patterns, implicit fallthrough, and broad pattern language work deferred

Status:

- planned

### M37: v0.2 Supervised Alpha Gate

- require full suite, `prove`, Linux alpha gate, stress leg, schemas, docs, policy sidecar, release layout, and teaching corpus all green
- call the next surface stable only after machine-readable evidence and release artifacts agree
- keep this as the v0.2 supervised alpha checkpoint rather than a feature milestone

Status:

- planned

## Feature Ordering

Features required before first success:

- lexer
- parser
- diagnostics
- resolution
- type checker
- move/borrow checker
- C emitter
- runtime support
- executable runner

Features explicitly not required before first success:

- user-defined generics
- methods
- loop families beyond bootstrap `while`

## v0.2+ Candidates

- user-defined generics
- methods / `impl`
- `for`
- labeled or valued `break` / `continue`
- propagation sugar beyond statement-boundary evidence-backed `?`
- typed holes / repair obligations
- richer standard library
- stronger borrow analysis
- direct native backend exploration
- richer module/package tooling beyond flat-root imports

## Testing Milestones

- M2: lexer and parser tests
- M3: resolver and type tests
- M4: borrow tests
- M5: C emission goldens
- M6: full example execution tests
- M7: diagnostic and lint snapshots

## Diagnostics Milestones

- lexer spans present at M1
- parse diagnostics stable by M2
- type and resolve diagnostics stable by M3
- borrow diagnostics stable by M4
- lint diagnostics added by M7
- diagnostics JSON v1 added by M11

## Scope Freeze Rule

After M0, changes to core syntax or semantics require:

- a recorded decision entry
- a stated blocker or contradiction
- a stated impact on implementation and docs

## Backend Boundary

The current flat selfhost fact pipeline is allowed to own semantic front-end work for the trusted subset.

It is not allowed to own:

- stage1 borrow checking
- stage1 IR lowering
- stage1 C emission

Those phases must consume the structured checked handoff defined after the semantic near-parity checkpoint.
