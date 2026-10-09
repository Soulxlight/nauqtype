# Verification Tiers

Nauqtype's verification is intentionally layered so ordinary milestone work does
not repeat the same expensive selfhost and release proof several times.

## Gate Selection Before Each Run

The immediate priority is the
[PRE-M56 efficiency campaign](PERFORMANCE_CHECKPOINT.md). Choose the smallest
relevant feedback check before starting work, and record elapsed time including
any compiler construction. The broader fixture tier and final close have
separate jobs:

| Change or purpose | Iteration feedback | Acceptance boundary |
| --- | --- | --- |
| Planning or nonpackaged documentation | Diff/relative-link/contract checks | Required documentation audit; no compiler performance claim |
| One compiler behavior or runtime boundary | Relevant existing Nauqtype fixture or focused native/shell probe, using a verified current compiler where needed | Complete fixture tier and unchanged full milestone gate |
| Cache, seed, timeout, or attestation machinery | Focused success, tamper, failure, and interruption probes | Required mixed audit and real complete provenance/seed gate |
| Reviewed executable milestone candidate | Affected checks after any audit repair | One composed full milestone invocation |
| Release candidate or stable freeze | Relevant fixes first | Independent final alpha/stable gates below |

`nauqc test` currently accepts no suite selector. Do not invent a filter flag
or describe the current complete suite as a focused run. P1 owns adding
selection if existing individual probes cannot provide sufficient feedback.
Until then, use the existing direct fixture commands where applicable.

The campaign aims for <=10-second focused feedback, <=60-second warm full
fixtures, and at least a 50% reduction in the new same-host cold gate, with
10 minutes as the working target. These objectives do not change phase
ceilings or required acceptance coverage. A stale compiler rebuild must be
disclosed; exclude it only from an explicitly labeled warm measurement.

## Fast Feedback

Run the Nauqtype-owned fixture and tooling tier:

```bash
scripts/check_fast.sh
```

This is the active local confidence tier. Corpus and copied-selfhost proof
claims run once through `nauqc prove` in the composed milestone gate. The
archived Python unit suite is not part of milestone or release verification.

`check_fast.sh` reuses `selfhost/build/nauqc` only when
`scripts/stage1_cache.sh` proves that the complete selfhost/seed/current-runtime input
fingerprint and both generated artifacts still match. A missing or stale cache
rebuilds automatically; explicit `--reuse-stage1` gates fail closed instead of
silently accepting an executable that merely exists.

M54.10 cache v2 additionally validates the strict seed inventory, derivation
receipt, physical compiler identity/target, and exact flags. Only the builder
publishes a cache, after compiling captured inputs and verifying originals
have not persistently changed. The old standalone `record` operation is gone.
Fast feedback also runs focused provenance and attestation unit/stub checks;
those are not substitutes for a real seed or copied-release proof.

M54's focused upstream checks are also available when changing Linux
input/filesystem or library-resolution contracts:

```bash
bin/nauqc check tests/fixtures/m54_runtime.nq
bin/nauqc check tests/fixtures/m54_library_dependency/vendor/std/src/status.nq
```

The corresponding Python modules are frozen historical host harnesses, not
active focused, milestone, or release gates. Use the Nauqtype-owned fixtures
and current shell/native integration checks. This clarification does not
change the gate selection, budgets, or acceptance boundaries above.

## Milestone Gate

Build stage1 from the frozen seed once, reuse that artifact for the fixed-point
comparison, run the selfhost/corpus/tooling proof once, build and smoke one
Linux release, replay the stress leg against that same release, then run the
fast fixture/tooling tier and ownership sanitizers:

```bash
scripts/check_milestone.sh
```

The command writes a timing and failure-localization artifact to
`build/verification/milestone-summary.json`. Reuse happens only inside this
single invocation, after the stage1 driver and proof have freshly succeeded.

The same invocation enforces the checked-in Linux wall-time and peak-RSS
ceilings without rerunning a phase. It writes those measurements separately to
`build/verification/performance-summary.json`; proof-summary v3 is separate.
See [PERFORMANCE_BUDGETS.md](PERFORMANCE_BUDGETS.md) for the runner
contract, initial ceilings, and CI rationale.

The locked corpus performs one stage1 `emit-c`, one host-C compile, and one
native run for every case. Exactly `hello`, `multi_file_main`, and
`m53_ownership_values` additionally exercise the public `build` and `run`
routes and compare their normalized C with the canonical `emit-c` output. The
proof-summary v3 keeps the artifact roles: `build_c` records the
C that was compiled and `run_c` records the C behind the executed program;
`corpus.structural_c_compare` includes the three command-routing comparisons.

Artifact hashes are explicit SHA-256 objects, never `nqsum` attestations.
Skipped/unreached artifacts and unperformed comparisons are null, even when
stale files exist. Earlier summary schemas remain available for historical
evidence; active proof emits v3.

The gate captures the indexed candidate before running and verifies source,
toolchain, cache, proof, and copied-release identities afterward. Its strict
`build/verification/milestone-attestation-v1.json` can be checked with
`scripts/milestone_attestation.sh verify`. Run from a fully indexed frozen
candidate. For the five explicitly allowlisted nonpackaged completion docs,
`scripts/milestone_attestation.sh close <full-commit-id>` and `verify-close`
bind a disclosed documentation delta; no source, schema, script, README, or
release artifact change is permitted after the gate. These records detect
staleness/transplants, not a malicious owner rewriting every trust root.

## Milestone Close Order

Use the expensive gate only after the candidate is ready:

1. Iterate with focused checks.
2. Freeze the diff and run the required trailing audit or audits.
3. Repair findings and rerun only affected focused checks.
4. Run `scripts/check_milestone.sh` once on that exact candidate.

Any source change after the full run invalidates that evidence. This ordering
removes the former audit/fix/full-gate repetition without weakening what the
final green run proves.

## CI Tiers

Pushes and pull requests run the clearly named `quick` job from
`.github/workflows/quick.yml`. The complete Linux Alpha workflow runs nightly,
on manual dispatch, and for `v*` release tags. A milestone still requires an
exact-candidate local full gate before commit/push; release candidates retain
the independent checks below. Configure branch protection to require `quick`.

## Final Alpha Gate

The final stable-surface gate remains deliberately redundant:

```bash
bin/nauqc prove
scripts/check_linux_alpha.sh
scripts/run_stress_leg.sh
scripts/check_seed_bootstrap.sh
```

Run it for release candidates and stable-surface freezes. These independent
commands remain intentionally stronger than the composed ordinary milestone
gate.
