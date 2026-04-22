# Nauqtype

Nauqtype is a small compiled language designed for AI-authored software under human supervision.

Current bootstrap status:

- `stage0`: Python bootstrap compiler in the current workspace
- flat-root multi-file imports with one workspace root
- explicit types at function boundaries
- nominal `type` and `enum`
- `option<T>` and `result<T, E>`
- builtin `io_err` and `list<T>`
- explicit `match`
- bootstrap file input and string helpers
- minimal move / borrow checking
- structural copy for all-copy user `type` / `enum`
- compile-to-C backend with a tiny runtime
- `selfhost/`: first Nauqtype-written front-end that can load flat-root modules, lex, shallow-parse, resolve the current graph, and run the current trustworthy selfhost semantic slices across its loaded module graph

## Quick Start

Install local bootstrap dependencies:

```powershell
python scripts/setup_deps.py
```

Run the full test suite:

```powershell
python -m unittest discover -s tests -v
```

Compile and run an example:

```powershell
python -m compiler.main run examples\hello.nq
```

Run the AI-friendliness audit:

```powershell
python scripts/run_ai_audit.py
```

Emit a machine-readable review summary:

```powershell
python -m compiler.main review examples\review_contracts.nq
```

Run the current stage1 selfhost front end:

```powershell
python -m compiler.main run selfhost\main.nq
```

Example programs worth checking first:

- `examples\hello.nq`: minimal print path
- `examples\while_counter.nq`: bootstrap-track `while` loop semantics
- `examples\fibonacci.nq`: functions plus mutable locals and `while`
- `examples\review_contracts.nq`: AI Contracts and `review` workflow

Current selfhost semantic coverage:

- top-level item collection
- flat-root import collection and top-level visibility checks
- flat-root selfhost module loading by `<module>.nq`, plus missing-module and import-cycle diagnostics
- flat type-reference collection for returns, params, local annotations, fields, and enum payloads
- visible vs hidden-imported vs unknown type diagnostics
- function-scope collection
- parameter and local binding collection
- first body-level unknown-name / duplicate-local diagnostics
- first expression-aware name resolution for call targets, plain values, and struct-literal type heads
- callable-vs-value diagnostics for local call targets and bare function names
- first pattern-aware constructor resolution inside `match`
- body-level imported visibility diagnostics for hidden names, constructors, and struct-literal type heads
- first selfhost type-checker slice for entry `main` shape plus function/constructor/pattern arity
- recursive span-based selfhost value typing for the current subset: literals, names, calls, constructors, `base.field`, struct literals, parentheses, unary `not` / unary minus, arithmetic, comparisons, and `and` / `or`
- nested field-chain typing over the current supported base-expression subset
- contextual builtin typing for `Some`, `None`, `Ok`, `Err`, and `list()` in annotated locals, assignments, returns, call-argument contexts, constructor-payload contexts, and match-arm bodies
- explicit selfhost limitation diagnostics for expression shapes outside that supported recursive subset
- simple unannotated-local inference for inferable supported expressions
- assignment compatibility checks when the target type and rhs type are both inferable
- field-access-aware local/return inference including imported type facts in the loaded graph
- full-graph body resolution and current value-flow checking across the loaded selfhost module set
- differential stage0-vs-stage1 subset coverage for trusted semantic comparison, including the retained explicit non-name-callee limitation boundary

Current selfhost semantic gaps:

- full expression-aware resolver parity beyond the current call/value/struct-head split
- fuller body-level resolver parity after the current expression-class slices
- richer selfhost value inference beyond the current supported recursive subset
- richer match-result typing and broader pattern-bound value typing
- non-name callee syntax and member-call syntax still intentionally stop at the explicit stage1 limitation boundary
- selfhost type-checker parity beyond the current signature/arity/value-flow slices

## Key Docs

- [RESEARCH_MEMO.md](RESEARCH_MEMO.md)
- [SPEC.md](SPEC.md)
- [GRAMMAR.md](GRAMMAR.md)
- [ARCHITECTURE.md](ARCHITECTURE.md)
- [ROADMAP.md](ROADMAP.md)
- [DECISIONS.md](DECISIONS.md)
- [RISKS.md](RISKS.md)
- [DEFERRED.md](DEFERRED.md)
- [AI_AUDIT.md](AI_AUDIT.md)
- [AI_CONTRACTS.md](AI_CONTRACTS.md)
- [BOOTSTRAP_STAGE1.md](BOOTSTRAP_STAGE1.md)

## Repository Notes

- The current compiler is a Python bootstrap because this workspace did not provide a Rust toolchain.
- The long-term implementation preference remains Rust.
- The language surface is still intentionally small, but bootstrap-critical stage1 features are now active: imports, file input, bootstrap string helpers, and builtin `list<T>`.
