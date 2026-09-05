# M54.8 Contract And Evidence Corrections

Status: M54.8a complete, 2026-09-05. Focused checks, independent trailing and
repair audits, and the replacement frozen-candidate executable gate passed.
The parent M54.8 milestone remains open for M54.8b.

The owning repository is NauqType. Library, AIML, and Tool Codex workspaces and
their drafts are outside this write set. No new syntax, runtime authority,
ownership model, or Python implementation is part of this work.

## M54.8a: One Contract Validation Boundary

- Extract and validate the existing fixed audit grammar once per checked
  project: `intent`, `mutates`, `effects`, then optional `propagates`.
- Return structured diagnostics and the existing review summary; retain the
  extracted function/declaration facts for review/diff/change renderers.
  Propagation declarations retain their resolved semantic target IDs.
- All compilation and evidence commands reject the same invalid source
  contracts before emission, execution, or checked-success output.
- The outer driver emits diagnostics exactly once per analyzed input.
  Warnings remain nonfatal, including absent public audits. Policy-backed
  change reporting does not emit after-input warnings a second time.
- Use `NQ-CONTRACT-002` for malformed fixed grammar, with the unexpected or
  missing-token span; allow trailing commas, but not empty interior entries.
  Keep `NQ-CONTRACT-010` for duplicate names. Use `NQ-PROPAGATE-006` for an
  unresolved or non-type propagation declaration, without an overdeclaration
  warning for the same invalid entry.
- Preserve direct-only mutation inference. Its absence of a write cannot
  prove overdeclaration in a function containing calls, so emit
  `NQ-CONTRACT-006` only for a call-free body without the declared direct
  write. Do not erase declarations or claim a complete inferred footprint.
- Compiler and tooling share the value-plan completeness invariant and its
  existing internal diagnostic identities. Test missing counts synthetically.
  Output files are written only after internal summary checks succeed.
- Keep successful output shapes and schemas unchanged. Keep the M54.7 seed
  pinned unless the existing bootstrap/fixed-point proof requires a refresh.

Intended write set: `selfhost/review.nq`, `selfhost/main.nq`, the narrow shared
value-plan invariant and probe, `selfhost/proof.nq`, new Nauqtype fixtures,
proven-invalid existing audit declarations, and focused contract/status docs.
No blanket golden regeneration or proof-normalizer changes.

## Focused Acceptance

The invalid-source matrix covers `check`, `emit-c`, `build`, `run`, facts
v1/v2/v3, review v1/v2, review-diff v1/v2, change-report v1/v2, policy-check,
and refactor-rename. It requires nonzero exits, exactly one primary source
diagnostic per invalid input, no replacement of existing output artifacts,
no execution of the program, and no checked-success JSON.

Fixtures cover missing effects; invalid/omitted direct mutation; call-free
versus call-containing overdeclaration; malformed/missing/repeated/reordered
clauses and comma boundaries; builtin/local/imported public propagation types
versus unknown/value/hidden names; absent-public-audit warnings; and synthetic
missing type-property/value-use coverage. Valid warnings still allow output.

Use the owned fixture/golden gate and focused commands during development,
then independent trailing audit and one frozen `scripts/check_milestone.sh`.
Record exact evidence and any compatibility fixture correction. Do not rerun
an equivalent gate or modify successful JSON schemas to silence a failure.

## Implementation Evidence

- `selfhost/build/nauqc emit-c selfhost/main.nq -o build/m54_8/combined.c`
  bootstrapped the combined source from the preceding M54.7 executable in
  251.97 seconds; `cc -std=c11 -O2 -D_POSIX_C_SOURCE=200809L -Istdlib
  build/m54_8/combined.c stdlib/runtime.c -o build/m54_8/combined` succeeded.
- `build/m54_8/combined test` passed in 4.15 seconds. This includes the new
  15-route invalid-contract matrix, strict grammar/type fixtures, warnings,
  sentinel/no-execution checks, synthetic coverage probe, and existing
  fixture/golden checks. The copied-selfhost module list includes the new
  shared coverage module.
- Focused `check --diagnostics json` runs verified missing effects and a
  quoted-comma grammar error each fail with one correctly spanned primary
  diagnostic, while an absent-public-audit warning leaves `ok: true`.
- `build/m54_8/combined fmt --check` passed for both
  `selfhost/checked_coverage.nq` and `selfhost/probe_checked_coverage.nq`.
- `build/m54_8/combined prove-corpus` passed all 42 locked cases in 22.67
  seconds, without changing structural comparison or expected runtime output.
- Existing `examples/for_list.nq` and the M53 control-boundary fixture
  incorrectly declared local variables in `mutates(...)`; those declarations
  now correctly name no mutref parameters. Runtime behavior is unchanged.
