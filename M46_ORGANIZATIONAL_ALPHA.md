# M46 Organizational Alpha Proof

Status: complete for `nauqtype-0.3.0-alpha.1`.

M46 proves a practical internal-tool shape without widening Nauqtype's source language: a root operations workspace imports a locked local reporting workspace, prints a checked readiness result, and carries human/agent ownership metadata through the supervision surfaces.

## Fixture

`tests/fixtures/organizational_tool/` contains the released tool shape:

- `org.operations_tool` declares `src/app/main.nq` as its `report` entrypoint.
- Its `reporting` dependency is a local `org.reporting` workspace fixed by `nauqtype.workspace.lock.json` manifest and source hashes.
- The root policy assigns `main` to `human:operations` with required review and the exported reporting function to `agent:reporting` with supervised review.
- The checked program prints exactly `operations: ready`.

`tests/fixtures/organizational_tool_before/` is the same workspace identity with an earlier locked reporting source hash and `operations: pending`. Comparing it to the current fixture proves that the checked dependency change impacts the root `main` caller.

## Evidence Contract

The stage1-owned `nauqc prove` gate now locks all of these artifacts:

- `tests/golden/organizational_tool/facts_v3.json`: the canonical workspace snapshot, direct dependency hashes, exports, and checked call graph.
- `tests/golden/organizational_tool/policy_check_v1.json`: canonical ownership/review targets accepted against checked facts.
- `tests/golden/organizational_tool/change_report_v2.json`: one changed dependency and its one impacted root caller.
- A successful `nauqc run` with only `operations: ready` on stdout.

`scripts/check_organizational_alpha.sh` persists the active facts snapshot, policy result, and change report under `build/organizational-alpha/`. It then creates and verifies the copied Linux release, copies the organizational fixture to a fresh temporary directory, and requires the copied `bin/nauqc` launcher to check, snapshot, policy-validate, and run the tool without source-checkout support.

The clean bootstrap boundary remains:

```text
host cc -> checked C seed -> stage1 -> stage2 structural proof
```

`scripts/check_seed_bootstrap.sh` verifies that boundary independently. M46 does not add a hidden Python fallback, registry fetch, package script, or automatic policy approval.

## Next Language Batch Ranking

The organizational tool proves the module, lock, evidence, policy, release, and supervision path. It deliberately avoids claiming that one small tool validates every future ergonomic feature. The next language-completeness candidates remain ranked by direct usefulness to real internal tooling and by their supervision cost:

M47 closed the M46 exit-audit P0 before this batch: [composite_field_backend.nq](examples/composite_field_backend.nq) now proves dependency-safe carrier ordering for `list<T>`, `option<T>`, and `result<T, E>` product fields, plus correct `ref product.field` list-helper lowering. It is existing-surface correctness work, not new syntax.

1. List `for` loops: remove manual index bookkeeping while retaining nearest-loop `break` / `continue` semantics.
2. Surgical helper modules: remove repeated text/path/list plumbing without broad runtime or package growth.
3. Explicit `try` boundaries and expression-position propagation: build on checked `?` evidence only when its return boundary remains visible to reviewers.
4. Structured error sets: make larger tool error contracts more precise without implicit conversion.
5. Generic foundations: defer until the preceding concrete tooling needs establish a small, auditable monomorphization contract.

No candidate is admitted merely because it resembles another language. Any selected feature must pass the syntax identity discipline, add canonical teaching material, preserve deterministic facts/review/policy evidence, and extend the standing proof corpus.
