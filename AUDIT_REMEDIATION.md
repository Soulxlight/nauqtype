# Astra Audit Remediation

Status: M54.7-M54.10 and M55 complete, 2026-09-06 UTC. M55 closes F14's
process-correctness prerequisite and the separate process/time contract.

The 2026-09-04 Astra audit reviewed `d2c7592ae5e4dc11fba7ffe715334a881d715b62`.
Its report and executable evidence were recorded in the external archive
named `Astra Audit NauqType` (not bundled here; availability must be verified):

- `NauqType Audit Report.md`, SHA-256
  `e28e646077cf5bba781241b4a18b23138f13a2094059b7813840fc0cfd7f09aa`;
- `audit-evidence.json`, SHA-256
  `6a0343d772cb108e3e5df8b3011db1808710ce01daf0cadeb8106dc21b03ba70`.

This file records the owning team's disposition and executable closure
criteria. A green self-build proves compiler consistency; specification-based
expected results are also required to prove the affected language behavior.

## M54.7: Expression And C Backend Correctness

Status: complete. Independent Sol xhigh and GPT-5.5 xhigh source and seed-delta
audits returned PASS, followed by the clean frozen-candidate milestone gate.

- F01: select rightmost operators at each left-associative precedence level in
  both typechecking and checked-handoff construction. Keep equality below
  relational comparison as specified in `GRAMMAR.md`. Preserve parentheses,
  unary operators, operand evaluation order, and exact integer typing.
- F02: preserve the first matching arm for enum, option, and result statement
  and expression matches. A fallback before a later specific arm must win;
  later duplicate cases must not produce duplicate C labels. Use the existing
  ordered condition-chain lowering for all matches, preserving scrutinee,
  binding, and control-flow cleanup. The sanitizer exposed a missing
  expression-arm binding drop; the exporter now closes that arm scope after
  transferring the result, using existing canonical cleanup.
- F04: use injective C encodings for source-derived identifiers, including
  user fields, enum members, module paths, and named generic payloads. Keep
  semantic identities and runtime-native ABI names unchanged.
- Refresh the generated C seed as required by the changed output. Record its
  generating source snapshot, generator identity, and checksums, then prove
  the fixed point using the existing structural comparison. Do not normalize
  away differences in operators, control flow, or user identifiers.

Acceptance: permanent Nauqtype fixtures for both integer widths, chained and
mixed operators, parenthesized controls, side-effect order, fallback-first and
fallback-last matches, wildcard/binding arms, repeated constructor arms, owned
payload cleanup, C-keyword names, and distinct module/type names that formerly
collided. Run the owned fixture and corpus paths, focused ownership sanitizers,
independent mixed-model trailing audits, then one frozen-candidate milestone
gate. New expected values come from the specification, not generated goldens.

## Follow-Up Sequence

| Slice | Findings | Required closure |
| --- | --- | --- |
| M54.8: Canonical contract and evidence validation | F03, F05, F08, F11, F15 | Make commands agree on contract validity; resolve contract names; distinguish absent declarations and partial mutation coverage; version any changed evidence shape explicitly; give failures truthful requested-version envelopes and deduplicated producer diagnostics. |
| M54.9: Integer and allocation-size semantics | F06, F13 | Record ordinary overflow/division/negation behavior at both widths; implement it without C undefined behavior; check size/capacity arithmetic; exercise runtime edges at `-O0` and `-O2` plus UBSan and injected capacity limits. |
| M54.10: Dependency and verification provenance | F07, F09, F10, F12 | Version framed source-tree locks; reject path/boundary/enumeration changes; enforce seed provenance; bind cache publication and gate evidence to captured source/artifact identities; retain direct proof comparisons and distinguish triage checksums from cryptographic identities. |
| M55 prerequisite: Process wait correctness | F14 | Retry interrupted read/wait operations where appropriate; distinguish failures; guarantee child reaping and capture cleanup before adding deadlines or cancellation. |
| Current documentation map | F16 | Correct active architecture, module/loop capability guidance, and historical present-tense claims. Treat old milestone records as history rather than current implementation contracts. |

F05 is a documented direct-assignment-only inference limit. That does not
justify presenting partial mutation evidence as a complete empty footprint.
First make coverage explicit, then add builtin and resolved-call summaries with
named-argument mapping and a bounded fixed point. Its closure belongs with the
evidence milestone rather than an ownership-model expansion.

F09's current seed record must be refreshed during M54.7 because C output
changes. Automatic rejection of an unrecorded future seed refresh remains in
M54.10; updating a manifest alone does not close that enforcement finding.

M54.8 is split at its compatibility boundary. M54.8a shares strict source
contract extraction/validation and value-plan completeness checks across
commands. M54.8b retains F05/F08, the remaining F11 schema/failure-envelope
work, and F15 producer diagnostics. The reviewed implementation contract is
[M54_8_CONTRACTS.md](M54_8_CONTRACTS.md). No successful schema is silently
changed in M54.8a, and the parent milestone remains open.

M54.8a is complete as of 2026-09-05. Independent Sol xhigh source and repair
audits returned PASS; the replacement frozen candidate passed all seven
`scripts/check_milestone.sh` phases in 1,520 seconds. The first attempt exposed
an obsolete empty-stderr refactor assertion, which was narrowly repaired and
added to fast coverage before the complete repeat. F03's inconsistent
source-contract acceptance is corrected. This does not close F05/F08, general
F11 envelopes, or general F15 duplication; exact hashes, failed-run provenance,
and remaining scope are in `M54_8_CONTRACTS.md`.

M54.8b1 completed the bounded review-v3 migration: absent/declared audit
emission, checked-ID direct assignments, and explicit partial lower-bound
coverage. Independent Sol xhigh audit PASS and one 1,574-second frozen gate
close emitter/golden coherence only. It does not close call-summary validation,
standing F08 standards
schema enforcement, F11 diff/change failure envelopes, or F15 diagnostics.

The final M54.8 implementation now has focused green evidence for those
remaining contracts: checked call-aware mutation validation and review v4,
explicit change-report v3 policy truth, shared evidence-error v1 failures,
producer diagnostic deduplication, and an owned bounded schema profile.
Candidate3 owned tests passed in 7.48s and all 42 corpus cases in 22.85s.
The independently compiled final schema repair passed its focused probes.
The final independent audits returned PASS. Frozen tree
`79a954257ea43e976d2a5f0003561af060f1d874` passed all seven milestone phases
in 1,908 seconds. `M54_8_CONTRACTS.md` records exact command, timing, hashes,
and the bounded bootstrap-runtime repair. M54.8 is complete; no
numeric/provenance finding is closed by this work.

M54.9 now closes F06/F13: both-width wrapping arithmetic and checked division,
bounded strict-C constant lowering, immediate ordered value reads, allocation
size/retain guards, and allocation-free fallible IO errors are implemented.
An adversarial audit also exposed an invalid borrow-arithmetic argument;
the place-only repair preserves existing read-only field borrows. Final
Sol max and GPT-5.5 xhigh reviews returned PASS. Frozen tree
`756577157e6018962e938872548dc962449a40dd` passed all seven milestone phases
in 2,048 seconds with empty stderr. `M54_9_CONTRACTS.md` records the exact
focused checks, seed lineage, gate timings, and artifact hashes. Provenance
enforcement remains M54.10; process interruption handling remains M55/F14.

