# NauqType Language Charter

Status: approved by the owner 2026-10-31 (revision 4). Compiler lead.
Replaces `STABLE_RELEASE.md` (archived at
`docs/history/STABLE_RELEASE_2026-10.md`) as the definition of NauqType v1.0.
The independent reviewer (gpt-6.1-sol xhigh) returned REVISE on
revision 1 (twelve major, one minor), revision 2 (eight major, three minor)
and revision 3 (one major, three minor), then SOUND on revision 4 with two
wording nits, both applied.

Owner direction (2026-10-31): the goal is a language that is feature complete,
follows its own rules, makes logical sense and genuinely targets its
principles. It is not a Linux release, and it is not Rust with JSON and audits
bolted on.

## Identity

NauqType is a language for programs written by AI and supervised by people.
A NauqType program states, in its source, what authority it holds, what it
changes, how it can fail, and who owns what. The compiler checks those
statements, and review evidence is a reading of checked semantics rather than
an add-on report.

Evidence comes in four classes, and every evidence surface labels which one a
fact belongs to:

| Class | Meaning | Examples |
| --- | --- | --- |
| Checked | Derived from the program by the compiler; a contradiction is an error | mutation, may-effects, propagation, ownership transfers, capability use |
| Declared bound | Written by the author; the compiler checks the program stays inside it | a `pub fn` contract, a function type's contract |
| Unchecked | Written by the author; recorded verbatim, never validated | `intent` text |
| Template | Facts about a generic template before instantiation; structural only | uninstantiated generic bodies |

The language never claims more than its class allows. Compiler correctness
itself is established by the verification gates, not by the language.

Every feature serves the principles below or is the plainest way to write
ordinary code. A feature that resembles another language (Rust, Go, ML) is
kept only when it serves a principle; resemblance is never a reason.

## Principles

Unchanged from SPEC's Language Philosophy: predictable structure; explicit
behaviour; visible mutation; visible fallibility; visible ownership-sensitive
operations; low syntax ambiguity; strong compile-time checking; readable
generated code and diagnostics.

## Design Rules

Each rule is testable. A violation is a defect.

- **R1 Fail at check.** For the supported language on supported targets,
  every validity rule in the specification is enforced by `nauqc check`. An
  accepted program never fails in the C compiler, never reaches a
  "stage1 limitation" diagnostic, and never falls through to an undefined
  default (including a function that ends without returning).
- **R2 Canonical forms.** The specification lists, per construct, its
  canonical form and any intentional alternative with the reason for it (for
  example positional and named arguments; `[]` and `list()`). The formatter
  normalizes everything else. An unlisted second spelling is a defect.
- **R3 Visible authority.** External authority (files, processes,
  environment, clocks, standard streams, foreign code that requires it) exists
  only as capability values. Internal runtime services (allocation, task
  scheduling, channel synchronization) need no capability but are reported as
  effects where the charter says so.
- **R4 Visible ownership.** Ownership transfers of named places are written
  `move`. Lifecycle resources (processes, tasks, task groups, channel ends)
  must be explicitly consumed on every normal exit; permission values
  (capabilities) may be dropped.
- **R5 Visible fallibility.** Recoverable failure is `option`/`result`.
  Program termination has defined causes reported in evidence.
- **R6 Contracts at boundaries.** Every `pub fn` declares a contract, checked
  as a bound. Private functions are inferred, checked and shown.
- **R7 Explicit abstraction.** Reuse comes from explicit generics and plain
  function values. No closures, traits, interfaces, methods, overloading or
  implicit dispatch. A call through a function value is an explicit indirect
  call whose contract is bounded by the function type.
- **R8 One truthful evidence surface.** One current evidence format is the
  default, every evidence tool accepts every program the compiler accepts
  (including generics, function values and capabilities), and evidence is
  kept truthful as each feature lands, not repaired afterwards.
