# M54.8 Contract And Evidence Corrections

Status: M54.8a and M54.8b1 complete, 2026-09-05. Both passed independent
audits and frozen-candidate executable gates. M54.8b1 closes only review-v3
emitter/golden coherence; the parent M54.8 milestone remains open.

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

### M54.8b1: Review Evidence Migration

Gate A: independent Sol xhigh PASS after locking the following bounded slice.
Implementation, focused replay, Gate B, and the frozen executable close passed.

- Add opt-in `review --format v3` only. Preserve review v1/v2 success JSON,
  defaults, schemas, and goldens; diff/change-report still reject v3.
- Set `evidence.audit` to `absent` exactly when `audit` is null, otherwise
  `declared`. Keep `evidence.inferred` as `checked`.
- Export direct assignments to mutable reference parameters from checked
  statement/binding/parameter identities, not name matching. Deduplicate and
  order inferred names by parameter index. Validate dense one-based binding
  lookup, function identity, parameter identity, and borrow bits. Impossible
  checked data emits `NQ-INTERNAL-012`, fails, and produces no review JSON.
- Every v3 function carries the same capability-level `mutation_coverage`:
  interpretation `lower_bound`, scope `direct_mutref_parameter_assignments`,
  completeness `partial`, and ordered uncovered categories
  `builtin_call_writes`, `local_call_writes`, `imported_call_writes`.
  This is a lower bound on syntactically observed parameter writes, not a
  claim of path feasibility, purity, or full validation. Owned-local field
  writes are outside the parameter contract, not an uncovered category.
- v3 remains successful-output-only: invalid input exits nonzero with
  diagnostics on stderr and empty stdout. Warnings are nonfatal and emitted
  once. There is no new JSON failure envelope in this slice.
- Publish a strict Draft 2020-12 v3 schema with audit/evidence coherence.
  Owned tests prove emitter/golden coherence, not general schema validation.
  Any external standards-validator check is auxiliary evidence only; standing
  F08 schema enforcement remains open. No broad JSON engine is added.
- Cover audited/absent public/private functions, reverse-order and repeated
  assignments, shadowing, builtin/local/imported call-only writes, single
  warnings, source failures, synthetic invalid checked IDs, and legacy output.

The compiler repository owns `selfhost/review.nq`, `selfhost/main.nq`, CLI
help, `selfhost/proof.nq`, focused Nauqtype fixtures/goldens, the v3 schema,
and contract/status documentation. No parser, runtime, ownership, seed, Python,
other-repository, or source-validation change is intended.

Follow-up: checked call summaries must use canonical child parameter indexes,
builtin mutation summaries, and a recursive fixed point. Source-contract
validation currently precedes handoff and must be split or moved deliberately
before enforcing those summaries. Missing callee/argument truth must retain
partial coverage. b1 does not close that work, diff/change failure envelopes,
or F15 diagnostics.

Development evidence: the first candidate was emitted by the installed M54.8a
compiler in 282.06 seconds, then compiled with host C. Its v3 fixture output
has eight functions, correct absent/declared markers, `first, second` direct
writes in parameter order despite reversed/repeated assignments, no shadow
write attributed to the parameter, and explicitly partial builtin/local/
imported call-only coverage. Exactly one public-audit warning was emitted.
The legacy v1 golden was captured from the unchanged M54.8a compiler; v2's
existing schema and golden were not edited.

Auxiliary `npm exec --yes --package=ajv-cli@5.0.0 -- ajv validate
--spec=draft2020 --strict=false -s schemas/review-v3.schema.json -d
tests/golden/review/review_v3.json` accepted the positive golden. The same
validator rejected all four generated malformed cases: null/declared,
object/absent, missing coverage, and a numeric mutation-array entry.
These ignored build artifacts and the cached external validator do not add
an active toolchain dependency or a standing schema gate.

The first `build/m54_8b/candidate test` failed at the new unsupported-format
assertion: the pre-existing CLI prints argument errors on stdout, unlike
source diagnostics. The test now requires nonzero status, the exact route's
message, and no versioned JSON for unsupported diff/change v3, while retaining
empty stdout for review-v3 source failures. CLI behavior was not changed to
satisfy the test. The focused replay and audited frozen gate below supersede
that failed run; the failure is not acceptance evidence.

### M54.8b1 Close Evidence

- The repaired candidate emitted successfully in 282.41s and host C compiled
  it. `build/m54_8b/repaired test` passed in 4.05s, including twelve direct
  identity cases. `build/m54_8b/repaired prove-corpus` passed all 42 cases in
  22.72s. No Python gate ran.
- `build/m54_8b/repaired review selfhost/main.nq --format v3` passed in
  280.52s without diagnostics: 1,467 functions, 1,251 absent audits, 35 direct
  writers, all audit markers coherent, and every function explicitly partial.
  Auxiliary Draft 2020-12 validation also accepted this full-tree output.
- Independent Sol xhigh Gate B returned PASS on the exact staged diff and
  focused evidence, authorizing one frozen full gate. No source repair was
  needed after that audit.
- One `scripts/check_milestone.sh` passed all seven phases in 1,574s:
  driver 307s, seed bootstrap 346s, proof 908s, Linux alpha 4s, stress leg 1s,
  owned tests 5s, ownership sanitizers 3s. No stderr or budget violation.

The indexed snapshot `/tmp/nauqtype-m54-8b1-final-JVHl4w` and canonical
checkout matched tree `1b9b3495b67a35267150d73c5b3529ace5500562` and the
ordered tracked path/content SHA-256 digest
`2a2abb1515461cccb795483ea51dee5f8409d920666633bb4fc8585734e8084f`
before and after the gate. The digest command was
`git ls-files -z | xargs -0 sha256sum -- | sha256sum`; Git tree identity and
`git diff --exit-code` also protected file modes and index/worktree agreement.
Unrelated drafts were excluded. Only non-packaged status/evidence documents
changed afterward; source, schemas, fixtures, seed, and packaged README stayed
frozen.

| Artifact | SHA-256 |
| --- | --- |
| `build/verification/milestone-summary.json` | `9602d679322627b06e83237cd7f4a807032e3d48c368dfa44ae45a35c3c762b9` |
| `build/verification/performance-summary.json` | `2875107c44d8f65e5147618d28d9c7adbf1ea8a40cbb980877143d7288d858ac` |
| `build/proof/summary.json` | `d0ec9cbe11be70af4453b84967cfbfa16e5ca474fe1eac8a94c9e46927bfaaa7` |
| `selfhost/build/nauqc` | `fcc5899891e3e8d2873827c80b519e464e950ec02721e1f9650ef2f05621038d` |
| stage1/copy-selfhost C | `029c36799be140b0c99b5f5ed55b873970bac4f0fa98cd19ddf11770c594e6a5` |

Verified generated artifacts were copied back, the compiler replaced atomically,
and its matching cache manifest published last. Input fingerprint:
`51580c2c84cddd4f2ba526c601f70a0f24892d48f8ccd3e5cd2fe2bec1471d03`.
Canonical `scripts/stage1_cache.sh require` and
`scripts/verify_linux_release.sh build/linux-release/nauqtype` passed.
The M54.7 seed remains unchanged. Logs live under `build/m54_8b/`.

M54.8a is not completion of M54.8. A separately reviewed versioned migration
must close F05's mutation coverage and call summaries, F08's absent-audit
provenance, and F11's policy/schema/failure-envelope inconsistencies. General
F15 producer duplication and repair guidance remain open. In particular,
current change-report v2 failure envelopes and review v2 absent-audit evidence
are known limitations, not made truthful by consistent rejection alone.
