# P1 Serial Capture And Validation Reuse

Proposed for mixed pre-implementation review. Warm and cold execution remain
serial. The host-concurrency proposal was withdrawn without implementation:
nested GNU timeout groups need a separate cleanup contract, not a speed waiver.
Keep the original complete order, natural timeout tests and fail-fast rules.

## Measured Pressure

The current focused host tier still takes provenance34.14s/attestation16.89s.
One diagnostic shell trace attributes most provenance delay to repeated real
production builder/bootstrap/cache invocations against synthetic inputs:
roughly1.0-2.0s per invocation. This is attribution, not production speedup.
An ignored scalar-parser prototype on the same immutable record took0.909s
versus0.518s for40 reads, with equal parsed bytes; its total impact is limited.

## Captured Source Metadata

Inside each `seed_verify`, enumerate/validate source paths once and reconstruct
the current inventory from those exact paths, with fresh file-mode/hash reads.
Only after comparing that fresh inventory byte-for-byte with the declared
inventory and checking its manifest hash may it supply two derived views:

- derive the unchanged `nauqtype-selfhost-source/v1` path-NUL-hash-NUL digest
  from its freshly observed entries, instead of rereading the same sources;
- form the expected checksum path set from the captured validated source set,
  instead of enumerating that same source subtree again.

Retain the independent fresh walk of the ENTIRE bootstrap tree, exact path-set
comparison, and fresh checksum read of EVERY actual artifact/source. Retain
coherence between observations: each fresh source hash in the final checksum
loop must equal that source's captured, validated inventory hash. Regenerating
SHA256SUMS after a persistent source mutation must not make the earlier source
identity authoritative. Reuse that loop's hash; do not add another hash pass.
Add a controlled source AND SHA256SUMS mutation after inventory capture while
leaving manifest/inventory unchanged, and require rejection.
Retain
all original/captured input, compiler, mode, source and post-build checks in
builders/caches/publishers. No cross-invocation metadata/content cache, no
timestamp authority, no trusting the declared inventory without reconstruction.
The existing public inventory/path/tree helpers keep their fresh-read behavior
and exact encodings. Add narrow internal from-paths/from-inventory helpers,
not a general cache or manifest parser. Validate canonical records/counts,
sorted unique safe .nq paths, lengths, modes, hashes, LF/EOF and NUL rejection.

Compare derived hashes/path sets with the unchanged rereading helpers. Keep
every156 existing provenance assertion. Add source/include set, mode, tamper,
symlink and malformed-inventory oracles and a controlled persistent mutation
between inventory observation and the retained checksum/tree checks. No
atomic-filesystem-snapshot or malicious-owner claim is introduced.

## Batched Git Blob Validation

`attest_candidate_state` may batch its repeated `git hash-object --no-filters`
calls into one `--stdin-paths` call for ordinary safe physical roots. Preserve
every indexed path/stage check and explicit actual-mode/regular-file/ancestor
validation BEFORE a path enters the batch. Do not pass unvalidated symlinks,
directories or unsafe paths to Git. Use absolute line-framed paths and exact
source-order expected OIDs; require successful Git status and exact count/order/
hash correspondence. Reject partial, malformed or extra output.

For root spellings unsuitable for unambiguous line input, retain the old
per-file path, not a new rejection. Preserve source-order failure reporting
on static defects: validate/hash only the safe prefix before the first mode/
stage/path failure, report an earlier prefix byte mismatch first, and never
turn any failed batch into success through fallback. Keep actual candidate
framing, untracked membership, write-tree and before/after checks unchanged.
Keep SHA-1 Git-object identity separate from SHA-256 attestation identities.

All151 attestation assertions, escaped path cases, real framing oracle and
tamper/closing tests must stay. Add batch versus legacy validation cases for
empty/multiple files, spaces/quotes, mode/content defects, failed/partial Git
output, and explicitly unsupported root framing. No attestation/schema change.

## Optional Scalar Fast Path

Only if still useful after measurement, skip the per-character JSON string
decoder for scalars containing neither backslash nor an embedded quote. Keep
the existing decoder unchanged for escaped/malformed candidates, all fixed
field validators, canonical writer and raw byte comparison. No accepted JSON
shape/encoding or schema changes; retain every strict malformed/escaped case.
Compare exact success and rejection against the old decoder, not just speed.

## Ownership And Close

Lead owns `scripts/seed_manifest.sh`, `scripts/milestone_attestation.sh`,
registration/integration and measurements. A bounded worker may add standalone
host-unit oracles after interfaces are fixed; no Python or runtime work. No
compiler/borrow/type/schema policy changes, new CLI or production flag changes.
The accepted fixture-C-cache and function-index slices remain separate.

Resolve both independent pre-reviews before these production edits. Run focused
equivalence/tamper checks, measure the complete SERIAL warm tier including
all validation and cleanup, then freeze for trailing audits and one unchanged
fresh seven-phase close. Targets stay <=10s focused, <=60s warm, >=50% lower
cold time versus2520.62s, with10min as the working target. Do not relax them.
