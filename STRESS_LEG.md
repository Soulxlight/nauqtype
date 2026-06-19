# Nauqtype Stress-Leg Checks

Stress-leg checks are dense, temporary multi-module programs used to catch feature-composition failures that focused tests can miss.

They are not a replacement for goldens, differential tests, or the stage1-owned `prove` gate. When a stress leg exposes a bug, reduce it into a focused fixture before closing the milestone.

## Cadence

Run a stress leg:

- after every three completed milestones
- before any stable-surface declaration
- before any Linux release-layout checkpoint
- before any `v0.x` release checkpoint
- after dense language/tooling interactions have changed, even if fewer than three milestones have passed

## Required Surface

A dense stress leg should combine as many of these as the current language surface supports:

- imports across multiple flat-root modules
- records and record update
- enums and qualified variants
- list literals and list builtin calls
- `let-else`
- statement-boundary `?` with `propagates(...)`
- `while`, `break`, and `continue`
- qualified calls and named arguments
- `check`
- `review --format v2`
- `facts --format v2`
- `change-report --format v1`
- `fmt --check`
- `emit-c`
- `build`
- direct runtime execution of the built artifact

## Current Runner

Run:

```bash
scripts/run_stress_leg.sh
```

The script creates a temporary workspace under `/tmp`, writes a dense multi-module Nauqtype program, then runs the required stage1-owned commands through `bin/nauqc`.

As of M31, the runner also builds and verifies the copied Linux Alpha RC1 layout, copies that layout into the temporary workspace, and reruns the dense check/review/facts/change-report/fmt/emit/build/runtime path through the copied `bin/nauqc` launcher. This keeps stress coverage aligned with the Linux release layout instead of only proving the source-checkout launcher.

Expected final output:

```text
stress leg ok
```

## Reduction Rule

Do not keep a failed dense program as the only evidence for a compiler bug.

For each exposed issue:

- keep the temporary stress program only long enough to understand the interaction
- add a focused regression fixture or driver test for the smallest reproducer
- update `ROADMAP.md`, `TODO.md`, or `DECISIONS.md` if the finding changes milestone scope
- decide separately whether any successful stress program should become canonical corpus material

## M27 Closure

The first Linux stress leg exposed two compiler bugs and one evidence-surface gap. Those are now reduced to focused stage1 driver tests:

- qualified enum constructors in match expressions participate in exhaustiveness
- nested qualified calls used directly as call arguments stay positional
- propagation contracts/sites appear in facts, review, and change-report evidence

The dense stress runner remains as milestone hygiene. It should be used periodically, not added blindly to every fast test run.

## M31 Closure

Stress-Leg 2 extended the dense runner to cover the copied Linux Alpha RC1 launcher outside the repository root. The existing dense program passed through both the repo-local launcher and the copied release launcher.

No new compiler bugs were exposed in this leg, so there were no findings to reduce into focused fixtures. The added reusable coverage is the copied-release rerun inside `scripts/run_stress_leg.sh`.
