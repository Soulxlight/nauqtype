# Cross-Package Governance v1

M45 extends Nauqtype’s existing supervision surfaces across locked local workspace dependencies. It does not introduce hidden enforcement, dependency fetching, or a language server.

## Canonical Targets

Every cross-package target uses its workspace identity before its module identity:

```text
workspace:<workspace>::module:<module>::fn:<function>
workspace:<workspace>::module:<module>::type:<type>
workspace:<workspace>::module:<module>::field:<type>::<field>
```

Source aliases remain reviewable spelling only. Policy, facts, change reports, and snapshot keys use canonical targets so a path alias cannot change ownership authority.

## Snapshot Contract

`nauqtype.workspace.snapshot.json` v1 captures:

- root workspace identity
- locked direct dependency workspace identities and source hashes
- checked exported definitions and call edges grouped by workspace
- advisory policy target status

`facts --format v3` is the current serialized snapshot surface: it carries the root workspace, locked direct dependencies, workspace-qualified modules, exported definitions, and checked call edges. Persisting that deterministic JSON as `nauqtype.workspace.snapshot.json` is a release/workflow action, not a hidden compiler write. Snapshots neither approve a change nor replace `check`, `review`, or `policy-check`.

## Policy Boundary

- A policy may target a direct local dependency only when that dependency is present in the checked lock.
- Unknown workspace IDs and alias-only dependency targets are diagnostics; alias-only targets use `NQ-POLICY-007` and must be rewritten to the canonical workspace target.
- Existing `policy-check` stays advisory unless an explicit future sidecar opts into enforcement.
- `change-report --format v2` names added, removed, and changed dependency identities plus impacted root-workspace callers. It keeps the older v1 report unchanged for compatibility.

## M45 Acceptance

M45 is complete when one locked two-workspace fixture produces stable facts, review/change evidence, policy diagnostics for an unknown target, and a snapshot golden without invoking Python, a registry, or the network. The stage1-owned `prove` gate now covers that fixture, including a changed dependency and its impacted local caller.