M54.10 now closes F07/F09/F10/F12 with captured dependency text, framed lock
v2, explicit facts/change v4 compatibility, strict seed snapshots, builder-only
cache derivation, proof-summary v3 SHA-256/null truth, and gate/closing
attestations. Sol xhigh and GPT-5.5 xhigh final reviews passed. Frozen tree
`6d548d35de4c5f4fd64ffd3a84f6fc32e09e9a31` passed all seven phases and final
attestation verification in 2,716 seconds with empty stderr. An earlier
supervisor-terminated attempt is retained as incomplete, not hidden or counted
as acceptance. See `M54_10_CONTRACTS.md` for exact evidence and limitations.
Old external workspace locks require explicit owner-managed migration;
legacy evidence shapes remain compatible but are not secure-change claims.

## M55: Process And Time Closure

F14 is closed: interrupted legacy capture/read/wait operations retry safely,
and persistent cleanup failures cannot silently abandon an owned child.
M55 adds the narrow process/time surface in `M55_CONTRACTS.md`. Gate B found
and required repairs for persistent legacy kill/reap failure, the final
group signal after terminal observation and before draining/reaping, borrowed
outcome-field metadata, and qualified user calls sharing builtin names.
Those findings have focused permanent fixtures; none was waived.

Final primary `gpt-5.6-sol` max and independent `gpt-5.5` xhigh reviews both
returned PASS. Max followed the protocol's conflicting-verdict escalation.
Native strict-C, optimized, ASan/UBSan, injected-fault, and child-lifecycle
probes passed. The Nauqtype process gate covers move/borrow rejection,
recursive cleanup, nominal/opaque types, deadlines, cancellation, evidence,
policy, refactor plans, and imported call/propagation identity. The separate
contract-evidence probe passed its missing/duplicate/noncontiguous-call tests
and the existing mutation, schema-profile, diagnostic, and failure cases.

`scripts/check_milestone.sh` ran once on frozen staged tree
`64a0832a8bc73582949cefd9a5bcbc8f57a26d8c`: exit 0, empty stderr, all seven
phases and real final attestation PASS in 2,504 seconds. Phase wall times:
driver 488.33s, seed bootstrap 573.54s, proof 1213.77s, copied Linux alpha
13.04s, stress leg 2.07s, owned tests 156.21s, ownership sanitizers 8.23s.
All original wall/RSS ceilings held. The proof includes the copied selfhost,
43-case corpus, and tooling confidence cases; copied release build/run emits
`process and time ok`. Python suites were not used as active gates.

The refreshed seed was produced by an actual compile and re-emission: raw C
comparison and `prove-seed` both passed, followed by strict seed verification.
The manifest honestly retains the unpublished repaired seed `2fd56266...` as
its observed predecessor; no synthetic cache receipt or verifier change was
used. Frozen identities:

| Artifact | SHA-256 |
| --- | --- |
| Exact source tree | `be878c88dca696269c4c565c5b7f22f5d883d41ab1299b929c22a3d863b4a217` |
| Generator input/output and seed C | `2ec30ab03c77d5b113eb414e18e5b4ba52c6217d9cf3283f938eea8b150c5084` |
| Generator executable | `553e3d7e824d9e0e99aaf6361eb2d49cc0e743cc85dd42a8e298e56305209cbb` |
| Runtime C | `afb8f0c7b618e5b7439a530ae2bd8e4a6d97fdb3277347d4ef9670600d12bf46` |
| Full-gate driver | `faaad197d7b3291ddaea3684c7fbb3aff07ac729ba3caa119d5f494cee06c88d` |
| Proof summary | `c374f5f6b0377a7ba91e1a0883b9f8ce38c62e6e01836c3ad652799c76fcc238` |
| Copied release tree | `3c869702dd7771abc54d33b42a6192f70fe90f6936ca9be8943a74c81556bdd5` |

Evidence was recorded under `build/verification/` in the isolated Linux
snapshot `nauqtype-m55-yzh3R7`; focused/audit packets were in
its `build/m55_process/`. Only the existing completion-doc allowlist changed
after the gate. A milestone-close attestation binds that text-only delta to
the final commit. No M56, external repository, syntax, schema, or general
ownership expansion is part of this checkpoint. Linux cleanup limits and the
narrow unrecoverable-cleanup fatal exception remain as documented.

## Architecture And Product Direction

The active implementation is `selfhost/` plus the narrow C runtime in
`stdlib/`. The frozen C seed is the bootstrap boundary; the Python compiler and
unit suites are historical references. See [ARCHITECTURE.md](ARCHITECTURE.md)
for the active phase map and [VERIFICATION.md](VERIFICATION.md) for gate order.

Preserve M54.6's measured scope and child indexes. After corrective closure,
migrate expression/type families incrementally to parser-owned, ID-addressed
structures so semantic consumers do not reinterpret token spans. Measure each
slice against current wall time, memory, diagnostics, and evidence. This is a
separate reviewed architecture project; it is not a prerequisite rewrite for
the immediate wrong-code repairs.

The later Linux direction remains structured process/time/cancellation,
explicit numerical and storage contracts, qualified type provenance, bounded
generic reuse, data facilities, FFI, and tasks. General-purpose modules remain
owned by NQType Libraries; numerical reference algorithms remain owned by
NQType AI/ML. Their provisional requests are coordinated in
[NAUQTYPE_COORDINATION.md](NAUQTYPE_COORDINATION.md).

## Verification Record

- Baseline: `scripts/stage1_cache.sh require` passed at `d2c7592` before edits.
- Initial fixtures reproduced old precedence rejection, duplicate C case
  labels, illegal C members, and colliding-name declaration failure.
- The initial seed bridge caught an unsupported source `else if` spelling in
  the new helper; it was corrected to existing nested `if` syntax before the
  successful build. An exploratory whole-file formatter check for `c_emit.nq`
  was not green; this pass does not reformat the pre-existing compiler file.
  Canonical new fixtures are checked separately.
- The first ownership sanitizer run failed with 1,280 leaked bytes in 128
  allocations. The missing expression-arm cleanup was repaired rather than
  weakening the fixture. Its in-progress seed emission was stopped and
  discarded, not recorded as a successful bootstrap artifact.
- Repaired `build/m54_7/E2 test` passed (`nauqtype test ok`), and
  `build/m54_7/E2 prove-corpus` passed all 42 locked cases. The initial four
  direct M54.7 runs used E1 and exited 0 with empty output; the repaired E2
  owned suite reran all four entrypoints after the cleanup correction.
- All nine fixtures listed in `scripts/check_m53_ownership.sh` were emitted
  using E2, compiled with C11/address sanitizer against `stdlib/runtime.c`, and
  passed with leak detection enabled. A further move-only list-payload arm
  regression passed normal execution and the same sanitizer after addition.
- All six new Nauqtype source files pass E2 `fmt --check`; focused relative
  documentation link checks, shell syntax, and `git diff --check` pass.
