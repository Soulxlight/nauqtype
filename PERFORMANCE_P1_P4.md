# PRE-M56 P1-P4 Performance Evidence (Provisional)

Status: pre-close component report,2026-10-19. At this capture P1-P4 are not
complete; this report does not change the acceptance contract in
[`PERFORMANCE_CHECKPOINT.md`](PERFORMANCE_CHECKPOINT.md) or
[`docs/P1_P4_CONTRACT.md`](docs/P1_P4_CONTRACT.md). The working tree is dirty
on the reported base `a833b31`; this is not a frozen candidate identity. The
lead's ignored `STATE.md` and native receipts are the source of the in-flight
measurements summarized here.
Later frozen-gate acceptance, if obtained, belongs in the allowlisted
completion ledger [`AUDIT_REMEDIATION.md`](AUDIT_REMEDIATION.md), not a rewrite
of this pre-gate report after its candidate has been attested.

## Concurrent Warm Pre-Close Follow-Up

As of2026-10-21, exact seed/runtime propagation and the reviewed `03a3b53`
seven-phase native gate pass in1011.04s/520388KiB,59.89% below P0. Its focused
route takes0.64s and complete serial warm100.58s. Those remain historical
candidate-bound observations, not acceptance of subsequent host-script edits.

The owner explicitly approved only the opt-in local concurrent warm tier.
The first complete observation took46.99s with aggregate peak94785536B;
a separate postcheck proves all23 receipt bodies/inodes/mtimes plus protected
input/toolchain/boot/index/artifact readbacks unchanged. Its measurement wrapper
stopped on benign retired-cgroup stderr before a second warm pass. The narrow
diagnostic repair passes67 UNIT/native checks in25.31s, but audits also require
uncertain common-lock retention, independent running-manager version checks
and explicit pre-resource/pre-ACK rejection evidence for a detached child.

