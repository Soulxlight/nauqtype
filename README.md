# Nauqtype

Nauqtype is a small compiled language designed for AI-authored software under human supervision.

Current bootstrap status:

- `stage0`: frozen Python bootstrap/reference compiler in the current workspace
- Linux alpha development is supported through the repo-local `bin/nauqc` stage1 launcher and the copied Alpha RC1 layout; see [LINUX.md](LINUX.md)
- flat-root multi-file imports with one workspace root
- explicit types at function boundaries
- top-level `const` for small compile-time configuration values
- nominal `type` and `enum`
- `option<T>` and `result<T, E>`
- builtin `io_err` and `list<T>` with narrow list literals
- explicit `match`
- match expressions for value-producing exhaustive branches
- narrow `let-else` guard binding for `Some(name)` / `Ok(name)` success paths
- statement-boundary `?` propagation for unchanged `result<T, E>` errors, with optional `?[context_label]` evidence and checked by `propagates(E)`
- fixed `effects(io)` contracts with checked read/write/create-directory/process evidence in v2 supervision outputs
- named function arguments and direct module-qualified function/data names
- minimal nearest-`while` `break` / `continue`
- copy-only record update with explicit `Type { from base, field: value }` provenance
- direct field assignment for owned `let mut` product locals
- integer literal and nested constructor patterns with an explicit fallback arm
- bootstrap file input and string helpers
- minimal move / borrow checking
- structural copy for all-copy user `type` / `enum`
- compile-to-C backend with a tiny runtime
- `selfhost/`: Nauqtype-written stage1 pipeline that can load flat-root modules, lex, parse, resolve, type-check, borrow-check, lower to IR, emit deterministic C for the in-repo selfhost tree with no `stage1 limitation` diagnostics, and now act as the active executable driver for `check`, `emit-c`, `facts`, `review`, `review-diff`, `change-report`, `refactor-rename`, `policy-check`, `fmt`, `build`, `run`, `prove`, `prove-selfhost`, and `prove-corpus`

v0.2 supervised alpha status: `nauqtype-0.2.0-alpha.1` is the current checked Linux alpha identity. The M23 language and tooling baseline remains stable, and the current alpha surface extends it through explicit milestones, examples, proof coverage, and decision records rather than opportunistic syntax growth.

The active roadmap now prioritizes a Nauqtype-owned test and bootstrap path before workspace syntax grows. [BOOTSTRAP_RETIREMENT.md](BOOTSTRAP_RETIREMENT.md) records the Python-retirement contract, and [SYNTAX_IDENTITY.md](SYNTAX_IDENTITY.md) records the syntax-evolution discipline that future features must satisfy.

## Quick Start

Install local bootstrap dependencies:

```bash
python3 scripts/setup_deps.py
```

Run the full test suite:

```bash
python3 -m unittest discover -s tests -v
```

Run the active Nauqtype-owned fixture suite after bootstrapping stage1:

```bash
bin/nauqc test
```

Bootstrap the stage1 driver once:

```bash
python3 -m compiler.main run selfhost/main.nq
```

Use the active Nauqtype-owned driver for `check`:

```bash
bin/nauqc check examples/hello.nq
```

Use the active Nauqtype-owned driver for `emit-c`:

```bash
bin/nauqc emit-c examples/hello.nq -o build/hello.c
```

Export deterministic semantic facts for agent-pair supervision:

```bash
bin/nauqc facts examples/hello.nq
bin/nauqc facts examples/hello.nq --format v2
```

Use the active Nauqtype-owned driver for `review`:

```bash
bin/nauqc review examples/review_contracts.nq
bin/nauqc review examples/review_contracts.nq --format v2
```

Compare two checked review surfaces with stable semantic identities:

```bash
bin/nauqc review-diff before/main.nq after/main.nq
bin/nauqc review-diff before/main.nq after/main.nq --format v2
```

Produce a supervised semantic change report, optionally linked to policy metadata:

