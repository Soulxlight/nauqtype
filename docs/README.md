# Nauqtype Documentation Guide

Source-checkout index, reviewed 2026-10-19. Start by task rather than reading
the milestone history end to end. This guide is not a language specification
or a copied-release manifest.

## Start By Task

| Task | Read first | Then use |
| --- | --- | --- |
| Write a program | [SPEC](../SPEC.md), [Teaching Corpus](../TEACHING_CORPUS.md) | [Grammar](../GRAMMAR.md), [AI Contracts](../AI_CONTRACTS.md), [Formatter](../FORMATTER.md) |
| Build/run on Linux | [Linux guide](../LINUX.md) | [Bootstrap](../BOOTSTRAP_STAGE1.md), [verification tiers](../VERIFICATION.md) |
| Change the compiler | [AGENTS](../AGENTS.md), [coordination](../NAUQTYPE_COORDINATION.md) | [architecture](../ARCHITECTURE.md), [compiler map](COMPILER_MAP.md), [refactor plan](REFACTOR_PLAN.md) |
| Work on R2/R3 | [Execution contract](R2_R3_CONTRACT.md), [measurements](R2_R3_RESULTS.md) | [Performance checkpoint](../PERFORMANCE_CHECKPOINT.md), [verification tiers](../VERIFICATION.md) |
| Work on R4-R6 | [Execution contract](R4_R6_CONTRACT.md), [compatibility matrix](R4_R6_MATRIX.txt) | [Focused results](R4_R6_RESULTS.md), [refactor scope/retention decisions](REFACTOR_PLAN.md), [verification tiers](../VERIFICATION.md) |
| Work on M56 | [Explicit reuse contract](M56_CONTRACT.md), [host memory boundary](M56_GCC_MEMORY_CONTRACT.md) | [Spec](../SPEC.md), [teaching corpus](../TEACHING_CORPUS.md), [roadmap acceptance](../ROADMAP.md) |
| Work on M56.1 | [Generic-aware facts/review v5 contract](M56_1_CONTRACT.md) | [D066](../DECISIONS.md#d066-generic-aware-facts-and-review-v5), [M56 contract](M56_CONTRACT.md), [AI Contracts](../AI_CONTRACTS.md), [schema profile](../EVIDENCE_SCHEMA_PROFILE.md) |
| Work on M56.2 | [Scalar `f64` contract](M56_2_CONTRACT.md) | [D067](../DECISIONS.md#d067-scalar-f64), [Spec](../SPEC.md), [grammar](../GRAMMAR.md), [teaching corpus](../TEACHING_CORPUS.md) |
| Work on M57.1 | [Library-enabling core contract](M57_1_CONTRACT.md) | [D068](../DECISIONS.md#d068-library-enabling-core), [Spec](../SPEC.md) |
| Work on M58.1 | [Correctness and diagnostics contract](M58_1_CONTRACT.md) | [D070](../DECISIONS.md#d070-accepted-programs-mean-what-they-say-diagnostics-are-honest), [producer ledger](M58_1_PRODUCER_LEDGER.md), [Spec](../SPEC.md), [grammar](../GRAMMAR.md) |
| Work on M58.2 | [Remainder and counting loops contract](M58_2_CONTRACT.md) | [D071](../DECISIONS.md#d071-remainder-and-counting-loops), [Spec](../SPEC.md), [grammar](../GRAMMAR.md) |
| Propose syntax | [Syntax Identity](../SYNTAX_IDENTITY.md), [deferrals](../DEFERRED.md) | [Decisions](../DECISIONS.md), [Grammar](../GRAMMAR.md) |
| Consume evidence | [AI Contracts](../AI_CONTRACTS.md) | [schemas](../schemas/), [schema profile](../EVIDENCE_SCHEMA_PROFILE.md), [workspace locks](../WORKSPACE_LOCK.md) |
| Choose a gate | [Verification](../VERIFICATION.md) | [performance checkpoint](../PERFORMANCE_CHECKPOINT.md), [budgets](../PERFORMANCE_BUDGETS.md) |
| Plan toward v1.0 | [Language Charter](../LANGUAGE_CHARTER.md) | [release manifest](../LINUX_RELEASE_MANIFEST.md), [bootstrap retirement](../BOOTSTRAP_RETIREMENT.md) |
| Change shared libraries | [coordination](../NAUQTYPE_COORDINATION.md) (NQType Libraries is dormant; needs an owner assignment first) | [upstream response](../NQTYPE_LIBRARIES_UPSTREAM_RESPONSE.md) |

## Current Position

The active compiler, test runner, and proof runner are Nauqtype-owned. The
host-C seed, narrow native runtime, and shell build/release integration remain
intentional. Python is archived reference code, not the active path.

M55, required PRE-M56 efficiency goals, and M56 explicit generic reuse have
recorded Linux acceptance; none is a stable-release claim. M56.1 adds
generic-aware `facts`/`review` v5 (acceptance in the roadmap); every other
evidence format rejects generic graphs. M56.2 adds scalar `f64` (acceptance in
the roadmap). M57.1 adds the library-enabling core and M58.1 the
correctness and diagnostics sweep, and M58.2 `%` with range and indexed
`for`; M58.3-M69 are not complete. This is an organizational
alpha, not a stable or feature-complete application language. Current sequencing
lives in [ROADMAP](../ROADMAP.md#current-position-and-resumption); open actions
live in [TODO](../TODO.md#next-actions).

Historical E1 and P2 mapping have candidate-specific executable evidence. P2's measured
comparisons improve about 25-26x, but its one cold complete gate was only
1.40% faster than P0. The subsequent P1-P4 checkpoint met its required goals;
the10-minute cold working target remains unmet. See
[Performance Mapping](../PERFORMANCE_MAPPING.md); this documentation refactor
alone added no performance result. R2/R3's subsequent scan/table implementation
has a separate [execution contract](R2_R3_CONTRACT.md); current acceptance
belongs in TODO, not in historical documentation evidence.

The P0/E1/P2 baseline is locally committed as `0564a32`; it is not a new
published release. A historical gated candidate, the current tree, and a
published revision are different things. The authoring
kit is staged, not integrated or compiler-validated; its probes are not yet
canonical teaching examples.

## Authority And Compatibility

| Question | Authority |
| --- | --- |
| What does source mean? | SPEC, Grammar, and the applicable focused contract below |
| What architecture must changes preserve? | Architecture and the checked-handoff contract |
| What counts as evidence? | Verification, versioned schemas, and candidate-specific receipts |
| How should agents work? | AGENTS, required coordination skill, coordination, and routing |
| What ships? | Linux release manifest and the actual [assembler](../scripts/make_linux_release.sh) |
| What happens next? | Roadmap and TODO; refactor proposals are not completed behavior |

Guides do not override contracts. A code/contract disagreement needs a bug or
an explicit migration, not a silent edit blessing existing behavior. Later
explicit decisions may supersede earlier historical entries.

Evidence numbers are independent, not one universal "latest v4" switch:

- `facts` v1 remains default. v2 adds per-source semantic evidence; v3/v4 are
  workspace evidence, with v4's captured-provenance migration.
- `review` v3 retains partial direct-write coverage. v4 adds checked call-aware
  parameter may-writes, not a purity or safety guarantee.
- `review-diff` supports v1/v2; `change-report` supports v1-v4. v4 carries
  captured workspace/dependency provenance; v3 established explicit
  absent/checked/failed advisory-policy state.
- Diff/change failures use separate `evidence-error` v1. `proof-summary` v3
  records invocation-produced SHA-256 artifacts or null.
- Policies do not approve changes. Rename is plan-only. Intent text and model
  opinions are not compiler-checked behavior.

## Complete Root Document Inventory

Every root Markdown document is routed below. Historical does not mean safe
to delete: manifests, audits, teaching material, and proof contracts may refer
to it. No document is moved or deleted by this checkpoint.

### Project And Operating Rules

| Document | Role |
| --- | --- |
| [README](../README.md) | Packaged introduction/quick start; its R1 rewrite has a separate executable acceptance checkpoint |
| [AGENTS](../AGENTS.md) | Startup, delegation, independent audits, and verification rules |
| [Agent Routing](../AGENT_ROUTING.md) | Task-fit routing and explicit model-availability fallbacks |
| [Coordination](../NAUQTYPE_COORDINATION.md) | Roles, repository states, and current position (one page); the old cross-repository ledger is [archived](history/COORDINATION_LEDGER_2026-10.md) |
| [Architecture](../ARCHITECTURE.md) | Active architectural boundaries and implementation ownership |
| [Roadmap](../ROADMAP.md) | Current sequence followed by preserved milestone history |
| [TODO](../TODO.md) | Current actions followed by historical/completed checklists |
| [Deferred](../DEFERRED.md) | Deliberate exclusions, not implementation requests |
| [Syntax Identity](../SYNTAX_IDENTITY.md) | Explicit-authority syntax evolution SOP |

### Language And Evidence

| Document | Role |
| --- | --- |
| [SPEC](../SPEC.md) | Language and value semantics |
| [Grammar](../GRAMMAR.md) | Legal forms and first-version restrictions |
| [AI Contracts](../AI_CONTRACTS.md) | Declared versus checked mutation, effects, propagation, and review |
| [Propagation](../PROPAGATION.md) | Exact forwarding, context labels, and local `try` boundaries |
| [Checked Handoff](../SELFHOST_HANDOFF.md) | Typed downstream contract; its first-proof narrative is historical |
| [Formatter](../FORMATTER.md) | Output-only formatter-lite and `--check`, not write mode |
| [Teaching Corpus](../TEACHING_CORPUS.md) | Canonical lessons, negative cases, examples, and corpus membership |
| [Workspace Contract](../WORKSPACE_CONTRACT.md) | Manifest-owned modules, aliases, dependencies, flat-root compatibility |
| [Workspace Lock](../WORKSPACE_LOCK.md) | Captured-source lock v2 and explicit legacy compatibility |
| [Cross-Package Governance](../CROSS_PACKAGE_GOVERNANCE.md) | Canonical cross-workspace evidence/policy identities |

### Verification And Linux Delivery

| Document | Role |
| --- | --- |
| [Verification](../VERIFICATION.md) | Focused feedback, reviewed milestone close, independent release gates |
| [Linux](../LINUX.md) | Supported development/launcher workflow, not distro readiness |
| [Linux Release Manifest](../LINUX_RELEASE_MANIFEST.md) | Exact copied layout and packaged-file boundary |
| [Language Charter](../LANGUAGE_CHARTER.md) | Identity, design rules, v1.0 definition and milestone sequence |
| [Stress Leg](../STRESS_LEG.md) | Dense cross-feature exercise and finding reduction |
| [Performance Budgets](../PERFORMANCE_BUDGETS.md) | Checked ceilings; goals do not relax them |
| [Stage1 Bootstrap](../BOOTSTRAP_STAGE1.md) | Current host-C seed chain and copied-selfhost proof |
| [Bootstrap Retirement](../BOOTSTRAP_RETIREMENT.md) | Python retirement and C-seed lineage/promotion |
| [Evidence Schema Profile](../EVIDENCE_SCHEMA_PROFILE.md) | Bounded owned validation, not a general JSON/standards engine |
| [WSL Development](../WSL_DEVELOPMENT.md) | Native-Linux verification setup and cross-agent boundaries |

### Performance Campaign

| Document | Role |
| --- | --- |
| [Performance Checkpoint](../PERFORMANCE_CHECKPOINT.md) | PRE-M56 P0-P4 scope, goals, and acceptance |
| [Performance Baseline](../PERFORMANCE_BASELINE.md) | Exact P0 environment, inputs, costs, and baseline |
| [Performance Enablement](../PERFORMANCE_ENABLEMENT.md) | E1 `str_join` semantics and assembly-only benefit boundary |
| [Performance Mapping](../PERFORMANCE_MAPPING.md) | P2 algorithm, invariants, timings, memory, and seed evidence |

### Focused Contracts And Provider Requests

| Document | Role |
| --- | --- |
| [M54.8 Contracts](../M54_8_CONTRACTS.md) | Shared validation, mutation coverage, versioned failure evidence |
| [M54.9 Contracts](../M54_9_CONTRACTS.md) | Integer/allocation boundaries and corrective evidence |
| [M54.10 Contracts](../M54_10_CONTRACTS.md) | Captured provenance, seed/cache derivation, attestations |
| [M55 Contracts](../M55_CONTRACTS.md) | Processes, time, deadlines, cleanup, platform exclusions |
| [Audit Remediation](../AUDIT_REMEDIATION.md) | Findings and recorded closures, not future-correctness guarantees |
| [Libraries Needs](../NQTYPE_LIBRARIES_NEEDS.md) | Consumer pressure, not provider permission or completion evidence |
| [Libraries Upstream Response](../NQTYPE_LIBRARIES_UPSTREAM_RESPONSE.md) | Compiler-owned response and integration evidence |

### History And Research

| Document | Role |
| --- | --- |
| [Research Memo](../RESEARCH_MEMO.md) | Original design research, not the current implementation map |
| [Decisions](../DECISIONS.md) | Decision history with explicit later supersessions |
| [Risks](../RISKS.md) | Risk inventory; current contracts govern resolved behavior |
| [AI Audit](../AI_AUDIT.md) | Historical AI-friendliness benchmark design |
| [Bootstrap Migration Map](../BOOTSTRAP_MIGRATION_MAP.md) | Historical Python-to-owned-fixture responsibility mapping |
| [M39 Fixture Manifest](../M39_FIXTURE_MANIFEST.md) | Archived-test migration and coverage ledger |
| [M46 Organizational Alpha](../M46_ORGANIZATIONAL_ALPHA.md) | Two-workspace alpha checkpoint, not stable certification |
| [Archived coordination ledger](history/COORDINATION_LEDGER_2026-10.md) | Multi-repository ledger as of `e34d459`, archived 2026-10-31 |
| [Archived status narratives](history/STATUS_NARRATIVES_2026-10.md) | ROADMAP/TODO status narratives as of `e34d459`, archived 2026-10-31 |

### Optional Model Assistance

| Document | Role |
| --- | --- |
| [Authoring Kit](../AUTHORING_KIT.md) | Guide/pilot plan and rejected prototype assumptions, not shipped tooling |
| [TypeSafe Jev](../TYPESAFE_JEV.md) | Opt-in advisory boundary; never replaces tests/audits |
| [TypeSafe Evaluation](../TYPESAFE_JEV_EVALUATION.md) | Bounded historical evaluation protocol/evidence |
| [Jev Evaluation Report](../JEV_EVALUATION_REPORT.md) | Historical questions/results/costs, not current compiler facts |

## Maintenance Rule

Update the owning contract once, then update affected summaries and links.
Do not copy whole milestone narratives into every guide or agent prompt.
Preserve schema versions and historical receipts; do not relabel old evidence
as fresh verification.

These contributor guides are source-only, not installed by the current release
assembler. Packaged documentation changes need the boundary in Verification;
this index does not extend an earlier milestone attestation.
