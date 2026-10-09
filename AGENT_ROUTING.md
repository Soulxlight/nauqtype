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
