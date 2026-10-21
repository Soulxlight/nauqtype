# P2 Review Call Membership Slice

Proposed for independent pre-implementation review; not accepted performance
evidence or a language milestone. Keep P1-P4 goals and all existing gates.

## Measured Selection

The initial indexed component's diagnostic check still materializes619,181,573
call-fact clone helpers on the same retained e9d3 selfhost source. The prior
profile attributes almost all of those to direct/transitive print and IO
effect scans. The new diagnostic samples review effect builders and direct
effect queries heavily after parameter scans were removed. Instrumentation
selects this mechanism, not an elapsed-time claim.

## Bounded Change

Build one invocation-owned compact owner index over the exact supplied
`call_fact` collection in the review phase. Keys are exact module/function
strings plus original source index. Support interleaved records, duplicate
names, empty/missing owners, and filtered collections. Query only matching
source rows in their original order; do not materialize nonmatching full
call facts. Sorted list-backed rows/ranges and binary owner lookup are enough.
No general indexing subsystem or new runtime/language mechanism.

Use it only for direct and transitive print/IO/IO-subkind effect builders.
Preserve the original fixed-point iteration, caller/function order, callee
resolution and checked origin/builtin rules, cycle behavior, missing targets,
and first-discovery output order. Do not pre-resolve or reinterpret callees.
Returning small owned per-function call lists to unchanged legacy algorithms
is acceptable. Do not touch mutation/propagation semantics or output formats.
Public review APIs and schemas remain unchanged; no checked/backend consumer
may fall back to these front-end facts.

## Ownership And Proof

After both Gate A approvals, one Sol high worker may edit only
`selfhost/review.nq` and a narrow `selfhost/review_index_probe.nq`. The lead
owns registration in the current compiler-index suite/copied module list,
integration, performance measurement, seed, final audits and Git operations.
No descendant, commit, push or native heavy test by the worker.

Compare indexed owner rows and all effect outputs with retained linear
oracles: interleaving, import/local collisions, builtin/direct calls, qualified
targets, unknown targets, duplicate owners/calls, empty/filtered input, mutual
recursion, transitive chains and exact output ordering. Existing facts/review/
review-diff/change-report/policy/refactor goldens stay locked. Run the standing
Nauqtype-owned tests/proof; compare selected old/new C and evidence directly.

Retain source/CC/flags identities. Obtain two ordinary checks of the final
compiler against the retained common source; a spread over10% is inconclusive.
Count materialization reductions with diagnostic profiles without calling
retains deep copies or instrumented time a production gain. Propagate the
actual compiler through the exact seed and mixed trailing audits, then one
fresh complete seven-phase close. Missing a performance goal stays open.
