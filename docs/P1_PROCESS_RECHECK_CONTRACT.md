# P1 Bounded Process Exit Recheck

Independently approved at Gate A, 2026-10-19. Implementation/final evidence
remain subject to trailing review and fresh candidate verification. This is an
internal scheduling optimization, not an M55 API/ownership change or new
runtime primitive. Original P1-P4 targets, budgets and proof coverage remain.

## Measured Window

The O2/no-`-pg` diagnostic cache-oracle component used an ignored link-time
`--wrap=poll` observer that preserved arguments, results and errno. Its one
run passed with all protected readbacks and recorded29.562s wall. Of30,760
poll calls,1,498 had all three descriptors negative and requested10ms. Those
idle calls consumed15.147s, or51.24% of component wall. This is attribution,
not a production speedup. Parent CPU was5.597s and waited-child CPU4.028s.

## Exact Scheduling Change

In private `nq_process_pump`, retain the existing10ms maximum and exact
deadline-derived smaller bound. Only when all input/output/error descriptors
are already closed and child completion is not yet observed, clamp the first
five consecutive poll attempts to at most1ms. Count EINTR attempts too and
saturate the counter; interruptions must not restart an unbounded short-wait
window. After five attempts, resume the existing computed bound. Reset the
local counter whenever any I/O descriptor is live. An already smaller or
zero timeout stays unchanged.

The counter is local to this pump invocation, bounded and not public state.
Do not add spin/yield loops, descriptors, pidfds, handlers, syscalls, threads,
parallelism, environment options, API fields or target-specific heuristics.
The existing loop must still execute every fresh child probe and monotonic
deadline/cancellation decision in its original order. Keep terminal capture
snapshots, signal/group authority, anchor lifetime, draining, error handling,
reaping and descriptor cleanup unchanged. Faster observation is not license
to signal a reused PID, change a deadline, or bypass a failure.

## Evidence

Add focused scheduling assertions in the existing native process fault
fixture: a deliberately live, no-capture/no-input child must show bounded
short waits followed by the original longer bound; no busy spinning or
unbounded1ms polling. A captured-I/O child must keep ordinary behavior, and
deadline clamping and EINTR/fault handling must remain valid. Use real owned
children plus the existing explicitly labeled fault seams, preserving every
existing assertion and locked success output.

Run the complete existing process native fault/runtime/limits/allocation/
platform/legacy-interruption checks and sanitizers. Compare ordinary old/new
component oracle wall and CPU on identical inputs/flags/host, twice without
heavy overlap. Check output and child/resource cleanup independently of time.
Measure the real complete warm tier only on a legitimately rebuilt current
compiler, with unchanged receipt readbacks and complete environment identity.
Do not infer overall acceptance from the diagnostic or a single fast probe.

## Ownership And Close

After both Gate A reviews, the Sol High process worker owns only
`stdlib/runtime.c` (the bounded local pump policy) and the existing
`tests/fixtures/m55_process/native_faults.c` focused tests. The separate
literal-scan worker owns only its Nauqtype file. The lead owns harness work,
integration, measurements, seed/runtime propagation and Git. No other runtime
or semantic edits are authorized. If tests need another file, request a scope
amendment first rather than widening silently.

Require mixed independent trailing audits on actual changes and focused
evidence, exact regenerated seed/runtime provenance, and a fresh frozen
seven-phase native close. Preserve the old attested candidate as its own
evidence. The60s warm goal remains strict; no source-language work begins
until the performance campaign is honestly closed.
