# NauqType Work Coordination

Last live review: 2026-09-06.

Compiler/tooling planning update: 2026-10-09. Gate efficiency is the first
priority before M56. WSL Ubuntu base tools and the reviewed native compiler
P0 baseline are verified: seven-phase cold gate 2520.62s, repeated checks
304.23s/308.99s. `PERFORMANCE_BASELINE.md` records identities and scope;
overall speedup acceptance remains open. E1 and the bounded P2 normalizer
mapping slice are evidenced below, not full P1-P4 closure. The user assigned
the guide-only authoring lane to the compiler lead with a Sol High Professor
worker; its draft is staged separately and not yet integrated or evidenced.
The nonpackaged [documentation refactor](docs/REFACTOR_PLAN.md) adds a
[task/authority index](docs/README.md) and [compiler map](docs/COMPILER_MAP.md)
while preserving executable inputs and the existing performance sequence.
Its source slices remain pending. The exact reviewed P0/E1/P2 baseline is
locally committed as `0564a32`, with verified P2 closing evidence. A separate
R1 packaged README passed mixed trailing audits and its own fresh Linux
milestone gate on the exact candidate recorded below. That documentation
acceptance does not extend the earlier P2 attestation or complete the source
refactor, performance campaign, stable release, or publication.
This update does not refresh dated downstream evidence or recover the missing
workspaces/documents listed below. The required read-only status snapshot on
2026-10-09 found local Libraries changes; they remain outside this write set.

This is the canonical cross-repository ledger for active NauqType work. It
records coordination state, not aspirational completion. Every Codex working
on NauqType must load the `$nauqtype-work` skill and read this file before
planning, editing, testing, auditing, committing, pushing, or handing off.

## Active Workspaces

| Workspace | Repository location | Owns |
| --- | --- | --- |
| NauqType | This checkout's root | Language, compiler, runtime, builtins, evidence schemas, workspace resolution, ABI/FFI, release machinery |
| NQType Libraries | Separately configured `NQType-Libraries` checkout | General-purpose NauqType libraries, public APIs, examples, docs, and library tests |
| NQType AI/ML | Separately configured `NQType-AI-ML` checkout | AI/ML shapes, tensors, reference algorithms, codecs, metrics, backend adapters, examples, docs, and tests |

`Gemmi Nauqtype`, `NauqType-compiler-audit`, `NauqTypeAudit`, the tutorial,
mounted Windows paths, and other snapshots are not active implementation roots
unless the user explicitly assigns them.

### Portable Locations

Resolve the active root with `git rev-parse --show-toplevel`; paths in this
repository's instructions are relative to that root unless stated otherwise.
Keep machine-specific checkout and credential locations in untracked local
configuration. Do not assume related repositories are siblings or use a
remembered home directory to locate them. Verify each separately assigned
checkout before claiming current consumer status; the dated evidence below
does not establish that a workspace still exists on the current host.

Historical candidate names in milestone reports are snapshot identifiers, not
paths to available directories. Their original host-specific parent locations
have been omitted from prose; recorded revisions, digests, measurements, and
raw audit artifacts remain unchanged. Sanitizing documentation neither
recovers missing local artifacts nor reruns historical verification. Git
history is not rewritten by this cleanup.

Checkout inventory on 2026-09-19: `AIMachineLearning_NEEDS.md`,
`AIMachineLearning_UPSTREAM_RESPONSE.md`, and `TOOLING_STUDY.md` are absent
from the recovered tracked tree. References below are historical pointers,
not available local documents or fresh evidence of another lane's status.
Recover or obtain them from their owners before relying on those records.

### Shared Linux Verification

[WSL_DEVELOPMENT.md](WSL_DEVELOPMENT.md) defines the local Codex/Kimi Code
integration workflow. Ubuntu 24.04 now runs under WSL2 with a non-root user,
GCC 13.3.0, Git, GNU time, and native ext4 home storage. Kimi's earlier
`wsl.exe` access check does not establish a fresh Linux integration pass.
The specific reviewed compiler P0 capture/cache and baseline are now verified
in `PERFORMANCE_BASELINE.md`; library integration remains pending. No remote relay access,
shared credentials, or agent permission changes are implied. Keep each
repository owner's sources and compiler/dependency pins explicit.

