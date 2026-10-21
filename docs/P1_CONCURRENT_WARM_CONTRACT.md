# P1 Concurrent Warm Contract v2

Owner approved the opt-in direction on 2026-10-21. Strict60 is not waived.
v1 design is superseded. Both independent mixed Gate A reviews passed this
design before implementation dispatch; final acceptance is pending.
Existing03a3 gate/attestation/capsule stay immutable.

## Surface And Scope

NQ_FAST_CONCURRENT=1 selects only no-argument full check_fast.sh with
NQ_TEST_REUSE_C=1. Unset/0 keeps original serial order/fail-fast; reject
empty/unknown values, partial+concurrent, and concurrent+reuse0. Milestone
explicitly sets NQ_FAST_CONCURRENT=0 alongside reuse0. No proof/release,
compiler-phase, syntax/runtime/API/schema, Python or result-cache changes.

Cache validation and genuine rebuild remain serial before fan-out, with all
cost included/disclosed. Source/seed/producer closure is unchanged, so avoid
unnecessary seed regeneration or whole-workspace copy. Full final gate still
must attest the new script candidate, not inherit03a3 acceptance.

Fixed groups:0 bin/nauqc test;1 seed-capture then provenance;2 attestation
batch then151units;3 budget14. All original assertions, probes and flags stay.
Four separate shell processes isolate PATH/CC/TMPDIR mutations. The latest-*
attestation leaves belong only to group2. Existing other outputs are disjoint.
The provenance routing fixture explicitly forces its serial model calls to0
and stubs concurrent routing: no nested actual scope/proof/test invocation.

## Ownership Anchor And Control Protocol

Use sourceable coordinator functions in check_fast.sh so the outside waiter
and its traps are the actual top-level shell, not an untracked helper child.
systemd-run --scope EXECs the internal coordinator; do not assume an outside
supervisor and never combine --wait with --scope.

Use one new private0700 directory, fresh random unit+independent nonce, and
fixed absolute provider commands. No unit/PID signals or StopUnit calls.
All full check_fast invocations hold one atomic checkout tier lock through
completion/drain. This excludes participating tier invocations, NOT arbitrary
builders, prove, direct tests or source writers; operator serialization remains
required. Stale/uncertain locks fail closed, never auto-recover by PID guessing.
Before the contained coordinator owns cleanup, failed or interrupted cache,
builder, or serial work retains the lease. Normal serial completion releases
it explicitly; only verified contained cleanup/drain may release it otherwise.

Initial certified provider: Ubuntu24.04 systemd255.4-1ubuntu8.18 installed
client AND independently queried running user-manager Version,
cgroupsv2. Other builds reject opt-in until separately verified; serial remains available.
Pin --expand-environment=no and effective MemoryMax536870912,swap0,OOMPolicykill,
KillModecontrol-group,SendSIGKILLyes,RuntimeMaxSec300s,TimeoutStopSec5s.
CPUQuota400% and TasksMax256 bound aggregate work. No privilege/delegation or
permission changes. Missing provider/capability rejects opt-in, not serial fallback.

Outside starts one fixed GNU timeout --foreground --kill-after=1s 320s around
systemd-run. Its C supervisor owns its own direct child; Bash $! is only a
wait handle, never signalling authority. Scope lifetime300s plus stop5s is a
backstop, not the60s success criterion. Outer SIGKILL cannot run cleanup; the
manager deadline remains a finite orphan backstop, not immediate-cleanup proof.

Entry publishes bounded READY only when its actual cgroup/InvocationID exist,
then blocks on GO for at most5s without launching groups. Outside readiness
discovery is bounded10s, queries individually bounded1s. Description alone is
NOT readiness: require one ACTIVE snapshot with matching nonce, Transient=yes,
valid invocation UUID, actual coordinator membership and effective properties.

Outside pins read-only exact cgroup directory/events/procs/resource descriptors
and opens exact cgroup.kill and cgroup.freeze WRITE-ONLY before GO. Verify owner UID, cgroup device/
inode against opened descriptors, active invocation and child membership again
after binding. All subsequent cancellation addresses ONLY this retained kill
FD. Never reopen a kill path or stop by unit name; replacement cannot redirect
that capability. On mismatch no GO and nonzero outcome. If binding/creation is
ambiguous, withhold GO, wait the bounded launcher, retain failure records; do
not signal an unverified unit. A late entry still times out without GO.

Opt-in cancellation uses immediate SIGKILL through the pinned cgroup.kill FD,
including children that create process groups/sessions. It does NOT claim
graceful TERM delivery. This is a local test-tier cancellation policy only;
production process semantics and normal serial failure behavior are unchanged.
Before binding, INT/TERM/HUP latch cancellation, withhold GO and drain/wait the
bounded launcher. After binding they latch cancellation, prevent further
launches, kill the owned cgroup via FD, verify drain and genuinely reap launcher.
Manager changes/disappearance cause infrastructure failure, never scope reuse.

Installed-kernel feasibility probe3 PASSED: actual FD write0 killed only owned
live scope with genuine wait137/removal; retained old FD after removal then
same-private-name replacement with different UUID/inode yielded ENODEV, while
replacement stayed live and naturally exited0. Native concurrent-fd-v3 holds
results. v1 parse failure before launch and v2 safe premature-readiness failure
remain preserved. Probe evidence is not production approval.

## Environment Domain And Oracle

Do not change fixture_c raw-environment hash. Reject at waiter entry initial
raw/proc environment: duplicate/malformed/non-identifier keys, preexisting
INVOCATION_ID including empty, shell startup hooks/functions/options exports,
and a documented reserved private-variable prefix. Use only that reserved
prefix for ALL helper locals; do not shadow an existing exported caller name.
Reject allexport state. Unusual legal values, including empty/newlines and
literal dollars, remain allowed. Do not print/persist raw caller environment.

