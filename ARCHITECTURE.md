# Nauqtype Compiler Architecture

This is the architectural authority for the active compiler, not the archived
Python design. The compiler and its command/proof runners are written in
Nauqtype. The narrow native runtime and generated bootstrap seed are C.

For task routing and the documentation inventory, start at
[docs/README.md](docs/README.md). [COMPILER_MAP.md](docs/COMPILER_MAP.md) locates
the actual entrypoints; it does not replace this contract. Inspection was
refreshed on 2026-10-09 without changing executable sources or claiming a new
Linux acceptance run.

## Pipeline And Ownership

```text
manifest / source files
  -> tokens and source spans
  -> flat parser facts
  -> resolved and typed semantic facts
  -> structured checked handoff and checked source contracts
  -> canonical type properties / value-use plan and borrow validation
  -> structured typed IR
  -> C text
  -> host C compiler plus runtime
```

| Layer | Active source | Responsibility |
| --- | --- | --- |
| Driver | `selfhost/main.nq`, `build_info.nq`, `host_c.nq` | Command dispatch, phase orchestration, diagnostics, executable entry validation, host-C invocation. |
| Workspace | `workspace.nq`, `files.nq`, `source.nq` | Manifest-owned roots, nested module identities, aliases, locked local dependencies, physical source paths. Legacy flat-root projects remain supported separately. |
| Lex/parse | `token.nq`, `lexer.nq`, `parser.nq`, `ast.nq` | Tokens, stable source spans, declarations/statements, and flat semantic facts. Despite its name, `ast.nq` is not a universal recursive expression AST. |
| Semantic front end | `resolve.nq`, `typecheck.nq`, `type_text.nq` | Visible symbols, scope and type truth, context-driven expression validation, patterns, declarations and calls. Some expression families are still reconstructed from token spans. |
| Checked boundary | `handoff.nq` | Typed expression/control-flow structure, recursive type shapes, stable binding IDs, resolved function/constructor/field targets. |
| Values and borrowing | `value_plan.nq`, `borrow.nq` | Canonical copy/drop classification, copy/move/borrow use plans, move-state validation over checked identities. |
| IR | `ir.nq` | Deterministic program, signature, declaration, local, expression, pattern, and control-flow records. No raw fact/token fallback for downstream consumers. |
| C backend | `c_emit.nq` | IR-only C declarations, expressions, control flow, runtime calls, type-directed clone/move/drop, and private C identifier encoding. |
| Evidence | `facts.nq`, `review.nq`, `diag.nq`, `checked_coverage.nq` | Shared checked source-contract validity, versioned facts/review/change evidence, coverage checks, advisory policy, plan-only refactoring, and producer diagnostics. |
| Formatting/helpers | `fmt.nq`, `text.nq` | Output-only formatter-lite and exercised internal text/list helpers. No AST formatter or write mode. |
| Owned verification | `proof.nq`, `proof_artifacts.nq`, `schema_profile.nq`, focused `*_tests.nq` modules | `test`, seed/selfhost/corpus proof, invocation-produced artifacts, bounded schema checks, deterministic comparison, and proof summaries. |
| Native runtime | `stdlib/runtime.h`, `stdlib/runtime.c` | Representations, value storage/reclamation, and explicitly modeled Linux authority. General-purpose library policy belongs outside the runtime. |

Paths without a directory in the table are relative to `selfhost/`.

## Architectural Boundaries

The flat semantic pipeline is retained as the current front end, not the
substrate for backend growth. Borrow analysis consumes the structured checked
handoff and value plan. IR lowering consumes that checked representation; C
emission consumes IR. Backend passes must not guess binding, type, target, or
borrow meaning from names or source offsets. Missing required truth fails the
build. [SELFHOST_HANDOFF.md](SELFHOST_HANDOFF.md) records the detailed contract.

The current exporter still reconstructs some expressions from spans. The
duplicated operator scans in typecheck/handoff must agree with
[GRAMMAR.md](GRAMMAR.md). M54.7 repaired grouping without replacing them with
a parser-owned expression arena. A later migration must be separately
reviewed, incremental, identity-aware, and measured on the current baseline.

IR-only data flow does not mean a dependency-clean source graph: `ir.nq`
records still use checked binding/value-use/type-shape enums, and `c_emit.nq`
imports their defining modules. This is shared vocabulary, not permission to
consume flat facts or re-derive types. Neutral type ownership is a proposed
refactor, not implemented architecture.

