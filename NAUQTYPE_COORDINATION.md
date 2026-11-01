# NauqType Status And Ownership

Last reviewed: 2026-10-31.

This page is what every agent reads at startup, after `AGENTS.md`. It holds
who owns what and where the project stands, kept short. Milestone evidence
(hashes, timings, audits) lives in [AUDIT_REMEDIATION.md](AUDIT_REMEDIATION.md)
and each milestone's contract document, not here. The multi-repository
coordination ledger used until 2026-10-30 is archived verbatim at
[docs/history/COORDINATION_LEDGER_2026-10.md](docs/history/COORDINATION_LEDGER_2026-10.md).

## Roles

| Role | Holder | Owns |
| --- | --- | --- |
| Owner | Repository owner | Direction, approvals, publication, model/spend authorization |
| Compiler lead | Claude Code session, since 2026-10-30 (previously the Codex "Nauqtype Main" lead) | Critical path, contracts, integration, verification, commits, pushes |
| Workers and auditors | Assigned per task by the lead under [AGENT_ROUTING.md](AGENT_ROUTING.md) | Only the write set or review question they are given |

## Repositories

| Repository | State | Rule |
| --- | --- | --- |
| NauqType (this checkout) | Active | Language, compiler, runtime, builtins, evidence schemas, workspaces, ABI/FFI, release machinery, and status docs |
| NQType Libraries (`Soulxlight/NQType-Libraries`) | Dormant, no assigned lead since 2026-10-31 | Last published foundation `bed7bf6` (`text`, `utf8`, `num`, `path`, `stdio`, `env`); head `8ddefb8` adds only ownership docs. Read-only reference. It was built against the M54 compiler; current compilers require `workspace-lock/v2` ([WORKSPACE_LOCK.md](WORKSPACE_LOCK.md)), so it needs lock regeneration before reuse. Do not edit or commit there without an owner assignment. |
| NQType AI/ML | Retired | The workspace was lost with the retired Linux host and is not being recreated. Its old requests no longer drive the roadmap. |

Historical provider/consumer documents
([NQTYPE_LIBRARIES_NEEDS.md](NQTYPE_LIBRARIES_NEEDS.md),
[NQTYPE_LIBRARIES_UPSTREAM_RESPONSE.md](NQTYPE_LIBRARIES_UPSTREAM_RESPONSE.md))
remain as records of the M54 contract. Reusable modules that the stable
release needs (collections, JSON, and similar) will live in an in-repo
standard library shipped with the compiler (owner decision, 2026-10-31); M57
defines its layout.

## Current Position

- Organizational Linux alpha, `0.3.0-alpha.1`. Not stable or feature complete.
- Complete through M58.1 (correctness and diagnostics), including M57.1,
  M56.2, M56.1, M56 and the PRE-M56 performance checkpoint. Full milestone
  gate is about 33 minutes on the WSL2 Linux host.
- End goal (owner, 2026-10-31): the v1.0 language defined by
  [LANGUAGE_CHARTER.md](LANGUAGE_CHARTER.md), not a stable Linux release.
  Next: M58.2-M58.5, the rest of the corrective sweep. Sequence and scope:
  [ROADMAP.md](ROADMAP.md#current-position-and-resumption); open actions:
  [TODO.md](TODO.md#next-actions).

## Update Rules

- Update this page when a role, repository state, or the next milestone
  changes. Keep each entry to a line or two.
- Record evidence once, in the owning evidence document, and link to it.
- If another repository becomes active again, restore an explicit
  provider/consumer ledger with the contract states from the archived
  ledger (`requested -> scheduled -> implemented -> evidenced -> frozen ->
  consumed`) before any cross-repository dependency is claimed.
