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

- [ ] Extend `selfhost/` from the first body-level resolver slice to fuller resolver parity
- [x] Add the first `selfhost/` type-checker slice
- [x] Add the first `selfhost/` value-flow type-checker slice for annotated locals, returns, and conditions
- [x] Add simple inferred-local and assignment compatibility checks to the `selfhost/` value-flow slice
- [ ] Extend `selfhost/` type-checker work from the current signature/arity/value-flow slices to fuller parity
- [ ] Decide the first trustworthy self-hosting milestone and comparison strategy
