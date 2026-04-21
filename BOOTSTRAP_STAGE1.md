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

The first selfhost workspace now lives in `selfhost/` and can load, lex, shallow-parse, run top-level/import resolution, run a first body-level resolver slice, and diagnose its own module tree.

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

Stage1 is not self-hosting yet. The next work is semantic parity inside `selfhost/`:

- fuller body-level resolver parity beyond the current top-level/import slice
- type-checker parity
- stronger diagnostic fidelity
