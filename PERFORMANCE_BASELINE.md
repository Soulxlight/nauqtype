# PRE-M56 Native Baseline

Measured 2026-09-30 local time (2026-10-01 UTC). P0 is complete; P1-P4 and
the speed goals remain open. These are uninstrumented baseline measurements,
not an achieved speedup or a new language milestone.

## Candidate And Host

- Base revision: `f289fd6b785c7983b003810b48fccf02f67e413f`.
- Reviewed, indexed candidate: `27e9e57bea55cbf100d8cede2780f7878f4026f7`.
  The index, not HEAD or the capture directory name, identifies the candidate.
- Candidate SHA-256: `c18eee5246ac4d8665c0c347bcffd77e7ab4caf99a05b6bb792b513342cac87a`.
  Final attestation verified identical before/after identities and a matching
  worktree. The canonical Windows index was not staged or changed.
- Ubuntu 24.04 WSL2, native ext4, non-root user, GCC 13.3.0, target
  `x86_64-linux-gnu`, Git 2.43.0, GNU time and timeout 9.4.
- Bootstrap/proof compilation retains `-std=c11 -O2
  -D_POSIX_C_SOURCE=200809L`; no flags or budgets were changed.
- Seed manifest: `684a904faf510b475052d0e6b5c7b67e84834e9e4dc1af37144eb2ac15281268`.
- Build inputs: `d890c91ff74f51a6448e5beaf6345ce11e817ea636fae3a5abadfa2fc02a9fa2`.
- Verified driver: `faaad197d7b3291ddaea3684c7fbb3aff07ac729ba3caa119d5f494cee06c88d`.

The reports below were written after measuring that frozen candidate. They
do not extend its attestation to a later edited tree or establish library
integration. The native candidate and logs are retained, not recopied for
every measurement.

## Cold Complete Gate

`bash scripts/check_milestone.sh` passed once. The launching shell checked that
the seed and stage1 executables were absent in the fresh capture; this cold
precondition is a command-transcript observation, not a separately retained
preflight receipt in the compact packet. Outer GNU time recorded **2520.62s**, peak RSS
**433332 KiB**, exit 0. All seven phases and final attestation passed.

| Phase | Wall seconds | Peak RSS KiB |
| --- | ---: | ---: |
| stage1.driver | 485.37 | 433332 |
| seed_bootstrap | 575.08 | 102580 |
| proof | 1268.57 | 432664 |
| linux_alpha | 10.30 | 63004 |
| stress_leg | 1.93 | 63148 |
| owned_tests | 150.20 | 135544 |
| ownership_sanitizers | 5.87 | 56824 |

Driver, seed proof, and combined proof account for 92.4% of outer elapsed
time. Seed timing subdivides into historical comparison 81s, stage2 emission
402s, and current comparison 82s; the sidecar has one-second resolution.
Both direct comparisons remain required. Historical emission reuse was
validated (`historical_reused=true`), not assumed from an existing file.

The historical M55 2504s result is from another host and is not a speedup
comparison. The 150.20s owned-test phase is not a separate controlled warm
fixture benchmark; no <=60s warm-tier claim is established.

## Repeated Verified-Compiler Checks

`bash scripts/profile_selfhost.sh` reused the verified driver and one pinned
source capture for two serial `nauqc check selfhost/main.nq` runs.

| Run | Wall seconds | Peak RSS KiB |
| --- | ---: | ---: |
| 1 | 304.23 | 106684 |
| 2 | 308.99 | 106832 |

Both checks succeeded. Spread `100 * (max - min) / min` is **1.565%** wall
and **0.139%** RSS, within the 10% admissibility boundary. Version-2 summary
and all inspected JSON receipts parsed successfully. Original and copied
source, driver, toolchain, cache, and budget-runner identities were verified
before and after measurement.

| Workflow cost | Seconds | Bytes copied |
| --- | ---: | ---: |
| Setup/preflight | 4.402 | Not a copy counter |
| Source capture | 4.749 | 15327700 |
| Driver and budget-runner copy | 0.004 | 5260206 |
| Pre-run hash/identity validation | 3.344 | Not a copy counter |
| Post-run hash/identity validation | 2.444 | Not a copy counter |
| Complete profile workflow, including cleanup | 629.962 | See separate copy rows |