- **R9 No arbitrary asymmetry.** The specification carries a position
  matrix: for each construct (borrows, assignment, patterns, comparison,
  constants, calls, literals), the positions where it is legal. Every
  restriction in the matrix names the principle that justifies it.
- **R10 Measured mission value.** Each mission feature has a reviewer or
  authoring task with stated success criteria (for example: a reviewer
  identifies every file write in an unfamiliar program from evidence alone).
  A passing fixture is not enough.

## Semantic Commitments

These fix the meaning of the owner's decisions. Each area gets a design
record with Gate A review before implementation; the record may refine
details but not change these commitments without the owner.

### Naming and patterns (owner decision 2026-10-31)

- User-declared types, enum variants and type parameters are `UpperCamel`;
  functions, bindings, fields and modules are `snake_case`; constants are
  `UPPER_SNAKE`. The compiler enforces this. Builtin type spellings (`i32`,
  `str`, `list`, `option`, `result`, `bytes`, ...) keep their names and are
  exempt.
- In a pattern, an `UpperCamel` name is a constructor and must resolve to a
  visible variant; a `snake_case` name is a binding. A misspelled variant is
  an error, never a catch-all.
- Imported types are always written qualified (`json::Doc`); v1 has no
  selective item imports for types. One canonical rule, formatter-enforced.
  The `Nq` prefix convention ends.

### Ownership (owner decision 2026-10-31)

- `move place` transfers a non-copy named place: a local, parameter, or a
  field path of an owned local. It is required wherever a named non-copy place
  is transferred: owning call arguments, `let` initializers, assignment,
  constructor fields, `return`, and match scrutinees that consume. Temporaries
  (call results, literals, constructors) transfer without a marker.
- `move` on a place of a concrete copy type is an error (it would mean
  nothing). Inside a generic body, a type parameter is treated as non-copy for
  checking: transfers of `T` values are written `move`, and a moved `T` place
  cannot be reused. After instantiation with a copy type, such a `move` is a
  copy; this is the one place `move` applies to a copy value, and it is
  defined, not an error. Operations that the language checks per concrete
  instance today (comparison, `list_get`) keep that rule.
- A partial move (`move p.items`) leaves `p` unusable except for
  reassignment of the moved field; the design record fixes the exact rule.
