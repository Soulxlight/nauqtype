# P1-P4 Performance Execution Contract

Status: proposed for pre-implementation review, 2026-10-19. Base: `a833b31`.
This is the PRE-M56 performance campaign, not M56 language development.

## Acceptance

Preserve all seven milestone phases, both direct seed comparisons, copied
selfhost independence, deterministic evidence, provenance, cleanup, fixtures,
sanitizers, and existing wall/RSS ceilings. No new runtime primitives, source
syntax, reference forms, production flags, parallel compiler, split C units,
or Python implementation. Audit approval alone is not performance evidence.

Campaign goals remain those in `PERFORMANCE_CHECKPOINT.md`: verified-current
focused feedback <=10s, the complete warm fixture tier <=60s including cache
validation, and cold complete elapsed time at least 50% below the comparable
2520.62s P0 baseline (<=10 minutes remains the working target). Record missed
goals explicitly; do not mark the campaign complete by weakening its goals.

## Baseline And Measurement

The published R4-R6 checkpoint is clean. Its native seven-phase gate took
2304.10s: driver 500.42, seed bootstrap 411.06, proof 1172.57, Linux alpha
12.40, stress 2.64, owned tests 171.44, and sanitizers 7.46 seconds. Those
are historical candidate-specific observations, not a fresh paired speedup.

The lead owns one fresh diagnostic profile of the retained current compiler,
with production flags plus `-pg` only. Instrumented results select mechanisms;
they are never reported as production elapsed-time gains. Time warm tier
components separately before deciding on additional host optimizations.

The fresh current diagnostic has now passed (741.20s instrumented wall,
not production timing). It records 32.30B string drops and 32.27B retains,
1.244B parameter-fact clones, and 1.136B checked-parameter clones. Selected
mechanisms are function/parameter lookup, function membership, and exact
visible-item lookup; all remain present after R2. Representative self samples
are checked call parameter mode 7.18s, frontend parameter context 6.85s,
borrow parameter mode 6.54s, borrow count 4.97s, handoff function/block ID
4.62s/4.50s, and indexed-module item scan 11.20s. These are sampled attribution,
not additive production-time savings. Preserve the raw profile and identities.

Preserve the prior gated native capture. Make one new native-ext4 candidate
for implementation, transfer only changed files, and reuse derived artifacts
only through the existing complete input/artifact/toolchain cache contract.
Record setup, copying, hashing, builds, index construction, wall time and RSS.
Obtain two uninstrumented before/after full-tree checks on identical hashed
inputs and the same host/CC/flags, reporting order and repeat spread. A spread
above 10% is inconclusive. Compare emitted C bytes, diagnostics/evidence, and
runtime behavior as appropriate, independently of timing.

## P1: Honest Focused Routing And Warm Tier

Add an explicit fixed-name `nauqc test --suite <name>` route if pre-review
accepts it. Default `nauqc test` must retain the complete existing sequence,
fail-fast behavior, and success text. Partial routes must identify themselves
as partial and reject unknown/empty/duplicate/malformed selectors. Do not add
a broad registry/schema engine. `check_fast.sh` may expose explicit partial
routing; its no-argument default must retain cache validation and all owned,
provenance, attestation, and budget suites. Cache rebuild cost is separate
from focused feedback, never hidden.

Fixed compiler suite names are `compiler-index` (normalizer, visibility,
builtin and the selected new index oracles), `proof-artifacts`,
`workspace-capture`, `workspace-evidence`, `integer-policy`,
`allocation-policy`, `str-join`, `process-time`, `schema-profile` (including
the existing fixture manifest), `driver-fixtures`, and `formatter`. Register
each existing check once, guard groups in the original default order, and
keep default full execution as the empty internal selector. Do not accept
`all` as a named partial suite. Partial success is exactly
`nauqtype test suite <name> ok`, not the default full-suite marker. The shell
accepts exactly `--suite <compiler-name>` or
`--host-suite provenance|attestation|budget`, never both. Compiler routes
validate the cache; host-only unit/stub routes do not claim a current compiler.
Update public help and documentation deliberately; no evidence schema changes.

Remove avoidable elapsed waiting in the interruption fixture only while
retaining a real externally interrupted process and the existing assertions:
GNU timeout owns exit 124, the sidecar observes TERM/143, completed and
unreached phases remain distinct, and no successful receipt survives. A
readiness-triggered alarm to the owned GNU timeout supervisor is a candidate,
not approval to fabricate an exit code or signal unrelated processes. Keep
bounded readiness, timeout, kill-after, cleanup, and child-reaping behavior.

Further snapshot/hash reuse or shell optimizations require component timing
and an exact invalidation/authority contract before implementation. Never
substitute timestamps, directory existence, or a hand-blessed binary for
content and derivation verification.

