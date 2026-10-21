# P1 Time-Scaled Timeout Unit Fixture

Implemented and independently approved at both Gate A and trailing review,
2026-10-19. All14 unit cases pass; ordinary before9.48/9.57s versus
after4.41/4.57s retain exact success stdout and empty stderr. Complete warm
coverage passes in99.89s before the later seed promotion, still above60s.
Exact seed propagation and current-cache reconstruction are now recorded in
the [completion ledger](../AUDIT_REMEDIATION.md#follow-up-seed-propagation);
campaign acceptance and the fresh full gate remain pending. This is not the withdrawn
readiness/alarm controller: no new PID discovery, signalling or reaping code.

The unchanged `timeout137` unit case consumes about6.02s, including5s grace.
Keep `scripts/run_budgeted.sh`, its5s production argument, all14 cases,
success text, status/classification and completion-receipt rules unchanged.

Only this unit case gets a private, function-scoped PATH shim for `timeout`:

- Version queries exec the real `/usr/bin/timeout` unchanged.
- For an actual invocation, require exactly one `--kill-after=5s` argument
  and record that literal in a private witness file. Missing, duplicated or
  changed grace arguments fail the fixture. Inspect monitor options only
  before the first `--`; reject extra grace options even alongside a valid
  one. Use a closed list of the runner's existing monitor options, rejecting
  alternate GNU grace spellings too. Payload after the delimiter is unchanged.
- Substitute `--kill-after=0.01s` only in the test's delegated argv, then
  exec the real GNU timeout with every other argument unchanged. No shell
  controller or added child owner remains in between.
- Keep the real1s initial deadline and the original TERM-ignoring child.
  Genuine GNU TERM/KILL escalation and its actual137 status still occur.
- Assert the observed5s production argument in addition to every old case
  assertion. Do not fabricate statuses, timeout diagnostics or receipts.

This explicitly proves production argv configuration plus genuine escalation
under a shortened UNIT-ONLY grace; it does NOT prove a real5s elapsed grace.
The separate natural timeout124 case remains unscaled. Do not describe the
shim as an unchanged production invocation or independent release evidence.

Write scope is only `scripts/check_run_budgeted.sh`, using its existing
private executable-fixture pattern. No public option/environment knob,
runtime primitive, dependency, standalone helper, process authority,
concurrent scheduler, test-result cache or grace-policy change is added.
Use a dedicated shim subdirectory, not the scratch root that later fixtures
put on PATH. PATH/witness state must not escape the one fixture. Keep argv as an
array and never eval a command string. Include focused shim failures for
wrong/missing/duplicate5s arguments and witness-write failure, plus payload
passthrough. These are subassertions: keep the original14case identities,
case counter and complete success stdout unchanged.

After both Gate A approvals, a bounded worker implements that one script.
The lead reviews the diff and native focused checks, then independent
trailing reviewers inspect actual evidence before any final acceptance.
Compare two ordinary unit runs against the retained baseline, with every
case still executing. Fold it into a later complete warm measurement; no
claim that this small slice alone closes the60s campaign goal.
