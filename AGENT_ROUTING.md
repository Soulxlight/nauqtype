# Agent Routing Policy

This is a task-fit policy, not a billing promise. Model availability is
determined by the current host/tool metadata; recheck it when dispatching.
Actual tokens, latency, and account cost are unknown unless measured from the
run, so do not project account savings.

## Defaults

| Work shape | Default fit | Boundary |
| --- | --- | --- |
| Mechanical documentation, bounded inventories, and bounded test-command checks | `gpt-5.6-luna` medium | Keep the write set disjoint and the prompt compact. Escalate ambiguity rather than widening scope. |
| Scoped shell profiling or ordinary implementation after contracts are fixed | `gpt-5.6-terra` high | Profile existing cost first; do not turn a bounded task into architecture work. |
| Compiler semantic indexing or ownership-sensitive code | `gpt-5.6-sol` high/xhigh | Preserve semantic identity, cleanup, provenance, and output-order contracts. |
| Independent trailing audit | `gpt-5.6-sol` xhigh | Read-only, findings-first, and independent of the implementation verdict; this retains the `AGENTS.md` audit policy. |
| Ownership, bootstrap, process, FFI, or release boundaries | `gpt-5.5` xhigh alongside the existing mixed review pattern | Use the stronger mixed-model review required by the repository policy. |
| Decomposition, scope, integration, and escalation | Current lead model | The director owns orchestration and decisions, not routine implementation. This includes integration in `AGENTS.md`, `README.md`, `NAUQTYPE_COORDINATION.md`, and `PERFORMANCE_BUDGETS.md`. |

The 2026-09-20 preparation assignments were documentation routing on Luna high,
measurement/preflight on Terra high limited to
`scripts/profile_selfhost.sh` and `scripts/check_profile_selfhost.sh`, the
retained independent Sol xhigh auditor, and the director on the current model.
The explicit high assignment does not change the
medium default for future mechanical documentation.

The harness repair escalated from Terra high to Sol high after the independent
audit found cache-to-measurement identity and filesystem-verification gaps.
The repair keeps the same two-script write set; the original Sol xhigh auditor
remains read-only and owns the repair review. No extra full gate is authorized.

For the 2026-09-30 roadmap update, the bounded gate inventory and two-document
refresh use available `gpt-6-luna` medium; the lead owns integration and
`gpt-5.6-sol` xhigh owns the independent documentation audit. The older
Luna/Terra assignments above are historical, not a claim that those model IDs
remain offered by the current host. Recheck tool metadata before later work.

R1 packaged-documentation work on 2026-10-09 uses available `gpt-6-luna`
medium for the README-only worker. The lead owns baseline identity, native
candidate integration, and verification. Independent reviews use
`gpt-5.6-sol` xhigh and `gpt-6-astra` xhigh; the required historical
`gpt-5.5` model is unavailable in current spawn metadata. The exact prior P2
tree is checkpointed separately; its retained gate does not attest the new
README candidate. No compiler/runtime behavior or optional model service is
part of this documentation slice.

## Dispatch Rules

Lead handoff on 2026-10-30: the owner assigned the compiler lead to a Claude
Code session. The fit table above still describes task shape; a Claude lead
maps it onto Claude subagents for workers (cheapest capable model for
mechanical work, strongest for semantics/ownership/integration) and keeps the
formal audit policy unchanged by dispatching independent auditors as
read-only Codex threads. See [CLAUDE.md](CLAUDE.md). The lead's own model is
never the sole independent auditor of its own integration.

M56 on2026-10-23 uses `gpt-5.6-sol` high workers for disjoint generic
elaboration, owned Nauqtype fixtures, checked propagation evidence repair and
the bounded host compiler memory profile. Ownership transfers are explicit;
workers do not commit, promote seeds or launch native heavyweight jobs. The
lead owns integration, exact generated-seed lineage, docs and serial Linux
measurements. Independent `gpt-5.6-sol` xhigh and `gpt-6-astra` xhigh audits
retain the unavailable-GPT-5.5 fallback. M56 has no paid model dependency,
new runtime authority, traits, methods or inferred generic requirements.

