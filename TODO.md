# Nauqtype TODO

## Documentation

- [x] Write `RESEARCH_MEMO.md`
- [x] Write `DECISIONS.md`
- [x] Write `RISKS.md`
- [x] Write `SPEC.md`
- [x] Write `GRAMMAR.md`
- [x] Write `ARCHITECTURE.md`
- [x] Write `ROADMAP.md`
- [x] Write `DEFERRED.md`
- [x] Keep docs aligned with implementation as the compiler lands
- [x] Add `README.md`
- [x] Add `LICENSE`
- [x] Write `AI_CONTRACTS.md`
- [x] Write `BOOTSTRAP_STAGE1.md`
- [x] Write `SELFHOST_HANDOFF.md`

## Compiler Scaffold

- [x] Record and justify the Python bootstrap fallback for the current workspace
- [x] Create `compiler/` phase directories
- [x] Add CLI entrypoint
- [x] Add shared span and diagnostics infrastructure
- [x] Add reproducible dependency bootstrap script

## Front-End

- [x] Implement lexer
- [x] Implement parser
- [x] Implement AST definitions
- [x] Implement name resolution
- [x] Implement type checking
- [x] Implement minimal borrow/move checking

## Middle-End / Back-End

- [x] Define IR
- [x] Lower checked AST to IR
- [x] Implement C emitter
- [x] Add tiny runtime in `stdlib/`
- [x] Add C compiler invocation support
- [x] Replace user-triggerable backend crash paths with diagnostics or internal-error handling

## Examples

- [x] Hello world
- [x] Simple function
- [x] Product type usage
- [x] Enum plus match
- [x] Explicit `result` handling
- [x] Small fallible function
- [x] Ownership / mutation example

## Tests

- [x] Lexer tests
- [x] Parser tests
- [x] Resolver tests
- [x] Type checker tests
- [x] Borrow checker tests
- [x] C emission tests
- [x] Integration tests
- [x] Golden C tests
- [x] Diagnostic snapshot tests
- [x] Bootstrap reproducibility tests
- [x] AI audit execution tests

## Diagnostics And Lints

- [x] Stable diagnostic codes
- [x] Parse error formatting
- [x] Type error formatting
- [x] Borrow error formatting
- [x] `unused_mut`
- [x] discarded `result` warning
- [x] `audit` contract diagnostics
- [x] public API missing `audit` warning

## AI Contracts

- [x] Add `audit` blocks to the grammar and parser
- [x] Infer direct `mutates(...)` facts for `mutref` parameters
- [x] Infer transitive `effects(print)` across the single-file call graph
- [x] Add `review` JSON output
- [x] Add contract examples and tests

## AI Audit

- [x] Add paired Nauqtype/Python benchmark corpus
- [x] Add audit runner script
- [x] Generate and commit AI audit report outputs
- [x] Expand the corpus to compare plain Nauqtype, contract-enabled Nauqtype, and Python hints+docstrings

## Bootstrap Next

- [x] Implement acyclic imports
- [x] Add file input as `result<str, io_err>`
- [x] Add builtin `list<T>`
- [x] Add the first `selfhost/` stage1 front end

## Near-Self-Hosting Next

- [x] Extend `selfhost/` from the first body-level resolver slice to fuller semantic front-end parity for the trusted subset
- [x] Add the first `selfhost/` type-checker slice
- [x] Add the first `selfhost/` value-flow type-checker slice for annotated locals, returns, and conditions
- [x] Add simple inferred-local and assignment compatibility checks to the `selfhost/` value-flow slice
- [x] Add field-access-aware local/return inference for the flat selfhost value-flow slice
- [x] Extend the current `selfhost/` body-resolution and value-flow slices back to full-graph semantic parity
- [x] Replace root-shape selfhost value typing with recursive span-based typing for the current supported subset
- [x] Make stage1 fail closed with explicit limitation diagnostics for unsupported expression shapes
- [x] Add differential stage0-vs-stage1 subset parity coverage
- [x] Generalize selfhost flat-root module loading and reject import cycles
- [x] Extend the selfhost recursive type-checker slice to nested field chains and contextual builtin `Some` / `None` / `Ok` / `Err` / `list()` typing in current value-flow contexts
- [x] Expand the differential corpus to lock the current trusted subset and the retained non-name-callee limitation boundary
- [x] Batch current selfhost value-flow checking by module/function to avoid the obvious repeated full rescans
- [x] Extend `selfhost/` type-checker work from the current signature/arity/value-flow slices to semantic near parity for the trusted subset
- [x] Decide the first trustworthy self-hosting milestone and comparison strategy

## Machine-Readable Compiler Output

