# M55: Process And Time Contracts

Status: implementation contract, not completion evidence. Baseline `e2f6801`.
Compiler/runtime lane only; Libraries and AI/ML repositories are not modified.

## Gate A Decisions

Independent read-only `gpt-5.6-sol` xhigh and `gpt-5.5` xhigh reviews required
corrections before implementation. This contract incorporates them: consuming
wait, terminal error cleanup, recursive checked cleanup authority, absolute
executables, bounded capture, safe stdin writes, and direct-child-only reaping.
F14 interrupted legacy read/wait handling is the first implementation/test slice.

## Public Surface

No source syntax, effect atom, JSON schema enum, executor, thread, user
destructor, lifetime, or generic feature is added. Legacy `run_process` and
`process_result` retain their signatures, PATH lookup, and output behavior.

```nauqtype
duration_from_ns(value: i64) -> option<duration>
duration_as_ns(value: duration) -> i64
duration_between(start: instant, end: instant) -> option<duration>
wall_time_ns() -> result<i64, io_err>
monotonic_now() -> result<instant, io_err>
deadline_after(delay: duration) -> result<instant, io_err>
sleep_for(delay: duration) -> result<unit, io_err>
process_start(program: str, args: ref list<str>, cwd: str,
              env: ref list<str>, input: option<str>, capture: bool,
              max_output_bytes: i64) -> result<process, io_err>
process_wait(child: process, deadline: option<instant>) -> result<process_outcome, io_err>
process_terminate(child: mutref process) -> result<unit, io_err>
```

`duration` and `instant` are opaque copy types over signed 64-bit nanoseconds;
neither exposes fields, source constructors, arithmetic, or implicit conversion.
Durations are nonnegative. Wall time is Unix epoch nanoseconds. Instants come
from CLOCK_MONOTONIC and are meaningful only within the current boot clock
domain. `duration_between` succeeds only for ordered, representable subtraction.
Clock conversions and deadline addition are checked; negative duration inputs
return None, operational/representability failures return structured io_err.
Zero sleep returns immediately; interrupted sleep resumes against its deadline.
Clocks are not randomness or entropy sources.

`process` is an opaque move-only, drop-requiring owned handle. Its outcome is a
copy product with `exit_code: i32`, `stdout: str`, `stderr: str`,
`timed_out: bool`, and `cancelled: bool`. Normal exits use their status; signal
exits use 128 + signal. Outcome flags distinguish timeout/cancellation actions.

## Launch And Output

New launches require an absolute, NUL-free executable path and `execve`: no
PATH lookup, shell interpretation, or ENOEXEC shell fallback. Explicit nonempty
cwd may be relative to the parent's cwd; empty cwd is rejected before spawn.
Environment entries are KEY=VALUE
overrides on inherited environment; keys use ASCII identifier spelling. Invalid
keys, duplicates, or NUL are rejected before spawning. Parent env is unchanged.

`input=None` inherits stdin; `Some("")` supplies EOF; `Some(text)` supplies exact
bytes (including embedded NUL) followed by EOF. A child closing stdin early is
an ordinary EPIPE completion of input, not a signal that kills the parent.
`capture=true` captures both output streams; false inherits both and requires
`max_output_bytes=0`. Capture's combined byte cap is in 0..INT32_MAX, checked
before launch. Overflow kills/cleans up and returns `invalid_data`, never a
silently truncated outcome. Allocation failures remain structured errors.

Start performs setup/exec-error handshake, not background pumping. Wait pumps
stdin/stdout/stderr concurrently with nonblocking poll. A child may block on
pipe capacity between start and wait. No thread or hidden executor is added.

## Ownership, Cancellation, And Cleanup

States are active, outcome_ready, and inert/moved-from. Kernel exit alone does
not end ownership. Wait consumes the handle and returns the natural outcome,
cached cancellation outcome, timeout outcome, or a terminal error.

