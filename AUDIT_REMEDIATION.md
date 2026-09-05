# Astra Audit Remediation

Status: M54.7 and M54.8 complete, 2026-09-05. M54.9/M54.10 remain open.
Feature expansion waits for
the remaining evidence, numeric, and provenance prerequisites below.

The 2026-09-04 Astra audit reviewed `d2c7592ae5e4dc11fba7ffe715334a881d715b62`.
Its report and executable evidence are retained locally in
`/home/soulxlight/Documents/Astra Audit NauqType/`:

- `NauqType Audit Report.md`, SHA-256
  `e28e646077cf5bba781241b4a18b23138f13a2094059b7813840fc0cfd7f09aa`;
- `audit-evidence.json`, SHA-256
  `6a0343d772cb108e3e5df8b3011db1808710ce01daf0cadeb8106dc21b03ba70`.

This file records the owning team's disposition and executable closure
criteria. A green self-build proves compiler consistency; specification-based
expected results are also required to prove the affected language behavior.

## M54.7: Expression And C Backend Correctness

Status: complete. Independent Sol xhigh and GPT-5.5 xhigh source and seed-delta
audits returned PASS, followed by the clean frozen-candidate milestone gate.

- F01: select rightmost operators at each left-associative precedence level in
  both typechecking and checked-handoff construction. Keep equality below
  relational comparison as specified in `GRAMMAR.md`. Preserve parentheses,
  unary operators, operand evaluation order, and exact integer typing.
- F02: preserve the first matching arm for enum, option, and result statement
  and expression matches. A fallback before a later specific arm must win;
  later duplicate cases must not produce duplicate C labels. Use the existing
  ordered condition-chain lowering for all matches, preserving scrutinee,
  binding, and control-flow cleanup. The sanitizer exposed a missing
  expression-arm binding drop; the exporter now closes that arm scope after
  transferring the result, using existing canonical cleanup.
- F04: use injective C encodings for source-derived identifiers, including
  user fields, enum members, module paths, and named generic payloads. Keep
  semantic identities and runtime-native ABI names unchanged.
- Refresh the generated C seed as required by the changed output. Record its
  generating source snapshot, generator identity, and checksums, then prove
  the fixed point using the existing structural comparison. Do not normalize
  away differences in operators, control flow, or user identifiers.

Acceptance: permanent Nauqtype fixtures for both integer widths, chained and
mixed operators, parenthesized controls, side-effect order, fallback-first and
fallback-last matches, wildcard/binding arms, repeated constructor arms, owned
payload cleanup, C-keyword names, and distinct module/type names that formerly
collided. Run the owned fixture and corpus paths, focused ownership sanitizers,
independent mixed-model trailing audits, then one frozen-candidate milestone
gate. New expected values come from the specification, not generated goldens.

## Follow-Up Sequence

| Slice | Findings | Required closure |
| --- | --- | --- |
| M54.8: Canonical contract and evidence validation | F03, F05, F08, F11, F15 | Make commands agree on contract validity; resolve contract names; distinguish absent declarations and partial mutation coverage; version any changed evidence shape explicitly; give failures truthful requested-version envelopes and deduplicated producer diagnostics. |
| M54.9: Integer and allocation-size semantics | F06, F13 | Record ordinary overflow/division/negation behavior at both widths; implement it without C undefined behavior; check size/capacity arithmetic; exercise runtime edges at `-O0` and `-O2` plus UBSan and injected capacity limits. |
| M54.10: Dependency and verification provenance | F07, F09, F10, F12 | Version framed source-tree locks; reject path/boundary/enumeration changes; enforce seed provenance; bind cache publication and gate evidence to captured source/artifact identities; retain direct proof comparisons and distinguish triage checksums from cryptographic identities. |
| M55 prerequisite: Process wait correctness | F14 | Retry interrupted read/wait operations where appropriate; distinguish failures; guarantee child reaping and capture cleanup before adding deadlines or cancellation. |
| Current documentation map | F16 | Correct active architecture, module/loop capability guidance, and historical present-tense claims. Treat old milestone records as history rather than current implementation contracts. |

F05 is a documented direct-assignment-only inference limit. That does not
justify presenting partial mutation evidence as a complete empty footprint.
First make coverage explicit, then add builtin and resolved-call summaries with
named-argument mapping and a bounded fixed point. Its closure belongs with the
evidence milestone rather than an ownership-model expansion.