- [x] Add `check --diagnostics json`
- [x] Add versioned diagnostics JSON schema
- [x] Add diagnostics JSON golden tests
- [x] Add stable semantic defs/refs/call graph export
- [x] Lock `facts` v1 with schema, golden fixture, and representative selfhost-module smoke
- [x] Bound full-tree `facts` export performance for the complete in-repo selfhost graph
- [x] Add `facts --format v2` evidence fields without breaking v1
- [x] Add richer `review` v2 output
- [x] Add `review-diff`
- [x] Add `review-diff --format v2` evidence metadata
- [x] Add schema/golden coverage for facts v2, review v2, review-diff v1, and review-diff v2
- [x] Add named-argument label references to facts v2 and parameter rename plans
- [x] Add supervised `change-report --format v1`
- [x] Add schema/golden coverage for change-report v1
- [x] Add plan-only `refactor-rename`
- [x] Add `nauqtype.policy.json` sidecar metadata and `policy-check`
- [x] Add schemas for refactor plans, policy-check output, and policy sidecars
- [x] Expand root policy metadata over high-risk selfhost compiler surfaces
- [x] Harden `prove` as the active AI tooling confidence gate

## Genuine Parity Next

- [x] Build the structured checked handoff from trusted selfhost semantic outputs
- [x] Harden the structured checked handoff with stable binding identity, explicit borrow nodes, and fail-closed export
- [x] Add stage1 borrow checking on the structured checked handoff
- [x] Add stage1 IR lowering on the structured checked handoff
- [x] Add stage1 C emission on the structured checked handoff
- [x] Define and execute the first stage1-to-stage2 self-build comparison proof

## Nauqtype-Only Transition

- [x] Decide that Nauqtype is now the active implementation language and Python is frozen bootstrap/reference code
- [x] Cut over the stage1 executable driver for `check`
- [x] Cut over the stage1 executable driver for `emit-c`
- [x] Cut over the stage1 executable driver for `review`
- [x] Add the remaining minimal tooling runtime surface needed for `build` / `run`
- [x] Cut over the stage1 executable driver for `build`
- [x] Cut over the stage1 executable driver for `run`
- [x] Add a Nauqtype-owned `prove-selfhost` gate for the copied selfhost proof
- [x] Add the Nauqtype-owned locked example corpus runner
- [x] Retire the active Python proof/corpus orchestration after the Nauqtype runner covers both selfhost proof and corpus checks

## Next Language Ergonomics Batch

- [x] Start only after the pre-language AI tooling spine is green
- [x] Add top-level `const` with canonical Nauqtype examples
- [x] Add list literals with canonical Nauqtype examples
- [x] Add `match` as an expression with canonical Nauqtype examples (selfhost stage1)
- [x] Add `let-else` for `option` / `result` with canonical Nauqtype examples (selfhost stage1)
- [x] Add formatter-lite for the trusted teaching subset
- [x] Add named function arguments with canonical Nauqtype examples
- [x] Add direct module-qualified function calls with canonical Nauqtype examples
- [x] Add minimal nearest-`while` `break` / `continue` with canonical Nauqtype examples
- [x] Add direct module-qualified data names with canonical Nauqtype examples
- [x] Add copy-only record update with canonical Nauqtype examples

## Alpha Stabilization And Supervised Workflow

- [x] Freeze language growth during the alpha stabilization checkpoint
- [x] Document machine-readable output compatibility as part of the public tool contract
- [x] Add a canonical supervised-change fixture pair
- [x] Add deterministic goldens for facts v2, review v2, review-diff v2, change-report v1 with policy, policy-check, and refactor-rename
- [x] Extend the stage1-owned `prove` gate with the supervised evidence workflow
- [x] Keep `refactor-rename` plan-only and verify it does not mutate files

## Proof Hardening Next

- [x] Add deterministic proof summary v1 for easier comparison and triage
- [x] Add a versioned proof summary schema
- [x] Improve proof failure localization across selfhost, corpus, tooling, and emitted-C comparison steps
- [x] Keep `prove`, `prove-selfhost`, and `prove-corpus` stdout unchanged while writing summary artifacts
- [x] Add direct coverage for `prove-selfhost`, `prove-corpus`, and failure summary emission
- [x] Expand proof/corpus confidence further before starting Batch D syntax

## M21 Formatter And Teaching Corpus Hardening

- [x] Guard formatter-lite over every canonical example file, including helper-only modules
- [x] Document canonical teaching style expectations around formatter-lite output
- [x] Keep formatter-lite output-only / `--check` until comment-preserving write mode is safe
- [x] Add any new teaching examples to the formatter guard before they can be considered canonical

## M22 Evidence And Refactor Coverage For Recent Syntax

