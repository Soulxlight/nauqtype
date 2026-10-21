# P1 Invocation-Local Host Batching

Proposed independent Gate A amendment, not performance acceptance. The V8
complete warm tier passed in109.97s versus173.385s before, but misses60s.
Focused current-cache feedback passed in1.70s. Diagnostic external-stat
counting observed11,596 calls in all156 provenance assertions; instrumentation
time is not a production measurement. Keep every test and serial ordering.

## Path Validation

Replace temporary-file reconstruction in `prov_validate_paths` only with an
exact captured-byte equivalent. A Bash NUL-delimited read must reject any
NUL and unexpected read errors, preserve trailing LF, and validate the same
sorted unique ASCII-safe nonempty lines. Empty input remains allowed. Do not
use command substitution that strips final newlines. Compare the entire
accepted/rejected language with the frozen old validator, including missing
LF, duplicate/unsorted lines, controls, quoting and unusual printable names.
Public output stays empty; rejected lists cannot supply trusted paths.

Select the small-capture path only from checked regular-file metadata at
size<=65536 bytes; larger input uses the unchanged legacy streaming validator
BEFORE any bounded capture. Use LC_ALL=C, IFS=, `read -r -d '' -n (size+1)`:
status0 means NUL or over-bound data and rejects; only EOF/status1 with exactly
the observed byte count may proceed. Repeat that bounded read and compare all
captured bytes, then revalidate regular/readable metadata and size. Unexpected
errors, truncation/growth, incomplete data or mismatches reject, not fallback.
Validate the captured bytes, including final LF, rather than a later reread.
This preserves old fresh-comparison authority without an unbounded Bash value.

## Metadata Batches

Within each `prov_files_frame`, file observations may use bounded GNU stat
batches over already validated, quoted absolute argv paths. Preserve fresh
regular/readable/nonsymlink leaf and ancestor checks. Require successful stat
status, exact row count, canonical raw mode/size, regular file type, readable
mode bits and unchanged100644/100755 encoding. Reject partial/malformed/extra
output; a failed batch must not turn green through fallback.

Identity-binding revision: use private path-bearing NUL records
(`%f %s %n\0`), not anonymous mode/size rows. Validate each exact absolute
filename in expected argv order, literal separators and complete byte/record
consumption. This applies to frame metadata AND the proposed hash-row helper.
A swapped pair of otherwise valid stat records must reject. Public frame
bytes remain unchanged. Empty input invokes neither stat nor SHA-256 stdin.

Keep content reads fresh and in original source order, canonical bytes and
every producer/capture/toolchain pre/post guard. No metadata persists across
calls or timestamps become authority. Failed streams are unusable as before.
Do not silently reject old valid large lists/environments through ARG_MAX:
select legacy per-file behavior BEFORE batching when host/argument capacity
is unsupported. Bound batches by byte size and count. Environment-size checks
may pipe `env -0` directly to a byte counter, never persist or print raw
environment. No concurrent scheduler or new process-group framework.

Concrete batch preflight: require a supported positive `getconf ARG_MAX` of
at least131072, pipe-counted environment payload<=32768, and cap each batch
at64 entries AND8192 bytes of absolute input argv. Include actual program/
option/destination argv and conservative pointer+terminator overhead in the
capacity calculation; enforce per-argument bounds. If any capacity fact is
unknown or cannot fit, choose the old scalar path before batching. No silent
new large-input rejection or failed-batch fallback is permitted.

## Copy Groups

`prov_capture_inputs` may group validated files sharing a parent into bounded
quoted `cp --preserve=mode -- ... DEST/` calls. No tar extraction, recursive
copy, parent-symlink preservation or general publisher. Keep owned destination
preconditions, exact membership/file bytes/modes, independent original and
capture rereads, failures and cleanup. No sharing mutable outputs. Preserve
large-input behavior with preselected legacy mode/bounded argv. A source
changed during capture must still reject; failed copies cannot be blessed.

## Proposed Walk Metadata Extension

