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
- `selfhost/`: Nauqtype-written semantic front end that can load flat-root modules, lex, parse, resolve, and type-check the in-repo selfhost tree with no `stage1 limitation` diagnostics

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

Emit machine-readable compiler diagnostics for `check`:

```powershell
python -m compiler.main check examples\hello.nq --diagnostics json
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
- match scrutinee typing plus pattern-bound payload typing for the current enum / `option` / `result` subset
- full-graph body resolution and current value-flow checking across the loaded selfhost module set
- differential stage0-vs-stage1 subset coverage for trusted semantic comparison, including the retained explicit non-name-callee limitation boundary
- the in-repo selfhost tree runs with no `stage1 limitation` diagnostics

Current semantic near-parity milestone:

- `selfhost/` can load, parse, resolve, and type-check the full in-repo selfhost tree
- the trusted subset is differential-tested against stage0 by accept/reject family
- stage1 still stops before borrow checking, IR lowering, C emission, executable build, and self-rebuild

Architecture checkpoint:

- the current flat selfhost parser/resolve/typecheck pipeline is accepted as the semantic front-end path
- that flat pipeline is not the direct substrate for stage1 borrow checking, IR lowering, or C emission
- stage1 now materializes a deterministic structured checked handoff from the trusted semantic outputs
- genuine parity work now starts from that checked handoff boundary rather than the flat fact lists
- see `SELFHOST_HANDOFF.md` for the required downstream contract

Current selfhost semantic gaps:

- richer selfhost value inference beyond the current supported recursive subset
- non-name callee syntax and member-call syntax still intentionally stop at the explicit stage1 limitation boundary
- selfhost borrow checking
- selfhost IR lowering and C code generation
- stage1 self-build / stage2 comparison

Current AI-first compiler output:

- `review` JSON for function-level contract summaries
- `check --diagnostics json` for deterministic compiler diagnostics
- `review` v2 and `review-diff` are intentionally deferred

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
- [SELFHOST_HANDOFF.md](SELFHOST_HANDOFF.md)

## Repository Notes

- The current compiler is a Python bootstrap because this workspace did not provide a Rust toolchain.
- The long-term implementation preference remains Rust.
- The language surface is still intentionally small, but bootstrap-critical stage1 features are now active: imports, file input, bootstrap string helpers, and builtin `list<T>`.
