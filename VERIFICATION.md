# Verification Tiers

Nauqtype's verification is intentionally layered so ordinary milestone work does
not repeat the same expensive selfhost and release proof several times.

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
python3 -m unittest tests.test_m54_runtime tests.test_m54_library_dependency -v
bin/nauqc check tests/fixtures/m54_runtime.nq
bin/nauqc check tests/fixtures/m54_library_dependency/vendor/std/src/status.nq
```

The Python modules are bounded host harnesses around the Nauqtype-owned stage1
compiler and native executables; they do not implement active compiler
behavior.

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
