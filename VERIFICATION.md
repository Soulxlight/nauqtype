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
`build/verification/performance-summary.json`; proof-summary v2 remains
unchanged. See [PERFORMANCE_BUDGETS.md](PERFORMANCE_BUDGETS.md) for the runner
contract, initial ceilings, and CI rationale.

## Final Alpha Gate

The final stable-surface gate remains deliberately redundant:

```bash
bin/nauqc prove
scripts/check_linux_alpha.sh
scripts/run_stress_leg.sh
scripts/check_seed_bootstrap.sh
```

Run it for M37, release candidates, and any change that affects release
assembly, proof infrastructure, or the selfhost compiler boundary.
