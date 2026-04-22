# Nauqtype Stage1 Parity Plan

## Mission

Make the Nauqtype-written stage1 compiler front-end the long-term primary implementation by closing semantic parity with the Python stage0 compiler.

## Core Rule

Treat stage0 as a reference oracle while stage1 catches up:

- stage0 defines expected pass/fail behavior for the trusted subset
- stage1 must match stage0 behavior before broadening language surface
- differential coverage is required for every parity bugfix

## Parity Definitions

Parity is measured at three levels:

1. **Behavior parity**: accept/reject outcomes match for the trusted subset.
2. **Family parity**: error families match (`PARSE`, `RESOLVE`, `TYPE`, accepted limitation boundaries).
3. **Diagnostic parity**: stable error-code and span quality convergence (where stage1 has code-bearing diagnostics).

## Current Priority Backlog

### P0 (must close first)

- [ ] Eliminate behavior mismatches where stage0 accepts but stage1 rejects outside explicit limitation boundaries.
- [ ] Eliminate behavior mismatches where stage0 rejects but stage1 accepts.

### P1

- [ ] Extend stage1 type-checking from signature/arity/value-flow slices to fuller parity.
- [ ] Expand match-result typing and pattern-bound value typing.

### P2

- [ ] Improve diagnostic fidelity and consistency in stage1 output formatting/classification.

## Workstream Order

1. Expand and lock differential corpus first.
2. Implement stage1 parity slices in small batches.
3. Promote only when each batch is differential-clean.
4. Keep stage0 as shadow oracle until milestone cutover.

## Differential Suite Expectations

- Every parity bug needs a regression case in `tests/test_selfhost_differential.py`.
- Explicit limitation boundaries remain tracked as allowed stage1 outcomes only when intentionally retained.
- Environment-sensitive stage1 tests should skip with clear guidance when local bootstrap dependencies are missing.

## Cutover Criteria (Stage1 Primary)

- Zero known P0 mismatches in the trusted differential corpus.
- No unresolved P1 regressions across two consecutive full-suite runs.
- Stable stage1 behavior on selfhost performance smoke checks.
- Stage0 retained as fallback oracle, not primary development target.