```bash
bin/nauqc change-report before/main.nq after/main.nq --format v1
bin/nauqc change-report before/main.nq after/main.nq --policy nauqtype.policy.json --format v1
```

Canonical supervised workflow for an agent/human review loop:

```bash
bin/nauqc check tests/fixtures/supervised_workflow/after/main.nq
bin/nauqc facts tests/fixtures/supervised_workflow/after/main.nq --format v2
bin/nauqc review tests/fixtures/supervised_workflow/after/main.nq --format v2
bin/nauqc review-diff tests/fixtures/supervised_workflow/before/main.nq tests/fixtures/supervised_workflow/after/main.nq --format v2
bin/nauqc change-report tests/fixtures/supervised_workflow/before/main.nq tests/fixtures/supervised_workflow/after/main.nq --policy tests/fixtures/supervised_workflow/policy.json --format v1
bin/nauqc policy-check tests/fixtures/supervised_workflow/after/main.nq tests/fixtures/supervised_workflow/policy.json
bin/nauqc refactor-rename tests/fixtures/supervised_workflow/after/main.nq binding:fn:main::apply:1:bonus@25 extra
```

Plan a semantic rename without mutating files:

```bash
bin/nauqc refactor-rename examples/hello.nq fn:hello::main renamed_main
```

Validate sidecar ownership/review metadata against checked facts:

```bash
bin/nauqc policy-check selfhost/main.nq nauqtype.policy.json
```

Format trusted-subset Nauqtype source without mutating files:

```bash
bin/nauqc fmt examples/hello.nq
bin/nauqc fmt --check examples/hello.nq
```

Formatter-lite is output-only / `--check` for now. Its canonical teaching-corpus rules are documented in [FORMATTER.md](FORMATTER.md); write mode remains deferred until comment preservation is safe.

Use the active Nauqtype-owned driver for `build`:

```bash
bin/nauqc build examples/hello.nq
```

Use the active Nauqtype-owned driver for `run`:

```bash
bin/nauqc run examples/hello.nq
```

Run the Linux alpha gate:

```bash
scripts/check_linux_alpha.sh
```

The gate now verifies the Alpha RC1 copied layout, release identity, and an outside-repo smoke run for the copied `bin/nauqc` launcher.

For normal milestone work, use the layered verification commands in
[VERIFICATION.md](VERIFICATION.md). `scripts/check_fast.sh` provides quick
focused feedback, while `scripts/check_milestone.sh` runs the selfhost proof,
release smoke, and stress leg once each before focused tests. The standalone
commands below remain the deliberately redundant final Alpha/release gates.

Run the dense milestone stress leg when checking cross-feature interactions:

```bash
scripts/run_stress_leg.sh
```

Run the active Nauqtype-owned transition gate:

```bash
bin/nauqc prove
```

Run the individual proof gates when you need to isolate a failure:

```bash
bin/nauqc prove-selfhost
bin/nauqc prove-corpus
```

The proof commands keep their quiet success stdout and also write deterministic proof evidence to `build/proof/summary.json`, now locked by `schemas/proof-summary-v2.schema.json`. The summary uses richer phase IDs such as `selfhost.stage1_emit_c`, `corpus.run`, and `tooling.schema_golden`, preserves artifact paths and deterministic content hashes, and records corpus IDs for faster triage without relying on model prose. The locked corpus is also guarded so every runnable canonical example in `examples/` participates in `prove-corpus`, while every example source file, including helper-only teaching modules, participates in the `prove` formatter checks.

Current Linux cutover note: use `bin/nauqc` for day-to-day commands. It runs the active stage1 driver from the repo root because `build` / `run` still resolve the pinned Zig toolchain and `stdlib/runtime.c` from the workspace-local bootstrap layout.
The repo-local stage1 driver is built as `selfhost/build/nauqc`; copied Linux alpha layouts use `lib/nauqtype/nauqc-stage1` behind the public `bin/nauqc` launcher.

