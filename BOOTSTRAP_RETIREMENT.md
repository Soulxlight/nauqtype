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
- a seed manifest with entry and deterministic full-selfhost-tree identities, generator identity, and content hashes
- a small shell bootstrap that compiles the seed with `cc`

The required proof is:

```text
host cc -> seed compiler -> stage1 C -> stage1 executable -> stage2 C
```

The seed-generated and stage2-generated C match under the existing documented structural normalization through `scripts/check_seed_bootstrap.sh`. CI, release scripts, and Linux documentation use this path. `bootstrap/python-reference.json` records the frozen Python reference boundary and capability scope.

## Seed Refresh Rule

A seed refresh is a trust-boundary change. It requires a recorded fixed-point proof, manifest/hash update, reviewable generated diff, and clean-checkout reproduction. Generated seed C is not disposable build output.

The historical seed executable links against its matching
`bootstrap/seed/runtime.c,h`. Newly emitted current-source stage1 C links
against current `stdlib/runtime.c,h`, just like ordinary Nauqtype programs.
The seed runtime is not the runtime API ceiling for current selfhost sources.
Both current runtime files participate in the stage1 cache fingerprint; a
header-only or implementation-only runtime change invalidates reuse.

M54.7 records source identity as `nauqtype-selfhost-source/v1`: SHA-256 of the
UTF-8 domain string followed by NUL, then every regular `.nq` file under
`selfhost/` in C-locale relative-path order, each encoded as path, NUL,
lowercase file SHA-256 hex, NUL. This includes the intentionally retained
selfhost probes. There is no concatenation-only or path-insensitive digest.
The manifest records the parent revision plus this dirty-candidate identity,
the actual generator/compiler inputs, unchanged runtime hashes, host compiler
identity and flags, and comparisons. `SHA256SUMS` also binds the manifest.

When repairing a defective seed backend, the first emitted compiler is only a
bridge. Regenerate source with the repaired executable, compile that output,
and compare a further emission using the existing normalizer before seed
promotion. Validate the promoted candidate again, then run the seed bootstrap
and milestone gates from a clean candidate snapshot. Never normalize away
source-derived names, operators, or control flow to manufacture convergence.
The M54.7 record is in `AUDIT_REMEDIATION.md`.

M54.10 seed v2 retains the exact generating selfhost sources under
`bootstrap/seed/source-snapshot/selfhost/`, with a mode/path/hash inventory and
an exact checksum allowlist. Bootstrap validates canonical manifest bytes,
snapshot identity, runtime, compiler C, and recorded generator fields before
compiling. Historical generator identities are records, not signatures.

The seed gate checks historical snapshot output against checked-in seed C as
well as current-source stage1 against stage2 C. Identical captured source
identities and emission inputs allow reuse of one emission for both direct
comparisons; otherwise the historical edge runs separately. The normalizer
does not change. `build/seed/seed-bootstrap-proof-v1.txt` records which branch
ran and the compared identities. This adds no further compiler generation.

## Archive Rule

After cutover, retain the final Python stage0, tests, and audit generator as historical reference with a manifest naming their final commit and capability scope. Do not continue adding active behavior there. Historical benchmark source may remain as inert comparison data, but it must not run in required compiler or release gates.

## Non-Goals

- A general JSON Schema engine in Nauqtype.
- A second competing test framework.
- A requirement to port implementation-private Python unit structure one-for-one.
- A Python fallback in active build, test, proof, release, or CI commands after retirement.