- The regenerated C2/C3/C4 snapshots have identical SHA-256
  `9cabe9044b148eb1f76ef254f95c1e85565fa0a849872ae7e126ef4cc5f0efc1`.
  Both `E2 prove-seed C2.c C3.c` and `E3 prove-seed C3.c C4.c` passed the
  unchanged structural normalizer. C3 was promoted byte-for-byte; seed runtime
  C/H stayed unchanged. `bootstrap/seed/manifest.json` records the complete
  observed lineage and source digest, and all four `SHA256SUMS` entries pass.
- Source and final seed-delta audits returned PASS from independent
  `gpt-5.6-sol` xhigh and `gpt-5.5` xhigh auditors. Neither auditor edited the
  candidate or ran duplicate builds.
- One `scripts/check_milestone.sh` passed on the reviewed, clean indexed
  snapshot `nauqtype-m54.7-candidate-vpz0Fj`, starting without generated
  artifacts. All seven phases passed in 1,390 seconds (23 minutes 10 seconds)
  with unchanged wall/RSS budgets: stage1 driver 293s, seed bootstrap 302s,
  proof 784s, Linux alpha 3s, stress leg 2s, owned tests 3s, and ownership
  sanitizers 3s. The proof contains 42 corpus cases and all 12 phase IDs.
- The snapshot and canonical checkout had identical indexed tree
  `8cfec279b4d60fd3fae27d16f9c9b5596b8b4add` and full tracked
  path/content/Git-mode digest
  `0e95673c1be7baefc600bea52d80361e08debafab3e1e315cf5e26202da04bbe`
  before and after the gate. The digest frames the version
  `nauqtype-candidate/v1`, then NUL-delimited path, Git-style mode, and content
  SHA-256 for each byte-sorted tracked path. Only completion/evidence
  documentation changed after that frozen gate; executable and packaged
  release inputs did not change.
- All 230 files under the snapshot's `build/` were preserved byte-for-byte
  in the canonical checkout, including proof C artifacts, corpus artifacts,
  release layout, and performance results. The compiler was atomically
  replaced, then its cache manifest was published last. Both inputs had
  fingerprint
  `f79d9f733fb3b95d2eb7d1d6501519d6a0e65179703e79b7bf4e1608a9620574`.
  Canonical `scripts/stage1_cache.sh require`, `bin/nauqc version`, and direct
  runs of the operator and module-name fixtures passed after relocation.
- No Python gate ran; active verification is Nauqtype plus the existing
  shell/host-C boundary. No second equivalent full gate was run.

The local evidence is under `build/verification/`, `build/proof/`, and
`build/m54_7/`. The stress workspace is also retained at
`build/m54_7/stress-workspace`. These generated files are ignored, not source
inputs; their SHA-256 identities anchor the observed closure:

| Artifact | SHA-256 |
| --- | --- |
| `build/verification/milestone-summary.json` | `06ee62e35159161d8ddd686158b4c9fccd8e12c6b32f7268753d80489b2da474` |
| `build/verification/performance-summary.json` | `393cb4ecf5c445e03bcb60b8611dc5b1b9cd7774c3cfeed092ebf3396f444ff5` |
| `build/proof/summary.json` | `fa9f419bd6fdd905a8a26b87a3376b04c503dd999ebf97e8c96b9004aa09ca81` |
| Copied-selfhost stage1 and stage2 C (both) | `9cabe9044b148eb1f76ef254f95c1e85565fa0a849872ae7e126ef4cc5f0efc1` |
| Published `selfhost/build/nauqc` | `56b17fd0299273b8eaede99955279072972a9d980233f3bf6640fd19428847a3` |

## PRE-M56 P1-P4 Functional Candidate

2026-10-19: functional source/seed evidence passes locally; overall performance
campaign acceptance remains open. No commit, publication, stable release,
consumer adoption or M56 readiness is implied. The required60s complete warm
goal is not waived.

Independent `gpt-5.6-sol` xhigh and `gpt-6-astra` xhigh reviews passed the
source and final seed candidate. Astra is the recorded unavailable-GPT-5.5
fallback. Initial findings were repaired and re-reviewed: fail-closed spool
writes/counts, empty cache-mode rejection, GCC PCH shadow refusal and actual
full-record/cleanup oracles. Both final reviews preceded the single complete
native Linux gate on indexed candidate
`1afea662cc62bc88914a295ed407c6ddeaf650aa`.

`scripts/check_milestone.sh` passes in1055.02s with518896KiB peak RSS.
All phase ceilings remain unchanged; owned tests explicitly use
`NQ_TEST_REUSE_C=0`. All copied-selfhost/corpus, release, stress, fixture and
sanitizer coverage remains. The attestation verifies again after warm tests.

| Phase | Wall Seconds | Peak RSS KiB |
| --- | ---: | ---: |
| stage1.driver | 223.24 | 518804 |
| seed_bootstrap | 137.97 | 131252 |
| proof | 488.69 | 518896 |
| linux_alpha | 9.74 | 63348 |
| stress_leg | 2.90 | 63312 |
| owned_tests | 172.91 | 136164 |
| ownership_sanitizers | 7.59 | 57768 |

Phase totals are1043.04s; the remaining11.98s includes composed-gate setup
and attestation. Versus P0's2520.62s, observed complete wall time is58.14%
lower, meeting the>=50% goal, but not the10-minute working target. This is
not a randomized causal estimate. Owned-test cold time is slightly above
R4-R6's171.44s while adding adversarial coverage. Compiler-build RSS is close
to its524288KiB ceiling; no memory improvement or spare growth capacity is
claimed.

Final current-cache focused feedback passes in0.75s/5144KiB. Warm population
takes180.52s; the complete warm tier passes functionally in128.52s/63604KiB,
25.88% below the173.385372168s reference observation but still above60s.
All23 fixture receipts retain their metadata on the warm pass; that is
observability, not cache authority. Every probe executes. Inputs, CC, running
kernel, compiler and attestation readbacks pass; cached test results are not
used. The owner decision on the remaining warm goal is pending.

Ordinary checks94.46s/93.38s and emissions96.79s/97.56s use the unchanged
e9d3 source. All82 compatibility rows and11 user C files agree; both whole
reference emissions match raw bytes. The exact current80-source self-emission
takes125.00s and equals its builder input C byte-for-byte. The seed and all86
checksums validate. No generated C was manually edited or cache hand-blessed.

| Identity | SHA-256 |
| --- | --- |
| Verified milestone attestation | `d1e8e416021eb6453c21f222a4caf99071b2b1ff37c984cf0653b62de8482021` |
| Builder input, self-emission and promoted seed C | `f3e07bc8f01b3b30a06bcd9ed79391f82bcf69537c229a9abe445c904e83fcdc` |
| Generating compiler | `b433c28985766400a085523162c8b5b820b31d35865db351f857b3529ebd599f` |
| Source inventory | `4fdea26aa0c43c7c37b9cee79a2b1dba87cc3b29f8648ed808d6eee5b4974d79` |
| Source tree | `842ae7506518d14ae3c3c4c639da558a4486445cc832ea5a63e3370f78b88b11` |

The native candidate is retained rather than recopied for each probe. Its
changed-file transfer is1,487,090bytes/24.865071774s; seed copy-back changes
14,302,976bytes excluding checksums in8.421834152s, with complete readback.
One-time construction, setup/copy and warm population costs are separate from
steady-state feedback. Native receipts are retained under
`build/verification/p1-p4/`; compact canonical evidence is under
`build/verification/p1-p4-20261019/`. These ignored receipts are not a release.
Only allowlisted completion documents change after the attested candidate.

