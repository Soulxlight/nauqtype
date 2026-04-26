# Nauqtype

Nauqtype is a small compiled language designed for AI-authored software under human supervision.

Current bootstrap status:

- `stage0`: frozen Python bootstrap/reference compiler in the current workspace
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
- `selfhost/`: Nauqtype-written stage1 pipeline that can load flat-root modules, lex, parse, resolve, type-check, borrow-check, lower to IR, emit deterministic C for the in-repo selfhost tree with no `stage1 limitation` diagnostics, and now act as the active executable driver for `check`, `emit-c`, `facts`, `review`, `build`, `run`, `prove`, `prove-selfhost`, and `prove-corpus`

## Quick Start

Install local bootstrap dependencies:

```powershell
python scripts/setup_deps.py
```

Run the full test suite:

```powershell
python -m unittest discover -s tests -v
```

Bootstrap the stage1 driver once:

```powershell
python -m compiler.main run selfhost\main.nq
```

Use the active Nauqtype-owned driver for `check`:

```powershell
selfhost\build\main.exe check examples\hello.nq
```

Use the active Nauqtype-owned driver for `emit-c`:

```powershell
selfhost\build\main.exe emit-c examples\hello.nq -o build\hello.c
```

Export deterministic semantic facts for agent-pair supervision:

```powershell
selfhost\build\main.exe facts examples\hello.nq
```

Use the active Nauqtype-owned driver for `review`:

```powershell
selfhost\build\main.exe review examples\review_contracts.nq
selfhost\build\main.exe review examples\review_contracts.nq --format v2
```

Compare two checked review surfaces with stable semantic identities:

```powershell
selfhost\build\main.exe review-diff before\main.nq after\main.nq
```

Use the active Nauqtype-owned driver for `build`:

```powershell
selfhost\build\main.exe build examples\hello.nq
```

Use the active Nauqtype-owned driver for `run`:

```powershell
selfhost\build\main.exe run examples\hello.nq
```

Run the active Nauqtype-owned transition gate:

```powershell
selfhost\build\main.exe prove
```

Run the individual proof gates when you need to isolate a failure:

```powershell
selfhost\build\main.exe prove-selfhost
selfhost\build\main.exe prove-corpus
```

Current cutover note: invoke stage1 `build` / `run` from the repo root for now, because that slice still resolves the pinned Zig toolchain and `stdlib/runtime.c` from the workspace-local bootstrap layout.

Frozen bootstrap/reference workflows that still exist during the cutover:

```powershell
python -m compiler.main check examples\hello.nq --diagnostics json
python -m compiler.main run examples\hello.nq
python scripts/run_ai_audit.py
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
- stage1 now also enforces the current stage0-parity borrow rules on the structured checked handoff
- stage1 now also lowers the trusted subset from the checked handoff into a deterministic internal IR
- stage1 now also emits deterministic C from that IR and writes `build/main.c` through the minimal builtin `write_file(path: str, text: str) -> result<unit, io_err>`
- the first copied-selfhost stage1-to-stage2 comparison proof is now complete
- the stage1 executable now owns the active `check`, `emit-c`, `review`, `build`, `run`, `prove`, `prove-selfhost`, and `prove-corpus` workflow while preserving the no-arg copied-selfhost proof path

Architecture checkpoint:

- the current flat selfhost parser/resolve/typecheck pipeline is accepted as the semantic front-end path
- that flat pipeline is not the direct substrate for stage1 borrow checking, IR lowering, or C emission
- stage1 now materializes a deterministic structured checked handoff from the trusted semantic outputs
- the checked handoff now carries stable binding identities, explicit `ref` / `mutref` borrow nodes, recursive type-shape truth with origin-aware named types, checked pattern trees, and fail-closed export diagnostics for the trusted subset
- genuine parity work now continues from that checked handoff boundary rather than the flat fact lists
- see `SELFHOST_HANDOFF.md` for the required downstream contract

Current remaining gaps:

- richer selfhost value inference beyond the current supported recursive subset
- non-name callee syntax and member-call syntax still intentionally stop at the explicit stage1 limitation boundary
- broader proof hardening beyond the first copied-selfhost stage1-to-stage2 checkpoint
- Python proof/corpus tests remain only as frozen bootstrap/reference regression coverage; active proof/corpus orchestration is stage1-owned through `prove`

Current AI-first compiler output:

- `review` JSON for function-level contract summaries
- `facts` JSON for stable definitions, references, and call graph edges
- `review --format v2` JSON with stable function/call identities, reference entries, call graph edges, and checked-vs-declared evidence fields
- `review-diff` JSON for deterministic semantic changes over stable function identities and call graph edges
- `check --diagnostics json` for deterministic compiler diagnostics

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

- Nauqtype is now the active implementation language for the project.
- The Python compiler remains in-repo only as a frozen bootstrap/reference path.
- The language surface is still intentionally small, but bootstrap-critical stage1 features are now active: imports, file input, bootstrap string helpers, builtin `list<T>`, minimal file output through `write_file(path: str, text: str) -> result<unit, io_err>`, and the narrow toolchain runtime surface for args, directory creation, and subprocess execution.