Those bounded repairs, repeated whole-tier timing and the new frozen gate are
still pending at this report's freeze. Default/full-milestone/proof/release
remain serial; no test-result cache, compiler/runtime behavior or language
feature is added by this host tier. See the
[contract](docs/P1_CONCURRENT_WARM_CONTRACT.md) and later
[completion ledger](AUDIT_REMEDIATION.md#pre-m56-concurrent-warm-close).

## Warm Follow-Up Candidate

The earlier frozen candidate's1055.02s seven-phase close and128.52s warm
result are recorded in
[the completion ledger](AUDIT_REMEDIATION.md#pre-m56-p1-p4-functional-candidate).
They do not attest the new follow-up source changes described here. The60s
warm goal remains strict; M56 is held and no owner waiver is assumed.

Same-session component attribution selected two small follow-ups, each
independently cleared at Gate A. Literal scanning preserves the original
byte predicates and adds98 bounded matrix/four runtime-source oracle pairs.
The runtime change only shortens the first five no-I/O exit recheck attempts;
it preserves deadlines, ownership, signals, drain/reap order and API shape.
EINTR counts toward the five-attempt allowance. See the
[literal-scan contract](docs/P1_FIXTURE_SCAN_CONTRACT.md) and
[recheck contract](docs/P1_PROCESS_RECHECK_CONTRACT.md).

| Ordinary component comparison | Before, seconds | After, seconds | Boundary |
| --- | --- | --- | --- |
| Literal scan, old runtime fixed |29.16,28.46|25.35,25.19|12.29% lower mean wall;2.43%/.63% repeat spreads. All cache-oracle checks and fresh protected readbacks pass. |
| Recheck policy, new literal scan fixed |25.05,25.90|12.12,11.78|53.09% lower mean wall;3.34%/2.85% repeat spreads. Fixture CC inputs remain the old runtime in both variants, isolating the parent policy. |

Both comparisons used O2 without profiling and interleaved before/after/
after/before order in one native session. They are component evidence, not
end-to-end speedups; do not multiply the percentages or extend the old gate.
All six existing native process fixtures passed with the original ASan/UBSan
flags, expected stdout and empty stderr, including seven new scheduling
assertions. Source, toolchain, artifact, boot, cache and attestation readbacks
pass on the retained native candidate. Its tracked files were not replaced
by the captured runtime experiments.

An ignored poll observer identified1,498 all-negative-FD waits consuming
15.147s of a29.562s diagnostic run. Instrumentation selected the window; the
ordinary pairs above measure the actual component change. A proposed
timeout137 acceleration was withdrawn without implementation because safely
anchoring its supervisor would need disproportionate new machinery. Every
original budget-runner case and the production grace policy stay unchanged.

The follow-up still needs trailing source review, legitimate current-compiler
construction, a complete warm measurement, exact seed/runtime propagation
and a fresh frozen seven-phase close. Earlier acceptance is not transferred
to changed source bytes.

## Baselines And Current Measurements

| Evidence | Result | Boundary |
| --- | ---: | --- |
| P0 cold seven-phase gate | 2520.62s | Accepted baseline; see [`PERFORMANCE_BASELINE.md`](PERFORMANCE_BASELINE.md). |
| R456 cold seven-phase gate | 2304.10s | Current comparison receipt; not the final P1-P4 gate. |
| Fresh ordinary full-tree checks | 291.72s, 289.05s; mean 290.385s | Reference checks, not the <=60s owned-fixture tier. |
| Reference warm-tier run | 173.385372168s | Baseline complete tier, not final acceptance. |
| V8 focused current-cache feedback | 1.70s, RSS4108 KiB | Focused goal met on this intermediate candidate. |
| V8 complete warm tier | 109.97s, RSS63452 KiB | All tests passed; unchanged receipt metadata is observability, not cache authority. The60s goal remains unmet. |
| V10 focused current-cache feedback | 0.71s, RSS4428 KiB | Real seed-built intermediate compiler; includes current-cache validation. |
| V10 complete warm tier | 115.71s, RSS63436 KiB | All existing tests ran serially; all23 fixture receipts remained unchanged. The60s goal is missed. |
| Component-driver ordinary check | 126.68s, RSS 109148 KiB | Exploratory single run using common old source; not a repeated before/after binary pair and not a final timing claim. |
| V9 ordinary common-source checks | 94.78s, 95.80s; mean95.290s | Same retained e9d3 source/CC;1.076% repeat spread. Observed67.18% less wall time than the fresh reference pair. Not a complete-gate claim. |
| V10 ordinary common-source emissions | 196.50s, 197.37s; mean196.935s | Production flags, identical retained source, unchanged CC and reference index; both complete C outputs match the reference bytes. Baseline for the separate C-emission membership slice. |
| V11 ordinary common-source checks | 94.46s, 93.38s; mean93.920s | Real seed-built compiler;1.157% repeat spread and67.66% observed wall reduction versus the fresh reference pair. |
| V11 ordinary common-source emissions | 96.79s, 97.56s; mean97.175s | 0.796% repeat spread;50.66% observed wall reduction versus the V10 emission pair. Both complete C outputs match the reference bytes. |
| Cache V8 component probe | 15.04s, 21948 KiB | Focused component evidence only, including real CR refusal; V8 is a probe version, not a pass count. |

The cold-gate comparison is provisional until the exact current candidate has
passed its final gate. The126.68s observation is exploratory; the later V9
pair uses identical retained inputs and production flags. Its peak RSS is
109004/109412KiB, versus108788/108912KiB reference. The reference pair preceded
V9 in time, not randomized/interleaved; stable hashes and low repeat spread
do not establish a controlled causal study. Diagnostic `-pg` attribution is
never production timing.

## Implemented And Focused Evidence

- Bounded compiler suite routing and host-unit routing are implemented with
  fixed names and fail-closed selection; the no-argument path retains the
  complete default sequence. The selected compiler-index route includes the
  new index oracles once registered by the lead. See
  [`scripts/check_fast.sh`](scripts/check_fast.sh) and the relevant
  `nauqc test` implementation in [`selfhost/main.nq`](selfhost/main.nq) and
  [`selfhost/proof.nq`](selfhost/proof.nq).
- The V8 cache oracle passed in15.04s. V7 evidence includes20
  actual JSON-context receipts and a zero-output negative case; producer,
  current-working-directory, environment, and runtime changes were exercised.
  Cache reuse is raw-environment/pipe-only, with Ubuntu/GCC 13/LF closure,
  refusal, symlink, and live-fault checks retained.
- The serial host path avoids concurrent host checks. The new provenance,
  attestation, budget, capture, and index oracles are bounded components, not
  replacement proof schemas or reductions in required default coverage.
- The earlier indexed component's diagnostic, before the later review-call
  membership slice, reports drops moving from
  32,298,298,848 to 13,258,906,043 and retains from 32,272,177,637 to
  13,232,675,596. Function-parameter clone count moves from 1,244,426,528 to
  6,934,682; checked-parameter clone count from 1,136,280,579 to 46,595,721.
  These are diagnostic event counts, not measured deep-copy counts or
  production-time savings. GCC aliasing affects per-helper attribution.

V9's82-command compatibility matrix passes before/after: all11 present user
C artifacts match exactly, and exits/evidence/runtime output remain identical
apart from the explicitly added test-selector help text. No golden changed.
The real V9 component construction used the verified V8 producer, emitted C
in270.29s and compiled it in45.17s/498680KiB. It is not a current-cache
derivation or the final seed-builder/gate. `-pg` supports attribution only.

V10 was constructed through the actual old-seed builder in659.47s with
499152KiB peak RSS, inside the unchanged900s/524288KiB production ceiling.
Its generated C equals the V9 component C; the executable identities differ,
so V9 check timings are not relabeled as a final-binary measurement. The V10
source, toolchain, artifacts, cache derivation and running-kernel identities
were read back. Later source repairs intentionally require a new construction.

The separate V10 C-emission diagnostic ran in400.57s with `-pg`. Cleanup,
child-link, parameter-local and block-statement scans account for about half
its sampled flat self time. This supports the bounded IR-only membership
proposal in [`docs/P2_C_EMIT_MEMBERSHIP_CONTRACT.md`](docs/P2_C_EMIT_MEMBERSHIP_CONTRACT.md),
not a predicted speedup. Its full emitted reference C is byte-identical.

The C-emission slice now has a quiet passing direct probe:18 owner/collection
configurations,10 literal emission-order cases,3 signatures and a missing-child
negative. An initial fixture-layout failure was localized and repaired without
changing literal expectations or production behavior. This functional WSL/DrvFS
probe is not a native performance measurement or a whole-compiler acceptance.

The integrated V11 old-seed construction passed in599.83s/519020KiB under
the unchanged900s/524288KiB ceiling; its compiler-index route passed in0.10s.
Both independent trailing source audits passed frozen tree
`59170a93fce708855f41a237f875b8a6b5c00842`. This leaves5268KiB of measured
compiler-build RSS headroom, not permission to relax the ceiling. The one
native candidate received1,487,090 changed bytes in24.865071774s; it was not
recopied for every probe.

V11's fresh82-command before/after matrix passes, including all11 present C
artifacts. Complete C bytes, exits, cwd, evidence and runtime output agree,
except for the deliberately expanded test-selector help text. Ordinary V11
measurements use the unchanged e9d3 source and CC, with source, artifact,
kernel-boot, toolchain, index and cache readbacks. Checks peak at108796/108700KiB;
emissions at108744/109664KiB. These serial historical pairs are not randomized
causal estimates. No diagnostic `-pg` timing enters their comparisons.

The actual V11 compiler C SHA-256 is
`f3e07bc8f01b3b30a06bcd9ed79391f82bcf69537c229a9abe445c904e83fcdc`;
its executable SHA-256 is
`b433c28985766400a085523162c8b5b820b31d35865db351f857b3529ebd599f`.
Neither is a promoted seed or final-gate attestation at this report's freeze.

Both independent B1 audits initially required repairs. Focused repair evidence
now includes real GCC PCH introduction/removal refusal,185 metadata cases,
16 seed-capture cases,28 batch/scalar/write-fault cases,10 routing spies,151
attestation assertions, and direct adapter/full-record/nested-cleanup oracles.
The same auditors passed the narrow repairs independently. Those verdicts do
not attest a final seed, complete candidate, or unrun seven-phase gate.

An ignored research note rejected adding a tar-based validation context:
fresh membership and archive-binding work would remain necessary, and no
warm-tier saving was demonstrated. No such context or scheduler was added.

## Acceptance At This Freeze

- Measure the complete warm fixture tier, including provenance and cache
  validation, and the focused feedback path against their goals.
- Finish seed propagation and the required mixed independent audits, then run
  one seven-phase close on the exact reviewed candidate with final attestation.
- Report the resulting total and phase times, RSS, setup/copy/hash costs,
  achieved goals, and remaining gaps. Any repair after the gate requires
  affected focused checks and a fresh complete gate.

The goals remain <=10s focused feedback, <=60s complete warm fixtures, and at
least 50% cold-gate reduction versus P0 (10 minutes is the working target).
Focused feedback meets its goal on an intermediate candidate. The complete
warm target is missed; no owner waiver is assumed. The final cold goal is
unmeasured. Preserve all default
coverage, interruption/tamper checks, seed/provenance proofs, and the existing
proof/evidence schemas.