### Warm Follow-Up: Unpromoted Source Candidate

The separate `379392c84d2ee1623dc431d3ac9f5542ff02307c` candidate has both
independent source-readiness approvals, not final milestone approval. Its
literal-scan change preserves the old byte predicates through retained
linear oracles. Its eight-line runtime change bounds the first five no-I/O
exit rechecks, including EINTR, without changing deadlines or ownership.
All six native process fixtures pass with the original ASan/UBSan flags,
including seven new scheduling assertions. Both ordinary component pairs
and their boundaries are recorded in `PERFORMANCE_P1_P4.md`.

The original seed builder legitimately constructs this current-source
compiler in 222.18s at 520068 KiB, below the unchanged 524288 KiB ceiling.
Focused feedback is 0.76s. In one persistent native session, complete warm
population takes 152.52s and the warm repeat takes 104.53s. All checks
execute; all 23 receipt body hashes and inode/mtime records are unchanged
on the repeat. Input, CC, boot, artifact, index and cache readbacks pass.
This is 18.67% less warm time than 128.52s, but still misses 60s by 44.53s.
The earlier 1055.02s cold gate is not evidence for these new source bytes.

| Follow-Up Identity | SHA-256 |
| --- | --- |
| Current compiler | `d334d2d9e4eaf46fb8edd29b1ef07237339802e95a38a9f3a9502ed5fe53b716` |
| Builder-generated C | `44c6a2f620a2513596965a5839fc68701bd08ac36c26018e3c30189849f4436f` |
| Pre-promotion input frame | `060f7b1bc22c3c16885523e0b8c86f585e02a7af35084bc7b40283abf312d2ca` |

Old source/artifact/release evidence is preserved in
`build/verification/p1-p4/warm-followup-build-v1/old-capsule/`. Current
construction and warm receipts are in `warm-followup-build-v1/` and
`warm-followup-measure-v1/` under the same evidence root. This capture
preceded the seed propagation below; a fresh complete gate remains pending. The strict warm goal,
overall P1-P4 acceptance and M56 remain held; no waiver, commit, push or
consumer-pin update is claimed.

Remaining-cost research uses a passing 156-assertion host provenance run:
39.76s wall, 19.32s user and 7.78s system CPU. A separate diagnostic records
8280 stat, 4306 cat and 2859 SHA provider-wrapper entries. These are attempted
delegations, not syscall counts or production timing. No test is removed or
cached. A timeout137 shortcut was withdrawn rather than adding an unsafe or
disproportionate supervisor. Further host reuse needs a measured, independently
reviewed fresh-read contract before implementation.

The later time-scaled timeout unit is a separate, independently approved
design, not the withdrawn process controller. It preserves the production
runner, all14 cases and exact success text. A private unit-only shim proves
the literal5s production argument and genuine GNU TERM/KILL escalation with
0.01s delegated grace; it does not prove5s elapsed grace. Both trailing
auditors pass. Ordinary ABBA unit times are9.48/4.41/4.57/9.57s.

With unchanged `379392c` compiler/producer inputs plus that reviewed test
script, a fresh same-session complete population takes145.77s/141388KiB;
the complete warm repeat passes in99.89s/63528KiB. Every check executes,
all23 fixture receipt body hashes and inode/mtime records remain unchanged,
and artifact/input/CC/boot/index/cache readbacks pass. The single temporary
native script substitution is restored exactly afterward; this is composed
warm evidence, not a new indexed-source attestation or seed promotion.
Receipts are retained under `build/verification/p1-p4/warm-timeout-v1/`.
Warm is22.28% below128.52s but still39.89s above the strict60s target.

Two independently designed experiments were removed after measurement:
fresh attestation metadata batching made the complete tier4.22% slower;
kernel-anchored ELF hashing improved a padded component by9.42%, below its
15% adoption threshold. Their rejected contracts retain the exact boundary;
neither implementation remains. No tests, failure paths or budgets were
weakened. An opt-in concurrent local warm tier is only proposed for owner
approval and read-only safety research; serial/release/proof behavior is
unchanged. P1-P4 and M56 remain held, with no new commit or push.

### Follow-Up Seed Propagation

The current compiler actually self-emits C in130.07s/126144KiB; full-byte
comparison equals the builder's `44c6a2f6...` input. Both independent
pre-install reviews approve the bounded mechanical recipe on source index
`379392c84d2ee1623dc431d3ac9f5542ff02307c`. The exact output, current runtime
and complete80-source snapshot are promoted with the unchanged19-field
manifest, inventory and86 checksums. Installation takes6.12s/4976KiB.

The predecessor `f3e07bc8...` seed remains in native and canonical backups.
Native installation is two renames with catchable rollback, not a crash-safe
atomic exchange. Canonical copy-back is in-place and is accepted only after
complete tree/byte/checksum readback. Six files change:12,705,819bytes in
14.312843997s, excluding checksum-copy bytes. All six staged Git blobs also
match their raw sealed bytes; NTFS modes are not Linux mode certification.

The original seed builder then legitimately rebuilds from the new seed in
224.02s/520020KiB, below the unchanged600s/524288KiB ceiling. Total wrapper
work, including validation and focused feedback, is228.625767586s. Generated
C again matches exactly, the executable is byte-identical to the earlier
`d334d2d9...` compiler, and fresh source/input/CC/boot/index/artifact/seed/cache
readbacks pass. Verified-current focused feedback passes in0.65s/5776KiB.
The old cache was expectedly stale after promotion; only the real builder
published its replacement. An earlier ignored-wrapper preflight stopped
before compilation on a relative-path hashing argument; that harness-only
error was corrected without source changes or discarding its evidence.

| Promoted Identity | SHA-256 |
| --- | --- |
| Seed and rebuilt generated C | `44c6a2f620a2513596965a5839fc68701bd08ac36c26018e3c30189849f4436f` |
| Seed manifest | `19ab725e2398cce3c15b8a6ce94ef81e9fa45523cdf488f13e4d4801b6d570ae` |
| Source inventory | `2d8639f423bd97a3bbfcf20fc8a980756195ecb605d62228df69714f964d4c77` |
| Source tree | `3528fa5c070782f8f42ca38ae3d23f555908b06b3bcb0a56823975bb6ca7afd8` |
| Current build input frame | `d8db0622d5cf14a40a1cba5ca6b3434a08d59fa6187dcbe3dde71cd3797fffc9` |
| New cache manifest | `71701aa59421105ab9308698942c6fc373406a4a3904b98df8abd82a6e6bd172` |
| New derivation receipt | `a2345cf238e0ffd8df2613ee76ad700716f4ede79c6e8dd9141fe3a7fcbb1953` |

Native construction index is `a501b673243f707ee7a975a89de91b15716fb866`.
Local receipts are in `followup-self-emission-v1/`, `followup-promotion-v1/`
and `followup-promoted-build-v2/` under `build/verification/p1-p4/`; canonical
copy/readback records remain in `build/verification/p1-p4-20261019/`.
This completes seed propagation and current-cache reconstruction, not the
fresh seven-phase close or overall P1-P4 acceptance. The99.89s full warm
observation belongs to the preceding composed capture, not a new full-gate
attestation. Strict60, M56, commit and push remain held; opt-in concurrent
warm execution remains unapproved and unimplemented.