On 2026-10-21 the owner explicitly approved an opt-in local concurrent warm
tier. Both independent mixed Gate A reviews passed the revised
`docs/P1_CONCURRENT_WARM_CONTRACT.md`, including descriptor-bound cleanup and
frozen resource quiescence. Existing Sol High workers have disjoint ownership:
the production coordinator is `scripts/fast_concurrent.sh`; the fixture worker
owns `scripts/check_fast_concurrent.sh` and its small Nauqtype witnesses under
`tests/fixtures/p1_concurrent/`. The lead owns routing, locks, registration,
forced-serial milestone behavior, native measurements, docs and Git. Workers
do not launch native gates or touch compiler/runtime/seed code. The same
independent Sol xhigh/Astra xhigh fallback audits apply. Default, milestone,
proof and release remain serial; the strict60s target is not waived.

The follow-up warm-tier attribution on 2026-10-19 uses available
`gpt-6-luna` medium for bounded same-session timing and one host CPU capture,
not production edits. After both independent Gate A approvals, the Sol High
literal-scan worker owns only `selfhost/fixture_c.nq`'s two private predicates
and their retained linear oracles; the Sol High process worker owns only the
bounded local recheck in `stdlib/runtime.c` and scheduling assertions in the
existing `tests/fixtures/m55_process/native_faults.c`. The contracts are
`docs/P1_FIXTURE_SCAN_CONTRACT.md` and `docs/P1_PROCESS_RECHECK_CONTRACT.md`.
The lead owns integration, ordinary paired measurements, exact seed/runtime
propagation and the eventual fresh close. Native heavy jobs are serial and
explicitly handed off. The same independent mixed audit fallback remains;
no new runtime API, scheduler, test-result cache, budget relaxation or M56
language work is authorized. The proposed timeout137 acceleration was
withdrawn without implementation rather than adding a process controller.

The later, separately approved time-scaled timeout unit is not that controller:
Luna medium changes only `scripts/check_run_budgeted.sh`, retaining production
argv and real GNU escalation with an explicitly unit-only shortened grace.
Both mixed trailing audits pass; ordinary complete14-case pairs are9.48/9.57s
before and4.41/4.57s after. The two-file Sol High attestation-metadata
experiment was rejected and removed: its complete tier, including new oracles,
was4.22% slower. The separately Gate-A-reviewed Sol High running-image digest
acquisition experiment was also removed after its9.42% component gain missed
the required15% threshold. Retained local evidence distinguishes padded ELF
components from the real compiler; neither experiment changes current code.
The lead measures each candidate and drops unearned complexity; no component
result closes the still-open60s full warm goal or authorizes M56.

PRE-M56 P1-P4 on2026-10-19 uses `gpt-5.6-sol` high for the disjoint
frontend/checked metadata indexes, the measured review call-owner slice, and
the private fixture-C cache. Available `gpt-6-luna` medium owns bounded
selectors, metadata/seed oracles and provisional evidence documentation.
Assignments change only after explicit handoffs: the review worker next owns
the standalone host-batch oracle; the checked/cache worker next owns the
attestation scalar shortcut, then the running-image/cache-confirmation repair.
The lead owns host producer edits, integration, native measurements and exact
seed propagation. Independent `gpt-5.6-sol` xhigh and `gpt-6-astra` xhigh
reviews retain the explicit unavailable-GPT-5.5 fallback. Invocation-local
batching and kernel-image identity require their recorded pre-reviews; no
paid service, adjacent-repository change, concurrent host scheduler or
language/runtime feature is part of this pass. Do not consume spare slots
merely to duplicate an active command or audit.

The follow-up C-emission profile selects a separate bounded Sol High worker
slice: `c_emit.nq`, new IR-only position helpers, and its direct probe, after
both Gate A approvals in `docs/P2_C_EMIT_MEMBERSHIP_CONTRACT.md`. The lead
owns registration and compatibility/ordinary measurements. Hold worker builds
until the lead's baseline pair has finished. A separate Sol High worker may
research invocation-local serial validation reuse in ignored notes only; that
study is not permission to implement a new cache or host scheduler. Formal
auditors remain read-only and independent; the original goals remain in force
unless the owner explicitly revises them.