- The existing named-argument facts golden remains byte-for-byte unchanged.
  Its unaudited public function now produces exactly one expected warning on
  stderr; the fixture assertion permits only that named warning, not blanket
  stderr suppression.

Gate A: Sol xhigh returned PASS after resolving strict grammar, mutation
warning conservatism, extracted target identity, and warning ownership choices.
Gate B: the same independent Sol xhigh auditor returned PASS on the actual
combined diff and focused evidence, with no blocking findings. Repeated
internal facts collection for policy-backed change reporting remains a
non-blocking F15 efficiency follow-up; diagnostics are emitted once.
The final gate must prove the unchanged seed builds the reviewed source and
that current-source self-build, release, corpus, and sanitizers remain green.

The first frozen gate stopped after 1,292 seconds at the tooling refactor
assertion: the legacy named-argument rename fixture still required empty
stderr despite its expected public-audit warning. The repair requires exactly
one `NQ-CONTRACT-001` and the same successful plan fields, and reuses that
assertion in the fast M54.8a tests. No compiler behavior, fixture source, or
golden changed for this repair. The earlier gate is failed evidence only;
a fresh full gate is required after focused replay and repair audit.

Focused repair replay: a temporary copy of `selfhost/proof.nq` with only a
small `main` entrypoint called the complete tooling-confidence gate and owned
test gate against `build/m54_8/combined`. Direct execution from the repository
root, `build/m54_8/proof_probe/build/main`, passed in 221.53 seconds, including
the full-tree policy check. This tests the revised proof functions without
rerunning self-build first; it does not replace the frozen full gate. The
probe and its copied imports are ignored build artifacts, not new CLI surface.
The independent Sol xhigh repair audit returned PASS, preserving the original
plan assertions and requiring the exact single warning. A new frozen full
gate, not the failed run's successful phases, owns final acceptance.

## Frozen Close Evidence

The replacement `scripts/check_milestone.sh` passed all seven phases in 1,520
seconds (25 minutes 20 seconds), with no stderr and no budget violations:
stage1 driver 301s, seed bootstrap 332s, proof 874s, Linux alpha 4s, stress leg
2s, owned tests 4s, ownership sanitizers 3s. The proof covers all 42 locked
corpus cases, copied-selfhost structural comparison, and tooling evidence.
The pinned M54.7 seed is unchanged.

The clean indexed snapshot `/tmp/nauqtype-m54-8a-final-Oq8VAM` and canonical
checkout both had tree `b5c35a2c451b05c6b0a931661fc73fc70eb4b736` and framed
tracked path/content/Git-mode SHA-256
`e767d3884c25293c466696af0fc1c68e0da04ee62e517f584ee1d60b087b54fe`
before and after the gate. Only non-packaged completion/evidence documents
changed afterward; compiler, fixtures, schemas, runtime, seed, and packaged
README stayed frozen. Unrelated AIML/tooling drafts were excluded.

Generated build/proof/release evidence was copied back byte-for-byte, the
compiler was atomically replaced, and the matching cache manifest was
published last. Input fingerprint:
`52e03640345a9c15243bd225a7e26396c23bcd0b01afae8ab6d6bc91af8fa6e7`.
Canonical `scripts/stage1_cache.sh require`, `bin/nauqc version`, and
`bin/nauqc check tests/fixtures/m54_8a/trailing_comma_ok.nq` passed afterward.

| Artifact | SHA-256 |
| --- | --- |
| `build/verification/milestone-summary.json` | `99c46f4d43fc8e716f3e80bcdb730495fc9c4ada5abb9310027438aa31804bd6` |
| `build/verification/performance-summary.json` | `7ac77c69cf318667e46f90cd4d0e4bbdd92bca793da2ff2a5247765f517d7731` |
| `build/proof/summary.json` | `cd1157b736cc9d4995496c5b1427777798ca0260918ee597873afc2c92d7a682` |
| `selfhost/build/nauqc` | `a78cc4a6a544462e2026aba0a8da85d4eb931cc9b32faa15714f3953c30d673b` |

Logs and the failed first gate summaries remain under `build/m54_8/`.
No Python gate ran. There were two full-gate attempts, not two equivalent
passing runs: the first exposed the legacy assertion, and only the fully
repeated replacement run closes the repaired candidate.

## Remaining M54.8 Work

M54.8a is not completion of M54.8. A separately reviewed versioned migration
must close F05's mutation coverage and call summaries, F08's absent-audit
provenance, and F11's policy/schema/failure-envelope inconsistencies. General
F15 producer duplication and repair guidance remain open. In particular,
current change-report v2 failure envelopes and review v2 absent-audit evidence
are known limitations, not made truthful by consistent rejection alone.
