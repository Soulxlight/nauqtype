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

The first stage1 structured checked handoff is now implemented, hardened for backend consumers, exercised by the stage1 borrow checker, consumed by stage1 IR lowering, and used as the required upstream truth for stage1 C emission.

It is currently built from the trusted selfhost semantic outputs after parse, resolve, and typecheck, and it is exercised by the in-repo handoff probes plus full-tree selfhost runs.

The implemented handoff currently captures:

- resolved module and function identities
- stable binding identities for params, locals, and typed pattern payload bindings
- top-level constant declarations for the narrow trusted const subset
- typed params, locals, returns, and assignment targets
- typed expression trees for the trusted subset
- recursive checked type-shape truth with canonical backend-facing `type_id` values, including origin-module truth for named types and `ref` vs `mutref` shape truth
- explicit `ref` / `mutref` borrow nodes instead of borrow-sensitive name reconstruction
- typed `if`, `while`, and `match` statement structure
- recursive checked pattern trees for the trusted pattern subset
- typed pattern bindings for the current enum / `option` / `result` subset
- resolved function / constructor / field targets
- resolved top-level constant targets
- stable source spans for downstream diagnostics and comparison work
- fail-closed export diagnostics for trusted-subset constructs that cannot be materialized into the checked handoff

This completes the boundary-definition and backend-readiness hardening step. Stage1 borrow checking, stage1 IR lowering, and stage1 C emission now run downstream of this representation rather than on raw flat facts. The first copied-selfhost stage1-to-stage2 self-build comparison proof is now complete on top of this boundary, so later work should not backslide into direct backend work on flat fact lists.

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
- typed top-level constants for the trusted const subset
- typed parameter declarations with stable parameter ordering carried through binding identity
- typed local declarations and assignment targets
- typed return sites
- typed assignment statements
- typed expression trees for the already-trusted subset
- typed control-flow blocks for `if`, `while`, and `match`
- typed pattern bindings for the current enum / `option` / `result` subset
- constructor targets with resolved origin
- function call targets with resolved origin
- top-level constant references with resolved origin
- field access nodes with resolved base type and resolved field target
- stable source spans carried through for downstream diagnostics
- truthful borrow bits and explicit borrow-node shape for `ref` / `mutref`

## Trusted Expression And Statement Scope

The handoff only needs to model the semantic subset already trusted in stage1.

That subset includes:

- literals
- local and top-level names in supported expression positions
- top-level constant declarations and references for the narrow `i32` / `bool` / `str` const subset
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

## First Self-Build Proof Contract

The first self-build proof reused the current downstream boundary instead of inventing a separate proof path.

Locked proof chain:

1. run `selfhost/main.nq` under stage0 in a copied workspace
2. capture the stage1-emitted `build/main.c`
3. compile that emitted C into a stage2 executable
4. run the stage2 executable on the same copied workspace
5. capture the stage2-emitted `build/main.c`
6. compare stage1 vs stage2 output by normalized structural C
7. also require matching smoke behavior: success exit, expected stdout, no `stage1 limitation`, and no `stage1 c error`

Comparison notes:

- the proof target is the in-repo copied selfhost workspace first
- normalized structural C is the parity target, not raw byte-for-byte text identity
- the proof harness should reuse the copied-workspace helper, emitted-C compile/run helper, and structural C normalization already present in the current tests
- keep stage1 and stage2 on the same copied workspace and existing `build/` directory because `write_file` is overwrite-only and does not create directories
- the shared structural C normalization now lives in the test support layer so proof and C-emission checks use the same normalization rules
- Windows serial execution, longer copied-selfhost timeout, and temp-dir cleanup friction should be treated as explicit harness constraints when the proof milestone is implemented

Current status:

- done for the first copied-selfhost target
- stage1-emitted and stage2-emitted `build/main.c` now match by normalized structural C on that target
- stage1 and stage2 smoke behavior now match on that target
- any broader proof hardening or wider proof targets remain future work

Backend work should not be planned directly against the current flat parser/typecheck facts.
