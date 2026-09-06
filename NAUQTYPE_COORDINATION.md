# NauqType Work Coordination

Last live review: 2026-09-05.

This is the canonical cross-repository ledger for active NauqType work. It
records coordination state, not aspirational completion. Every Codex working
on NauqType must load the `$nauqtype-work` skill and read this file before
planning, editing, testing, auditing, committing, pushing, or handing off.

## Active Workspaces

| Workspace | Canonical root | Owns |
| --- | --- | --- |
| NauqType | `/home/soulxlight/Documents/NauqType` | Language, compiler, runtime, builtins, evidence schemas, workspace resolution, ABI/FFI, release machinery |
| NQType Libraries | `/home/soulxlight/Documents/NQType-Libraries` | General-purpose NauqType libraries, public APIs, examples, docs, and library tests |
| NQType AI/ML | `/home/soulxlight/Documents/NQType-AI-ML` | AI/ML shapes, tensors, reference algorithms, codecs, metrics, backend adapters, examples, docs, and tests |

`Gemmi Nauqtype`, `NauqType-compiler-audit`, `NauqTypeAudit`, the tutorial,
mounted Windows paths, and other snapshots are not active implementation roots
unless the user explicitly assigns them.

## Active Codex Roles

| Codex | Owns | Current mode | Boundaries |
| --- | --- | --- | --- |
| Compiler Codex (Astra lead) | Active compiler/runtime and compiler-owned proof/seed contracts | M54.8 complete after independent audits and a 1,908-second seven-phase frozen gate; M54.9/M54.10 corrective work continues in isolated preparation trees | Call summaries/validation, versioned evidence failures, bounded schema enforcement, and F15 are evidenced. Integer/allocation and dependency/seed/cache/gate provenance remain open. No other repository edits or M55 feature work. |
| Tool Codex | Nauqtype developer and distribution tooling: package-management and registry design, dependency workflows, CLI ergonomics, build/test/format/lint/docs/editor/debug tooling, release packaging, installation, and toolchain version management | Study only as of 2026-09-04; inventory needs, research precedents, and propose staged contracts without implementation | Does not own language semantics, compiler/runtime internals, general libraries, or AI/ML libraries. Any required provider change follows the contract ledger, and implementation waits for explicit user authorization. |

## Contract Ledger

| Request | Provider | Consumer | State | Current evidence and next action |
| --- | --- | --- | --- | --- |
| [NQTYPE_LIBRARIES_NEEDS.md](NQTYPE_LIBRARIES_NEEDS.md) | NauqType | NQType Libraries | Frozen upstream foundation | [NQTYPE_LIBRARIES_UPSTREAM_RESPONSE.md](NQTYPE_LIBRARIES_UPSTREAM_RESPONSE.md) records the M54 contracts. M54 is implemented at `93a43f9` with the locked `tests/fixtures/m54_library_dependency/` copied-release proof. |
| First six general-library modules | NQType Libraries | NauqType and NQType AI/ML | Frozen initial alpha revision | `src/text.nq`, `src/utf8.nq`, `src/num.nq`, `src/path.nq`, `src/stdio.nq`, and `src/env.nq` pass `scripts/check.sh` with both the source-checkout and copied-release M54 compilers. Public revision [`bed7bf65c9d6e78d13d27d69b9a8019f305a3f0d`](https://github.com/Soulxlight/NQType-Libraries/commit/bed7bf65c9d6e78d13d27d69b9a8019f305a3f0d) carries locked source hash `638bf061fde6a14b51ae2aa031a86308b38745293f4713ff67519a7481b8764d`. Consumers may pin that exact revision; APIs remain experimental across future revisions. |
| [AIMachineLearning_NEEDS.md](AIMachineLearning_NEEDS.md) | NauqType | NQType AI/ML | Responded; A1 unblocked, numeric contracts scheduled/provisional | [AIMachineLearning_UPSTREAM_RESPONSE.md](AIMachineLearning_UPSTREAM_RESPONSE.md) accepts the product pressure, authorizes provisional A1 shape/error work now, and splits remaining work into AI-U1 scalar numerics, AI-U2 storage/bytes, AI-U3 math/codec/RNG, and AI-U4 integration proof. Public milestone numbers and numerical contracts are not frozen yet. |
| AIML A1 shape/error groundwork | NQType AI/ML | Future AIML tensor work | Evidenced locally, not frozen | `NQType-AI-ML/src/shape.nq` now provides provisional checked dimensions, canonical row-major strides, layout, offsets, reshape, and closed errors; the locked source hash is `e0afabc92ca93d29948a06b269371d3850d10c4cf5eb92a8e5e10899f4f15e41`. `NQType-AI-ML/scripts/check.sh` passes library/formatter checks, a locked copied-workspace facts v3/review v2 build/run, and the generated program separately passed the address/leak sanitizer. The repository remains unborn, so review plus an exact revision are still required before freezing or consumption. No float or tensor-storage promise is implied. |
| AIML scalar floats and math | NauqType, then NQType Libraries | NQType AI/ML | Blocked/requested | `f32`/`f64`, conversions, IEEE policy, classification, bit conversion, and reference math are not implemented end to end. Compiler primitives come first; ordinary wrappers belong in NQType Libraries. |
| AIML contiguous storage and binary codecs | NauqType, then NQType Libraries | NQType AI/ML | Blocked/requested | Current `list<T>` is contiguous but append/read-oriented and allocation failure aborts. Recoverable fixed-size construction, indexed replacement, copy/fill, byte mutation/slicing, overflow rules, and later native-borrow rules remain open. General endian/dtype codecs belong in NQType Libraries. |
| AIML deterministic RNG and entropy | NauqType, then NQType Libraries | NQType AI/ML | Blocked/requested | Seeded RNG needs versioned wrapping/bit operations or another frozen primitive. Seeded generation must remain pure. OS entropy is separate checked authority and must not be replaced by time-derived seeding. |
| Locked `nauqtype.ai` integration fixture | NauqType | NQType AI/ML | Blocked | Add only after float, storage, codec, and deterministic RNG contracts are evidenced. It must prove library-only checking, facts/review provenance, source and copied-release build/run, deterministic numeric behavior, failures, and cleanup. |

## Completed Foundation

- NauqType stage1 is self-hosted and has checked handoff, borrow checking, IR,
  deterministic C emission, copied self-build proof, and Linux release gates.
- M54 supplies exact `i64`, owned `bytes`, Linux streams/environment/cwd,
  checked filesystem operations, stable structured `io_err` accessors, fixed IO
  evidence subkinds, explicit locked local dependencies, facts v3 provenance,
  library-only `check`, and a copied-release general-library fixture.
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
  No external repository was modified. M55 must first repair interrupted
  process read/wait handling (F14); no process feature expansion landed here.

- M54.7 closes expression precedence, ordered matches, and C-name collisions,
  including the sanitizer-discovered expression-arm binding leak. The seed
  fixed point, 42-case corpus, Linux release, and nine ownership sanitizer
  cases passed the one frozen-candidate gate after independent audit PASS.
- The immediate work is M54.8-M54.10 corrective closure of the independent
  Astra audit. See [AUDIT_REMEDIATION.md](AUDIT_REMEDIATION.md) for findings,
  acceptance evidence, and boundaries. M55 structured process, time, timeout,
  and cancellation remains the next feature milestone after those repairs.
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
