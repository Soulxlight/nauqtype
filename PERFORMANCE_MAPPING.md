# PRE-M56 P2: Incremental Normalizer Mapping

Measured candidate snapshot, 2026-10-04: implementation, focused production
measurements, and exact seed reproduction evidenced. `ROADMAP.md` and
`TODO.md` will record final closure only after the required audits, full gate,
and attestation succeed; this report does not extend an earlier gate's
attestation to the candidate.
Compiler-owned work only. No consumer adoption, publication, or whole-gate
speedup is claimed. This slice does not close the complete P1-P4 campaign.

## Pressure And Boundary

The frozen E1 comparison takes 85-89 seconds on retained P0/E1 C in the
current serial production measurements.
A separate diagnostic GCC `-pg` build of the verified E1 C attributed 79.65%
of sampled CPU to `mapping_lookup`; string drop/clone accounted for 9.32%
and 9.12%, with 8.001/7.925 billion calls respectively. These are retain/drop
operations, not evidence of deep byte copies. The instrumented command took
186.88s; that is not production timing. The reference source, runtime, and
compiler identities were checked before and after attribution.

The candidate may replace only the private normalizer mapping scan with an
incremental append-only sorted-run index. It must not change syntax, type or
borrow rules, runtime primitives, schemas, CLI, policy, or language features.

## Transparency Contract

- Maintain four independent states: left/right times binding/tmp.
- Keys are exact digit text. `01` and `1` are different keys; never convert
  them to integers, truncate long keys, or renumber by sorted iteration.
- A new key receives the next one-based first-appearance ordinal only after
  its complete existing token shape has been recognized. Lookups reuse it.
- Recognize and normalize tokens inside quoted C text exactly as the old
  implementation does; this change is not a new C lexer or normalizer policy.
- Preserve trimming, blank-line skipping, internal spaces, final-newline
  behavior, complete current-line normalization, and early mismatch before
  later lines. Do not pre-scan or materialize normalized whole-C output.
- Sorted ranges and run metadata are private append-only implementation
  data. Explicit `ref`/`mutref` access remains visible in Nauqtype source.
  Report retained-memory cost; do not widen borrowing or add collection APIs.

## Proof And Measurement

Keep the original 15-pair oracle and add old-key reuse, namespace/order
cases, long decimal keys, leading zeros, failed prefixes, quoted text, and an
early mismatch with a large suffix. Compare exit, stdout, and stderr exactly.
Focused probes must execute the actual changed Nauqtype functions, not merely
type-check them. A source-extracted probe is focused evidence only, never a
published compiler, verified cache, or substitute for the complete gate.

Measure two serial production runs per version on the same retained P0/E1 C
bytes, with physical compiler identity, unchanged GCC flags, input/output
hashes, run order, wall time, RSS, and spread recorded. Profiling is diagnostic
only. No concurrent Linux compiler work is an operator observation, not an
independently monitored interval. Overlapping/noisy timings are inconclusive.

Regenerate the exact seed through an actual compiler and exact re-emission.
Freeze the complete generated delta, obtain independent mixed-model trailing
audits, then run one full seven-phase cold gate. Both direct seed comparisons
and the copied-selfhost comparison remain mandatory. Any later source edit
invalidates that candidate's gate. Completion docs may disclose closure only
through the existing allowlisted documentation-delta boundary.

## Results

### Construction And Focused Coverage

The Nauqtype implementation keeps append-only mapping records and a previous
chain of sorted power-of-two runs. Lookup binary-searches each active run;
equal-size runs merge into a fresh appended range. Stored replacements never
change during sorting or merging. Lookup uses `O(log^2 U)` comparisons for
`U` distinct keys, with `O(U log U)` retained mapping records and `O(U)` run
metadata. This is private normalizer data, not a general indexing subsystem.

`scripts/check_normalizer_index.sh` extracts the actual Nauqtype helper bodies
into a focused executable and runs the original 15 oracle pairs plus 21 P2
pairs. It also runs the same oracle under address/undefined-behavior
sanitizers with leak detection. `normalizer_index_cases()` executes active-run
invariants, all retained key ordinals after merges, long/leading-zero keys,
namespace isolation, exact normalized text, and no later-line pre-scan.
The existing owned `test` path calls it without changing success output.
The production-plus-sanitizer focused command passed in 6.25s, peak RSS
104160 KiB. A full retained-C comparison by that source-extracted executable
took 3.51s; it is smoke evidence only, not the complete compiler measurement
below or a replacement for the full gate.