## Active Codex Roles

| Codex | Owns | Current mode | Boundaries |
| --- | --- | --- | --- |
| Compiler Codex (director plus scoped workers) | Active compiler/runtime and compiler-owned proof/seed contracts | M55 complete; candidate-specific P0, E1, and P2 mapping evidenced; pre-M56 gate efficiency remains the highest priority | Use `PERFORMANCE_BASELINE.md`, `PERFORMANCE_MAPPING.md`, and the closure below; broader P1-P4 must still shorten focused checks and measured snapshot/scan/comparison/clone costs before M56. Use `AGENT_ROUTING.md`; the modest single cold-run gain does not meet campaign goals, and no external repository change is claimed. |
| Tool Codex | Nauqtype developer and distribution tooling: package-management and registry design, dependency workflows, CLI ergonomics, build/test/format/lint/docs/editor/debug tooling, release packaging, installation, and toolchain version management | Study only as of 2026-09-04; inventory needs, research precedents, and propose staged contracts without implementation | Does not own language semantics, compiler/runtime internals, general libraries, or AI/ML libraries. Any required provider change follows the contract ledger, and implementation waits for explicit user authorization. |

## Contract Ledger

R1 documentation checkpoint (2026-10-09): the packaged README and documentation
routing passed independent gpt-5.6-sol xhigh and gpt-6-astra xhigh audits
(explicit unavailable-GPT-5.5 fallback), followed by one fresh seven-phase
Linux gate on indexed candidate
`16b8e84271c5c3e4db20384c17977a102710395b`: 2507.89s, 437144 KiB peak RSS,
44 corpus cases, verified attestation, and byte-identical copied README with
valid packaged links. Only allowlisted completion documents change afterward.
The baseline remains separately checkpointed in `0564a32`; no executable
source, runtime, schema, or seed changed in R0/R1. The next proposed R2 slice
is a bounded visible-item lookup index based on separate sampled attribution,
not a claimed speedup. No downstream workspace or consumer pin is changed.

PRE-M56 P2 mapping (2026-10-04): compiler-owned private append-only sorted
runs preserve the old structural normalizer result and early-exit boundary.
The 36-pair oracle, actual owned invariants, sanitizers, complete-compiler
measurements (25-26x comparison gain), and exact self-generated seed passed.
Source SHA-256 is `6c161ecfcf254b602d4aa9199024f3e4890f2e7d26daba6f147b157af7bc379d`;
seed C is `5221d8ab5c788140bea2a079b2a37bc2de6204c0939399bf328c6803d3f0bc08`.
Both independent final audits passed, then the one cold seven-phase gate and
matching attestation passed on candidate
`36e68e791d3ec2bb3b068fbabd69894a01913803`: 2485.30s, 436232 KiB peak RSS,
44 corpus cases. Total is 2.90% less than E1 and 1.40% less than P0; proof
and compiler construction still dominate, and the campaign goals remain open.
Comparison memory rises to 43948-44768 KiB versus 25940-26496 KiB reference.
See `PERFORMANCE_MAPPING.md` and `ROADMAP.md`; this candidate evidence was
checkpointed locally in `0564a32` on 2026-10-09. It is not publication,
an external consumer pin, or full generics.
Next compiler action is bounded compiler-scan attribution; no other repo
is changed or unblocked by an inferred adoption claim.

PRE-M56 E1 (2026-10-01): compiler-owned `str_join(parts: ref list<str>) -> str`
is implemented/focused-evidenced under `PERFORMANCE_ENABLEMENT.md`: assembly
batches improve 18.3x, while representative ~80s comparisons show no
conclusive gain. Exact self-generated seed C is `73ee8c354d3241dbcce9da003708a8ff6b3c5e0e903fe8c425c3aad7e0ec55de`;
source lock is `317fcc1aa4d2415493700e406ba41368d328043adfebbbdca7c74bd4991b5e2f`.
It is the sole admitted performance-enabling builtin; full M56 generics and
P1-P4 goals remain separate. Both independent final audits and the one cold
seven-phase gate/attestation passed on indexed candidate
`7a5a1a894537989c64ca59ce7803fd8d8c398781` (2559.57s, 436000 KiB peak RSS,
44 corpus cases). The cold gate is not faster than P0. The implementation is
content-locked/evidenced and now locally checkpointed in `0564a32`: no
consumer pin migration, publication, or adoption is claimed. Next compiler-owned action is bounded
P2 scan/mapping attribution and optimization, not full generics.

