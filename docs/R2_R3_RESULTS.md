# R2/R3 Measurements And Compatibility

Measured 2026-10-19 on Ubuntu 24.04 WSL2, native ext4, GCC 13.3.0,
`x86_64-linux-gnu`, ordinary production flags. This report records focused
evidence, not the final milestone gate or a stable release. Final acceptance
and remaining work belong in [TODO](../TODO.md#current-refactor-checkpoint).
The [execution contract](R2_R3_CONTRACT.md) and exact
[37-row matrix](R2_R3_MATRIX.txt) remain the comparison authority.

## Measured Boundary

R2 adds phase-owned immutable visibility ranges, borrowed through recursive
typing and handoff construction. R3 shares only the identical facts/review
IO-subkind and propagation-error tables. Existing wrappers, checked-builtin
guards, policy identities, syntax, schemas, runtime, and proof edges remain.
These measurements describe the combined candidate, not an isolated causal
estimate for either extraction or each indexed helper.

The original `scripts/profile_selfhost.sh` ran twice per checkout. Then the
new compiler checked the exact retained baseline input twice, serially, with
input and executable hashes rechecked. No compiler build ran alongside the
measurements. No instrumented timing is used as a production speedup.

| Check | Wall seconds | Peak RSS KiB | Spread |
| --- | --- | --- | --- |
| Reference compiler on baseline tree | 333.80, 331.23 | 104060, 104060 | 0.776% |
| Candidate on expanded current tree | 289.82, 289.36 | 104436, 104564 | 0.159% |
| Candidate on identical baseline inputs | 269.12, 268.30 | 108028, 108008 | 0.306% |

The identical-input means are 332.515s and 268.710s: **19.19% less wall time**,
or 1.237x throughput, with about 3.8% higher maximum RSS. Current-tree checks
average 289.590s, 12.91% less than the old-tree reference, despite the added
source/test modules; that comparison intentionally includes source changes.
All spreads satisfy the existing 10% repeatability limit.

### Costs Kept Separate

| Cost | Reference | Candidate |
| --- | --- | --- |
| Profile setup | 6.444s | 5.566s |
| Source capture | 3.417s / 15580081 bytes | 2.355s / 15618868 bytes |
| Pre-measurement copy | 0.010s / 5352406 bytes | 0.006s / 5441606 bytes |
| Pre-run hash validation | 4.179s | 3.547s |
| Post-run hash validation | 5.033s | 3.907s |
| Complete two-run profile, including cleanup | 687.246s | 596.945s |

Candidate cache validation separately took 2.20s / 3920 KiB. The actual
predecessor-seed construction took 543.80s / 438144 KiB; this paid the old
compiler's cost and is not a measurement of the optimized gate. Exact
self-re-emission took 388.22s / 108808 KiB. These are construction costs, not
substitutes for the final seven-phase acceptance run.

Focused compile/run probes also cost real time: the reference-driven final
visibility oracle took 29.72s / 288696 KiB; the new compiler's typecheck probe
took 47.99s / 334148 KiB. Builtin-table, import-collision, and hidden-import
probes took 1.48s, 12.65s, and 13.40s respectively and exited zero with empty
stdout/stderr. They are different probes, not an old/new timing pair.
The broader <=10s feedback, <=60s complete warm-fixture, >=50% cold-gate,
and <=10-minute working goals remain open. No budgets or coverage were cut.

## Compatibility And Source Evidence

All 37 matrix rows matched exit status, stdout, and stderr byte-for-byte;
the six emitted user-program C files also matched byte-for-byte. The explicit
propagation example correctly retains exit 7. Physical argv records differ
by compiler/output path and are retained, not falsely compared as identical.
No golden was rewritten.

The old public signatures (81 across the five changed historical modules),
all old function names, and eleven policy target names remain. R2's oracle
compares the old linear implementation, indexed implementation, and independent
expected origins, including interleaved runs. R3 tests 48 independent inputs
per shared table, including defaults and near misses. These focused checks
complement, not replace, owned tests, proof, release, and sanitizer coverage.

## Identities And Seed

- Base revision: `1105a7e195d50c12c66082a812e6cf79d0ba74c6`.
- Construction index tree: `ed2506626852ca443fc3db9c77b1d03e505ea72e`.
- Frozen source tree SHA-256: `0e7d7046570cf99b704b7f8f9b4d2c92a73cf5b9ce0ce19e0afb1d3153d16a85`.
- Common baseline inputs SHA-256: `6db84fc52abdceae3b348095ee1b59d16a7af43474cb950451c38859813f93d8`.
- Reference executable SHA-256: `f685a64569519c298d3b003de3a30bcef497e02d31b625d3219a62792746a767`.
- Candidate/generator executable SHA-256: `d766e07e4621ad399fb022b37958594604f6693200be06f2511f9d868f4796ab`.
- Predecessor seed C SHA-256: `5221d8ab5c788140bea2a079b2a37bc2de6204c0939399bf328c6803d3f0bc08`.
- Actual generator input, re-emitted output, and promoted seed C SHA-256: `1d3a29919dd5a44a61732096ce2071311b86b97d658b1c49e178e35f913223e2`.
- Exact 74-file snapshot inventory SHA-256: `0d39d2ce970b7326ade7acd1ea87fa4457e2c02f8d94beae3b0fd348d38bdd20`.

The strict seed v2 manifest records full runtime, compiler, target, flag,
snapshot, and predecessor identities. C is compiler-generated, never manually
edited. Two pre-publication attempts safely stopped on the recipe's relative
path misuse of an absolute-path provenance helper; both logs were retained,
the recipe was repaired and independently reviewed, and only the successful
exact emission was promoted. Post-install input checks run before the
promotion's commit marker while catchable-failure rollback remains active.

## Retained Receipts And Scope

Local receipts use `build/verification/refactor-r2-r3-20261019/`: compatibility
before/after, native profile/measurement records, focused probe logs, recipe,
seed readback, and later final-gate evidence. Full native input captures remain
in the single campaign, rather than being recopied for each command. Receipts
are local evidence, not tracked release artifacts or a new public interface.

No fresh controlled pre-change cold gate was run. Any comparison with earlier
P0/P2/R1 cold gates is historical context, not a same-day cold A/B experiment.
R4-R6, the wider PRE-M56 campaign, and M56-M61 remain separate. No downstream
library checkout, consumer lock, archived Python implementation, or optional
paid model workflow changed.