- **Must-consume types.** Process handles, task handles, channel ends and
  other authority-carrying resources are must-consume. On every normal exit
  from their scope (fallthrough, `return`, `?` propagation, `break`,
  `continue`) each must have been transferred or passed to a consuming
  operation. Consuming operations distinguish two failures in their
  signatures and evidence: failure *before* consumption returns the live
  resource inside the error value; failure *after* disposal completed (for
  example M55's `process_wait` error after terminal cleanup) returns an error
  without ownership. Every must-consume type has a terminal disposal operation
  that always consumes (for a process: terminate, reap, report), so a caller
  can always discharge the obligation before returning. A product or enum
  holding a must-consume value is itself must-consume. Must-consume values
  cannot be stored in lists or maps in v1; dynamic sets of tasks use the
  builtin task group (Concurrency). Abnormal termination is exempt: the
  runtime's best-effort cleanup is documented, not guaranteed.

### Capabilities (owner decisions 2026-10-31)

- Capabilities are opaque values of builtin types: `Stdio`, `Env`, `Clock`,
  `Fs`, `FsRead`, `Proc`. They cannot be constructed or forged in NauqType
  code; the guarantee is language-level, not an OS sandbox, and does not
  extend across the FFI boundary.
- The runtime constructs them once and passes them to
  `fn main(caps: Caps) -> i32`, a product holding one of each. Libraries
  receive capabilities only as parameters.
- Capabilities are **permissions, not lifecycle resources**: they are
  move-only (never duplicated implicitly), used by borrow (`ref fs`), and may
  be dropped silently, so unused members of `Caps` need no disposal. A
  permission is duplicated only explicitly, by an attenuation call that may
  return the same authority (`fs_share(ref fs) -> Fs`), which is how a task
  receives its own copy. They may be stored in products and moved into tasks.
- **File authority types and attenuation.** Read operations take
  `ref FsRead`; write operations take `ref Fs`. `fs_reader(ref fs) -> FsRead`
  derives read-only authority from write authority (an explicit attenuation,
  not an implicit conversion). `fs_dir(ref fs, path) -> result<Fs, io_err>`
  and `fs_read_dir(ref r, path) -> result<FsRead, io_err>` narrow either kind
  to a directory subtree without ever adding write authority. Attenuation
  never widens authority, and narrowed handles are checked at runtime for
  path escape.
- Every M54/M55 authority builtin gains a capability parameter (for example
  `read_file(ref r, path)` with `r: FsRead`, `stdout_write(ref io, text)`).
  The design record lists every replacement signature.

### Effects and contracts (owner decision 2026-10-31)

- Evidence distinguishes **available** authority (capability parameters a
  function receives) from **may-effects**: the conservative, transitive set
  of effect operations the function can reach. Static checking establishes
  possibility, not execution. Each may-effect records its provenance:
  checked code, the declared bound of an indirect call through a function
  value, or a trusted foreign declaration.
- Effect atoms are per operation class: `stdio`, `env.read`, `clock`,
  `fs.read`, `fs.write`, `proc.spawn`, `proc.wait`, `proc.signal`,
  `task` (start, join, cancel), `chan` (send, receive, close), plus
  `terminate` (below). Tasks and channels touch no external system, so they
  need no capability, but they are effects and appear in contracts.
- A `pub fn` contract declares `mutates`, `effects` and `propagates` as an
  upper bound: underdeclaration is an error, overdeclaration a warning.
  Private functions need no declaration; their inferred contract appears in
  evidence. `intent` is required on `pub fn` and is unchecked (evidence
  class: Unchecked).
- **Termination** is reported with its cause: `terminate.arith` (division by
  zero, `MIN / -1`), `terminate.explicit` (an exit call), `terminate.limit`
  (documented size limits), `terminate.runtime` (unrecoverable resource
  cleanup failure, as M55 defines for process cleanup; attached to the
  operations that can raise it). Allocation failure and stack exhaustion are
  ambient: documented once in the specification, never attached to every
  function, so the atom stays informative. Termination is distinct from
  operation failure, which is always a returned `result`.

### Function values (owner decision 2026-10-31)

- A function type is written `fn(ref str, i32) -> i64` and may carry a
  contract bound: `fn(ref str) -> i64 effects(fs.read) mutates()`. Without a
  bound, a function type permits no effects, mutation of no parameter other
  than its `mutref` parameters, and no propagation.
- Values are named top-level functions, including generic instances
  (`hash_str`, `identity::<i64>`). No closures, no captured environment.
  Function values are copy and may be stored in products, lists and maps.
- Passing a function whose inferred or declared contract exceeds the
  function type's bound is a type error. A call through a function value
  composes into the caller clause by clause, so callbacks are never an
  inference blind spot: its **effects** bound joins the caller's may-effects
  (provenance: indirect-call bound); its **mutation** bound is stated over
  canonical parameter positions and maps through the actual arguments to the
  caller's places (named arguments normalized first; field and scoped element
  borrows attribute to their root); its **propagation** stays callee
  evidence, because the callback returns a `result` the caller handles, and
  caller propagation arises only from the caller's own forwarding `?`. An
  error captured by a local `try` boundary is local evidence and does not
  enlarge the enclosing function's `propagates` bound, exactly as today. The
  design record's acceptance cases cover each clause, including a callback
  error handled by `match` and one captured by `try`.
- Stateful callbacks use an explicit context parameter:
  `fn(mutref Ctx, ref T) -> bool`.

### Containers and recursive data

- Recursion is allowed through `list` and `Map`/`Set` edges (heap
  indirection), never by value or through `option`/`result` alone.