Both independent mixed-model trailing reviews return **PASS for the P4 seed
portion only**, with no blocking findings. Their overall verdict remains
**HOLD** for the missed60s warm goal and pending fresh seven-phase gate.

### Follow-Up Frozen Gate And Warm Results

The subsequent reviewed, frozen candidate
`03a3b53c865b9bccfd6a372668a600e5c1239770` now passes its own complete
native `scripts/check_milestone.sh`: exit 0, 1011.04s / 520388 KiB. This
is an observed 59.89% wall reduction from the same-host P0's 2520.62s,
not a controlled paired A/B claim. The >=50% cold goal is met; the
10-minute cold working target is not. The existing phase ceilings are unchanged.

| Phase | Wall Seconds | Peak RSS KiB |
| --- | ---: | ---: |
| Driver | 223.49 | 520388 |
| Seed bootstrap | 137.64 | 132656 |
| Proof | 475.78 | 519968 |
| Linux alpha | 8.17 | 63504 |
| Stress leg | 2.80 | 63412 |
| Owned tests | 145.92 | 141372 |
| Ownership sanitizers | 5.84 | 57472 |

Both direct seed comparisons, all 12 proof phases, all 44 corpus cases,
copied release checks, stress and sanitizer coverage pass. The cold owned
tests explicitly use `NQ_TEST_REUSE_C=0`. Driver peak RSS has only 3900 KiB
headroom below its unchanged 524288 KiB ceiling; this is not broad memory
margin. Source/input/index, CC, boot, seed, protected scripts, retained prior
receipts and closing artifact readbacks all pass.

The actual post-gate same-session serial measurements are focused 0.64s /
4700 KiB, full fixture-cache population 154.38s / 141540 KiB, and complete
warm coverage 100.58s / 63544 KiB. Every Nauqtype probe and host assertion
executes. All 23 fixture receipt body hashes and inode/mtime records are
unchanged on warm reuse; metadata stability is observability, not cache
authority. The complete measurement workflow, including setup, population,
warm run and all final readbacks, is 266.178453369s. Final cache and
attestation verification pass. The older 99.89s observation is not reused
as this candidate's result.

| Frozen Gate Identity | SHA-256 |
| --- | --- |
| Milestone attestation | `e9ba14fb03848f977ca50a2093f8846e9118a284ab82064aa065b56b85074c7c` |
| Performance summary | `280f6c9c3a8ef6e871959338fb697138b473a70c0265ff1934d827367f5a8d44` |
| Proof summary | `b8609960f36159f87f0a117009b69060366240547b4f1fa7c8cdd21083bc2894` |

The seed, runtime, generated C, compiler and input identities remain those
of the seed-propagation table above. Native receipts are retained in
`build/verification/p1-p4/followup-full-gate-v1/` and
`followup-gated-warm-v1/`. The compact canonical byte-verified capsule is
`build/verification/p1-p4-20261019/followup-final-evidence-v1/`; its
`SHA256SUMS` seals the copied receipts without copying compiler C or whole
workspaces again. Only the allowlisted completion ledgers change after the
frozen gate; they do not extend its exact candidate identity.

Source/seed and fresh full-gate evidence have independent mixed-model
functional passes. This completes the functional P4 slice, not overall
performance acceptance: the strict warm 60s target still misses by 40.58s.
An opt-in concurrent local tier remains proposed, unapproved and unimplemented;
no tests, failure paths, serial/release behavior or budgets are weakened.
P1-P4 campaign closure and M56 remain held. No commit, push, release or
downstream pin change is claimed.

### Owner-Authorized Concurrent Warm Tier (In Progress)

On 2026-10-21 the owner explicitly authorized the proposed opt-in local warm
tier. Both independent mixed Gate A reviews passed the repaired design before
worker dispatch; the approved review-packet SHA-256 is
`375311b26ba68a7286dbc71c5eb94fadcdfab3443b21302f5277d1b064429aa3`.
The tracked [contract](docs/P1_CONCURRENT_WARM_CONTRACT.md) records that design.
This is not implementation, performance, publication or M56 acceptance.

One sourceable shell coordinator owns four fixed, isolated groups; the existing
Nauqtype tests remain authoritative. An opt-in user scope has fixed aggregate
resource/deadline limits. Retained cgroup descriptors, not unit-name/PID signals,
bind cancellation. A blocked READY/GO handshake and bounded frozen quiescence
precede green resource evidence. Default and full milestone/release/proof
behavior remain serial; scope cancellation is explicitly immediate SIGKILL,
not a new production process rule or graceful-shutdown guarantee.

Approved disposable native capability probes establish only feasibility. The
metadata probe passed. A first FD harness had a syntax error before launch;
the next failed safely because Description appeared before ACTIVE/cgroup/UUID.
No kill FD was opened in that failed run. The corrected probe passes genuine
owned-FD write0/wait137/drain, then retains the old descriptor across removal
and deliberate private-name replacement: old-FD write fails with ENODEV,
while the replacement stays live and naturally exits0. The earlier failures
remain preserved. These probes do not substitute for the production fixtures.

The native routing UNIT/SPIES suite passes all18 cases in0.27s/3560KiB with
source-byte readbacks. A small Nauqtype actual-exec witness builds in
1.39s/63416KiB, with source guards and its invalid mode returning64 with empty
outputs. Actual caller environment/argv comparisons will use memory/FIFOs,
never regular environment dumps. Native receipts are under
`build/verification/p1-p4/concurrent-capability-v1/`, `concurrent-fd-v3/`,
`concurrent-routing-native-v1/` and `concurrent-witness-v1/`.

Coordinator and fixture workers have disjoint write sets; the lead owns routing,
forced-serial milestone behavior, integration and all native runs. Compiler,
runtime, seed and producer inputs are unchanged. Focused implementation tests,
two full opt-in warm observations, final mixed audits and one new frozen
seven-phase gate remain required. The old03a3 attestation is retained only
for its prior candidate. Strict60 and overall P1-P4 acceptance remain open.

## PRE-M56 Concurrent Warm Close

Required P1-P4 goals pass on reviewed frozen candidate
`42999a5f31a8993b5ac8e38235ef5645d074af2d`,2026-10-21. Both independent
source-readiness Gate B verdicts are PASS before the one new full gate.
Primary `gpt-5.6-sol` xhigh and independent `gpt-6-astra` xhigh retain the
explicit unavailable-GPT-5.5 fallback. Final closing review checks these
receipts and only the allowlisted completion-document delta; no changed
executable is covered by an earlier gate.

The repaired source retains uncertain common leases on interrupted cache,
builder or serial work; normal serial completion releases explicitly.
Installed client AND running-manager Version are pinned independently, before
launch and on unit observations. The detached live-child negative proves
rejection before resource capture/ACK with exercised positive spies. Its
owned kill/drain is not mislabeled as a naturally exiting-before-ACK case.
Retired-node stderr is quiet only with independent descriptor-bound retirement
proof; unproven read failure still fails closed. Native routing22 cases pass
in1.81s/3952KiB and focused UNIT/native69 checks in24.66s/7676KiB. Default
unit execution does not require a real manager. Manager-checker refusal uses
actual checker/stub providers; prepare entry order is explicitly STATIC.

