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

- [ ] Centralize duplicated pure-Nauqtype string/path/list helpers used by active tooling
- [ ] Add only helpers exercised by selfhost, proof tooling, or canonical examples
- [ ] Widen proof confidence without starting a stage3/stage4 chain
- [ ] Keep broad stdlib, package manager, and OS/runtime growth deferred
