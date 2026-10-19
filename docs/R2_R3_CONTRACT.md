# R2/R3 Execution Contract

Status: frozen R2/R3 execution contract, 2026-10-19. Completion evidence
belongs in [TODO](../TODO.md#current-refactor-checkpoint), not this plan.
Owner: compiler repository only. Libraries and AI/ML workspaces are untouched.
Base: `1105a7e`, with `0564a32` immediately preceding it, both initially local.

## Scope And Ownership

R2 replaces one measured visibility scan, not the semantic architecture.
`typecheck::visible_item_origin` accounts for 19.72% of sampled CPU in the
retained diagnostic profile; this is not an ordinary timing or speedup claim.
R3 extracts only the identical facts/review builtin IO-kind and propagation
error tables. No source syntax, ownership, ABI, runtime helper, effect atom,
CLI, schema version, resolver policy, or proof edge changes.

The R2 worker owns `selfhost/typecheck.nq`, `selfhost/handoff.nq`, and
`selfhost/typecheck_probe.nq`. The R3 worker owns a shared builtin-evidence
module, its direct probe, and the delegates in `selfhost/facts.nq` and
`selfhost/review.nq`. The lead owns proof/test registration in
`selfhost/proof.nq`, fixture integration, docs, measurement, actual seed
generation/promotion, audits, commits, and push. No worker commits or pushes.

## R2 Index Boundary

Build one immutable item/use module-run index at each project-wide semantic
phase entry and once in `build_checked_handoff`. Ranges retain module,
domain, start, and end; support multiple disjoint runs for the same module.
Own the list at phase entry and pass it by `ref` throughout recursive typing
and handoff construction. Do not store references or add ownership powers.

Narrowly exported compiler-internal range/build/indexed operations are allowed
where handoff must call typecheck. Existing public signatures and identities
remain wrappers. Recursive indexed calls must not route through wrappers that
rebuild the index. Do not duplicate resolution logic in handoff.

Preserve all local runs before import lookup, kind-specific shadowing,
public-only matching imported items, original `uses` order, alias behavior,
builtin precedence, empty-string missing truth, and the separate existing
handoff origin fallback. No mutable global cache, fact sorting, or pre-resolved
semantic target table. Keep a linear/indexed oracle with independently stated
expected origins, including interleaved runs and ambiguous imports.
The standalone entry is `selfhost/visibility_index_probe.nq`; the existing
typecheck probe and owned tests also exercise the oracle.

## R3 Shared Tables

The two facts/review pairs are text-identical at the base. New shared functions
must have distinct names to avoid local-wrapper shadowing. Retain all four
historical wrappers and their identities. Checked-builtin guards stay at the
consumers. `builtin_propagation_error` currently has no callers: leave its
delegates unused rather than introducing a new semantic dependency.

Directly probe both shared tables against frozen independent expectations for
every listed name, empty and unknown names, and case-sensitive near misses.
Pure builtins, including `str_join`, must retain empty IO/error classifications.
The lead registers the shared module in the copied-selfhost module list and
the direct probes in the owned test path. Inventory other duplicated builtin
knowledge, but do not migrate names, signatures, borrowing, labels, runtime
mappings, or other classifiers in this slice.

### Retained Duplication Inventory

| Knowledge | Existing owners | R3 disposition |
| --- | --- | --- |
| IO subkind and propagation-result error | facts/review identical private tables | Share pure classifications; retain consumer guards and four delegates |
| Function/variant recognition | facts/review exact copies; resolve has related name/type policy | Retain; not part of this extraction |
| Arity, return/parameter types, argument labels | typecheck, handoff, borrow | Retain phase-specific checks; no universal builtin registry |
| Borrowed argument modes | typecheck, borrow, value_plan | Retain; related tables are not interchangeable ownership rules |
| Mutation coverage and builtin field types | review and checked-handoff consumers | Retain existing checked authority and evidence boundaries |
| Runtime C names | c_emit and native ABI | Retain backend mapping separately from evidence rendering |

The direct entry probe is `selfhost/builtin_evidence_probe.nq`; owned tests
also call the table self-test directly without another compiler build.

## Frozen Compatibility And Measurements

Keep the base checkout, executable, and hashed fixtures in one native-ext4
capture. Use the same retained input paths for old/new commands. Preserve
exit status, stdout, stderr, JSON ordering, existing stable IDs, and user C.
Whole-selfhost evidence may legitimately gain new internal definitions and
call edges; do not silently rewrite user-program goldens to hide differences.

The exact selected comparisons are in [R2_R3_MATRIX.txt](R2_R3_MATRIX.txt),
one row per ID, expected exit, and complete source/command/format arguments.
Run both executables serially from the same retained baseline workspace.
An `emit-c` row appends `-o <output>/<id>.c`. Every row captures
`<id>.stdout`, `<id>.stderr`, `<id>.exit`, and NUL-framed `<id>.argv` under
`build/verification/refactor-r2-r3-20261019/compatibility/before/` and `after/`.
Byte-compare stdout, stderr, exit, and emitted C. The argv records deliberately
identify different physical executables and output paths; do not compare those
as if identical. Hash all matrix source inputs and imported fixture files at
capture, then recheck before/after execution. No golden updates are authorized.
The unchanged seven-phase gate owns wider workspace/provenance, runtime,
process/time, filesystem, propagation, sanitizer, and proof composition.

Run two pre-change and two post-change ordinary full-tree checks with the
existing `profile_selfhost.sh` capture/identity contract, identical production
flags, setup costs, wall/RSS, order, and spread. Also compare both executables
on the same frozen baseline tree. Record cache validation and focused probe
cost separately. A spread over 10% is inconclusive, not a speedup. Do not
mistake instrumented timing or retain counts for production savings.

## Seed, Audit, And Close

Actual compile/re-emission must produce the promoted seed; never edit generated
C. Include every new source in the snapshot, strict inventory, manifest, and
checksums. Preserve predecessor/generator/toolchain/flag identities, exact
self-generated C, both direct seed comparisons, and rollback on catchable
promotion failure. Full milestone coverage remains all seven phases.
Pin the base revision, staged tree, and expected dirty relationship; recheck
immutable inputs after installing the seed while rollback is still active.
Exclude only the expected seed worktree delta from that post-install check.

One combined R2/R3 close avoids redundant full gates: focused checks and
measurements, exact seed generation, frozen candidate, independent mixed
trailing audits, then one `scripts/check_milestone.sh` invocation. Repair
blocking findings first. Any later executable change needs fresh acceptance.
Only the existing allowlisted completion docs may change after that gate.

Audit primary: `gpt-5.6-sol` xhigh. Independent adversarial fallback:
`gpt-6-astra` xhigh because historical GPT-5.5 is unavailable. Neither receives
the other's conclusion before reaching its own. No paid service calls.

Commit only the reviewed work, verify the closing receipt, then push the new
commit with `0564a32` and `1105a7e` to original `origin/main` as a fast-forward.
The broader PRE-M56 goals and R4-R6 remain separate, even if R2/R3 pass.