Scoped entry verifies its injected ID against the owned invocation BEFORE
removing ONLY that newly added key. Keep nonce/unit/spool/GO/control variables
out of exported environment; pass private state positionally. Close control
descriptors before actual payload exec. No unrelated caller key filtering,
normalization, environment cache, or changing the modeled fixture identity.

Prove full ordered NUL environment and literal argv at an actual exec witness
against an equivalent DIRECT route with the same interpreter/worker depth,
including SHLVL and underscore. Use memory/anonymous pipes or private named
FIFOs, not regular raw-environment files. A small Nauqtype exec witness is
preferred. Synthetic duplicate-entry validator cases must be labelled unit
evidence, not a claimed real execve duplicate injection. Unsupported cases
reject before scope/payload. No crossmode cache-hit equality is promised;
actual opt-in repeats must preserve all23 valid receipts/body+inode+mtime.

## Status, Logging, Resource And Drain Boundary

Use checked, bounded loggers (e.g. GNU tee --output-error=exit, logger-only8MiB
limit) and genuine waits, not unjoined process substitutions. Never impose
the log size limit on tests/compiler output files. For a narrow implementation,
combine stdout/stderr per group and replay in original group order to stdout;
document this opt-in reporting behavior. Infrastructure errors remain stderr.

Join every launched producer/logger; collect actual statuses individually,
clear handles after reaping, and preserve failures. Trap-interrupted wait is
not terminal evidence. Exact fresh bounded status records must match nonce+
group; missing/duplicate/malformed status, capture/replay error, partial launch,
output overflow, deadline or OOM is infrastructure failure. No reused results.

Coordinator remains alive at FINISHED, blocked in a shell-builtin control read
with no fork/payload work, until outside confirms complete statuses. Before
resource capture, outside freezes the exact scope through its pinned freeze
FD and requires descriptor-bound cgroup.events frozen1. Read the pinned
cgroup.procs and require EXACTLY the verified blocked coordinator; reject
ANY descendant cgroup directory, other member, unknown or failed observation.
This proves quiescence rather than treating joined direct producers as proof
of no detached descendants. Capture effective aggregate memory.peak and
memory.events only then. Outside ACK is queued while frozen, then pinned-FD
unfreeze permits only the known coordinator to consume ACK and exit without
fork or payload work. A freeze/bind/quiescence/unfreeze failure is infrastructure
failure; pinned kill works even when frozen. No payload work after capture.
The ENTIRE freeze-request/frozen1 wait/quiescence/resource/ACK/unfreeze
transaction has one nonresetting5s monotonic deadline, derived from proc uptime
with centisecond bounds and checked before/after each step. The freeze write
is asynchronous, not proof of completion. Failure to observe frozen1 by that
deadline triggers pinned-FD kill, a separate bounded5s drain attempt, preserved
failure evidence/lock on uncertainty, and infrastructure failure. Scoped
coordinator's final ACK builtin read is separately bounded10s. Native sysfs
observations and auxiliary provider operations remain within the fixed outer
deadline. No successful status is emitted after a missed transaction deadline.
Green requires all4 genuine worker/logger results, launcher reap, successful
replay/cleanup, and verified drained old cgroup. A pinned cgroup.events reports
populated0; if kernel already removed the original node, require descriptor-
bound removed-node evidence (not a replacement pathname) and the kernel's
empty-before-removal rule. Treat operational uncertainty as failure. Surviving
descendants after normal coordinator exit cause pinned kill+drain and failure.

Cancellation wins, then infrastructure/OOM/deadline/cleanup failure, then first
nonzero producer in original group order. All groups join: explicitly not serial
fail-fast equivalence. Record true aggregate memory, not GNU time max-individual
RSS as aggregate. Setup/population/measurement/cleanup overhead remains visible.

## Write Sets, Tests And Acceptance

Production worker: scripts/fast_concurrent.sh only after GateA.
Fixture worker: scripts/check_fast_concurrent.sh and optional Nauqtype witness
under tests/fixtures/p1_concurrent only after GateA, no native jobs until assigned.
Lead: routing+lock in check_fast.sh, routing spies, explicit milestone force0,
unit registration, contract/VERIFICATION/AGENT_ROUTING/completion docs, integration,
native runs, Git and final evidence. No compiler/runtime/seed writes planned.

Focused unit fixtures cover all4 runs/overlap/order, first ordered failure,
nonzero124/137, capture/replay/overflow failure, unsupported provider/domain,
partial startup and signals at each handshake boundary. Real-provider focused
cases cover FD ownership/replacement, pre-GO safety, nested setsid descendants,
drain/reap, effective resources/OOM failure, and full actual-exec environment.
Include a detached closed-stdio descendant that survives FINISHED and allocates.
Keep it live through frozen1, require rejection BEFORE resource capture or ACK,
and verify subsequent owned kill/drain. A later empty drain alone cannot pass
this test. This exercises rejection, not a naturally exiting-before-ACK child.
Native freeze support/properties must be verified. Additionally
test freeze-write0 with frozen1 never arriving, requiring bounded failure.
Default serial/fresh/partial routing must not require systemd. Unit coverage
registered in the host-only group uses spies, not recursive native scopes.

Then new same-session population plus two full opt-in warm runs, verified23
receipt bodies/metadata, artifact/input/CC/boot/index readbacks, and fresh
attestation checks. Strict60 includes cache checks and coordinator overhead.
Keep serial100.58 evidence and honest aggregate/workflow costs. Required final
mixed audits precede ONE new full frozen seven-phase gate. No commit/push or
M56 until actual whole-goal acceptance. Disclose the10min cold working target
as unmet; it is not a second hard deadline replacing the stated >=50% goal.
