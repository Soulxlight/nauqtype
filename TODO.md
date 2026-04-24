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
- [ ] Add richer `review` v2 output
- [ ] Add `review-diff`

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
- [ ] Replace the active Python proof/corpus orchestration with a Nauqtype-owned runner