Outer GNU time recorded 629.99s and 106832 KiB. Nanosecond fields are
realtime clock readings, not nanosecond accuracy or a monotonic-clock claim.
Unallocated elapsed time includes command startup, publication, and remaining
bookkeeping; these rows are not an exhaustive cost attribution.

The following setup figures are operator observations from command results,
not retained transfer receipts or audited P0 timing evidence. Initial native
candidate transfer was a 20971520-byte archive: 0.413s
index/archive creation and 2.369s whole native setup invocation, including
WSL startup, clone, extraction, and indexing. Reviewed repairs were transferred
once as a 122880-byte delta: 0.337s index/archive creation and 3.101s native
application/verification invocation. Archive hashing was outside those capture
stopwatches. These are setup observations, not complete gate copy counters.

## Gate Work Inventory

This is the code-path inventory, not a claim of per-operation timing or exact
total bytes hashed across the gate. Only the costs above were measured.

| Phase | Required work and reuse boundary |
| --- | --- |
| stage1.driver | Independent input capture; compile frozen seed C; seed emits current C; compile current driver; verify source/toolchain/artifacts and publish cache/derivation |
| seed_bootstrap | Separate checked input capture and copied verified artifacts; validate historical reuse; two direct structural comparisons and current stage2 C emission; recheck source/toolchain/cache hashes |
| proof | Copied selfhost workspace, two emitters and compiled stage2, normalized structural comparison; locked corpus emit/compile/run and public-route samples; tooling goldens/policy, fresh artifact hashes and proof summary |
| linux_alpha | Reuse verified stage1, skip the already-run repo proof; independently copy/verify release and smoke it outside the repository |
| stress_leg | Reuse that copied release in an isolated dense workspace, preserving focused failure/evidence checks |
| owned_tests | Reuse checked compiler; Nauqtype-owned tests plus full provenance, attestation, and budget-runner fixture suites; synthetic captures/faults remain separate from real compiler evidence |
| ownership_sanitizers | Sanitizer availability probe; nine fixture C emissions, host compilations, and ASan/LSan executions |

Attestation brackets the complete gate with indexed-tree, source, artifact,
toolchain, proof, and release identity checks. Independent release captures
and both seed comparisons must not be removed to meet a time goal.

## Repairs And Focused Evidence

Audits ran before freezing the measured tree. Primary Sol xhigh and
adversarial Astra xhigh returned PASS on their assigned repair scopes; the
historical GPT-5.5 model was unavailable, as recorded in `AGENT_ROUTING.md`.

- Seed publication now invalidates stale success before fallible setup,
  checks every JSON write, and handles interruption during finalization.
  Focused publication assertions: 32 PASS; complete provenance: 156 PASS.
- Budget results distinguish observed wall timeout from direct exit 124.
  A private, complete child-exit receipt prevents forged target stderr from
  proving a timeout. Ambiguous 124 and receiptless hard-kill 137 remain command
  failures. Fourteen focused cases passed; budgets are unchanged.
- Profile identity includes the actual copied runner; workflow cost fields
  and success publication include finalization/cleanup. Twenty synthetic
  cases passed; they are not the real baseline.
- Full attestation fixture suite: 151 PASS. Changed scripts passed syntax
  checks, and the candidate subsequently passed the real full gate above.

Raw compact evidence is retained locally under
`build/verification/p0-20260930/` with `SHA256SUMS`; native full artifacts
remain in the frozen WSL capture. Generated receipts contain real host paths
and stay ignored, rather than becoming portable source documentation.

## Next Work

1. P1: use the focused fixture paths already available; measure a narrow
   selection/capture/hash improvement while retaining the complete close.
   `nauqc test` still has no suite selector.
2. P2: investigate compiler visibility/membership work and structural
   comparison mapping/string costs. The comparisons already stream normalized
   lines. A five-minute check and two ~81s comparisons warrant attribution;
   the separate-host v3 report remains a hypothesis, not local proof.
3. P3: change clone/drop transfers only after demonstrating redundant work
   and preserving cleanup; retain counts are not deep-copy byte counts.
4. P4: propagate any compiler improvement through real seed regeneration,
   audit, then one final cold seven-phase gate on the reviewed candidate.

Reusing captures avoids churn, but this measured source capture is seconds
while compiler work is minutes. Prioritize proven dominant computation rather
than claiming copy reuse alone solves the cold gate. The >=50% same-host
reduction and <=10-minute working target remain goals, not outcomes.
