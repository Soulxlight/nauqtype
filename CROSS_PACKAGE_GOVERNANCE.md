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

Snapshots are deterministic evidence for a reviewed workspace state. They neither approve a change nor replace `check`, `review`, or `policy-check`.

## Policy Boundary

- A policy may target a direct local dependency only when that dependency is present in the checked lock.
- Unknown workspace IDs, unlocked dependencies, and alias-only targets are diagnostics.
- Existing `policy-check` stays advisory unless an explicit future sidecar opts into enforcement.
- A cross-package change report names added/removed dependency identities and impacted local callers.

## M45 Acceptance

M45 is complete only when one locked two-workspace fixture produces stable facts, review/change evidence, policy diagnostics for an unknown target, and a snapshot golden without invoking Python, a registry, or the network.
