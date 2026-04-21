# Nauqtype Bootstrap Stage1

## Goal

Define the minimum post-alpha language expansion needed to begin a realistic self-hosted Nauqtype compiler.

## Locked Feature Order

1. Acyclic imports
2. File input as `result<str, io_err>`
3. Builtin `list<T>`

No other feature family should jump ahead of those three unless a concrete bootstrap blocker proves this order wrong.

## Acyclic Imports

Stage1 import scope:

- activate `use foo;`
- one workspace/package root only
- single source file still defines one module
- imported `pub fn`, `pub type`, and `pub enum` become visible across files
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
- construction, push, indexing/iteration strategy to be defined in the corresponding design pass
- no `map`, `set`, or `dict` before `list<T>` proves necessary and stable

## Relationship To AI Contracts

- `review` output should consume imported function audits once imports land.
- AI Contracts should remain small while Stage1 focuses on expressiveness needed for a self-hosted compiler.
- Do not let the AI-first differentiator stall bootstrap-critical work.
