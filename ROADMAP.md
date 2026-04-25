# Nauqtype Roadmap

## MVP Definition

Nauqtype "compiles and runs code" when all of the following are true:

- a `.nq` program is lexed and parsed successfully
- names resolve
- a meaningful subset type-checks
- move/borrow rules are enforced for the supported subset
- the compiler emits readable C
- the emitted C is compiled by a system C compiler
- the produced executable runs successfully
- example programs and tests cover the path

## Bootstrap Terms

- `stage0`: the frozen Python bootstrap/reference compiler
- `stage1`: a compiler semantic front end and active executable driver written in Nauqtype and built by stage0
- `semantic near parity`: stage1 can load, parse, resolve, and type-check its own source tree for the trusted subset, with no retained limitation path used by the in-repo `selfhost/` tree
- `genuine parity`: stage1 adds borrow checking and backend work closely enough to participate in a real self-build proof chain
- `architecture checkpoint`: the current flat selfhost fact pipeline is accepted as the semantic front-end path, but backend work must target a downstream structured checked handoff instead of raw flat facts

## Working Vertical Slice

The first real success target is:

- one source file
- `fn main() -> i32`
- local bindings
- arithmetic and boolean expressions
- structs
- enums
- `result` / `option`
- `if`
- bootstrap-track `while`
- `match`
- explicit `return`
- `print_line`
- minimal move / borrow checking

## Milestones

### M0: Locked Design

- write research memo
- write spec, grammar, architecture, decisions, risks
- freeze v0.1 scope

### M1: Scaffold And Diagnostics Core

- create bootstrap compiler package layout
- add shared span and diagnostic types
- add CLI shape

### M2: Lexer And Parser

- tokenize the v0.1 grammar
- parse items, statements, expressions, patterns, and types
- add parser golden tests

### M3: Resolution And Type Checking

- resolve top-level and local names
- type-check functions, structs, enums, calls, returns, and matches
- emit stable semantic diagnostics

### M4: Minimal Ownership Enforcement

- classify copy vs move types
- detect use-after-move
- validate `ref` / `mutref` rules for calls

### M5: IR And C Emission

- lower checked programs to a small typed IR
- emit readable C
- include tiny runtime support

### M6: End-to-End Execution

- compile generated C with a detected system C compiler
- run example programs
- add integration coverage

### M7: Lints And Hardening

- `unused_mut`
- discarded `result`
- stabilize diagnostic wording

### M8: AI Contracts Alpha

- add fixed-shape `audit` blocks on functions
- infer `mutates(...)` from direct write-through `mutref` parameters
- infer `effects(print)` through the single-file call graph
- add deterministic `review` JSON output

### M9: Bootstrap Stage1

- activate acyclic imports for one workspace root
- then add file input as `result<str, io_err>`
- then add builtin `list<T>`

Status:

- done in the current bootstrap compiler
- `selfhost/` now exercises the stage1 surface by loading, lexing, shallow-parsing, resolving top-level/import facts, resolving a first body-level slice, and diagnosing its own module graph

### M10: Semantic Near Parity

- extend the Nauqtype stage1 front end beyond the first resolver and value-flow slices
- add trusted-subset stage1 body-level semantic parity
- differential-test stage0 vs stage1 by accept/reject family
- require the in-repo `selfhost/` tree to pass without `stage1 limitation` diagnostics
- keep the language core frozen unless a concrete bootstrap blocker requires otherwise

Status:

- done for the current semantic front-end milestone
- backend work has moved downstream of the structured checked handoff
- semantic near parity is now the trusted front-end checkpoint for the first self-build proof

### M11: Diagnostics JSON v1

- add `check --diagnostics json`
- ship a stable versioned JSON schema
- snapshot-test representative warning and error payloads

### M12: Flat-Architecture Checkpoint

- accept the current flat selfhost parser/resolve/typecheck pipeline as the trusted semantic front-end path
- explicitly forbid stage1 borrow/IR/codegen growth directly on raw flat facts
- define the structured checked handoff contract required for downstream genuine-parity work

Status:

- done as an architecture checkpoint
- the next parity work starts with the structured checked handoff, not direct backend work on flat facts

### M13: Genuine Parity Backend Path

- build the structured checked handoff from trusted semantic outputs
- harden the checked handoff for backend consumers
- add stage1 borrow checking
- add stage1 IR lowering
- add stage1 C emission

Status:

- done on the current trusted subset
- borrow checking now runs on the structured checked handoff
- IR lowering now runs on the structured checked handoff
- C emission now runs on the structured IR path

