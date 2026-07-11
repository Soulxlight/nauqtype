# Removing Python From The Active Nauqtype Toolchain

Status: M40 complete. Python source remains in-repo as an archived historical reference and is not part of the active toolchain.

## Goal

Nauqtype must own its active compiler, test, proof, release, and CI paths. Python may remain as archived historical bootstrap/reference material, but it must not be required to build, test, prove, release, or teach the current compiler.

The replacement host contract is intentionally small: a Linux C11-compatible `cc`, standard shell tools, and the checked-in Nauqtype source and runtime. A host C compiler is the seed boundary; it is not a hidden language implementation dependency.

## Current Active Python Responsibilities

| Responsibility | Current owner | Required replacement |
| --- | --- | --- |
| First compiler executable | `compiler/` stage0 | Versioned C seed compiled by host `cc` |
| Test execution and fixtures | `tests/` and `tests/test_support.py` | `nauqc test` fixture and golden runner |
| Self-build reference harness | `tests/test_selfhost_proof.py` | Stage1-owned proof plus seed-to-stage2 gate |
| Dependency/bootstrap setup | `scripts/setup_deps.py` | Host-C seed bootstrap; historical audit dependencies removed from active setup |
| Milestone and Linux gates | shell scripts that invoke Python | Shell orchestration invoking `nauqc test`, `nauqc prove`, and release checks |
| CI bootstrap | Linux workflow Python setup | C seed build and Nauqtype-owned gates |

## M38: Replacement Contract

- Inventory every active Python assertion and classify it by observable claim: diagnostics, checked facts, review output, emitted C, runtime behavior, fixture behavior, or release behavior.
- Define a deterministic test-case manifest, fixture convention, golden comparison rule, expected-failure rule, and archival rationale for claims that do not need one-for-one migration.
- Separate historical AI-audit dependencies such as `tiktoken` from the active compiler toolchain.
- Do not delete, move, or weaken the Python reference during this milestone.
- `BOOTSTRAP_MIGRATION_MAP.md` is the required suite-level claim inventory and M40 exit checklist.

## M39: Nauqtype-Owned Test Runner

Extend the existing proof runner into `nauqc test`; do not create an unrelated framework. It must support:

- positive run cases with expected exit code, stdout, and stderr
- deterministic expected diagnostics
- JSON and text golden comparisons
- normalized structural-C comparisons
- facts, review, policy, change-report, and refactor-plan fixtures
- grouped fixtures and explicit case identifiers

Migration order is proof and corpus first, then diagnostics and supervision outputs, then handoff/borrow/IR/C probes. The Python suite stays frozen as a comparison layer until every active behavior has a Nauqtype case or an archival rationale.

`nauqc test` validates the M39 fixture manifest, then runs representative check and expected-failure fixtures, stage1 diagnostics JSON failure goldens, facts/review JSON goldens, supervised workflow and policy fixtures, formatter checks, the locked runtime corpus, and the copied-selfhost proof. The fixed M39 ledger in `tests/fixtures/m39_fixture_manifest.txt` records every frozen suite as an owned gate, M40 seed coverage, or explicit historical-reference claim.

## M40: C Seed And Active Python Retirement

Check in a versioned generated seed under `bootstrap/seed/`, including:

- generated C for the seed compiler
- matching runtime sources
- a seed manifest with source identity, generator identity, and content hashes
- a small shell bootstrap that compiles the seed with `cc`

The required proof is:

```text
host cc -> seed compiler -> stage1 C -> stage1 executable -> stage2 C
```

The seed-generated and stage2-generated C match under the existing documented structural normalization through `scripts/check_seed_bootstrap.sh`. CI, release scripts, and Linux documentation use this path. `bootstrap/python-reference.json` records the frozen Python reference boundary and capability scope.

## Seed Refresh Rule

A seed refresh is a trust-boundary change. It requires a recorded fixed-point proof, manifest/hash update, reviewable generated diff, and clean-checkout reproduction. Generated seed C is not disposable build output.

## Archive Rule

After cutover, retain the final Python stage0, tests, and audit generator as historical reference with a manifest naming their final commit and capability scope. Do not continue adding active behavior there. Historical benchmark source may remain as inert comparison data, but it must not run in required compiler or release gates.

## Non-Goals

- A general JSON Schema engine in Nauqtype.
- A second competing test framework.
- A requirement to port implementation-private Python unit structure one-for-one.
- A Python fallback in active build, test, proof, release, or CI commands after retirement.