F09's current seed record must be refreshed during M54.7 because C output
changes. Automatic rejection of an unrecorded future seed refresh remains in
M54.10; updating a manifest alone does not close that enforcement finding.

M54.8 is split at its compatibility boundary. M54.8a shares strict source
contract extraction/validation and value-plan completeness checks across
commands. M54.8b retains F05/F08, the remaining F11 schema/failure-envelope
work, and F15 producer diagnostics. The reviewed implementation contract is
[M54_8_CONTRACTS.md](M54_8_CONTRACTS.md). No successful schema is silently
changed in M54.8a, and the parent milestone remains open.

M54.8a is complete as of 2026-09-05. Independent Sol xhigh source and repair
audits returned PASS; the replacement frozen candidate passed all seven
`scripts/check_milestone.sh` phases in 1,520 seconds. The first attempt exposed
an obsolete empty-stderr refactor assertion, which was narrowly repaired and
added to fast coverage before the complete repeat. F03's inconsistent
source-contract acceptance is corrected. This does not close F05/F08, general
F11 envelopes, or general F15 duplication; exact hashes, failed-run provenance,
and remaining scope are in `M54_8_CONTRACTS.md`.

M54.8b1 completed the bounded review-v3 migration: absent/declared audit
emission, checked-ID direct assignments, and explicit partial lower-bound
coverage. Independent Sol xhigh audit PASS and one 1,574-second frozen gate
close emitter/golden coherence only. It does not close call-summary validation,
standing F08 standards
schema enforcement, F11 diff/change failure envelopes, or F15 diagnostics.

The final M54.8 implementation now has focused green evidence for those
remaining contracts: checked call-aware mutation validation and review v4,
explicit change-report v3 policy truth, shared evidence-error v1 failures,
producer diagnostic deduplication, and an owned bounded schema profile.
Candidate3 owned tests passed in 7.48s and all 42 corpus cases in 22.85s.
The independently compiled final schema repair passed its focused probes.
The final independent audits returned PASS. Frozen tree
`79a954257ea43e976d2a5f0003561af060f1d874` passed all seven milestone phases
in 1,908 seconds. `M54_8_CONTRACTS.md` records exact command, timing, hashes,
and the bounded bootstrap-runtime repair. M54.8 is complete; no
numeric/provenance finding is closed by this work.

## Architecture And Product Direction

The active implementation is `selfhost/` plus the narrow C runtime in
`stdlib/`. The frozen C seed is the bootstrap boundary; the Python compiler and
unit suites are historical references. See [ARCHITECTURE.md](ARCHITECTURE.md)
for the active phase map and [VERIFICATION.md](VERIFICATION.md) for gate order.

Preserve M54.6's measured scope and child indexes. After corrective closure,
migrate expression/type families incrementally to parser-owned, ID-addressed
structures so semantic consumers do not reinterpret token spans. Measure each
slice against current wall time, memory, diagnostics, and evidence. This is a
separate reviewed architecture project; it is not a prerequisite rewrite for
the immediate wrong-code repairs.

The later Linux direction remains structured process/time/cancellation,
explicit numerical and storage contracts, qualified type provenance, bounded
generic reuse, data facilities, FFI, and tasks. General-purpose modules remain
owned by NQType Libraries; numerical reference algorithms remain owned by
NQType AI/ML. Their provisional requests are coordinated in
[NAUQTYPE_COORDINATION.md](NAUQTYPE_COORDINATION.md).

## Verification Record

- Baseline: `scripts/stage1_cache.sh require` passed at `d2c7592` before edits.
- Initial fixtures reproduced old precedence rejection, duplicate C case
  labels, illegal C members, and colliding-name declaration failure.
- The initial seed bridge caught an unsupported source `else if` spelling in
  the new helper; it was corrected to existing nested `if` syntax before the
  successful build. An exploratory whole-file formatter check for `c_emit.nq`
  was not green; this pass does not reformat the pre-existing compiler file.
  Canonical new fixtures are checked separately.
- The first ownership sanitizer run failed with 1,280 leaked bytes in 128
  allocations. The missing expression-arm cleanup was repaired rather than
  weakening the fixture. Its in-progress seed emission was stopped and
  discarded, not recorded as a successful bootstrap artifact.
