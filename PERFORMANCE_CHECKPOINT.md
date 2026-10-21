# PRE-M56 Performance Checkpoint

Priority updated 2026-10-21: shorten the development feedback loop and the
complete milestone gate before starting M56. M55 remains the last completed
language milestone. P0 now has an audited native-ext4 baseline: the complete
gate passed in 2520.62s and repeated full-tree checks passed in 304.23s and
308.99s. See
[PERFORMANCE_BASELINE.md](PERFORMANCE_BASELINE.md) for identities, costs, and
the exact baseline boundary.

Current P1-P4 component work is recorded separately in
[PERFORMANCE_P1_P4.md](PERFORMANCE_P1_P4.md). Repeated common-source compiler
checks improve. The later frozen `03a3b53` seven-phase gate passed in1011.04s,
59.89% less elapsed time than P0; its post-gate focused route passed in0.64s.
Complete serial warm100.58s still misses60s. The owner approved an opt-in local
concurrent warm tier on2026-10-21; its first guarded complete observation was
46.99s, followed by audit-driven host-script repairs. Repeat timings, trailing
audits and a fresh complete gate are required for the changed candidate.
Later acceptance belongs in the
[completion ledger](AUDIT_REMEDIATION.md#pre-m56-concurrent-warm-close), not an
extension of earlier attestations. The10min cold working target is distinct
from the required>=50% reduction and remains unmet at this pre-close freeze.

## Goals And Current Evidence

| Measurement | Campaign goal | Evidence needed |
| --- | --- | --- |
| Focused feedback with a verified current compiler | At most 10 seconds | Timed relevant checks; disclose any compiler rebuild separately |
| Warm complete fixture tier | At most 60 seconds | Time the complete tier, including provenance tests and cache validation |
| Cold complete milestone gate | At least 50% less elapsed time than the new same-host baseline; working target at most 10 minutes | All seven phases, final attestation, phase wall/RSS, and comparable source/toolchain identities |

These are engineering goals, not measured results or replacements for the
checked-in wall/RSS ceilings. Missing a goal keeps the efficiency work open;
it does not justify dropping a proof edge, test, or diagnostic. Report total
time including setup, snapshot/hash work, compiler rebuilds, and cleanup so a
faster inner command cannot hide a slower complete workflow.

The recorded M55 gate took 2,504 seconds: driver 488.33, seed bootstrap
573.54, proof 1,213.77, Linux alpha 13.04, stress 2.07, owned tests 156.21,
and sanitizers 8.23 seconds. The first three phases account for about 91% of
the recorded total. This historical host is not the new WSL baseline. See
[AUDIT_REMEDIATION.md](AUDIT_REMEDIATION.md#m55-process-and-time-closure) for the source report;
the M55 section records exact artifact identities.

## Contract

### P0: Reproducible Baseline

- Use a dedicated, separately verified supported Linux runner with a native
  filesystem for the baseline. WSL2 Ubuntu 24.04 now runs with a non-root
  user, native ext4 home, and GCC 13.3.0. The reviewed P0 compiler capture,
  cache, complete gate, and repeated-check evidence are now recorded in
  `PERFORMANCE_BASELINE.md`; library integration remains separate.
  Do not hardcode a local checkout path or infer Linux results from the Windows
  host or the read-only relay check, which lacked `cc`.
- The helper's initial filesystem allowlist is native `ext4`, checked through
  mount type and filesystem identity for both checkout and snapshot. Windows
  mounts, network filesystems, and unverified filesystem types are rejected.
  Supporting another native filesystem requires a separately verified change.
- `scripts/profile_selfhost.sh` is the first-slice measurement helper. It
  requires the current verified cache and runs two non-instrumented full-tree
  checks. `scripts/check_profile_selfhost.sh` is a stub/contract test; it must
  not require a real verified driver or produce a P0 measurement.
- P0 is complete for indexed candidate
  `27e9e57bea55cbf100d8cede2780f7878f4026f7`. Later source changes do not inherit
  that candidate's attestation. P1-P4 remain open.
- Capture one immutable native-filesystem candidate and reuse that capture
  for its repeated measurements. Record snapshot/hash duration and copied
  bytes separately; do not recreate a complete checkout for each probe.
- Inventory each gate's compiler emissions, host-C compilations, comparisons,
  source captures, and hashing. Existing seed phase instrumentation in the
  dirty tree passed independent repair audits and focused checks before the
  indexed baseline; phase timing does not replace comparison/provenance proof.
- Obtain one cold complete-gate baseline on a reviewed, indexed candidate.
  This deliberate baseline run and the final acceptance run are separate
  measurements; intermediate optimization slices use focused checks.
- Record source revision/content identity, seed identity, compiler identity,
  target, and flags before measuring.
- Run two ordinary repeated full-tree checks and record wall time and peak RSS.
  For each metric define repeat spread exactly as `100 * (max - min) / min`.
  A spread `<=10%` is admissible; `>10%` is inconclusive, not a speedup or
  regression. Cold release proof is separate from this repeated warm/cache
  measurement.
- Optional `gprof` attribution may follow later; it is diagnostic only, not
  release timing or release evidence, and is not implemented in this first
  slice.

### P1: Iteration And Snapshot Reuse

Choose the relevant existing fixture/command before launching a broad suite.
The in-flight P1-P4 candidate adds fixed `nauqc test --suite` and
`scripts/check_fast.sh --suite` selectors, plus explicitly host-unit-only
routes. A published older compiler may not implement them. Scope-specific
feedback must retain the complete fixture tier at milestone close.

Measure cache validation, fixture startup, copied source bytes, and hash/read
passes. The in-flight candidate replaces the former30-second interruption
wait with ready-triggered interruption of a real blocked phase. Completion,
timeout exit, unreached phases, cleanup and missing receipt assertions remain.
The0.71-second V10 focused result and115.71-second complete warm result are
different measurements; neither extends an earlier candidate's attestation.

Only share inputs whose content and derivation have been checked. Preserve
isolated mutable outputs, failed/unreached artifact handling, dependency and
toolchain pins, and fresh captures required by independent release proofs.
An existing file, directory name, or matching timestamp is insufficient.

### P2: Compiler And Comparison Hotspots

Authorized exception PRE-M56 E1: one explicit borrowed `str_join` primitive
may unblock linear compiler text assembly before full M56. Follow
`PERFORMANCE_ENABLEMENT.md` and the syntax/evidence SOP; no other language
growth is authorized. Measurements and the frozen acceptance gate remain
required; this exception does not complete P1-P4.

Measure only a selected candidate involving visibility precomputation or the
existing function-index ranges. Preserve shadowing, ambiguity, origin
provenance, and output order. Any candidate that cannot demonstrate those
invariants remains a hypothesis. Compare the selected scan/index optimization
against the previous implementation on the same inputs.

Also attribute the two seed comparisons and copied-selfhost structural
comparison. Current comparison already streams normalized lines; investigate
remaining mapping scans and per-character string construction only when
phase measurements support it. Preserve both direct seed comparisons and
the existing normalization result, including negative mismatch fixtures.

P2 mapping slice (2026-10-04): local diagnostic profiling of the frozen E1
driver attributes 79.65% of sampled CPU to mapping lookup. This authorizes
one private, incremental append-only sorted-run index in `selfhost/proof.nq`,
not a general indexing subsystem or a new runtime primitive. Preserve four
independent namespaces (left/right times binding/tmp), exact digit-text keys,
one-based first-appearance ordinals, complete token recognition, and current
behavior inside quoted C text. No integer-key conversion or full-input
pre-scan is permitted. Each current line is fully normalized on both sides;
comparison stops before later lines after the first mismatch. Retained sorted
ranges may increase memory; report that cost rather than hiding it.

Keep the original 15-pair oracle and add adversarial old-key reuse, decimal
keys beyond integer range, leading-zero families, failed prefixes, quoted
tokens, independent namespaces, and early mismatch with a large suffix.
Measure two production runs per driver on identical hashed inputs and GCC
flags, recording order, spread, wall time, and RSS. Instrumented `-pg` results
are attribution only. Regenerate the exact seed before freezing the final
diff for mixed-model audits, then run one complete reviewed seven-phase gate.

### P3: Clone/Drop Temporaries

Measure existing clone/drop temporary transfers before editing. Change only a
proven redundant transfer, and require cleanup and behavior proof; success does
not mean every clone was removed. String clone retain counts are counts of retain
operations, not proof of deep byte copies. Source-copy reductions precede any
new borrowing syntax.

### P4: Frozen Acceptance And Seed Propagation

Review focused results before one complete final gate on the indexed
candidate. Preserve all seven phases, existing proof/schema contracts,
copied-release independence, sanitizers, and final attestation. Compiler
improvements must reach the frozen seed through the existing actual
compile/re-emission and provenance procedure; never edit generated C or
bless an old binary to make the driver phase appear faster.

Compare total and phase time with P0, report memory and setup costs, and
explain any slower phase. Record achieved reductions and remaining goal gaps
before reopening M56. A necessary cold baseline and final close are allowed;
repeated full closes during every repair are not the development loop.

## Evidence Order And Scope

Keep warm reuse distinct from a cold release measurement. Use focused tests,
then an independent audit, then one frozen full gate on the reviewed candidate.
Any source or contract change after that gate invalidates its evidence.

New reference syntax, parallel runtime/compiler work, split C translation
units, and flag changes are separate proposals, not part of this checkpoint.

The externally supplied `Nauqtype_Gate_Performance_Recommendation_Sheet.md`
(report title: v3; received-file SHA-256
`6d5a4a8d36c76ebcf7251ec44fb3e8fa490be226f8a1cb0335c4f9f4fb7a003e`)
reports 33.7B clone/drop events for each category in `gprof` and a
separate-host 24% visible-lookup figure. Its tested source revision is
`f289fd6`; that revision does not identify the report or its raw profiles.
The report remains external, and those observations are unverified in this
checkout. Treat them as hypotheses to reproduce, not current measurements
or a seconds promise for this repository.