| Complete Native Measurement | Seconds | Scope |
| --- | ---: | --- |
| Focused compiler-index with current-cache validation |0.85|No compiler rebuild hidden in this number. |
| Population/setup pass in retained concurrent context |50.13|Existing valid artifacts may hit; not relabeled as fresh compilation. |
| Complete opt-in warm1 |49.46|Aggregate scope peak96215040B; GNU time max-individual63748KiB. |
| Complete opt-in warm2 |46.82|Aggregate scope peak99516416B; GNU time max-individual63640KiB. |
| Whole focused/population/two-warm workflow |150.274565627|Includes setup, three complete passes and final readbacks. |
| New complete serial seven-phase gate |1055.50|520116KiB maximum individual RSS;58.13% below P0's2520.62s. |
| Whole cold measurement workflow |1064.651207127|Includes pre/postflight identity checks and receipt preservation. |

Both warm runs are exit0/drained1 with zero OOM counters, empty stderr and
all8 coverage markers. All23 receipt bodies/inodes/mtimes are unchanged
after EACH warm run. Metadata stability is observability, not cache authority;
the ordinary input/producer/environment/compiler/artifact checks still run.
The complete native workflow preserves source/input/index, toolchain, boot,
provider and protected artifact identities. The cold rebuild reproduces the
same compiler/C/cache/derivation images used by the warm measurements; a
duplicate warm test is not needed merely because construction ran again.

| Fresh Gate Phase | Seconds | Peak RSS,KiB |
| --- | ---: | ---: |
| Stage1 driver |235.04|520116|
| Seed bootstrap |142.53|132540|
| Proof |493.01|519284|
| Linux alpha |9.68|63528|
| Stress leg |2.67|63380|
| Owned tests |153.12|141440|
| Ownership sanitizers |7.83|57848|

All7 phases, both direct seed comparisons, all12 proof phases and44 corpus
cases pass. The cold owned tier explicitly forces reuse0/concurrency0;
default/full-milestone/proof/release remain serial. Strict warm60 is met only
by the explicitly selected supported concurrent local mode. Every test still
executes, no test-result cache is added, and existing budgets remain unchanged.
Driver RSS headroom is4172KiB below its524288KiB ceiling, not broad margin.

| Frozen Artifact | SHA-256 |
| --- | --- |
| Milestone attestation | `3f1de94bd3c608853dad092ec47cfa8c7cd759acb2281270a6d2c85abec10520` |
| Performance summary | `778082b58557b36ebd21b4a914839a8ef1e667b305a916c8c2064e1236b19d82` |
| Proof summary | `b8609960f36159f87f0a117009b69060366240547b4f1fa7c8cdd21083bc2894` |
| Compact evidence capsule SHA256SUMS | `0070cb30aed03a8964375a59946f927f9303aa43efa864e6768e98d151d8002e` |

The compiler SHA remains`d334d2d9e4eaf46fb8edd29b1ef07237339802e95a38a9f3a9502ed5fe53b716`;
emitted/seed/proof C remains`44c6a2f620a2513596965a5839fc68701bd08ac36c26018e3c30189849f4436f`.
Seed/runtime/input identities remain the exact80-source propagation recorded
above. The compact byte-verified capsule is
`build/verification/p1-p4-20261019/concurrent-final-evidence-v1/`; native
`concurrent-focused-v3/`, `concurrent-warm-v2/` and `concurrent-full-gate-v1/`
remain under`build/verification/p1-p4/`. Collection takes20.454243446s and
copies small receipts/source probes, not generated C, seed or whole workspaces.
The9-file196181B repair transfer's4.481862651s excludes its preceding
unmeasured Windows-mounted Git preflight; that partial cost is NOT a complete
workflow speedup. The earlier03a3 capsule and its seal remain unchanged.
Local`refs/nauqtype/verification/pre-m56-20261021` retains the gated tree;
`refs/nauqtype/verification/pre-m56-followup-20261019` preserves03a3 without
rewriting either candidate.

Earlier46.99s/67-check observations remain partial historical evidence and
are not reused as these results. Pre-close pending statuses in the frozen
design/report refer to their earlier capture; this completion entry is current.
Observed cold comparisons are not a randomized causal estimate. Required
focused10/warm60/cold>=50% goals pass, while the10min cold working target
remains unmet and separately tracked. This unblocks M56 planning only: no
language/runtime widening, M56 implementation, stable-release certification,
publication or downstream consumer pin change is claimed.

## M56 Generic Reuse Close

M56's explicit function/product/enum foundation passes on frozen candidate
tree `67272d00dd7d3e6cbb3945cc5777141148ff2cc1`,2026-10-23, based on
`2ddd097f9c233bf407830227639a2b95c60b419c`. Native Ubuntu24.04/ext4 WSL2,
GCC13.3.0 and unchanged serial milestone budgets are the acceptance boundary.
Independent `gpt-5.6-sol` xhigh and `gpt-6-astra` xhigh source/seed readiness
and repair reviews pass; the unavailable-GPT-5.5 fallback remains explicit.
Closing review checks only these receipts and the allowlisted completion docs.

`docs/M56_CONTRACT.md` records explicit n-ary applications, deterministic
definition-owned monomorphization, concrete checked ownership/type/audit
validation, authenticated generated identities, bounded expansion and original
source diagnostics. No traits, methods, inferred constraints, implicit
conversion, runtime helper, public command or active Python work was added.
Unused templates receive structural/name checks, not a universal type proof.
Legacy facts/review/diff/change/policy/rename reject generic graphs with
NQ-GENERIC-008; versioned source/instance evidence must precede generic library
adoption. This is a foundation close, not complete generic evidence parity.

Proof-driven repairs cover exact declaration-local binding/type identity,
checked operand propagation evidence, token-kind-aware generic syntax and
existing negative integer patterns. Owned probes cover positive runtime,
negative diagnostic families, original/UTF-8/two-instance spans, expansion
limits, import provenance, formatter stability and no source/output mutation.
The existing change-report-v4 error output now matches its schema's requested
format enum; no JSON version or failure-envelope shape changed.

The host-GCC profile retains O2 and the512MiB construction ceiling. Its fixed
two GC flags are capability/identity checked, stream bounded independently of
Bash POSIX limit units, invocation frozen and bound to executed argv before
publication. Portable and historical eight-argument recipes remain valid.
Synthetic checks cover20 compiler-profile,7 relocated-input,177 provenance,
153 attestation and14 budget-runner assertions/cases; they are not relabeled
as real compiler proof. The concurrent fixture's synthetic-state publication
is atomic; production containment and cleanup rules are unchanged.

| Fresh Gate Phase | Seconds | Peak RSS,KiB |
| --- | ---: | ---: |
| Stage1 driver |250.62|387048|
| Seed bootstrap |157.36|141012|
| Proof |524.13|610596|
| Linux alpha |8.74|63516|
| Stress leg |2.23|63436|
| Owned tests |177.11|141576|
| Ownership sanitizers |5.40|57664|