### Complete Compiler Measurements

All four reference comparisons preceded candidate comparisons, in the order
P0 twice, then E1 twice for each driver. GCC, runtime bytes, production flags,
input bytes, and driver identities were sealed. Each comparison exited zero,
printed exactly `seed structural proof ok\n`, and had empty stderr.

| Retained C input | E1 reference seconds | P2 complete compiler seconds | Mean speedup | Candidate repeat spread |
| --- | --- | --- | --- | --- |
| P0 | 85.08 / 86.99 | 3.42 / 3.47 | 24.97x | 1.46% |
| E1 | 88.51 / 88.48 | 3.36 / 3.42 | 26.10x | 1.79% |

Spread is `100 * (max - min) / min`. Reference spread is 2.24% for P0 and
0.03% for E1. Candidate comparison peak RSS is 43948-44768 KiB versus
25940-26496 KiB for the reference, roughly 1.7x higher. That retained-memory
tradeoff remains within the unchanged budgets and is not hidden by reporting
wall time alone. The operator observed no concurrent Linux compiler work;
this is not independent host-isolation certification.

The full candidate was emitted by the pinned E1 compiler in 435.22s and
compiled with unchanged production GCC flags in 43.69s (436084 KiB peak RSS).
These one-time rebuild costs are separate from the faster comparisons;
end-to-end gate savings require the reviewed full gate, not extrapolation
from this inner command.

Identity anchors:

- predecessor/reference C: `73ee8c354d3241dbcce9da003708a8ff6b3c5e0e903fe8c425c3aad7e0ec55de`
- reference executable: `7dd12165501dada79d5d4839e93d520eeb7c72b116069ad718df3260609d8319`
- retained P0 C: `2ec30ab03c77d5b113eb414e18e5b4ba52c6217d9cf3283f938eea8b150c5084`
- physical GCC: `1b99826121ae6682a634e5efe09bd3e3df58ce58e0b28f849114ab5b89139c26`
- candidate source: `6c161ecfcf254b602d4aa9199024f3e4890f2e7d26daba6f147b157af7bc379d`
- candidate executable: `82377a7bc1ee012a63b8409caccae745b209683fc50d6a85ddbcdf1b7a5301ad`
- exact generated C: `5221d8ab5c788140bea2a079b2a37bc2de6204c0939399bf328c6803d3f0bc08`

The actual candidate re-emitted its own C in 434.12s; input and output are
byte-identical. The strict seed manifest binds the 70-file source inventory,
unchanged runtime, predecessor, actual generator, physical GCC, and NUL-framed
flags to construction index `1183aa1cd4047e232449836fa7ee834a76c88ed9`.
The pinned generation/promotion recipe passed in 941.38s, peak RSS 436084 KiB.
It includes both emissions, compilation, oracle, candidate measurements,
identity checks, and promotion, but not the earlier reference runs, profiling,
candidate capture, audits, or the later complete gate. Recipe SHA-256 is
`aa5272253d6e20babca763c275386a96d1fa23bd45189199186f31da6bd6a955`.
Catchable failure/signal rollback preserves the predecessor; no SIGKILL or
power-loss atomicity guarantee is claimed.

Raw host paths, profiles, hashes, command receipts, and rejected attempts stay
ignored under `build/verification/`. The diagnostic profiling child succeeded
with exact stdout and empty stderr; its surrounding temporary runner was
interrupted by a lead-side file edit after execution. The retained profile was
finalized separately and its identities rechecked. That runner interruption
is not a successful production run or a compiler failure.

### Acceptance Boundary

The exact seed is only a prerequisite: review the frozen complete delta with
both independent auditors, then run the unchanged seven-phase cold gate and
attestation once. Record that gate's actual identity, phase costs, memory,
and total result in the allowlisted completion documents. No cold-gate
speedup, P1-P4 closure, full generics, external consumer adoption, commit, or
publication is claimed by the production comparison result.
