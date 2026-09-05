# Nauqtype Compiler Architecture

This is the active Linux implementation map, not the archived Python design.
The compiler and its command/proof runners are written in Nauqtype. The narrow
native runtime and generated bootstrap seed are C.

## Pipeline And Ownership

```text
manifest / source files
  -> tokens and source spans
  -> flat parser facts
  -> resolved and typed semantic facts
  -> structured checked handoff
  -> canonical value-use plan and borrow validation
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
| Evidence | `facts.nq`, `review.nq`, `diag.nq` | Versioned semantic facts, review/diff/change evidence, policy validation, plan-only refactoring, and producer diagnostics. |
| Formatting/helpers | `fmt.nq`, `text.nq` | Output-only formatter-lite and exercised internal text/list helpers. No AST formatter or write mode. |
| Owned verification | `proof.nq` | `test`, seed/selfhost/corpus proof, tooling fixtures, deterministic comparison, and proof summaries. |
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
[GRAMMAR.md](GRAMMAR.md). M54.7 repairs their grouping; it does not claim to
replace them with a parser-owned expression arena. Any later migration should
be incremental, identity-preserving, and measured against the M54.6 baseline.

Evidence commands currently have separate collection/validation paths. They
must not be described as equivalent whole-program contract gates: Astra F03,
F05, F08, and F11 identify acceptance/coverage gaps. Canonical contract
validation and truthful evidence completeness are scheduled in M54.8. See
[AUDIT_REMEDIATION.md](AUDIT_REMEDIATION.md) for the explicit closure criteria.

## Values And Generated Code

- `i32` and `i64` are distinct types with exact matching, contextual integer
  literals, and no implicit conversion. Ordinary overflow/division edge
  behavior remains an open corrective item; C behavior is not a language
  specification.
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
  names remain ABI-owned. These are M54.7 repair obligations, not new syntax.

The runtime remains a trust boundary. Allocation-size arithmetic and
interrupted process wait/capture require the separate fixes recorded in the
audit ledger. New Linux APIs must not outrun those foundations.

## Bootstrap And Verification

`bootstrap/seed/nauqc-seed.c` is a versioned, checked-in bootstrap artifact,
with its matching runtime, manifest, and checksums. The active path is:

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
budgets; [STABLE_RELEASE.md](STABLE_RELEASE.md) defines independent release
requirements. Cached success or bootstrap consistency is never evidence of
semantic completeness by itself.

## Direction

Close the confirmed wrong-code, evidence, numeric, and provenance issues
before resuming M55 process/time/cancellation work. The product target is
trustworthy Linux terminal and native application development, not feature
parity with another language. Compiler/runtime changes stay here; general
libraries and AI/ML algorithms have separate owners under
[NAUQTYPE_COORDINATION.md](NAUQTYPE_COORDINATION.md). Apply
[SYNTAX_IDENTITY.md](SYNTAX_IDENTITY.md) before any language widening.