- [x] Extend facts evidence for copy-only record update inheritance and override provenance
- [x] Ensure refactor plans handle newer stable references without mutating files
- [x] Keep v1 machine-readable surfaces compatible; add evidence only through existing v2/versioned channels
- [x] Add goldens for any new evidence surfaces before relying on them in supervised workflows

## M23 Surgical Helpers And Proof Confidence

- [x] Centralize duplicated pure-Nauqtype string/path/list helpers used by active tooling
- [x] Add only helpers exercised by selfhost, proof tooling, or canonical examples
- [x] Widen proof confidence without starting a stage3/stage4 chain
- [x] Keep broad stdlib, package manager, and OS/runtime growth deferred

## M24 `effects(io)` Audit Atom

- [x] Add `io` as a fixed effect atom alongside `print`
- [x] Infer direct and transitive `io` from file/process builtins
- [x] Update audit blocks that call `read_file`, `write_file`, `create_dir_all`, or `run_process`
- [x] Keep user-defined effect atoms deferred

## M25 Evidence-Backed `?` Propagation

- [x] Lock the design direction in `PROPAGATION.md` and D036
- [x] Add statement-boundary `let name = result_expr?;`
- [x] Add exact `result<T, E>` propagation typing with no implicit conversion
- [x] Add `propagates(E)` audit contract inference and validation
- [x] Add versioned propagation evidence to facts/review/change-report surfaces
- [x] Add canonical example coverage for `?` propagation
- [x] Add negative driver coverage for `?` without `propagates(...)` expecting `NQ-PROPAGATE-004`
- [x] Make `NQ-PROPAGATE-003` teach explicit error mapping instead of implicit conversion

## M26 Linux Alpha Foundation

- [x] Add a repo-local `bin/nauqc` launcher for normal Linux shell use
- [x] Add a conservative local install script for `$HOME/.local/bin/nauqc`
- [x] Add a Linux alpha verification script around bootstrap rebuild, smoke run, and `prove`
- [x] Document current Linux alpha readiness and distro-readiness gaps
- [x] Replace the historical `main.exe` artifact name in release/install outputs
- [x] Define a copied install layout for runtime, schemas, examples, and docs
- [x] Add a Linux release manifest and packaging plan
- [x] Add CI or another clean-checkout Linux release gate

## M27 Stress-Leg Edge Cleanup

- [x] Add a repeatable multi-module "leg test" cadence after every three completed milestones and before stable/release declarations
- [x] Turn the first stress-program findings into focused regression fixtures instead of leaving them as temporary notes
- [x] Fix qualified enum constructors inside `match` expressions so exhaustiveness matches statement `match`
- [x] Fix nested qualified calls used directly as call arguments so named-argument export stays resolved
- [x] Align `review --format v2` constructor-call evidence with `facts --format v2`
- [x] Add explicit propagation-contract/site evidence to review/facts/change-report outputs as part of the existing M25 evidence work
- [x] Add a dense temporary stress-run checklist covering check, review v2, facts v2, fmt, emit-c, build, and direct runtime execution

## M28 Evidence Parity Lock For Current Syntax

- [x] Add a combined evidence-parity fixture covering shipped syntax families without adding new syntax
- [x] Lock facts v2, review v2, review-diff v2, change-report v1, policy-check, and refactor-rename goldens for that fixture
- [x] Ensure review-diff and change-report resolve builtin variants and user variants through the same checked identity path as review v2/facts v2
- [x] Include M28 evidence parity in the stage1-owned `prove` tooling gate
- [x] Run final full-suite, `prove`, Linux alpha, and stress-leg gates before closing M28

## M29 Proof Confidence Matrix v2

- [x] Add proof-summary v2 with richer phase metadata while keeping proof command stdout stable
- [x] Preserve selfhost stage1/stage2 C artifacts and per-corpus emit/build/run C artifacts for triage
- [x] Add deterministic artifact hashes and corpus IDs to `build/proof/summary.json`
- [x] Add a versioned `schemas/proof-summary-v2.schema.json`
- [x] Add focused tests for success and failure summary shape
- [x] Run final full-suite, `prove`, Linux alpha, and stress-leg gates before closing M29

## M30 Linux Alpha RC1

- [x] Add explicit repository and copied-release version identity
- [x] Emit deterministic `share/nauqtype/release.json` from `scripts/make_linux_release.sh`
- [x] Add a copied-layout verifier for launcher, runtime, schemas, examples, docs, and artifact exclusions
- [x] Smoke-test the copied release from a temporary project outside the repository root
- [x] Keep M30 scoped to release-readiness scaffolding, not distro packaging or language growth

## M31 Stress-Leg 2