Compilation and evidence commands share checked source-contract validation
after handoff. Driver collection paths still repeat phase assembly, but the
M54.8 corrective gate is complete, not scheduled. Review v4 exposes checked
call-aware parameter may-writes; legacy v3 deliberately remains a partial
direct-write lower bound. Evidence commands do not all run IR/C emission or
prove whole-program semantic completeness. Policy remains advisory. See
[M54_8_CONTRACTS.md](M54_8_CONTRACTS.md) for coverage/failure contracts and
[AUDIT_REMEDIATION.md](AUDIT_REMEDIATION.md) for recorded closure.

## Values And Generated Code

- `i32` and `i64` are distinct types with exact matching, contextual integer
  literals, and no implicit conversion. Addition, subtraction, multiplication
  and negation wrap at their width. Division truncates toward zero and fails
  deterministically for zero and minimum-value divided by `-1`; evaluated
  invalid constant division produces source diagnostics. Typed IR/native
  helpers implement the rules in [M54_9_CONTRACTS.md](M54_9_CONTRACTS.md),
  rather than relying on C signed overflow.
- Heap-backed `str` retains copy semantics through reference-counted runtime
  storage. `list<T>` and `bytes` are move-only. Nominal products/enums derive
  copy and drop behavior from their fields/payloads.
- Checked binding IDs, not names, drive move state and IR locals. Explicit
  `ref`/`mutref` nodes retain their target and type truth.
- Cleanup covers replacement, block exits, returns, propagation, pattern
  payloads, compiler temporaries, and nearest-loop `break`/`continue` for
  `while` and list-only `for`.
- Ordered match conditions preserve first-match source priority and evaluate
  the scrutinee once. Private C spelling must be injective for module/type,
  function, field, variant, and generic-carrier identities; runtime-native
  names remain ABI-owned. M54.7 closed those recorded repair obligations;
  refactoring must preserve them.

The runtime remains a trust boundary. M54.9 checks allocation-size arithmetic;
M55 closes the recorded interrupted wait/capture defect and adds owned process
handles and nominal time/deadlines. Cleanup authority is checked for owned
recursive aggregates, not inferred from a borrow alone. Failures and platform
exclusions remain explicit in [M55_CONTRACTS.md](M55_CONTRACTS.md). Their
closure is evidence for the recorded cases, not a guarantee against all future
resource or concurrency defects.

## Bootstrap And Verification

`bootstrap/seed/nauqc-seed.c` is a versioned, checked-in bootstrap artifact,
with its matching runtime, source snapshot, inventory, manifest, generator
lineage, and checksums. The active path is:

```text
host cc -> checked C seed -> Nauqtype stage1 -> emitted stage2 C -> stage2
```

`scripts/build_stage1_from_seed.sh` publishes the active driver;
`bin/nauqc` is its repository launcher. `compiler/`, the Python unit suites,
and Python audit generators are frozen historical references, not required
build/test/proof dependencies. Seed promotion must satisfy
[BOOTSTRAP_RETIREMENT.md](BOOTSTRAP_RETIREMENT.md); a self-consistent compiler
can still miscompile source, so spec-derived runtime/diagnostic fixtures are
required alongside the fixed-point proof.

Active cases live in `tests/fixtures/`, `tests/golden/`, and `examples/` and
are exercised by the Nauqtype runner. Shell scripts provide narrow host build,
resource, release-copy, and sanitizer integration. They are not another
semantic reference implementation. Tracked historical probes and benchmark
assets remain intentionally preserved.

Development uses focused checks, independent audits, and one final frozen
candidate gate. [VERIFICATION.md](VERIFICATION.md) defines exact commands and
budgets; [LANGUAGE_CHARTER.md](LANGUAGE_CHARTER.md) defines the v1.0
language and its acceptance. Cached success or bootstrap consistency is never evidence of
semantic completeness by itself.

## Direction

Milestones through M56 (including the PRE-M56 performance checkpoint and the
R0-R6 [refactor program](docs/REFACTOR_PLAN.md)) are complete in the recorded
Linux evidence. The current sequence is in
[ROADMAP.md](ROADMAP.md#current-position-and-resumption).

The product target is trustworthy Linux terminal and native application
development, not feature parity with another language. Compiler/runtime
changes stay here. From M57 onward, reusable general-purpose modules
(collections, JSON, and later ones) also live in this repository as an in-repo
standard library shipped with the compiler; the separate NQType Libraries
repository is dormant and the AI/ML lane is retired (see
[NAUQTYPE_COORDINATION.md](NAUQTYPE_COORDINATION.md)). The narrow-runtime rule
still applies: library modules are Nauqtype source over checked primitives,
not new compiler builtins. Apply [SYNTAX_IDENTITY.md](SYNTAX_IDENTITY.md)
before any language widening.