`scripts/check_milestone.sh` exits0 with empty stderr. GNU time records1137.41s
including gate/attestation overhead (the whole-second summary records1138).
All7 phases, both direct seed comparisons, all12 proof phases/45 corpus cases
and9 ownership sanitizer fixtures pass. Actual imported generic composition
compiles/runs through both the seed-rebuilt compiler and the physically
relocated release launcher. Original/copied example bytes, modes and loading
boundaries are checked before/after; metadata insertion invalidates success.

| Frozen Artifact | SHA-256 |
| --- | --- |
| Milestone attestation | `1f1e76606c1be58fc42cb237ef0b333ffe38ed0d3663270796ed619f2b70da69` |
| Performance summary | `cb48c3e6f4ec2a81a1d664d8825a03c299673457d42e4a2083a6d3d956c917ae` |
| Proof summary | `d775dd8d5d383344702252b5ebc0e1bde9203fec96d80e8d4ac41119e3705c9a` |
| Seed manifest | `f3ca0e192e3e5e88901b9c2a645219a1eb580b2181d218f7cde6095820c3b4a1` |

Seed, current emitted C and both copied-selfhost C artifacts agree at
`93551f6ab88fe64cd3acc51e541c74616110797e7b7b1b81b3aafe611b0e19d2`;
driver SHA is`ab94e17afd64a450119aa59f8f59dd33a76ccac8c4415f3d0c0ee31ded929549`.
The strict86-source inventory binds construction tree
`21f9f83b5972d417591ba9833705dab72f9c8ee0`, predecessor C`44c6a2f6...`,
generator/runtime/toolchain/flags and exact full-byte self-emission. Generated
C was never hand edited. The compact receipt capsule is
`build/verification/m56-20261023/final-evidence-v1/`; native
`build/verification/m56/` retains component receipts and rollback material.

The first full close failed at synthetic attestation setup: its metadata-only
CC stub returned99 for the new query rather than modeling unsupported exit1.
Its failed summaries remain triage-only under `attestation-repair-v1/failed-gate/`.
The two-file fixture repair, focused153-assertion/sanitizer checks and mixed
repair audits precede the fresh accepted `final-gate-v2/`. The owned empty
serial lock was manually inspected/recovered after jobs ended; no automatic
stale-lock recovery or weakened production probe was introduced.

Historical Python reference tests were not run; they are not active acceptance
gates. Active compiler, fixture, teaching and proof changes remain Nauqtype-owned.

No warm timing, generic speedup, ten-minute cold pass, M57 implementation,
stable release, publication or downstream pin/API freeze is claimed. Prior
P1-P4 measurements and sealed evidence remain unchanged. The tested tree is
retained for strict verification; only allowlisted completion documentation
changes afterward, bound to the final commit by `close`/`verify-close`.

## M56.1 Generic-Aware Evidence Close

M56.1's `facts --format v5` and `review --format v5` pass on frozen candidate
tree `b11e264fb67b24806bbac5ecf08881a586bc7052`, 2026-10-31, based on
`bc0d0b4b38af463404f4434cbd4336c5149da87b`. Native Ubuntu 24.04/ext4 WSL2,
GCC 13.3.0 and unchanged serial milestone budgets are the acceptance
boundary. Compiler lead: Claude Code; implementation by lead-directed
workers in three slices (metadata/renderer, CLI/schemas, emitters/fixture).

`docs/M56_1_CONTRACT.md` (Gate A revision 3, `gpt-5.6-sol` xhigh) and D066
record the formats. Templates are reported once as declared; checked
instances carry rendered type arguments, template identity and
original-source application sites; generated names never appear. Facts and
review v1-v4, review-diff, change-report, policy-check and refactor-rename
still reject generic graphs with NQ-GENERIC-008. The nongeneric bytewise
oracle covers every input with a facts v4 or review v4 golden. NQ-GENERIC-005
is exercised through the CLI; 009 and 010 are reachable only in-process and
are tested there.

One routine trailing audit (`gpt-5.6-sol` xhigh, static review of the frozen
tree) first failed: template records were shape-checked but not
authenticated, so a missing or altered record for an unused template would
not fail. The repair re-runs the elaborator's declaration scan over the
original text and requires exactly one matching template record per generic
declaration (NQ-GENERIC-009 otherwise), with five corruption negatives. It
also fixed stale schema-profile wording and a vacuous-pass path in the
oracle. The re-review passed with no findings. The check shares the
elaborator's scanner, so it authenticates records against source, not the
scanner against itself.

The bootstrap seed was not promoted: no compiler-source language feature
changed. The seed gate therefore re-emits the unchanged M56 seed through its
historical-snapshot path, which is the main reason the seed phase took
longer than at M56.

| Fresh Gate Phase | Seconds |
| --- | ---: |
| Stage1 driver | 291 |
| Seed bootstrap | 329 |
| Proof | 620 |
| Linux alpha | 9 |
| Stress leg | 3 |
| Owned tests | 224 |
| Ownership sanitizers | 6 |

`scripts/check_milestone.sh` exits 0 with empty stderr. GNU time records
1497 s wall, 714300 KiB peak RSS, within the checked-in ceilings.

| Frozen Artifact | SHA-256 |
| --- | --- |
| Milestone attestation | `52646fd1b9bb538f8c0bca4caa8187b8061032190a18b3db1d3e7c0b65cc1eab` |
| Performance summary | `aa390e936edd293fc192f95f96a219bdd8df6127a7736e873cfbfae90f029da7` |
| Proof summary | `fe4b243d4b71942742f0febf18c1241431323ec88fb2b7c4b64b9b15df330644` |
| Seed manifest (unchanged) | `f3ca0e192e3e5e88901b9c2a645219a1eb580b2181d218f7cde6095820c3b4a1` |

Receipts are retained in the native gate clone
(`~/nauqtype-work/m56-1-gate/build/verification/`). Only these allowlisted
completion documents changed after the gate, bound to the final commit by
`close`/`verify-close`. No generic-aware diff/change/policy/rename, M56.2 or
M57 work, stable release or publication is claimed.

## M56.2 Scalar f64 Close

M56.2 scalar `f64` passes on frozen candidate tree
`efac1247490d7969ed4981b7c6f9ac656e085b3d`, 2026-10-31, based on
`0edd35e` (the Gate A contract commit). Native Ubuntu 24.04/ext4 WSL2,
GCC 13.3.0 and unchanged serial milestone budgets are the acceptance
boundary. Compiler lead: Claude Code; implementation by lead-directed
workers in three slices (compiler side, C runtime, tests/evidence/docs).

`docs/M56_2_CONTRACT.md` (Gate A revision 3, `gpt-5.6-sol` xhigh, which
required changes on revisions 1 and 2) and D067 record the feature. It adds
one IEEE binary64 primitive with one literal form, IEEE operators and
comparisons, and no implicit conversion. It also adds:

- six builtins: exact and checked conversions, ECMAScript-style shortest
  rendering with `-0`, and JSON-grammar parsing over length-delimited text
  under a per-call `"C"` locale;
- literal-only constants and no `match` on `f64`;
- NQ-PARSE-004 and NQ-TYPE-046..049;
- a `runtime.h` IEEE guard instead of a new compiler flag, and no libm;
- runtime-native `option<f64>`/`option<i64>` carriers.