- Non-copy elements are accessed through scoped borrows, without
  reference returns: borrowing loops (`ref` and `mutref` element bindings)
  and a scoped indexed borrow statement in both `ref` and `mutref` forms
  (exact syntax in the design record). While an element borrow is live, the
  containing collection cannot be replaced, grown, shrunk, moved or borrowed
  mutably by any other path; nested field access and early exits
  (`return`, `break`, `?`) inside the scope are covered by acceptance
  fixtures. Together with `list_replace`/`list_pop` this makes trees, JSON
  values and ASTs usable without index arenas.

### Concurrency (owner decision: in v1)

- Structured tasks: `task_start` takes a function value and moved arguments
  and returns a must-consume task handle; `task_join` consumes it. Tasks
  cannot outlive their handle's scope. A builtin must-consume task group
  holds a dynamic number of tasks and is consumed by joining all of them.
- Channels are typed, with must-consume send and receive ends transferred by
  `move`. In v1 a channel payload cannot be a must-consume type, so closing
  or cancelling never strands a resource in a buffer.
- **Transfer guarantee:** only owned values cross a task boundary (arguments,
  results, channel payloads); borrows never do. Everything that crosses,
  recursively through products, enums and containers, must be race-free:
  values that share runtime state today (reference-counted `str`) get
  race-safe copy and drop semantics (mechanism in the design record).
  Capabilities move or are explicitly shared into tasks.
- No shared mutable state and no hidden executor. Cancellation is
  cooperative: a cancelled task observes it at channel operations and
  explicit checkpoints. Bounded shutdown is a join with a deadline; a task
  that does not finish in time leads to documented program termination
  (`terminate.runtime`), never to silent abandonment.

### Foreign functions and libraries (owner decision: in v1)

- C imports and exports are explicit declarations with required contracts;
  foreign code is a trust boundary marked in evidence (class: Declared bound,
  unverifiable inside foreign code). Capabilities may be required to call an
  import.
- Reusable NauqType libraries build as artifacts with provenance recorded in
  workspace locks.

## Carry-Forward Disposition

Everything the language supports today is kept unless listed otherwise.

| Feature | v1 |
| --- | --- |
| `bytes`, structured `io_err`, nominal time values, owned processes | Kept; authority builtins take capabilities |
| Statement `?`, local `try` boundaries, `propagates` | Kept; asymmetries fixed per R9 |
| Constants, record update `{ from base, ... }`, named arguments, list literals | Kept |
| Workspaces and locks `workspace-lock/v2` | Kept; a lock command is added |
| `facts`/`review` and related tools | Consolidated under R8 |
| M57.1 list builtins, comparison rules, field places | Kept |
| M57 plan requirements (deterministic insertion-ordered collections, exact JSON number rule) | Kept; maps become generic `Map<K, V>` built with explicit hash and equality function values |
| STABLE_RELEASE packaging, install/upgrade/rollback, platform matrix | After v1 |

New v1 additions beyond the semantic commitments (scheduled in M58 unless
noted): struct-like enum variants (M60, with the naming change); indexed and
range `for` loops; integer patterns on `i64` and `bool` patterns; `%`;
missing-return analysis.

## v1.0 Definition

v1.0 is reached when the language in this charter is implemented, R1-R10
hold for the supported surface, the compiler and standard library are written
in the final language (the checked-in C seed and C runtime remain the
intentional bootstrap boundary), and an independent audit against this
charter passes.

### Excluded, each with its reason

- Closures and captured environments: hidden state crossing call boundaries
  (R7); explicit context parameters cover the need.
- Traits, interfaces, methods, overloading: compiler-resolved dispatch the
  reader cannot see at the call (R7).
- Stored and returned references: would require lifetimes; scoped borrows
  cover access (R4).
- Generic inference: hides instantiation from the reader (explicit
  behaviour); turbofish stays.