- [x] Run the dense cross-feature stress leg after M28, M29, and M30
- [x] Extend the stress runner to replay the dense program through a copied Linux Alpha RC1 launcher outside the repository root
- [x] Cover check, review v2, facts v2, change-report v1, fmt, emit-c, build, and runtime behavior through the stress path
- [x] Record that this leg exposed no new compiler findings requiring focused reduction fixtures
- [x] Keep the temporary stress program separate from the teaching corpus

## M32 Teaching Corpus v1

- [x] organize canonical examples into lessons, evidence demos, negative diagnostics, and runnable corpus entries
- [x] keep formatter-lite as the gate for teaching examples
- [x] make the corpus useful for future model training and human onboarding without growing source-language semantics
- [x] keep runnable corpus entries connected to `prove-corpus`

## M33 Propagation Context Labels

- [x] Add optional bare identifier labels at existing statement-boundary `?` sites using `?[context_label]`
- [x] Preserve labels as optional facts v2 and review v2 propagation-site context evidence
- [x] Treat label-only changes as changed functions in review-diff and change-report
- [x] Keep exact error typing, `propagates(E)`, lowering, and runtime behavior unchanged
- [x] Add canonical corpus and focused stage1 driver coverage

## M34 Effect Evidence Granularity

- [x] Preserve `effects(io)` as the only source-level IO audit atom
- [x] Emit checked `read`, `write`, `create_dir`, and `process` direct-call evidence in facts v2 and review v2
- [x] Infer canonical transitive IO subkind lists for review v2 function evidence
- [x] Surface subkind-only changes through existing review-diff and change-report changed-function evidence
- [x] Keep policy metadata, enforcement, and user-defined effects out of scope

## M34.5 Verification Reuse And Failure Localization

- [x] Add focused, non-selfhost test coverage for rapid feedback
- [x] Add a composed milestone gate that runs selfhost proof and Linux release work once in dependency order
- [x] Preserve standalone Linux alpha and stress-leg release gates for M37 and release candidates
- [x] Record milestone phase timing and failure-localization evidence under ignored `build/verification/`

## M35 Field Assignment V1

- [x] Add direct `binding.field = expr;` for owned mutable local product values
- [x] Reject immutable locals, `mutref` parameters, enums, list elements, nested paths, and arbitrary targets
- [x] Preserve type and move checking through handoff, borrow, IR, and C emission
- [x] Export checked `field_assign` facts and include writes in plan-only field renames
- [x] Add differential, selfhost, canonical-example, formatter, and locked-corpus coverage

## M36 Literal And Nested Constructor Patterns

- [x] Add `i32` literal patterns and recursively nested constructor patterns
- [x] Require an explicit wildcard or binding fallback for refined matches
- [x] Preserve refined patterns through stage0/stage1 checking, handoff, IR, C emission, facts, formatter, and locked corpus coverage

## M37 v0.2 Supervised Alpha Gate

- [x] Run independent full-suite, proof, Linux alpha, stress-leg, schema, release-layout, policy-sidecar, and teaching-corpus gates
- [x] Resolve the release identity mismatch and record the v0.2 supervised alpha evidence checkpoint

## M38 Nauqtype-Owned Test And Bootstrap Architecture

- [x] Inventory the active Python compiler, test, proof, release, and CI responsibilities
- [x] Map all 240 active Python test claims to a Nauqtype fixture target or archival rationale
- [x] Lock the host-C seed, test migration, CI cutover, and historical archive contract
- [x] Keep Python frozen pending the M39/M40 replacement proof

## M39-M46 v0.3 Organizational Runway

- [x] Add `nauqc test` as the Nauqtype-owned fixture, corpus, and selfhost runner foundation
- [x] Migrate every mapped proof, corpus, diagnostic, and supervision fixture group to that runner or record its checked historical-reference rationale
- [x] Prove a host-C seed bootstrap through stage1 and stage2 and retire Python from active workflows
- [x] Validate the syntax-evolution SOP and workspace/module contract before module syntax implementation
- [x] Add explicit manifests, nested modules, locked local dependencies, and reproducible source locking
- [x] Complete qualified function/type-head/enum/variant evidence migration and explicit source-level module aliases
- [x] Complete cross-package governance facts, policy targeting, semantic snapshots, and impact summaries
- [x] Prove a real multi-package internal tool through the C seed, copied Linux release, policy sidecar, facts snapshot, and changed-dependency impact report

## Post-M46 P0 Backend Closure

- [ ] Make a product field of `list<i32>`, `option<T>`, or `result<T, E>` lower with dependency-safe C carrier declarations
- [ ] Preserve the actual field base when lowering `ref product.field` into list helper calls
- [ ] Add a focused compile/run fixture for the reduced composite-field reproducer before new syntax work resumes
