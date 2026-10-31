# Claude Code Entry Point

[AGENTS.md](AGENTS.md) is this repository's operating protocol. It applies to
Claude Code sessions exactly as it applies to Codex agents. Read it
first; this file only maps its tool-specific wording onto Claude Code.

## Startup

1. Read `AGENTS.md`, then `NAUQTYPE_COORDINATION.md` (roles, repository
   states, current position; one page).
2. Read `CLAUDE.local.md` if it exists. It is untracked and holds host facts:
   checkout locations, the native Linux verification host, and the push method.
   Never copy its contents into tracked files (`AGENTS.md` startup step 2).
3. `$nauqtype-work` in `AGENTS.md` is a Codex skill. A Claude session uses its
   own `nauqtype-work` skill when installed; otherwise steps 1-2 cover it.
4. Current state lives in `NAUQTYPE_COORDINATION.md`, `ROADMAP.md` (Current
   Position), and the top of `TODO.md`. `DECISIONS.md`,
   `AUDIT_REMEDIATION.md`, and milestone contracts are long dated records:
   search them for the section you need instead of reading them end to end.
5. Run `git status --short --branch` and preserve unrelated changes.

## Role Mapping

| AGENTS.md term | Claude Code meaning |
| --- | --- |
| lead agent / director | The session the owner assigned as lead (see the Roles table in `NAUQTYPE_COORDINATION.md`). Only the lead integrates, commits, and pushes. |
| worker / subagent | A Claude subagent (Agent tool) or a Codex thread. Same delegation contract: question, read-only or write set, prohibited scope, evidence, handoff. |
| formal audit | Keep the `AGENTS.md` audit model policy. Independent auditors are dispatched as read-only Codex threads (cross-vendor diversity). A Claude subagent may add a review, but it does not replace a required independent auditor. |
| descendant agent | A worker may not spawn another agent without lead approval. |

Model fit for Claude workers follows the shape of [AGENT_ROUTING.md](AGENT_ROUTING.md):
mechanical documentation and bounded inventories on the cheapest capable
model; ordinary implementation after a fixed contract on a mid-tier model;
semantic, ownership, bootstrap, and integration work on the strongest model.

## Hard Boundaries

- Executable evidence comes only from native Linux, per `VERIFICATION.md` and
  `WSL_DEVELOPMENT.md`. A Windows-side edit or static check is not a gate
  result.
- Compiler, tests, fixtures, and tooling stay in Nauqtype. Python is frozen
  reference code; do not add Python or Perl to the active path.
- Run one full milestone gate on a reviewed, frozen candidate. Do not repeat
  expensive gates another agent is already running.
- Do not edit non-ASCII files through Windows PowerShell 5.1 `Get-Content` /
  `Set-Content`; use an editor tool that preserves UTF-8.
- Report exact commands, outcomes, and skipped gates. Agent summaries are not
  proof.