## P2: Profile-Selected Function Metadata And Membership

Only proceed on mechanisms supported by the current profile. First candidates
are repeated global function/parameter lookups and per-function membership
scans in the existing front end and checked-only downstream passes. Build
small immutable list-backed indexes at phase entry; avoid copying complete
records on every nonmatching lookup. Prefer bounded/log-scale lookup over
merely moving the same full scan into an index object.

Keep phase ownership explicit: front-end/exporter indexes may describe
semantic facts; borrow/value planning/IR indexes may describe only checked
handoff data. No downstream raw-fact fallback. Indexes refer to the exact
source collection supplied at that phase, including module-filtered lists;
global row offsets must never address a filtered/reordered collection.

Preserve original first/last-match behavior for each helper, source order,
shadowing, ambiguity, origins, diagnostic order, IDs, defaults on missing keys,
parameter indices/modes, and mutable local-state isolation. Support interleaved
module/function runs and noncontiguous IDs; do not assume sorted or dense
input. Keep public wrappers compatible. Do not silently change formerly
distinct lookup behavior while sharing an implementation.

Before accepting a selected index, add direct linear-oracle comparisons for
local/import collisions, ambiguous imports, qualified calls, named labels,
missing/out-of-range parameters, ref/mutref/value modes, duplicate keys,
noncontiguous IDs, interleaved records, nested scopes and match bindings.
Selected block/loop indexing also requires cleanup-target/order equivalence.
The existing normalizer's exact digit-text keys, four namespaces, lazy line
comparison and negative mismatch cases remain unchanged.

## P3: Proven Redundant Transfers Only

Attribute clone/drop traffic to the selected scans before editing. Record
the actual reduction in record materializations or generated retain/release
sites, with behavior and cleanup proof. A string retain is not a byte copy.
Do not delete scalar snapshots, field-temporary cleanup, match-payload copies,
or ownership operations based only on appearance. An index that demonstrably
avoids redundant nonmatching record transfers may satisfy this bounded slice;
the milestone does not require a new ownership optimization.

## P4: Exact Seed And Frozen Close

Propagate real compiler improvements through actual compile/re-emission and
the strict seed manifest/source inventory; never hand-edit generated C. Give
independent mixed-model trailing auditors the frozen actual diff, contract,
and exact focused results. Resolve blocking findings first, then run one
complete reviewed native-Linux milestone gate and final attestation. Repairs
after that gate require affected focused checks, review, and a fresh gate.
Report total/phase costs, memory, achieved goals and remaining gaps honestly.

## Ownership And Audit Routing

The lead owns decisions, integration, shared proof registration, measurements,
seed promotion, coordination/docs, Git and the complete gate. Bounded workers
receive disjoint approved source/fixture sets after Gate A. Current research
uses Sol high for compiler mechanisms and Luna medium for feedback routing.

Planned disjoint worker sets, subject to Gate A:

- Sol high frontend worker: `selfhost/typecheck.nq`, `selfhost/handoff.nq`,
  `selfhost/typecheck_probe.nq`. Extend existing phase-owned visibility/
  function ranges for exact item, function/parameter, and selected function
  membership queries. No checked-ID arithmetic assumptions; exact filtered
  collection ownership is required.
- Sol high checked-only worker: `selfhost/borrow.nq`, `selfhost/value_plan.nq`,
  narrow `selfhost/checked_index.nq` and `selfhost/checked_index_probe.nq`.
  Index checked function targets, params, and selected function-member ranges;
  preserve distinct first/last-match semantics and local mutation isolation.
  No raw facts/tokens, IR/C emitter or ownership-rule changes.
- Luna medium feedback worker: selected test routing in `selfhost/main.nq`
  and `selfhost/proof.nq`, `scripts/check_fast.sh`, and narrow selector
  fixtures. No shared semantic-model or host provenance implementation edits.
  The lead registers new worker oracles only after this write scope returns.
- Lead: contract/integration, host interruption optimization, measurement,
  any separately reviewed warm-reuse change, strict seed and final gate.

Workers use apply_patch, perform no commits/pushes, and do not start native
builds/timed tests while the lead's ordinary baselines are running. Report
changed files, exact validation and residual risk. Gate A must clear this
bounded choice before implementation; further unselected mechanisms need a
new evidence-based amendment, not scope creep.

Primary formal audit: `gpt-5.6-sol` xhigh. Independent adversarial audit:
`gpt-6-astra` xhigh, explicitly substituting for unavailable GPT-5.5 in current
tool metadata. Each reaches its own verdict before seeing the other's. No
paid model service, unrelated repository edits, or descendant spawning is
authorized. Record exact worker assignments before implementation.
