# Archived Status Narratives (to 2026-10-30)

Moved here on 2026-10-31 under the AGENTS.md status-document hygiene rule.
The two sections below are verbatim from commit `e34d459` (`ROADMAP.md`
"Current Position And Resumption" through "Documentation And Refactor
Checkpoint", and the top of `TODO.md`), with only relative links adjusted
for this location. They are dated records, not current status.

Headings are demoted one level so they nest under this document.

## From ROADMAP.md

### Current Position And Resumption

M55, the required PRE-M56 P1-P4 efficiency goals, and M56 explicit generic
reuse have recorded Linux acceptance. M56's reviewed frozen tree
`67272d00dd7d3e6cbb3945cc5777141148ff2cc1` passes all seven milestone phases
and strict attestation in1137.41s. The project remains an organizational
alpha, not a v1.0 stable or feature-complete terminal/application language.
M57-M61 below remain the release sequence; earlier sections retain milestone
history. Use the [documentation guide](../README.md) for authoritative
contracts rather than treating historical steps as current instructions.

Reviewed frozen candidate `42999a5f31a8993b5ac8e38235ef5645d074af2d` passes
the new native seven-phase gate in1055.50s/520116KiB,58.13% less elapsed time
than P0's2520.62s. Focused feedback is0.85s. Two complete opt-in warm runs
take49.46s/46.82s, with all23 fixture receipt bodies/inodes/mtimes unchanged.
Both independent source-readiness audits pass; both seed comparisons,12 proof
phases,44 corpus cases, copied Linux layout, stress, fresh fixtures and
sanitizers remain. See the
[current completion record](../../AUDIT_REMEDIATION.md#pre-m56-concurrent-warm-close).

The warm result applies only to the owner-approved
[concurrent local tier](../P1_CONCURRENT_WARM_CONTRACT.md) on its pinned
supported WSL2/Ubuntu24.04 provider. Default/full-milestone/proof/release
execution remains serial. No budget, coverage or strict60 waiver is involved.
The10min cold working target remains unmet and is tracked separately from
the required>=50% reduction. These measurements are observed historical
comparisons, not randomized causal estimates or release certification.

The [P1-P4 pre-close report](../../PERFORMANCE_P1_P4.md) preserves component and
intermediate evidence. Earlier1055.02s/1011.04s cold and128.52s/100.58s warm
observations remain bound to their older candidates in the completion ledger;
they do not attest the new host scripts. Current completion supersedes the
pre-close pending statuses without rewriting sealed evidence. No publication,
stable release, M56 implementation or downstream pin change is claimed.

The recorded M55 gate was 2,504 seconds, with about 91% in driver, seed
bootstrap, and proof. The native P0 now establishes 92.4% in those phases;
use the same-host costs before choosing an implementation.
Keep focused checks during edits, trailing audits before acceptance, and one
complete final gate on each reviewed candidate. Preserve current proof and
provenance obligations while reducing repeated captures, scans, comparisons,
and unnecessary value transfers. See
[VERIFICATION.md](../../VERIFICATION.md) and
[PERFORMANCE_BUDGETS.md](../../PERFORMANCE_BUDGETS.md).

The useful Kimi authoring-kit direction is accepted as a staged evaluation
plan in [AUTHORING_KIT.md](../../AUTHORING_KIT.md): compiler-checked teaching,
optional constrained generation, and a controlled behavioral/cost comparison.
The prototype is not adopted code. This optional lane can be evaluated before
M59 after its corrections and separate authorization; it does not delay M56,
weaken audits, add model decisions to the compiler, or change locked schemas.

#### Documentation And Refactor Checkpoint

The 2026-10-09 [refactor program](../REFACTOR_PLAN.md) starts with a
nonpackaged documentation foundation: a complete document index, descriptive
compiler map, and corrections to stale current-status guidance. It preserves
the incoming source/runtime/seed/schema/script/fixture/skill content and does
not extend an earlier executable attestation.

R2/R3 now implement the attributed visibility scan and one identical
builtin-fact family; both independent audits and the reviewed seven-phase
Linux executable acceptance passed on 2026-10-19.
R4-R6 are accepted as bounded implementation/retention work under the
[execution contract](../R4_R6_CONTRACT.md): borrowed driver assembly,
separate dispatch, intentional canonical backend-type retention, and one
shared proof invocation. Exact focused compatibility, both independent final
audits, and one fresh seven-phase Linux acceptance passed on 2026-10-19.
PRE-M56 efficiency stays first. The packaged README
rewrite received its own reviewed executable close after the `0564a32`
baseline checkpoint: both independent trailing audits passed, then all seven
Linux milestone phases and 44 corpus cases passed on indexed candidate
`16b8e84271c5c3e4db20384c17977a102710395b`. The one cold run took 2507.89s
with 437144 KiB peak RSS; matching attestation and copied README checks
passed. This is documentation acceptance, not a performance improvement,
source cleanup, new feature milestone, stable release, or publication. The
retained P2 attestation still applies only to its earlier candidate.

A separate instrumented profile now attributes 19.72% of sampled CPU time
to `typecheck::visible_item_origin`. R2's phase-owned immutable module-run
index preserves resolution order, visibility, and old entrypoint identities;
R3 retains facts/review wrappers around shared pure classifiers. Separate
ordinary identical-input measurements show 19.19% less mean wall time, with
matching output for the locked 37-row matrix. See
[R2/R3 results](../R2_R3_RESULTS.md). The one frozen executable gate passed
in 2290.24s / 437956 KiB on indexed candidate
`e77dc750af7a97d759700f83da9d56779a66115a`, with 44 corpus cases and verified
attestation; exact receipt identity is in TODO. This is candidate-specific
acceptance, not a controlled cold-gate speedup or stable release. R4-R6's
candidate has separate [focused results](../R4_R6_RESULTS.md). All 82
compatibility rows and 11 C files match. Its frozen gate passed in 2304.10s /
437820 KiB on indexed tree `c4eff216dae15edaf5bd03b7df5f5d1070d0bd5b`,
including 44 corpus cases and all 12 proof phases; exact attestation is in
TODO. Only the three selected completion documents change afterward.
R0-R6 maintenance is complete, not the broader PRE-M56 campaign. The observed
2.54% matched-check wall increase is disclosed, not presented as a speedup.
Next work remains bounded efficiency work before M56, not a new language
feature, stable-release claim, or inferred downstream adoption.

## From TODO.md

### Current Performance Checkpoint

P1-P4's required performance goals are met on reviewed frozen candidate
`42999a5f31a8993b5ac8e38235ef5645d074af2d` in the supported WSL2/Linux-ext4
environment. Focused feedback takes0.85s; two complete opt-in warm runs take
49.46s/46.82s. The new serial seven-phase gate passes in1055.50s,58.13% less
than P0's2520.62s. The10min cold working target remains unmet, not waived or
reclassified as a passing result.

Both independent source-readiness audits pass. Exact80-source/runtime seed
propagation, both seed comparisons,12 proof phases,44 corpus cases, copied
Linux layout, stress, fresh fixtures and sanitizers remain green. All23
receipt bodies/inodes/mtimes are unchanged across both warm runs; every check
executes. Whole warm workflow150.274565627s includes population and readbacks.
Default/full-milestone/proof/release execution remains serial; the under60s
result belongs only to the explicitly selected supported concurrent mode.
See the [current completion record](../../AUDIT_REMEDIATION.md#pre-m56-concurrent-warm-close)
for identities, costs, scope and closing-review evidence.

M56 explicit generic reuse passes its reviewed frozen Linux close on
`67272d00dd7d3e6cbb3945cc5777141148ff2cc1`: exact86-source seed, both seed
comparisons,12 proof phases/45 corpus cases, seed/release generic composition,
owned tests, sanitizers and strict attestation. See the
[M56 completion record](../../AUDIT_REMEDIATION.md#m56-generic-reuse-close).
No stable release, publication or downstream pin change follows from this
performance close. Earlier1055.02s/1011.04s cold and100.58s serial-warm results
remain historical candidate-bound evidence, not the new gate's measurements.

### Current Refactor Checkpoint

Use [docs/README.md](../README.md) for authoritative-document routing and
[docs/REFACTOR_PLAN.md](../REFACTOR_PLAN.md) for staged maintenance scope.
The checklists below retain milestone history, not a second current roadmap.

- [x] R0: inventory active/archive/generated boundaries, add the documentation index and compiler map, and repair stale architecture/status guidance without changing executable inputs
- [x] R1: P0/E1/P2 baseline checkpointed separately in `0564a32` with verified P2 closing evidence; packaged README passed independent mixed audits and one fresh seven-phase Linux milestone gate
- [x] R2: phase-owned visibility ranges implemented and measured; reviewed, seed-promoted candidate passed the complete seven-phase Linux gate
- [x] R3: identical facts/review builtin tables consolidated with retained delegates; exact compatibility and seed/proof acceptance passed with R2
- [x] R4: borrowed driver/checked-project assembly and separate dispatch accepted with exact compatibility, generated-code inspection, bounded cost, and the fresh Linux gate
- [x] R5: canonical backend type ownership intentionally retained without nominal-origin drift; static equality, C/runtime comparisons, and integrated acceptance passed
- [x] R6: three proof wrappers share only their identical host invocation; distinct publishers/proof policies, required coverage, and final documentation are preserved and accepted

R0/R1 change documentation only, not compiler behavior. R1's fresh Linux
gate on 2026-10-09 passed all seven phases and 44 corpus cases in 2507.89s,
with 437144 KiB peak RSS, on indexed candidate
`16b8e84271c5c3e4db20384c17977a102710395b`. Its verified attestation SHA-256 is
`9a422fed99c88c01d4605e2eaff76b5c033d2f0a63905b3992bd0c0504c5a210`.
Receipts are retained locally under
`build/verification/refactor-r1-20261009/full-gate/`; this is not publication
or a stable release. Source/copied README bytes and links also passed.

R2 attribution identifies `typecheck::visible_item_origin` at 19.72% of
sampled CPU time. That separate `-pg` run is not a production timing or
speedup result. The R2/R3 candidate now has ordinary measurements: identical
baseline checks improve from 333.80s/331.23s to 269.12s/268.30s (19.19% less
mean wall time); expanded current-tree checks take 289.82s/289.36s. All 37
locked compatibility rows and six C outputs match. The exact self-generated
74-file seed is promoted. Both independent final audits passed, then the one
frozen seven-phase Linux gate passed on 2026-10-19 in 2290.24s with 437956 KiB
peak RSS, 44 corpus cases, and all 12 proof phases. Indexed candidate:
`e77dc750af7a97d759700f83da9d56779a66115a`; verified attestation SHA-256:
`f9b53accd56b088179052f2d91013f1914def073a1f0e73406bfac460b938f27`.
Receipts are retained under
`build/verification/refactor-r2-r3-20261019/native-receipts/r23/final-gate/`.
Only allowlisted completion documents change after that gate. See
[R2/R3 results](../R2_R3_RESULTS.md). This is not a controlled cold-gate A/B
result, stable release, or full campaign closure. Broader P1-P4 efficiency
targets and M56-M61 remain open. The authoring-kit draft remains
staged and unvalidated; no external consumer adoption is inferred.

R4-R6's bounded candidate follows the
[execution contract](../R4_R6_CONTRACT.md). All 82 reference/candidate
cases and 11 emitted C artifacts match exactly; old function signatures,
protected driver declarations, and unchanged backend owners are checked.
Both independent source reviews passed. The new native compiler is built
and verified. Matched-input checks pass at 296.87s/297.02s, an observed
2.54% wall increase over the older reference, with 0.40% higher maximum RSS;
no speedup is claimed. Exact self-generated seed promotion and both final
mixed audits passed, then the one frozen seven-phase Linux gate passed on
2026-10-19 in 2304.10s / 437820 KiB, including 44 corpus cases and all 12
proof phases. Indexed candidate:
`c4eff216dae15edaf5bd03b7df5f5d1070d0bd5b`; verified attestation SHA-256:
`f943b10e5069a105a35201dfd4894b5f1cf1344120088ded0f2f35cee36703ee`.
Receipts are retained under
`build/verification/refactor-r4-r6-20261019/native-receipts/r456/final-gate/`.
Only TODO, roadmap, and coordination completion text changes after that gate.
See [focused results](../R4_R6_RESULTS.md). No owned project aggregate,
neutral-enum relocation, publisher framework, language feature, or downstream
pin migration is part of this work.
R0-R6 maintenance is complete; PRE-M56 efficiency remains first, before M56.
This is not campaign closure, a controlled cold-gate A/B result, a stable
release, or a claim of GitHub publication.