Frozen bootstrap/reference workflows that still exist during the cutover:

```bash
bin/nauqc check examples/hello.nq --diagnostics json
python3 -m compiler.main run examples/hello.nq
python3 scripts/run_ai_audit.py
```

Example programs worth checking first:

- `examples/hello.nq`: minimal print path
- `examples/while_counter.nq`: bootstrap-track `while` loop semantics
- `examples/fibonacci.nq`: functions plus mutable locals and `while`
- `examples/top_level_const.nq`: stage1-owned top-level constants
- `examples/named_arguments.nq`: Batch B named function arguments
- `examples/nested_break_continue.nq`: nested `break` / `continue` inside `if` within `while`
- `examples/nested_patterns.nq`: nested constructor and integer literal matching with an explicit fallback
- `examples/qualified_call_chain.nq`: multi-module qualified call chain
- `examples/qualified_calls.nq`: direct module-qualified function calls
- `examples/qualified_data_names.nq`: direct module-qualified struct and enum constructor names
- `examples/record_update.nq`: copy-only record update with explicit base provenance
- `examples/record_update_nontrivial.nq`: record update over a computed owned base value
- `examples/propagation_question.nq`: statement-boundary `?` with optional context-label and `propagates(...)` evidence
- `examples/break_continue.nq`: minimal loop control
- `examples/review_contracts.nq`: AI Contracts and `review` workflow

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
- recursive span-based selfhost value typing for the current subset: literals, names, calls, constructors, `base.field`, struct literals, list literals, parentheses, unary `not` / unary minus, arithmetic, comparisons, and `and` / `or`
- nested field-chain typing over the current supported base-expression subset
- contextual builtin typing for `Some`, `None`, `Ok`, `Err`, `list()`, and `[]` in annotated locals, assignments, returns, call-argument contexts, constructor-payload contexts, and match-arm bodies
- explicit selfhost limitation diagnostics for expression shapes outside that supported recursive subset
- simple unannotated-local inference for inferable supported expressions
- assignment compatibility checks when the target type and rhs type are both inferable
- field-access-aware local/return inference including imported type facts in the loaded graph
- match scrutinee typing plus pattern-bound payload typing for the current enum / `option` / `result` subset
- full-graph body resolution and current value-flow checking across the loaded selfhost module set
- top-level `const` parsing, resolution, type checking, semantic facts/refactor/policy visibility, IR lowering, and deterministic C emission for the deliberately narrow `i32` / `bool` / `str` initializer subset
- named function arguments for direct function calls, including modeled builtins and imported functions; arguments are exported to the backend in callee parameter order
- direct `module::function(...)` calls for public functions from directly imported flat-root modules
- direct module-qualified data names for public struct literals and enum variants from directly imported flat-root modules, preserving origin visibility for facts, handoff, IR, and C emission
- copy-only record update for product types using explicit `Type { from base, field: value }` syntax; inherited non-copy fields keep the existing field-move safety boundary
- minimal `break;` and `continue;` statements for the nearest enclosing `while`
- differential stage0-vs-stage1 subset coverage for trusted semantic comparison, including the retained explicit non-name-callee limitation boundary
- the in-repo selfhost tree runs with no `stage1 limitation` diagnostics

Current semantic near-parity milestone:

- `selfhost/` can load, parse, resolve, and type-check the full in-repo selfhost tree
- the trusted subset is differential-tested against stage0 by accept/reject family
- stage1 now also enforces the current stage0-parity borrow rules on the structured checked handoff
- stage1 now also lowers the trusted subset from the checked handoff into a deterministic internal IR
- stage1 now also emits deterministic C from that IR and writes `build/main.c` through the minimal builtin `write_file(path: str, text: str) -> result<unit, io_err>`
- the first copied-selfhost stage1-to-stage2 comparison proof is now complete
- the stage1 executable now owns the active `check`, `emit-c`, `facts`, `review`, `review-diff`, `change-report`, `refactor-rename`, `policy-check`, `fmt`, `build`, `run`, `prove`, `prove-selfhost`, and `prove-corpus` workflow while preserving the no-arg copied-selfhost proof path

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
- broader proof hardening beyond the current copied-selfhost and locked-corpus checkpoints
- Python proof/corpus tests remain only as frozen bootstrap/reference regression coverage; active proof/corpus orchestration is stage1-owned through `prove`
- the first live-in-the-language ergonomics batch now covers top-level `const`, list literals, match expressions, narrow `let-else`, formatter-lite, named arguments, direct module-qualified calls, minimal nearest-`while` loop control, direct module-qualified data names, and copy-only record update; the next semantic feature batch should stay attached to concrete examples and differential or stage1-owned coverage

Near-term focus:

- build on the completed M28 evidence-parity lock before adding more source-language surface
- keep Linux alpha release-layout checks green before more language sugar
- run `scripts/run_stress_leg.sh` periodically so dense multi-module programs catch feature-composition edges before stable/release checkpoints
- keep formatter-lite and the canonical teaching corpus locked as syntax grows
- keep semantic evidence/refactor surfaces aligned with the syntax already shipped
- add only surgical pure-Nauqtype helper-library improvements that are exercised by active tooling or examples
- keep statement-boundary `?` propagation evidence visible through facts v2, review v2, and change-report v1

Current AI-first compiler output:

- `review` JSON for function-level contract summaries
- `facts` JSON for stable definitions, references, and call graph edges, locked by `schemas/facts-v1.schema.json`
- `facts --format v2` JSON with explicit `declared` / `checked` / `builtin` / `unresolved` evidence fields, locked by `schemas/facts-v2.schema.json`
- checked facts for copy-only record-update overrides and inherited field provenance
- `review --format v2` JSON with stable function/call identities, reference entries, call graph edges, and checked-vs-declared evidence fields
- `review-diff` JSON for deterministic semantic changes over stable function identities and call graph edges
- `review-diff --format v2` JSON with checked-input and semantic-comparison evidence metadata
- `change-report --format v1` JSON that combines semantic diff evidence, optional policy status, and diagnostics for supervised change review
- `refactor-rename` JSON edit plans for supported semantic renames, including variant constructors, top-level constants, checked field definitions/uses, and named-argument labels for parameter renames; it never mutates files
- `policy-check` JSON validation for `nauqtype.policy.json` ownership/review sidecars
- `check --diagnostics json` for deterministic compiler diagnostics

Compatibility stance for the alpha checkpoint:

- `facts` v1 remains the default and stays stable
- v2/evidence formats are additive surfaces, not silent replacements for v1
- schema versions and `$id` values are part of the machine-readable contract
- the stage1-owned `prove` gate now includes the canonical supervised workflow so agent-pair review evidence cannot quietly drift

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
- [PROPAGATION.md](PROPAGATION.md)
- [TEACHING_CORPUS.md](TEACHING_CORPUS.md)
- [FORMATTER.md](FORMATTER.md)
- [LINUX.md](LINUX.md)
- [STRESS_LEG.md](STRESS_LEG.md)
- [BOOTSTRAP_STAGE1.md](BOOTSTRAP_STAGE1.md)
- [SELFHOST_HANDOFF.md](SELFHOST_HANDOFF.md)

## Repository Notes

- Nauqtype is now the active implementation language for the project.
- The Python compiler remains in-repo only as a frozen bootstrap/reference path.
- The language surface is still intentionally small, but bootstrap-critical stage1 features are now active: imports, top-level `const`, named arguments, direct module-qualified function and data names, copy-only record update, minimal `break` / `continue`, file input, bootstrap string helpers, builtin `list<T>` with list literals, minimal file output through `write_file(path: str, text: str) -> result<unit, io_err>`, and the narrow toolchain runtime surface for args, directory creation, and subprocess execution.