- Implicit conversions, exceptions, inheritance, reflection, macros,
  async/await: each hides behaviour or control flow (explicit behaviour).
- Broad `?` sugar beyond statements and `try`: hides control flow (R5).
- Mixed named and positional arguments: two spellings in one call (R2).

### After v1

`f32`, unsigned integers, `char`, tuples, mutable strings, networking,
randomness, labelled or valued `break`, constant function calls, user-defined
effect atoms, typed holes, invariants and pre/postconditions, packaging and
multi-platform release.

## Bootstrap Bridge

Breaking source changes must keep a clean checkout buildable from the
checked-in seed. Each breaking milestone:

1. **Checkpoint A (publishable):** a bridge compiler, still written in the
   old source form, that accepts both the old and the new form of the changed
   construct (bounded and reviewed). Its seed is promoted, and clean-checkout
   reconstruction from that seed is proven.
2. **Checkpoint B (publishable):** the compiler's own source migrated to the
   new form (preferably by a formatter-driven rewrite), built by the
   checkpoint A seed; the seed is regenerated and promoted, and reconstruction
   plus a fixed point are proven.
3. **Checkpoint C (publishable):** the old form removed, seed promoted,
   reconstruction and fixed point proven again.

Every checkpoint is buildable from its own checked-in seed; no intermediate
commit depends on a locally retained executable. Each records its evidence as
a bootstrap-boundary milestone does.

## Sequencing

| Milestone | Scope | Size |
| --- | --- | --- |
| M57.1 | Library-enabling core | closing |
| M58 | Corrective sweep: missing-return analysis; every reachable stage1-limitation path; match/pattern and constant asymmetries; `%`; spec/grammar drift; diagnostics (duplicate parse errors, help in text output); R9 position matrix; formatter rewrite tooling for later migrations | Medium |
| M59 | Design records with Gate A: ownership (`move`, must-consume), capabilities and effects, function types and contracts, scoped element access, tasks/channels, FFI. Paper only. | Medium |
| M60 | Naming: case rule, constructor patterns, qualified type annotations; compiler-source migration through the bridge | Large, mechanical |
| M61 | Ownership: `move` and must-consume, with evidence | Large |
| M62 | Capabilities, may-effect inference, required `pub` contracts, termination evidence | Large |
| M63 | Function values with contract bounds; recursion through containers; scoped element access | Large |
| M64 | Evidence consolidation: implement generic-aware (and function-value and capability-aware) `review-diff`, `change-report`, `policy-check` and `refactor-rename` with acceptance tests; then make the current format the default | Large |
| M65 | Tasks and channels | Large |
| M66 | FFI and library artifacts | Large |
| M67 | Standard library: layout and provenance, text, numbers, UTF-8, `Map`/`Set`, JSON | Large |
| M68 | Tooling (`nauqc test`, lock command, formatter write mode) and R10 measurements | Medium |
| M69 | v1.0 charter audit and gate | Medium |

Evidence for each feature lands with the feature (R8): until M64, every
milestone documents which evidence consumers support its feature and which
conservatively reject it, consistently across SPEC and AI_CONTRACTS.

## Owner Decisions (2026-10-31)

Plain function values; capability values, scoped with directory and
read-only attenuation; required `pub` contracts; explicit `move` with
must-consume resources; capitalization rule for patterns; tasks and channels,
FFI and library artifacts in v1.

Proposed by the lead, confirmed by approving this charter:

- recursion through containers, with scoped `ref`/`mutref` element borrows;
- capabilities are droppable permissions, duplicated only explicitly;
  must-consume applies to lifecycle resources (processes, tasks, channel
  ends), each with a terminal disposal operation;
- v1 concurrency scope: a builtin task group for dynamic task sets, and no
  must-consume channel payloads;
- termination causes in evidence, including runtime cleanup failure;
  allocation and stack failure stay ambient;
- one consolidated evidence format with generic-aware consumers;
- imported types always qualified, no selective imports.
