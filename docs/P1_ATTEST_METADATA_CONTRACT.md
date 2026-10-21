# P1 Fresh Attestation Index Metadata Batching

Status: experiment rejected after ordinary complete-tier ABBA. All functional
checks passed, but before17.97/16.65s (mean17.31) versus after17.99/18.09s
(mean18.04) is4.22% slower, not the required15% improvement. The after tier
includes all30 added oracle checks. Repeat spreads are7.93%/.56%. Both
changed scripts were restored to their exact pre-experiment staged contents;
no production implementation or new test workload is retained. Captures,
receipts and readbacks remain in local ignored `attest-metadata-v1` evidence.

Proposed for independent Gate A, 2026-10-19. The complete warm attestation
unit tier takes about16.9s. Current index checking batches Git hashes but
still invokes `prov_mode`/external stat separately for every indexed path.
This selects a mechanism, not a promised speedup. Defer artifact hashing,
CC identity reuse, reader parsing and shared-snapshot redesign.

## Scope And Data

Write only `scripts/milestone_attestation.sh` and
`scripts/check_attestation_batch.sh`. Retain the existing per-file-metadata/
Git-batch body as a fallback and direct oracle. Reuse `_prov_stat_rows` for
fresh metadata chunks of at most64 entries/8192 argv bytes. Its strict
status, count, byte framing, record order and exact path checks stay intact.
No sorting/deduplication or dense-ID assumptions for supplied index records.

Preselect supported Linux/capacity/GNU-stat/root handling before provider
operations. Unsupported cases use the old implementation; line-framed root
limitations retain the existing scalar wrapper route. A selected provider's
failure is never a reason to retry scalar or recover success.

Parse index records in original order, stopping before the first malformed
record or unsafe path/type/ancestor. Interpret successful metadata in the
same order; stop the valid Git-input prefix before the first mode/metadata
defect. The existing strict Git hash comparison runs on that prefix so an
earlier content mismatch still wins over a later ordinary mode/path/index
defect, including across chunks. Keep fresh live leaf/ancestor checks.

Retain full Git-output count/byte/hex checks, tracked-output publication and
write-failure handling. Candidate framing, both CC observations, artifact
hashing, before/after checks, canonical JSON and every public field remain
unchanged. No metadata cache between operations, result reuse, new executable,
runtime API, schema, CLI flag, environment bypass or concurrent scheduler.

## Explicit Provider-Failure Decision

An unsuccessful/malformed atomic metadata acquisition aborts before content
judgment, just as an unsuccessful Git-hash acquisition already does. Failed
metadata output supplies no checked prefix and is never replayed. Emit a
deterministic metadata-provider failure and fail the operation without
publishing tracked output or successful JSON.

This intentionally does not promise the old earlier-content diagnostic when
a later metadata provider is fault-injected to fail. Ordinary multi-defect
ordering with successfully acquired metadata stays exact. This failure-only
precedence is an explicit Gate A decision, not a silent claim of universal
stderr equivalence or weakened fail-closed acceptance.

## Tests And Acceptance

Retain all151 assertions and existing batch/write/scalar cases. Add direct
old/new status, stderr and tracked-output comparisons for stable supported
inputs; complete canonical JSON agreement; 64/65-entry and argv-byte bounds;
interleaved/repeated direct inputs; missing/symlink/unreadable/mode defects;
earlier content versus later mode/path/index defects within/across chunks;
unsupported capability preselection; and independent subsequent mutations.

Selected provider nonzero, partial, extra, malformed, reordered and wrong-path
records must fail without fallback, tracked publication or accepted JSON.
Test the explicit provider-failure precedence, rather than hiding it inside
an equivalence assertion. Retain source write-failure tests.

Only after both pre-reviews may the Sol High worker implement this two-file
slice. The lead reviews actual edits, runs ordinary paired complete host-tier
timings including new oracles, and requests mixed trailing reviews. Require
at least15% lower mean host-tier wall with repeat spread at most10% before
accepting the added complexity; otherwise revert only this owned experiment.
Unchanged compiler-cache identity is still freshly verified. A component
gain never substitutes for complete warm measurement, exact seed/runtime
propagation and the final reviewed frozen milestone gate. Warm60 stays open.
