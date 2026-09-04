# Nauqtype Repository Agent Protocol

This file is the required starting point for every agent working in this
repository. Read it before planning, editing, testing, reviewing, committing,
or pushing.

## Startup Check

1. Load and follow the `$nauqtype-work` skill, then read
   `/home/soulxlight/Documents/NauqType/NAUQTYPE_COORDINATION.md`. This is
   required even when the current task appears confined to this repository.
2. Resolve the repository root from this `AGENTS.md` and work in a native Linux
   checkout or agent worktree. The canonical checkout on this machine is
   `/home/soulxlight/Documents/NauqType`; legitimate Linux clones/worktrees are
   allowed. Never edit the mounted historical Windows-path workspace under
   `/opt/codex-desktop/C:\Users\...`.
3. Read the current task-relevant sections of `README.md`, `ROADMAP.md`,
   `TODO.md`, `DECISIONS.md`, `DEFERRED.md`, `SYNTAX_IDENTITY.md`, and
   `VERIFICATION.md` before changing a public contract.
4. Run `git status --short --branch` and preserve unrelated user changes.
5. Identify the smallest honest milestone slice and its acceptance evidence.
6. Keep active compiler, tooling, fixtures, and teaching work in Nauqtype.
   Python is frozen historical bootstrap/reference code unless a narrowly
   proven bootstrap blocker requires a repair.

## Lead-Agent Ownership

The lead agent owns the critical path, architectural decisions, shared-model
edits, integration, final verification, commits, and pushes. It must keep
working on the immediate task while delegated work proceeds in parallel.

The lead agent should use subagents when they materially improve confidence or
throughput:

- independent repository or design research;
- disjoint implementation slices with explicit file ownership;
- long-running, bounded verification that can run beside implementation;
- findings-first audits before a release, public-contract change, or push.

Do not spawn an agent merely to repeat work already underway. Do not delegate
the next blocking action when the lead can perform it directly.

## Delegation Contract

Every delegated task must state:

- the concrete question or deliverable;
- whether the task is read-only or may edit files;
- the allowed write set when edits are permitted;
- prohibited scope and architectural boundaries;
- expected tests or evidence;
- the required handoff: findings, files changed, commands run, and residual
  risks.

Implementation agents receive disjoint write sets. Audit agents remain
read-only unless the lead explicitly assigns a follow-up repair. Subagents do
not commit, push, rewrite shared history, or discard worktree changes.

## Descendant Agents

A subagent may identify useful work for another agent, but it must ask the lead
agent for approval before spawning a descendant. The request must include the
proposed task, why it is parallel-safe, and its intended write set. Only the
lead agent may approve the spawn and remains responsible for the descendant's
output.

## Required Gates

Use judgment for trivial, isolated edits. For a substantial milestone:

1. Use an independent pre-implementation review when syntax, semantics,
   runtime authority, machine-readable schemas, bootstrap boundaries, or
   release contracts change.
2. Use at least one trailing audit after implementation and focused tests are
   green. Give it the actual diff, acceptance contract, and exact test results.
3. Wait for assigned audits to finish. Do not rush, interrupt, or replace a
   deliberate audit with a shallow answer.
4. Resolve every blocking finding before commit or push.
5. The lead reviews all delegated edits rather than trusting a completion
   summary by itself.

## Audit Model Policy

Formal audit gates default to `gpt-5.6-sol` with `xhigh` reasoning. Keep the
auditor independent, read-only, and findings-first; model capability does not
replace the requirement to provide the actual diff, acceptance contract, and
exact verification evidence.

Use model diversity deliberately:

- routine substantial milestones require one `gpt-5.6-sol` `xhigh` trailing
  auditor;
- ownership, bootstrap, filesystem authority, process execution, FFI, and
  release-boundary milestones require a `gpt-5.6-sol` `xhigh` primary auditor
  plus an independent `gpt-5.5` `xhigh` adversarial auditor;
- M60/M61 release gates, conflicting verdicts, or materially ambiguous safety
  findings escalate the primary auditor to `gpt-5.6-sol` `max` while retaining
  the independent `gpt-5.5` `xhigh` review;
- `max` and higher-cost modes are not routine defaults. Use them only for the
  escalation cases above or when repository evidence demonstrates a measured
  audit-quality gain.

Auditors must reach their own verdicts before seeing another auditor's
conclusion. Do not silently substitute a different model or reasoning level;
record an unavailable-model fallback in the milestone evidence and preserve
the strongest available independent, mixed-model review.

## Verification Discipline

Use the smallest sufficient gate while developing. Do not run an equivalent
gate when another assigned agent already has it in progress.

- focused feedback: `scripts/check_fast.sh` or the narrow relevant command;
- executable milestone close: `scripts/check_milestone.sh` when compiler,
  runtime, fixtures, proof logic, release scripts, or generated seed behavior
  changed;
- documentation-only contract close: `git diff --check`, focused link/contract
  validation, and a trailing audit unless the text can affect an executable
  fixture or release artifact;
- stable/release candidate: the independent gates listed in
  `VERIFICATION.md` and `STABLE_RELEASE.md`.

For any milestone that needs the expensive executable close, use this order:

1. Iterate with the narrowest focused checks and do not launch duplicate gates.
2. Freeze the candidate diff and give auditors that diff plus focused evidence.
3. Resolve blocking findings, rerun only affected focused checks, and ask the
   same auditor to inspect only the repair when possible.
4. Run `scripts/check_milestone.sh` once on the reviewed, frozen candidate.
5. If that full gate exposes a defect, fix it, audit the changed slice, and run
   the full gate again; never treat an earlier run as evidence for changed code.

Do not routinely run the full gate before the trailing audit and then repeat it
afterward. Audit prompts should point to the plan, diff, and concise command
results rather than copying the full conversation or unbounded logs.

Report exact commands, outcomes, and skipped gates. Convert discovered
composition bugs into focused fixtures before closing a milestone.

## Nauqtype Mission Guardrails

- AI-first means checked facts, visible authority, deterministic evidence, and
  supervised changes. It does not mean model behavior inside correctness paths.
- Do not copy another language's feature merely because it is familiar. Apply
  `SYNTAX_IDENTITY.md` and preserve Nauqtype's explicit provenance, effects,
  mutation, and failure boundaries.
- Keep runtime primitives narrow. Prefer reusable Nauqtype modules over a broad
  pile of special compiler builtins.
- Do not widen ownership, lifetimes, methods, traits, implicit conversions, or
  hidden control flow without demonstrated pressure and a recorded decision.
- Stable Linux work follows `STABLE_RELEASE.md`; it must improve real terminal
  or application development rather than accumulate prestige features.