| Request | Provider | Consumer | State | Current evidence and next action |
| --- | --- | --- | --- | --- |
| [NQTYPE_LIBRARIES_NEEDS.md](NQTYPE_LIBRARIES_NEEDS.md) | NauqType | NQType Libraries | Frozen upstream foundation | [NQTYPE_LIBRARIES_UPSTREAM_RESPONSE.md](NQTYPE_LIBRARIES_UPSTREAM_RESPONSE.md) records the M54 contracts. M54 is implemented at `93a43f9` with the locked `tests/fixtures/m54_library_dependency/` copied-release proof. |
| [M55_CONTRACTS.md](M55_CONTRACTS.md) | NauqType | Future general process/time modules and applications | Frozen compiler contract in this checkpoint | Exact source SHA-256 `be878c88dca696269c4c565c5b7f22f5d883d41ab1299b929c22a3d863b4a217`; seed C `2ec30ab03c77d5b113eb414e18e5b4ba52c6217d9cf3283f938eea8b150c5084`. Owned start/wait/terminate, bounded capture, nominal time/deadlines, checked cleanup authority, and `tests/fixtures/m55_process/runtime.nq` pass the copied-release gate. Consumers must explicitly pin this compiler and migrate old workspace locks; no external consumer adoption is claimed. |
| First six general-library modules | NQType Libraries | NauqType and NQType AI/ML | Frozen initial alpha revision | `src/text.nq`, `src/utf8.nq`, `src/num.nq`, `src/path.nq`, `src/stdio.nq`, and `src/env.nq` pass `scripts/check.sh` with both the source-checkout and copied-release M54 compilers. Public revision [`bed7bf65c9d6e78d13d27d69b9a8019f305a3f0d`](https://github.com/Soulxlight/NQType-Libraries/commit/bed7bf65c9d6e78d13d27d69b9a8019f305a3f0d) carries locked source hash `638bf061fde6a14b51ae2aa031a86308b38745293f4713ff67519a7481b8764d`. Consumers may pin that exact revision; APIs remain experimental across future revisions. |
| [AIMachineLearning_NEEDS.md](AIMachineLearning_NEEDS.md) | NauqType | NQType AI/ML | Responded; A1 unblocked, numeric contracts scheduled/provisional | [AIMachineLearning_UPSTREAM_RESPONSE.md](AIMachineLearning_UPSTREAM_RESPONSE.md) accepts the product pressure, authorizes provisional A1 shape/error work now, and splits remaining work into AI-U1 scalar numerics, AI-U2 storage/bytes, AI-U3 math/codec/RNG, and AI-U4 integration proof. Public milestone numbers and numerical contracts are not frozen yet. |
| AIML A1 shape/error groundwork | NQType AI/ML | Future AIML tensor work | Evidenced locally, not frozen | `NQType-AI-ML/src/shape.nq` now provides provisional checked dimensions, canonical row-major strides, layout, offsets, reshape, and closed errors; the locked source hash is `e0afabc92ca93d29948a06b269371d3850d10c4cf5eb92a8e5e10899f4f15e41`. `NQType-AI-ML/scripts/check.sh` passes library/formatter checks, a locked copied-workspace facts v3/review v2 build/run, and the generated program separately passed the address/leak sanitizer. The repository remains unborn, so review plus an exact revision are still required before freezing or consumption. No float or tensor-storage promise is implied. |
| AIML scalar floats and math | NauqType, then NQType Libraries | NQType AI/ML | Blocked/requested | `f32`/`f64`, conversions, IEEE policy, classification, bit conversion, and reference math are not implemented end to end. Compiler primitives come first; ordinary wrappers belong in NQType Libraries. |
| AIML contiguous storage and binary codecs | NauqType, then NQType Libraries | NQType AI/ML | Blocked/requested | Current `list<T>` is contiguous but append/read-oriented and allocation failure aborts. Recoverable fixed-size construction, indexed replacement, copy/fill, byte mutation/slicing, overflow rules, and later native-borrow rules remain open. General endian/dtype codecs belong in NQType Libraries. |
| AIML deterministic RNG and entropy | NauqType, then NQType Libraries | NQType AI/ML | Blocked/requested | Seeded RNG needs versioned wrapping/bit operations or another frozen primitive. Seeded generation must remain pure. OS entropy is separate checked authority and must not be replaced by time-derived seeding. |
| Locked `nauqtype.ai` integration fixture | NauqType | NQType AI/ML | Blocked | Add only after float, storage, codec, and deterministic RNG contracts are evidenced. It must prove library-only checking, facts/review provenance, source and copied-release build/run, deterministic numeric behavior, failures, and cleanup. |
| [AUTHORING_KIT.md](AUTHORING_KIT.md) | Compiler lead owns guide-only integration; Sol High Professor worker stages the bounded draft | Human-supervised model authors | Guide-only work assigned 2026-10-04; not integrated/evidenced, grammar and pilot remain design | Compact repo-local onboarding skill and authoritative compiler/example references first, staged outside the frozen P2 candidate. Lead verifies before integration. No grammar/decoder/model call, savings claim, or pilot authorization; conditional M59 maintained-kit integration remains separate from M56. |
| [PERFORMANCE_CHECKPOINT.md](PERFORMANCE_CHECKPOINT.md) | NauqType | Compiler developers and future M56 work | Highest priority; candidate-specific P0 and P2 mapping evidenced, broader P1-P4 open | `PERFORMANCE_BASELINE.md`: P0 cold gate 2520.62s; repeat checks 304.23s/308.99s. P2 mapping cold gate 2485.30s; its single run improved modestly but did not meet the >=50% campaign goal. P1 focused checks/capture reuse; P2 compiler scans; P3 redundant transfers; P4 campaign-wide attested acceptance remain. Goals: <=10s focused, <=60s warm fixtures, >=50% faster cold gate with <=10min working target. No relaxed budget is claimed. |

## Completed Foundation

- NauqType stage1 is self-hosted and has checked handoff, borrow checking, IR,
  deterministic C emission, copied self-build proof, and Linux release gates.
- M54 supplies exact `i64`, owned `bytes`, Linux streams/environment/cwd,
  checked filesystem operations, stable structured `io_err` accessors, fixed IO
  evidence subkinds, explicit locked local dependencies, facts v3 provenance,
  library-only `check`, and a copied-release general-library fixture.
- M55 adds Linux owned process handles, consuming wait, cancellation, bounded
  capture, explicit environment/stdin, nominal duration/instant values, and
  checked cleanup authority. The contract does not promise hard-real-time
  deadlines, background pumping, or control of escaped descendants.
- NQType Libraries has published byte-oriented text, explicit UTF-8, checked
  integer parse/render, lexical Linux path, standard-stream, and
  argument/environment/cwd modules at exact revision `bed7bf65c9d6e78d13d27d69b9a8019f305a3f0d`.
  That revision is frozen for pinned consumption; APIs remain experimental
  across future revisions.
- NQType AI/ML has an initialized provisional workspace, ownership rules, a
  capability audit, an A0-A4 roadmap, and locally evidenced A1 shape/error
  groundwork. No tensor or numeric API is frozen, and A1 has no published
  revision yet.

## Current Parallel Lanes

### NauqType Compiler/Runtime

- Immediate work is the pre-M56 performance checkpoint. The director owns
  acceptance and integration; scoped workers own bounded implementation and
  documentation. The Ubuntu/GCC/ext4 runner has now passed the reviewed,
  indexed P0 candidate's complete gate and repeatable checks. M55 remains
  complete; broader P1-P4 remain open. P2 mapping closure is recorded above,
  separately from P0's baseline and E1's assembly-only gain. Seed-phase
  instrumentation passed repair audits, focused checks, and its candidate's
  gate; later changes do not inherit an earlier candidate's attestation.
- M54.10 migration notice: the completed compiler rejects old dependency locks and
  requires explicit `workspace-lock/v2` path/content framing. Published
  Libraries revision `bed7bf6` and provisional AIML source are not changed.
  Their owners must regenerate and evidence consumer locks before upgrading
  to this compiler; existing M54-pinned compiler/source evidence remains
  historical evidence, not proof of compatibility with the new lock contract.
  See `WORKSPACE_LOCK.md` and `M54_10_CONTRACTS.md`. No external lock edits or
  new numerical/AI APIs are authorized by this correction.
- M54.8-M54.10 corrective closure is now evidenced: M54.10's independent
  Sol xhigh/GPT-5.5 xhigh audits passed and the unchanged candidate passed all
  seven gate phases plus real attestation in 2,716 seconds. Exact source,
  seed, cache, proof, and release identities are in `M54_10_CONTRACTS.md`.
  No external repository was modified. That checkpoint deferred interrupted
  process read/wait handling (F14), now closed by M55 below.

- M54.7 closes expression precedence, ordered matches, and C-name collisions,
  including the sanitizer-discovered expression-arm binding leak. The seed
  fixed point, 42-case corpus, Linux release, and nine ownership sanitizer
  cases passed the one frozen-candidate gate after independent audit PASS.
- M55 is complete: focused native fault/sanitizer and Nauqtype integration
  checks, independent Sol max/GPT-5.5 xhigh audits, actual seed fixed point,
  and the unchanged seven-phase milestone gate plus attestation all passed.
  See [M55_CONTRACTS.md](M55_CONTRACTS.md) for exact signatures and lifecycle
  limits; `AUDIT_REMEDIATION.md` records the 2,504-second gate and identities.
  The next compiler milestone is M56, not started. M54.8-M54.10 are closed;
  the following intermediate notes are historical, not open corrective work.
- M54.8a now shares strict source-contract validity across compilation and
  evidence commands, with contract diagnostics emitted once per analyzed input
  and checked-plan readiness.
  All seven frozen-gate phases passed after the independent repair audit.
  M54.8b still owns absent/partial evidence and versioned failure envelopes;
  this is not blanket closure of the contract/evidence audit findings.
- M54.8b1 now provides opt-in review v3 with checked-ID direct-write evidence
  and absent/declared audit provenance. All 1,467 selfhost functions passed
  the v3 smoke. Legacy review outputs remain unchanged; the parent corrective
  milestone remains open for call summaries, validation, and failure evidence.
- M54.8 final closure now supersedes those intermediate open items: checked
  call summaries, review v4/change-report v3, evidence-error v1, bounded schema
  enforcement, and F15 passed independent audits and the seven-phase gate.
  See `M54_8_CONTRACTS.md` for frozen tree and artifact identities. This does
  not freeze M54.9/M54.10 or change external dependency lock contracts yet.
- M54.9 now closes integer/allocation findings F06/F13. Final Sol max and
  GPT-5.5 xhigh reviews passed; the unchanged candidate passed all seven gate
  phases in 2,048 seconds. See `M54_9_CONTRACTS.md` for arithmetic, allocation,
  borrow-place repair, and exact seed/gate evidence. This changes no Libraries
  or AIML implementation and does not yet close M54.10 provenance or M55/F14.
- M54.5 development-loop efficiency is complete and evidenced: content-verified
  stage1 caching, 44 corpus compiler passes in place of 114, audit-before-gate
  close ordering, and quick/full CI tiers all passed the 2,132-second
  exact-candidate milestone gate. This removes repeated development work but
  did not materially reduce the 2,128-second cold baseline.
- M54.6 is implemented and measured: function-local semantic slices, one
  private borrow-child index, and one-pass visible-item origin lookup reduced
  the same-host full-tree check from 349.76 seconds to repeat runs of 194.66
  and 194.51 seconds with effectively unchanged peak RSS. The audited
  exact-candidate milestone gate passed all seven phases in 1,517 seconds.
  Public semantic, evidence, proof, and release contracts remain unchanged.
- The AIML response now splits the numerical request into independently
  evidenced AI-U1 through AI-U4 slices. Public milestone numbers still need to
  be assigned before implementation begins.

### Model Authoring (Planned)

- `AUTHORING_KIT.md` records the accepted direction and the external Kimi
  prototype's blockers. No kit code, model benchmark, or savings claim has
  been adopted. Compiler source and checked evidence remain authoritative.
- Assign an implementation owner and bounded write set before work begins.
  Keep compiler/evidence contracts here and ordinary shared helpers in
  NQType Libraries; do not revive Python orchestration in the active path.
- A pilot needs separate data/spend authorization and isolated execution of
  all generated programs, independent of their declared effects. No live
  model call enters mandatory tests or replaces an audit.
- M56 remains the next compiler milestone. M59 is the conditional integration
  home for authoring components with measured benefit; a failed experiment
  does not block the stable Linux program.

### NQType Libraries

- Consumers may pin the published `text`, `utf8`, `num`, `path`, `stdio`, and
  `env` foundation at `bed7bf65c9d6e78d13d27d69b9a8019f305a3f0d`.
- Do not invent compiler/runtime primitives in this repository.
- Add general math, binary codec, and deterministic RNG modules only after
  their upstream primitives are frozen.

### NQType AI/ML

- A1 shape/error APIs are implemented and locally evidenced with provisional
  `NqAi`-prefixed names over exact integers. Review and a published revision
  remain before the contract can freeze.
- Do not freeze tensor, float, storage, RNG, codec, or native-backend APIs
  before the corresponding upstream response and executable evidence.
- Start with a deterministic single-threaded CPU reference backend. Generics,
  native acceleration, tasks, and GPU work remain later dependencies.

### Tool Codex

- [TOOLING_STUDY.md](TOOLING_STUDY.md) is the current study-only inventory and
  staged recommendation for workspace tooling, package management, registries,
  editor support, and toolchain/Linux distribution.
- No tooling implementation is authorized yet. Proposed command names,
  schemas, package rules, and provider requests remain provisional pending
  review.
- Tool Codex must not implement compiler/runtime prerequisites or library
  functionality; those dependencies enter this ledger as requests to their
  owning lanes.

## Planned Dependency Order

1. Preserve the M54.5/M54.6 development-loop and semantic-performance gains
   without weakening cold release proof; close M54.7-M54.10 audit corrections
   before adding feature surface.
2. Publish the current NQType Libraries tranche while AIML reviews and
   publishes its locally evidenced A1 shape groundwork.
3. Complete M55 without treating time as entropy.
4. Add scalar `f32`/`f64`, explicit conversions, IEEE behavior, and narrow math
   primitives through every compiler/evidence/proof phase.
5. Add recoverable contiguous numeric storage and mutable binary-byte support.
6. Let NQType Libraries provide general math, endian codecs, and a versioned
   deterministic RNG over those primitives.
7. Let AIML build a provisional monomorphic `NqAiTensorF32` reference slice.
8. Freeze the compiler-owned `nauqtype.ai` integration fixture.
9. Continue M56 generics, M57 data facilities, M58 FFI, and M59 bounded tasks;
   generalize and optimize AIML only when each dependency is evidenced.

## Update Rules

- Use `requested -> scheduled -> implemented -> evidenced -> frozen ->
  consumed` consistently. Do not skip states in prose.
- A needs file is not permission for a consumer to patch its provider.
- The owner of an implementation supplies exact files, checks, revision/hash,
  remaining risks, and whether APIs are provisional.
- A provider response is not frozen until executable evidence exists.
- Any NauqType Codex may propose a factual update to this ledger for work it
  personally verified. It must not rewrite another owner's plan or completion
  claim, and it must leave commit/push control with the compiler-repository
  lead.
- Preserve unrelated dirty work in every repository. Never use the historical
  mounted Windows checkout as a source of current truth.
