# Nauqtype Bootstrap Stage1

## Goal

Define the minimum post-alpha language expansion needed to begin a realistic self-hosted Nauqtype compiler.

## Locked Feature Order

1. Acyclic imports
2. File input as `result<str, io_err>`
3. Builtin `list<T>`

No other feature family should jump ahead of those three unless a concrete bootstrap blocker proves this order wrong.

## Current Status

The current stage0 compiler implements all three locked Stage1 unlocks:

- flat-root acyclic imports
- file input as `result<str, io_err>`
- builtin `list<T>`
- minimal bootstrap string helpers including `str_concat(left, right) -> str`

The first selfhost workspace now lives in `selfhost/` and can flat-root load its module graph, reject missing modules and import cycles, lex, parse, resolve, and type-check the current trusted subset across its own module tree.

Current trustworthy selfhost slice:

- recursive span-based typing for the current supported expression subset
- nested field-chain typing over supported base expressions
- contextual builtin typing for `Some`, `None`, `Ok`, `Err`, and `list()` in the current value-flow contexts
- match scrutinee typing and pattern-bound payload typing for the current enum / `option` / `result` subset
- explicit stage1 limitation diagnostics for unsupported expression shapes
- differential stage0-vs-stage1 coverage for the trusted subset
- the in-repo `selfhost/` tree itself runs with no `stage1 limitation` diagnostics

Current semantic near-parity milestone:

- stage1 is now trustworthy as a semantic front end for the trusted subset
- stage0 remains the semantic reference in the differential harness
- exact wording is not the parity target; accept/reject family is
- backend work is still outside this milestone

## Architecture Checkpoint

The current selfhost parser/resolve/typecheck design is accepted for the trusted semantic front-end milestone.

That means:

- the flat fact pipeline stays in place as the truth-producing front end for the trusted subset
- this is not a parser/typechecker rewrite checkpoint
- the current front end has earned the right to stay as the semantic source of truth

That does not mean:

- borrow checking should be added as more flat-fact logic
- IR lowering should target raw flat facts
- C emission should target raw flat facts

From this checkpoint onward, stage1 borrow checking, IR lowering, and C emission must consume a downstream structured checked handoff representation.

See `SELFHOST_HANDOFF.md` for the contract that now sits between semantic front-end parity and genuine backend parity.

## Acyclic Imports

Stage1 import scope:

- activate `use foo;`
- one workspace/package root only
- single source file still defines one module
- imported `pub fn`, `pub type`, and `pub enum` become visible across files
- imported public enum variants become visible as constructors/pattern names
- import cycles are rejected
- no package manager
- no re-export system

## File Input

Minimum file input goal:

- read a text file into `result<str, io_err>`
- no broad filesystem API surface
- no streaming API in the first pass

This is enough for a compiler to read source files without committing to a large runtime.

## Builtin `list<T>`

Minimum collection goal:

- one builtin growable sequence type
- `list()` requires expected `list<T>` context
- `list_push`, `list_len`, and `list_get` are builtin helper functions
- `list_get` is restricted to copy element types in stage1
- no `map`, `set`, or `dict` before `list<T>` proves necessary and stable

## Relationship To AI Contracts

- `review` output should consume imported function audits once imports land.
- AI Contracts should remain small while Stage1 focuses on expressiveness needed for a self-hosted compiler.
- Do not let the AI-first differentiator stall bootstrap-critical work.

## Immediate Remaining Gap

Stage1 is not genuinely self-hosting yet. The next work is beyond semantic near parity:

- stage1 C emission on that handoff
- stage1 self-build proof and stage2 comparison
- `review` v2 and richer machine-readable compiler surfaces after the current JSON diagnostics baseline
- retained explicit limitation boundary today: non-name callees and member-call syntax