The first script-only prototype still spends52.11s versus61.46s in the
matched156-case provenance workload (nested lab paths; not a clean native
whole-tier gain). Per-entry external stat remains in `prov_tree_paths`.
Before implementing this extension, obtain both independent approvals.

A supported GNU find may capture type, octal mode and full path in fixed
three-NUL-field records during the same fresh walk. Keep original live Bash
nonsymlink/type/readability and ancestor checks; remove only the redundant
per-file external stat, using the freshly observed find mode for readable
mode bits. Directories keep their old handling. All regular entries, including
ignored non-source outputs, remain validated before filtering. Preserve
source/snapshot/all policies and sorted output. Do not follow symlinks.

Check provider status, complete record framing, exact consumed versus spool
byte count, types, modes and path safety before publishing sorted paths.
Truncated/extra/unknown records reject. Unknown GNU-format capability selects
the unchanged old walk before operation; failure never recovers green.
All original/capture rereads remain; no atomic-filesystem snapshot is claimed.
Add direct legacy-versus-new walk tests for empty/nested trees, modes, unsafe
names, ignored outputs, symlinks/directories/FIFOs, malformed/truncated provider
records and persistent mutation. No frame/inventory/schema bytes change.

## Evidence And Ownership

### Proposed Fresh Hash Rows

The original diagnostic counted11,596 external stat calls in156 assertions;
the isolated walk prototype still passed every assertion but took74.15s
(versus52.11s in an earlier nonquiet lab run). That is inconclusive timing,
not evidence of a walk speedup. The seed inventory/checksum loops still
start separate mode/hash commands per entry. Obtain both Gate A reviews
before replacing only those loops' per-file dispatch with bounded fresh rows.
Small lists may preselect unchanged scalar handling before any provider call;
that is dispatch selection, not failed-batch fallback.

Add an invocation-local private file-row helper: for the exact validated,
sorted input paths, emit mode, SHA-256 and relative path in source order.
Use the existing64-entry/8192-byte capacity rules and preselected legacy
handling. A GNU SHA-256 provider may hash quoted absolute argv with `--zero`;
validate successful status, complete NUL framing, exact count/order/path,
64 lowercase hex digits, raw spool byte count and full consumption. Metadata
uses the same strict fresh GNU stat rows and live nonsymlink/readability/
ancestor checks as frames. Recheck live leaves before content acquisition.
Any failed/malformed provider fails closed, never fallback. Do not use
timestamps or cached declared hashes. Do not persist environment bytes.

The source-inventory builder may render these freshly acquired rows instead
of per-file mode/hash calls. The final seed checksum loop must independently
acquire a NEW row set for every artifact/source, retaining exact full-tree
membership and source-hash correspondence against the earlier checked
inventory. These are two distinct observations; do not reuse one for both.
Preserve every public inventory/checksum/frame/schema byte. Root spellings or
tool capabilities that cannot be handled select the unchanged scalar path
before operation. Keep direct old/new empty/binary/named-path/mode tests,
malformed/truncated/reordered/extra hash and stat output, provider failure,
source-plus-checksum mutation and all original guards/assertions. No new
runtime/helper executable or parallel host process framework.

Lead owns `scripts/provenance.sh`, integration and measurements. A bounded
worker may extend only `scripts/check_provenance_metadata.sh` after interfaces
are fixed. Keep all156 provenance and151 attestation assertions plus the
existing strict metadata/seed oracles. Add old/new frame/copy comparisons for
empty, binary/NUL content, spaces/quotes, execute modes, multiple parents,
interleaved parent groups, large lists, symlink ancestors/leaves, partial
stat output, failing copies and persistent source mutation.

Prototype in isolated script-only captures, not by invalidating the current
native compiler cache repeatedly. No Python/runtime/language/schema or ceiling
changes. Obtain two independent approvals before production edits. Final
acceptance still requires actual current construction, exact seed, ordinary
paired measurements, complete warm timing, mixed trailing audits and one
fresh seven-phase close; unmet campaign goals stay open.
