# Verification Tiers

Nauqtype's verification is intentionally layered so ordinary milestone work does
not repeat the same expensive selfhost and release proof several times.

## Fast Feedback

Run focused compiler/reference tests plus any feature-specific test modules:

```bash
scripts/check_fast.sh tests.test_field_assignment
```

This excludes copied-selfhost proof and release-layout work. It is for rapid
local feedback, not release approval.

## Milestone Gate

Run the selfhost proof once, build and smoke one Linux release, replay the
stress leg against that same release, then run the fast tier:

```bash
scripts/check_milestone.sh tests.test_field_assignment
```

The command writes a timing and failure-localization artifact to
`build/verification/milestone-summary.json`. Reuse happens only inside this
single invocation, after the stage1 driver and proof have freshly succeeded.

## Final Alpha Gate

The final stable-surface gate remains deliberately redundant:

```bash
bin/nauqc prove
scripts/check_linux_alpha.sh
scripts/run_stress_leg.sh
python3 -m unittest discover -s tests -v
```

Run it for M37, release candidates, and any change that affects release
assembly, proof infrastructure, or the selfhost compiler boundary.
