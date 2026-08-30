# Linux Performance Budgets

M53 turns compiler, proof, test, and release-gate resource use into checked
release evidence. These ceilings are regression tripwires, not benchmark
claims or optimization targets.

## Contract

`scripts/check_milestone.sh` runs each existing phase exactly once through
`scripts/run_budgeted.sh`. The runner uses GNU `/usr/bin/time` for elapsed wall
seconds and peak resident memory, plus GNU `timeout` for the wall ceiling. A
command that exceeds peak RSS after otherwise succeeding exits `97`; a timed
out command retains GNU timeout's exit `124`.

The gate preserves `build/verification/milestone-summary.json` and writes the
separate, deterministic-shape performance artifact at:

```text
build/verification/performance-summary.json
```

Proof evidence remains in `build/proof/summary.json`; performance measurements
do not change proof-summary v2.

## Initial Ceilings

| Phase | Wall seconds | Peak RSS KiB | Purpose |
|---|---:|---:|---|
| `stage1.driver` | 720 | 524,288 | active compiler construction from the frozen seed |
| `seed_bootstrap` | 720 | 1,048,576 | reused-stage1 fixed-point comparison |
| `proof` | 1,800 | 3,145,728 | copied-selfhost, corpus, and tooling proof |
| `linux_alpha` | 300 | 1,572,864 | reused-driver release assembly/smoke |
| `stress_leg` | 300 | 1,572,864 | dense cross-feature release leg |
| `owned_tests` | 600 | 2,097,152 | active Nauqtype-owned fixture suite |
| `ownership_sanitizers` | 300 | 1,048,576 | dense M53 ownership fixtures under ASan/LSan |

The wall ceilings include deliberate clean-checkout CI variance above the
measured M53 ownership-aware baseline. The first GitHub clean-checkout run used
379,108 KiB but reached the original 480-second stage1 wall ceiling, so the
three CPU-bound compiler/proof ceilings include a 50 percent runner margin;
the measured RSS ceilings are unchanged. The composed gate builds stage1 once,
then reuses its seed-emitted C and executable for the fixed-point comparison;
it does not pay a second seed emission. Change ceilings only in
`scripts/performance_budgets.sh`, backed by a controlled baseline and review.
Do not relax a ceiling merely to hide an unexplained regression.

## CI Shape

Linux CI runs the one composed milestone gate. It is intentionally not split
into nominally parallel jobs because isolated runners cannot reuse the freshly
built stage1 executable, proof result, or release layout; that split would
duplicate the slow work this gate was designed to consolidate.