The proof-options flag frame, the `host_c.nq` arguments and the fixture
argument allowlist are unchanged. D067 records six implementation
deviations the lead accepted. One was found during integration: the
fixture-C warm-reuse scanner now models `<float.h>`, `<locale.h>` and
exactly `#pragma STDC FP_CONTRACT OFF`; without it, every owned fixture
group silently compiled cold. The runtime unit test passes plain and under
ASan/UBSan/float-cast-overflow, with about 630,000 vectors cross-checked
against Python. Both focused host routes (provenance, attestation) passed
before the freeze.

One routine trailing audit (`gpt-5.6-sol` xhigh, static review of the
frozen tree) returned PASS WITH NITS, with no blocking finding. Repairs:

- the tiny-literal (`<= 2^-1075` → `0.0`) emission now has an executed
  regression on both sides of the boundary;
- the absent `zig cc` fallback now prints an explicit skip line instead of
  passing silently;
- the README's deferred list is corrected.

One nit was declined: a constant-type message pinned by the frozen Python
driver test, which valid `f64` constants cannot reach. The re-review passed.
The zig fallback and a comma-decimal locale are not present on this host, so
those two probes are recorded skips. Proving the zig path is an M60
packaging input.

The bootstrap seed was not promoted: no compiler source contains `f64`
values or float literals.

| Fresh Gate Phase | Seconds |
| --- | ---: |
| Stage1 driver | 300 |
| Seed bootstrap | 336 |
| Proof | 643 |
| Linux alpha | 11 |
| Stress leg | 3 |
| Owned tests | 248 |
| Ownership sanitizers | 6 |

`scripts/check_milestone.sh` exits 0. Its stderr holds only the two
recorded zig-skip lines. GNU time records 1562 s wall and 708036 KiB peak
RSS, within the checked-in ceilings.

| Frozen Artifact | SHA-256 |
| --- | --- |
| Milestone attestation | `63382826fee88d7660e2412a94713a5dd76ba4ac4a25b74910f9ef3e20bdbdd9` |
| Performance summary | `6f0cd2211bbd9b46e3ec52a29d54c8faa5c2ec360d22301bdc6ba3725b1f013f` |
| Proof summary | `3cc68901e612c1c8016c4f4a20e6893377bb67bbbcfde9eee8840117dc7b2f30` |
| Seed manifest (unchanged) | `f3ca0e192e3e5e88901b9c2a645219a1eb580b2181d218f7cde6095820c3b4a1` |

Receipts are retained in the native gate clone
(`~/nauqtype-work/m56-2-gate/build/verification/`). Only allowlisted
completion documents changed after the gate, bound to the final commit by
`close`/`verify-close`. No M57 work, stable release or publication is
claimed.

## M57.1 Library-Enabling Core Close

M57.1 passes on frozen candidate tree
`d3dfaed11be25ce2b1222091e46dfc60e30e3a1d`, 2026-10-31, based on `1aa6d4e`
(the M57 plan and Gate A contract commit). Native Ubuntu 24.04/ext4 WSL2,
GCC 13.3.0 and unchanged serial milestone budgets are the acceptance
boundary. Compiler lead: Claude Code; implementation by lead-directed workers
in three parallel slices (places/assignment, comparisons/match/layouts,
builtins/borrow), an integration slice (evidence, tests, docs) and two
repair rounds.

`docs/M57_1_CONTRACT.md` (Gate A revision 4, `gpt-5.6-sol` xhigh, which
required changes on revisions 1-3) and D068 record the feature: `mutref`
field places and field assignment through `mutref` parameters;
`list_replace`, `list_pop`, `i64_from_i32`, `i32_from_i64`; NQ-TYPE-007
(immutable assignment), NQ-TYPE-050 (comparison table, payload-free enum tag
equality), NQ-TYPE-051 (statement `match` exhaustiveness, with an NQ-C-001
emitter preflight backstop), NQ-TYPE-052 (located non-generic recursive
layouts, also in facts/review); forwarded borrow-parameter conflicts
(NQ-BORROW-006); NQ-RESOLVE-010 for enum variants named like builtin
callables; and per-surface mutation evidence for field writes. The contract's
Implementation Notes record seven accepted deviations, chiefly: the
builtin-name reservation was narrowed to enum variants because M55 Gate B
deliberately supports qualified user functions named like builtins.

Ownership-class trailing audit, independent verdicts. The required
`gpt-5.5` xhigh adversarial auditor is no longer offered on the Codex
account (`model_not_found`, 2026-10-31); `gpt-6.1-sol` xhigh, the strongest
available model distinct from the primary, substituted for it.

| Round | Primary `gpt-5.6-sol` xhigh | Adversarial `gpt-6.1-sol` xhigh |
| --- | --- | --- |
| Frozen `3c55c13` | FAIL: qualified user `list_pop`/`list_replace` routed to builtins | FAIL: same; annotated/inferred shadowing bypassed mutability checks; parenthesized `mutref` places failed handoff |
| Repair `ecbf86d` | FAIL: handoff still chose bindings by insertion order; qualified arity fell back to unqualified names | FAIL: handoff insertion order (counterexample: an `i32` context lowered into an `i64` field); a regression probe was never invoked |
| Repair `a3abd08` | PASS | PASS |

The repairs gate every builtin-specific typecheck and C-lowering branch on
the resolved builtin origin (older list builtins and the integer conversions
had the same name-only dispatch), publish each function's resolved bindings
in declaration order so every downstream nearest-binding scan is correct
(type lookup shared the bug), normalize parenthesized borrow roots, and keep
qualified calls on qualified arity. Each repair has a regression that failed
before it, including sanitized execution.

The bootstrap seed was not promoted; the compiler source compiles under the
stricter rules without source changes.

| Fresh Gate Phase | Seconds |
| --- | ---: |
| Stage1 driver | 331 |
| Seed bootstrap | 363 |
| Proof | 708 |
| Linux alpha | 10 |
| Stress leg | 3 |
| Owned tests | 285 |
| Ownership sanitizers | 6 |

`scripts/check_milestone.sh` exits 0. GNU time records 1720 s wall and
695024 KiB peak RSS, within the checked-in ceilings. Two earlier gate runs
on the superseded candidates (`3c55c13`, `ecbf86d`) also passed; they are
not acceptance evidence.

| Frozen Artifact | SHA-256 |
| --- | --- |
| Milestone attestation | `b6e2f99dee06435aa38be05c87acfb3798a2713d8f17b0a25b621afd22029a83` |
| Performance summary | `3039d90de62bd5a3bdbe559e2991f153d19da762743a53d0170cd3a88579d8a5` |
| Proof summary | `822d31c5f6269436afa0f9cc8ba3289887f7ebcb553b4aca0b3454b956893e13` |
| Seed manifest (unchanged) | `f3ca0e192e3e5e88901b9c2a645219a1eb580b2181d218f7cde6095820c3b4a1` |

Receipts are retained in the native gate clone
(`~/nauqtype-work/m57-1-gate/build/verification/`). Only allowlisted
completion documents changed after the gate, bound to the final commit by
`close`/`verify-close`. No later M57 work, stable release or publication is
claimed.
