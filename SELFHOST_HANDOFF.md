# Selfhost Structured Checked Handoff

## Purpose

This document defines the required downstream representation between the trusted stage1 semantic front end and all later genuine-parity work.

The current selfhost parser/resolve/typecheck pipeline is accepted as the truth-producing semantic front-end path for the trusted subset. It is not the direct substrate for stage1 borrow checking, IR lowering, or C emission.

The structured checked handoff is the one-way bridge from:

- flat semantic facts that are convenient for the current selfhost front end

to:

- structured, typed compiler data that is suitable for backend growth

This is an architecture checkpoint, not a parser/typechecker rewrite.

## Current Status

The first stage1 structured checked handoff is now implemented and hardened for backend consumers.

It is currently built from the trusted selfhost semantic outputs after parse, resolve, and typecheck, and it is exercised by the in-repo handoff probes plus full-tree selfhost runs.

The implemented handoff currently captures:

- resolved module and function identities
- stable binding identities for params, locals, and typed pattern payload bindings
- typed params, locals, returns, and assignment targets
- typed expression trees for the trusted subset
- explicit `ref` / `mutref` borrow nodes instead of borrow-sensitive name reconstruction
- typed `if`, `while`, and `match` statement structure
- typed pattern bindings for the current enum / `option` / `result` subset
- resolved function / constructor / field targets
- stable source spans for downstream diagnostics and comparison work
- fail-closed export diagnostics for trusted-subset constructs that cannot be materialized into the checked handoff

This completes the boundary-definition and backend-readiness hardening step. The next implementation step is stage1 borrow checking on this representation, not more backend work on flat fact lists.

## What The Flat Pipeline Owns

The current flat selfhost pipeline is allowed to own:

- flat-root project loading for the current stage1 model
- lexing and parsing of the trusted subset
- top-level and body-level resolution for the trusted subset
- trusted-subset type checking and limitation diagnostics
- the semantic truth needed to build the downstream handoff

It is not allowed to become the long-term direct substrate for:

- stage1 borrow checking
- stage1 IR lowering
- stage1 C emission
- stage1 self-build proof logic

## Required Consumers

The structured checked handoff is the required input for:

- stage1 borrow checking
- stage1 IR lowering
- stage1 C emission

Any genuine-parity work after semantic near parity must target this representation instead of depending directly on ad hoc flat parser/typecheck fact lists.

## Minimum Required Contents

The handoff must include, at minimum:

- resolved module identities
- resolved function identities
- stable binding identities for params, locals, and typed pattern bindings
- typed parameter declarations
- typed local declarations and assignment targets
- typed return sites
- typed assignment statements
- typed expression trees for the already-trusted subset
- typed control-flow blocks for `if`, `while`, and `match`
- typed pattern bindings for the current enum / `option` / `result` subset
- constructor targets with resolved origin
- function call targets with resolved origin
- field access nodes with resolved base type and resolved field target
- stable source spans carried through for downstream diagnostics
- truthful borrow bits and explicit borrow-node shape for `ref` / `mutref`

## Trusted Expression And Statement Scope

The handoff only needs to model the semantic subset already trusted in stage1.

That subset includes:

- literals
- local and top-level names in supported expression positions
- constructor expressions in supported positions
- supported direct calls
- field access
- struct literals
- parentheses
- unary `not`
- unary minus
- arithmetic
- comparisons
- `and` / `or`
- assignments
- `return`
- `if`
- bootstrap-track `while`
- `match` for the current trusted pattern subset

The handoff should preserve enough structure that downstream work does not need to reconstruct expression meaning from token spans or loose fact lists.

## Explicitly Out Of Scope

The handoff does not need to model:

- non-name callees
- member-call syntax
- deferred language features outside the current trusted subset

Those boundaries stay explicit until a later recorded design decision changes them.

## Design Constraints

The handoff should be:

- structured enough for backend work
- typed enough that borrow/IR/codegen do not need to re-derive semantic truth
- deterministic in ordering and identity assignment
- fail-closed when trusted-subset semantic facts cannot be exported
- stable enough to support later differential or self-build comparisons
- narrow enough to avoid turning into a second ad hoc front end

## Required Next Sequence

The genuine-parity sequence after this checkpoint is:

1. add stage1 borrow checking on the structured checked handoff
2. add stage1 IR lowering
3. add stage1 C emission
4. define the first stage1-to-stage2 self-build comparison proof

Backend work should not be planned directly against the current flat parser/typecheck facts.