R4-R6 on 2026-10-19 uses `gpt-5.6-sol` high for the bounded driver-only
assembly/dispatch refactor and `gpt-6-luna` medium for the three private
proof-driver invocation wrappers. Their write sets are `selfhost/main.nq`
and the approved helper/wrappers in `selfhost/proof.nq`, respectively. The
lead owns the R5 intentional-retention decision, identity checks, exact
compatibility/memory evidence, integration, seed promotion, and Git operations.
Independent `gpt-5.6-sol` xhigh and `gpt-6-astra` xhigh reviews retain the
explicit unavailable-GPT-5.5 fallback. Both pre-implementation reviews cleared
the revised `docs/R4_R6_CONTRACT.md` and 82-row matrix before source edits.
No publisher framework, neutral enum relocation, or paid service is included.

R2/R3 on 2026-10-19 uses `gpt-5.6-sol` high for the typecheck/handoff
visibility index and `gpt-6-luna` medium for the identical builtin-evidence
table extraction and direct cases. The lead owns proof registration,
compatibility measurements, integration, exact seed generation, and push.
Independent `gpt-5.6-sol` xhigh and `gpt-6-astra` xhigh audit the actual
bootstrap delta; GPT-5.5 remains unavailable, so this mixed fallback is
explicit. The revised execution contract is `docs/R2_R3_CONTRACT.md`.

PRE-M56 P2 mapping uses `gpt-5.6-sol` high for the bounded private normalizer
implementation and available `gpt-6-luna` medium for disjoint oracle fixtures
(the historical Luna model is unavailable). The lead owns profiling,
integration, seed propagation, and measurements. Primary `gpt-5.6-sol` xhigh
and adversarial `gpt-6-astra` xhigh independently audit the final bootstrap
delta; the unavailable GPT-5.5 fallback is explicit. No Python feature work,
paid external model call, or additional full gate is part of development.

PRE-M56 E1 uses the existing `gpt-6-sol` high worker for the modeled
builtin modules, checked value planning, and the structural borrow probe,
and `gpt-6-luna` medium for disjoint focused fixtures. The lead
owns runtime, bootstrap, integration, and measurement. Primary
`gpt-5.6-sol` xhigh and adversarial `gpt-6-astra` xhigh independently review
the runtime/bootstrap boundary; the unavailable GPT-5.5 fallback remains
explicit. No active Python feature work or external model calls are required.

The first native P0 run uses `gpt-6-luna` medium for bounded host-fixture checks
and the two profiling helpers, escalating bootstrap publication repair to
`gpt-6-sol` high. The lead owns runner integration. Independent reviews use
`gpt-5.6-sol` xhigh plus `gpt-6-astra` xhigh: the requested historical
`gpt-5.5` model is unavailable in current spawn metadata, so the mixed-model
fallback is explicit. Neither synthetic checks nor audit approval constitutes
the real Linux baseline; that must be measured on the frozen native candidate.

- Slots are permission to use additional capacity when it is valuable and work
  is genuinely disjoint, not an imperative or a fixed quota.
- Give each worker a compact prompt, exact acceptance evidence, and a disjoint
  write set. Default `fork_context=false`; do not send the full chat.
- Do not duplicate a gate or research already assigned to another worker.
- Escalate after one failed bounded attempt or any material ambiguity with a
  packet containing the objective, attempted command, concise output, diff,
  acceptance result, and blocker; do not run endless retries.
- A worker may not spawn a descendant without lead approval. The lead owns
  decomposition, integration, final verification, and any scope change.
- Model choice is a fit decision, not permission to weaken compiler evidence,
  required audits, or release gates.
- Do not make global model-config, account, or default-routing changes from a
  task-local assignment.

These model choices are pinned here as local available-tool metadata plus task
heuristics, not exact prices or billing estimates. The official model-selection
reference is <https://learn.chatgpt.com/docs/agent-configuration/subagents>.