- Repaired `build/m54_7/E2 test` passed (`nauqtype test ok`), and
  `build/m54_7/E2 prove-corpus` passed all 42 locked cases. The initial four
  direct M54.7 runs used E1 and exited 0 with empty output; the repaired E2
  owned suite reran all four entrypoints after the cleanup correction.
- All nine fixtures listed in `scripts/check_m53_ownership.sh` were emitted
  using E2, compiled with C11/address sanitizer against `stdlib/runtime.c`, and
  passed with leak detection enabled. A further move-only list-payload arm
  regression passed normal execution and the same sanitizer after addition.
- All six new Nauqtype source files pass E2 `fmt --check`; focused relative
  documentation link checks, shell syntax, and `git diff --check` pass.
- The regenerated C2/C3/C4 snapshots have identical SHA-256
  `9cabe9044b148eb1f76ef254f95c1e85565fa0a849872ae7e126ef4cc5f0efc1`.
  Both `E2 prove-seed C2.c C3.c` and `E3 prove-seed C3.c C4.c` passed the
  unchanged structural normalizer. C3 was promoted byte-for-byte; seed runtime
  C/H stayed unchanged. `bootstrap/seed/manifest.json` records the complete
  observed lineage and source digest, and all four `SHA256SUMS` entries pass.
- Source and final seed-delta audits returned PASS from independent
  `gpt-5.6-sol` xhigh and `gpt-5.5` xhigh auditors. Neither auditor edited the
  candidate or ran duplicate builds.
- One `scripts/check_milestone.sh` passed on the reviewed, clean indexed
  snapshot `/tmp/nauqtype-m54.7-candidate-vpz0Fj`, starting without generated
  artifacts. All seven phases passed in 1,390 seconds (23 minutes 10 seconds)
  with unchanged wall/RSS budgets: stage1 driver 293s, seed bootstrap 302s,
  proof 784s, Linux alpha 3s, stress leg 2s, owned tests 3s, and ownership
  sanitizers 3s. The proof contains 42 corpus cases and all 12 phase IDs.
- The snapshot and canonical checkout had identical indexed tree
  `8cfec279b4d60fd3fae27d16f9c9b5596b8b4add` and full tracked
  path/content/Git-mode digest
  `0e95673c1be7baefc600bea52d80361e08debafab3e1e315cf5e26202da04bbe`
  before and after the gate. The digest frames the version
  `nauqtype-candidate/v1`, then NUL-delimited path, Git-style mode, and content
  SHA-256 for each byte-sorted tracked path. Only completion/evidence
  documentation changed after that frozen gate; executable and packaged
  release inputs did not change.
- All 230 files under the snapshot's `build/` were preserved byte-for-byte
  in the canonical checkout, including proof C artifacts, corpus artifacts,
  release layout, and performance results. The compiler was atomically
  replaced, then its cache manifest was published last. Both inputs had
  fingerprint
  `f79d9f733fb3b95d2eb7d1d6501519d6a0e65179703e79b7bf4e1608a9620574`.
  Canonical `scripts/stage1_cache.sh require`, `bin/nauqc version`, and direct
  runs of the operator and module-name fixtures passed after relocation.
- No Python gate ran; active verification is Nauqtype plus the existing
  shell/host-C boundary. No second equivalent full gate was run.

The local evidence is under `build/verification/`, `build/proof/`, and
`build/m54_7/`. The stress workspace is also retained at
`build/m54_7/stress-workspace`. These generated files are ignored, not source
inputs; their SHA-256 identities anchor the observed closure:

| Artifact | SHA-256 |
| --- | --- |
| `build/verification/milestone-summary.json` | `06ee62e35159161d8ddd686158b4c9fccd8e12c6b32f7268753d80489b2da474` |
| `build/verification/performance-summary.json` | `393cb4ecf5c445e03bcb60b8611dc5b1b9cd7774c3cfeed092ebf3396f444ff5` |
| `build/proof/summary.json` | `fa9f419bd6fdd905a8a26b87a3376b04c503dd999ebf97e8c96b9004aa09ca81` |
| Copied-selfhost stage1 and stage2 C (both) | `9cabe9044b148eb1f76ef254f95c1e85565fa0a849872ae7e126ef4cc5f0efc1` |
| Published `selfhost/build/nauqc` | `56b17fd0299273b8eaede99955279072972a9d980233f3bf6640fd19428847a3` |