Terminate probes the waitable direct child with WNOWAIT|WNOHANG. If already
exited, preserve its natural outcome. Otherwise successful process-group kill
marks cancelled: this classifies the cancellation action, not proof of its
causal effect on a racing natural exit. Terminate synchronously reaps/drains
and caches the outcome; repeat terminate on outcome_ready is Ok. Wait then
consumes that cached result. Deadline applies to waiting, uses CLOCK_MONOTONIC,
and on expiry kills/cleans up with timed_out=true. An already-observed natural
completion or cached outcome takes precedence over a deadline.

Operational errors end ownership: emergency kill/reap/close, inert handle,
terminal io_err. Later operations on inert handles are invalid_input. Drop
performs the same resource cleanup without delivering an outcome. Descriptors
are CLOEXEC and normalized above stdio before child remapping. Partial/EINTR
exec-error messages, poll/read/write/wait interruptions, SIGPIPE, and setup
errors must not produce false success or leave the owned child unreaped.

Exception: if retry-safe recovery and a final terminal re-probe still leave a
valid direct-child anchor that the runtime cannot kill/reap, returning an
apparently recoverable result would abandon ownership. Emit exactly
`nauqtype runtime: process cleanup failed\n` to stderr best-effort and terminate
immediately with status 1, without unwinding. This is a runtime failure, not a
new source panic API. ECHILD clears the anchor and forbids further numeric
PID/PGID signals instead. Never retry Linux close after an error. Both Gate A
auditors approved this narrow unrecoverable-cleanup exception independently.

The runtime signals remaining members of the dedicated child process group
before reaping its direct child, including natural completion. It reaps only
the direct child, not grandchildren. Descendants escaping the group/session,
externally reaped children, process-global hostile signal handlers, and
uninterruptible kernel waits are outside the no-leak/timing guarantee. It never
signals a numeric PID/group after losing the waitable-child ownership anchor.
Deadlines are not hard-real-time promises.

## Checked Evidence

Clock reads/deadline calculation use effects(io), checked IO kind `read`.
Sleep means current-process suspension and uses `process`; lifecycle operations
also use `process`. Pure duration conversions have no IO effect. Terminate
mutates parameter 0; consuming wait has no mutref parameter.

Owned process-bearing params, locals, temporaries, and returns conservatively
carry IO/process cleanup authority under D055. Traverse canonical checked type
IDs through product fields, enum payloads, option/result/list, not spelling or
flat facts. Merely borrowing such a value does not add cleanup authority.
Seed this authority into the existing transitive IO fixed point before contract
validation. Existing review shapes expose inferred effects/kinds; facts keeps
source call edges only, with no invented implicit-drop call site. This is a
syntactic may-authority contract, not path-sensitive proof that a child is live.

Call references, graph targets, direct effects, and transitive IO kinds use the
checked call target kind/origin, never builtin-first name lookup. A private
callee-token offset joins source call sites to checked calls in per-function
ranges; missing or ambiguous matches fail closed. Qualified user functions
that share a builtin name remain user calls, including their checked result
error type in propagation evidence. No locked output shape changes.

New outcome field references use `builtin-field:process_outcome::<field>` with
`target_kind=field` and `evidence=builtin`, not an empty-module user-field ID.
Builtin targets are not source-editable rename targets. Older builtin-product
IDs and locked format shapes remain unchanged in this milestone.

## Acceptance And Scope

Focused native fault/signal probes first, then Nauqtype-owned process/time,
ownership/evidence, copied-release, and corpus fixtures. Preserve legacy
fixtures. Independent mixed-model trailing audits precede one frozen
`scripts/check_milestone.sh` run. Refresh seed from two matching actual compiler
emissions with the existing strict provenance contract. Do not modify the
milestone-close v1 completion-doc allowlist; freeze this file before that gate.
Record exact final outcomes in ROADMAP/TODO/AUDIT_REMEDIATION/coordination.

No M56 work, general OS library growth, async scheduling, task API, FFI, or new
ownership/lifetime analysis belongs here. Linux is the supported new runtime
target; other platforms return explicit unsupported operational errors.

Primary syscall references: [wait](https://man7.org/linux/man-pages/man2/waitpid.2.html),
[poll](https://man7.org/linux/man-pages/man2/poll.2.html),
[exec](https://man7.org/linux/man-pages/man3/exec.3.html).