### M14: First Self-Build Proof

- run stage0 on a copied selfhost workspace to emit stage1 `build/main.c`
- compile the emitted stage1 C into a stage2 executable
- run the stage2 executable on the same copied workspace to emit stage2 `build/main.c`
- compare stage1-emitted vs stage2-emitted output by normalized structural C
- also require matching proof smoke behavior: success exit, expected stdout, no `stage1 limitation`, and no `stage1 c error`

Status:

- done for the first copied-selfhost target
- the proof reuses the copied-workspace smoke, emitted-C compile/run helper, and shared structural C normalization
- stage1 and stage2 now match on normalized structural C plus smoke behavior for the in-repo copied selfhost workspace
- broader proof hardening and any wider proof targets remain explicit future work, not implied by this first checkpoint

### M15: Nauqtype-Owned Driver Cutover

- freeze `compiler/`, `scripts/`, and the Python-heavy harness as bootstrap/reference code
- turn the selfhost executable into the active compiler driver
- first slice: `check` and `emit-c`
- second slice: `review`
- third slice: `build` and `run`
- keep the no-arg copied-selfhost proof path intact while the executable driver grows

Status:

- done for the active driver slice
- the stage1 executable now owns `check`, `emit-c`, `review`, `build`, and `run`
- the legacy no-arg selfhost path is preserved for the copied-selfhost proof flow
- the current `build` / `run` slice still resolves the pinned Zig toolchain and `stdlib/runtime.c` from the repo-root bootstrap layout

### M16: Nauqtype-Owned Proof And Corpus Runner

- replace the active Python proof/test orchestration with a Nauqtype-owned runner
- keep the copied-selfhost proof as a standing serial gate on Windows
- run the locked example corpus through emit/compile/run from the Nauqtype-owned runner
- preserve normalized structural C plus smoke-behavior comparison

Status:

- done for the active proof/corpus runner slice
- the Nauqtype-only transition loop is closed for active driver and proof/corpus orchestration
- the stage1 driver now owns the combined transition gate as `prove`
- the stage1 driver now owns the copied-selfhost proof gate as `prove-selfhost`
- the stage1 driver now owns the locked example corpus gate as `prove-corpus`
- `prove-corpus` runs the locked examples through `emit-c`, `build`, and `run`, compares normalized structural C across driver paths, and checks smoke behavior
- the current Python proof/corpus harness remains only as frozen bootstrap/reference coverage until a later archival cleanup pass

### M17: AI-First Review Surfaces

- extend `review` without breaking v1 consumers
- add stable semantic identities for functions and call sites
- expose call references and call graph edges for agent-pair workflows
- distinguish declared audit data from checked compiler inference
- add `review-diff` after the v2 identity surface is stable

Status:

- in progress
- `review --format v2` now emits stable function/call identities, references, call graph edges, and evidence fields
- `review-diff` now emits deterministic semantic changes over stable function identities and call graph edges
- next AI-first review slices are richer defs/refs graph exports and compiler-mediated semantic refactors

## Feature Ordering

Features required before first success:

- lexer
- parser
- diagnostics
- resolution
- type checker
- move/borrow checker
- C emitter
- runtime support
- executable runner

Features explicitly not required before first success:

- user-defined generics
- methods
- loop families beyond bootstrap `while`

## v0.2+ Candidates

- user-defined generics
- methods / `impl`
- `for`
- `break` / `continue`
- propagation sugar
- typed holes / repair obligations
- richer standard library
- stronger borrow analysis
- direct native backend exploration
- richer module/package tooling beyond flat-root imports

## Testing Milestones

- M2: lexer and parser tests
- M3: resolver and type tests
- M4: borrow tests
- M5: C emission goldens
- M6: full example execution tests
- M7: diagnostic and lint snapshots

## Diagnostics Milestones

- lexer spans present at M1
- parse diagnostics stable by M2
- type and resolve diagnostics stable by M3
- borrow diagnostics stable by M4
- lint diagnostics added by M7
- diagnostics JSON v1 added by M11

## Scope Freeze Rule

After M0, changes to core syntax or semantics require:

- a recorded decision entry
- a stated blocker or contradiction
- a stated impact on implementation and docs

## Backend Boundary

The current flat selfhost fact pipeline is allowed to own semantic front-end work for the trusted subset.

It is not allowed to own:

- stage1 borrow checking
- stage1 IR lowering
- stage1 C emission

Those phases must consume the structured checked handoff defined after the semantic near-parity checkpoint.
