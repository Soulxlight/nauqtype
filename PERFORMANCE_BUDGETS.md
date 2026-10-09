# Linux Performance Budgets

M53 turns compiler, proof, test, and release-gate resource use into checked
release evidence. These ceilings are regression tripwires, not benchmark
claims or optimization targets.

## Pre-M56 Optimization Work

[PERFORMANCE_CHECKPOINT.md](PERFORMANCE_CHECKPOINT.md) defines the next
bounded performance pass: establish a reproducible Linux baseline, improve
measurement-selected visibility/index scans, then investigate redundant
clone/drop temporaries. It does not change the ceilings below or claim that
external instrumented timings are current release measurements.

The first implementation slice is an opt-in host measurement helper,
`scripts/profile_selfhost.sh`, with focused contract checks in
`scripts/check_profile_selfhost.sh`. It is not a new public compiler command,
mandatory proof phase, or cache producer. Real measurements require the
existing verified stage1 artifact and supported Linux tools; stub tests and
Windows source checks are not performance evidence. Optional instrumentation
is a later attribution step, separate from ordinary wall/RSS measurements.

### Current Priority And Evidence Boundary

Follow [PERFORMANCE_CHECKPOINT.md](PERFORMANCE_CHECKPOINT.md) for optimization
objectives and measurement gates. The latest detailed full-gate phase table is
the historical M55 run recorded in
[AUDIT_REMEDIATION.md](AUDIT_REMEDIATION.md#m55-process-and-time-closure):
2,504 seconds total; driver 488.33s, seed bootstrap 573.54s, proof 1,213.77s,
Linux alpha 13.04s, stress 2.07s, owned tests 156.21s, and ownership
sanitizers 8.23s. Driver, seed bootstrap, and proof account for 2,275.64s
(about 91%) of that run. These are historical measurements, not a fresh WSL
baseline. This checkout currently has no `build/verification` artifacts.

WSL's verified base tools do not establish a current compiler/cache or project
timing. Obtain a reproducible, non-instrumented WSL baseline only after the
owner-controlled checkout and verified stage1 artifact are available; do not
substitute the historical M55 figures. The checked-in wall/RSS ceilings below
remain unchanged. They are release regression limits, not iteration targets;
warm development feedback and cold exact-candidate release proof are distinct.
In particular, the earlier roughly 1.3-second warm `check_fast.sh` figure is
historical and predates the dirty provenance fixture's 30-second timeout, so it
is not a current timing promise. Treat source-copy reduction as a hypothesis to
measure, not proof of faster deep-copy behavior when string references may be
retained; preserve the separate cold proof requirements.

## Contract

`scripts/check_milestone.sh` runs each existing phase exactly once through
`scripts/run_budgeted.sh`. The runner uses GNU `/usr/bin/time` for elapsed wall
seconds and peak resident memory, plus GNU `timeout` for the wall ceiling. A
command that exceeds peak RSS after otherwise succeeding exits `97`; a timed
out command retains GNU timeout's exit `124`.

The runner distinguishes a command's own `124` from GNU timeout overriding a
different observed child exit status, using a private, atomically published
completion receipt. Child stderr cannot fabricate that receipt or the private
timeout diagnostics. An ambiguous `124` (including a timed-out child that
itself returns `124`) or a hard kill without a receipt remains `command`
failure; `137` is preserved. Failure classification never turns those exits
into successful evidence. This conservative boundary is exercised by
`scripts/check_run_budgeted.sh`, also included in the complete fixture tier.

The gate preserves `build/verification/milestone-summary.json` and writes the
separate, deterministic-shape performance artifact at:

```text
build/verification/performance-summary.json
```

Proof evidence remains in `build/proof/summary.json`, using proof-summary v3
after M54.10. Performance measurements remain a separate artifact and do not
change that versioned proof contract; v1/v2 schemas are historical contracts.

## Initial Ceilings

| Phase | Wall seconds | Peak RSS KiB | Purpose |
|---|---:|---:|---|
| `stage1.driver` | 900 | 524,288 | active compiler construction from the frozen seed |
| `seed_bootstrap` | 900 | 1,048,576 | reused-stage1 fixed-point comparison |
| `proof` | 2,400 | 3,145,728 | copied-selfhost, corpus, and tooling proof |
| `linux_alpha` | 300 | 1,572,864 | reused-driver release assembly/smoke |
| `stress_leg` | 300 | 1,572,864 | dense cross-feature release leg |
| `owned_tests` | 600 | 2,097,152 | active Nauqtype-owned fixture suite |
| `ownership_sanitizers` | 300 | 1,048,576 | dense M53 ownership fixtures under ASan/LSan |

The wall ceilings include deliberate clean-checkout CI variance above the
measured M53 ownership-aware baseline. The first GitHub run used 379,108 KiB
but reached the original 480-second stage1 wall ceiling. A second run completed
stage1 in 682.08 seconds at 380,104 KiB and seed proof in 705.36 seconds at
87,980 KiB, then reached the 1,800-second proof ceiling after selfhost and all
38 corpus cases had passed. The final CPU-bound ceilings retain reviewed
headroom over those measurements; the RSS ceilings are unchanged. The composed
gate builds stage1 once, then reuses its seed-emitted C and executable for the
fixed-point comparison; it does not pay a second seed emission. Development
reuse is separately guarded by `scripts/stage1_cache.sh`, whose manifest binds
the complete seed/selfhost input fingerprint plus the generated C and
executable hashes. The full milestone gate still rebuilds from the frozen seed
on every exact candidate.

The corpus proof now spends one frontend/backend pass per case, then compiles
and runs that C directly. Three fixed cases additionally exercise public
`build`/`run` routing, reducing compiler passes for the 38-case corpus
from 114 to 44 without narrowing runtime coverage or the copied-selfhost proof.
Change ceilings only in `scripts/performance_budgets.sh`, backed by a controlled
baseline and review. Do not relax a ceiling merely to hide an unexplained
regression.

## M54.5 Measured Outcome

The reviewed M54.5 candidate passed `scripts/check_milestone.sh` on 2026-09-04
in 2,132 seconds. Its phase totals were 410 seconds for `stage1.driver`, 459
seconds for `seed_bootstrap`, 1,256 seconds for `proof`, and 7 seconds for the
remaining four phases. This is effectively unchanged from the 2,128-second
pre-pass baseline, so M54.5 is not recorded as a cold compiler speedup.

The development-loop improvements are narrower and directly measured: a warm
stage1 cache check takes about 0.16 seconds, a warm `check_fast.sh` takes about
1.3 seconds, and the 38-case corpus takes about 20.8 seconds after reducing its
compiler invocations from 114 to 44. Required audits now happen before the one
full candidate gate, preventing routine audit-repair reruns of the entire cold
chain.

A bounded `gprof` investigation identifies the next optimization boundary.
The instrumented full-tree check spent its largest self-time in repeated module
export and scope-parent queries plus borrow expression lookup, while generated
record and string clone/drop helpers executed hundreds of millions to tens of
billions of times. The instrumented wall time is not a release benchmark;
M54.6 must establish any improvement with comparable non-instrumented
before/after measurements and unchanged semantic/proof outputs.

## M54.6 Measured Outcome

The same-host non-instrumented command
`selfhost/build/nauqc check selfhost/main.nq` took 349.76 seconds and 85,344
KiB peak RSS before the bounded optimization. Function-local scope and
statement slices plus a private borrow-expression child index reduced repeat
runs to 266.84 and 267.94 seconds. One-pass visible-item origin lookup then
reduced repeat runs on the final candidate to 194.66 seconds at 85,492 KiB and
194.51 seconds at 85,208 KiB. The final mean is 194.59 seconds, a 44.4% wall
time reduction with no material memory increase.

The final driver hash for those measurements is
`e23dabd21c4e8a8b99727f748dab0afaad595c91e6ffeb27a9b7c9bb4017c0bf`.
The optimization is private and list-backed: public handoff records, source
semantics, evidence schemas, proof phases, and release budgets are unchanged.
No performance ceiling was relaxed.

The independently audited exact candidate then passed
`scripts/check_milestone.sh` in 1,517 seconds: 411 seconds for
`stage1.driver`, 306 for `seed_bootstrap`, 792 for `proof`, and 8 for all
remaining phases. That is 615 seconds, or 28.8%, below the 2,132-second M54.5
close. The frozen seed-driven `stage1.driver` phase stayed effectively flat;
the measured savings appear in the later phases that execute the optimized
stage1 compiler, rather than being shifted into another phase.

## CI Shape

Push and pull-request CI runs `scripts/check_fast.sh` in one `quick` job. A
clean runner builds stage1 once before the owned fixture tier; a local warm run
reuses it only through the checked cache manifest. The composed full gate stays
serial so its phases can reuse freshly built artifacts, and runs nightly, by
manual dispatch, and on `v*` release tags. Release candidates still run the
independent gates in `STABLE_RELEASE.md`; the quick job is not release proof.
