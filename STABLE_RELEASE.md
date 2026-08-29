# Stable Linux Release Contract

## Purpose

Nauqtype's next program is a stable Linux release that is comfortable for
terminal tools and practical native application development while preserving
the language's AI-supervision mission. This is not a feature-parity race with
Rust, Python, Go, or shell.

The target is reached when developers can build, test, inspect, distribute, and
maintain real Linux programs without depending on the Nauqtype repository, the
archived Python compiler, or ad hoc shell glue for ordinary application logic.

## Stable Scope

### Linux terminal completeness

A stable terminal program must be able to:

- report compiler identity and discover command usage with stable exit codes;
- read arguments, environment values, current-directory state, and standard
  input, and deliberately write standard output or standard error;
- work with text and binary files, paths, metadata, directory entries,
  temporary locations, and atomic replacement;
- start a process with explicit arguments, working directory, environment,
  input, output mode, and bounded timeout/cancellation behavior;
- use wall and monotonic time for timestamps, deadlines, sleeps, and retries;
- parse and emit deterministic JSON without relying on a command-specific
  parser;
- use reusable collections needed by real tools without hand-written parallel
  lists for every lookup;
- expose all external authority through checked effect/evidence surfaces.

Shell remains appropriate for tiny bootstraps and packaging boundaries. A
Nauqtype program that merely delegates its logic to `sh -c` does not satisfy
this contract.

### Application-development completeness

The first stable application target is native command-line applications,
long-running services, reusable libraries, and applications built over explicit
platform bindings. A built-in GUI toolkit is not required for this release.

The application contract requires:

- manifest-authoritative workspaces, reproducible dependency locks, and stable
  package/module identities;
- reusable generic code sufficient for ordinary library and collection APIs,
  without implicit specialization or trait-style magic;
- explicit error boundaries that remain visible in facts and review evidence;
- a narrow, auditable C ABI/FFI boundary for Linux and existing native
  libraries;
- deterministic reclamation for owned heap-backed values before long-running
  service or task support is called stable;
- a bounded task/concurrency model with explicit cancellation and no hidden
  global executor;
- first-class tests, formatter write mode with comment preservation, editor
  diagnostics/navigation, and useful documentation generation;
- reproducible executable and library artifacts installable outside the source
  checkout.

## Engineering Rules

- Add a runtime primitive only when pure Nauqtype cannot implement the required
  operating-system boundary.
- Build ordinary path, process, JSON, collection, and testing conveniences as
  Nauqtype modules over those primitives.
- Every public capability receives canonical teaching examples, focused
  diagnostics, checked facts/review evidence where authority is involved, and
  copied-release coverage.
- Keep machine-readable v1/v2/v3 contracts stable. Incompatible changes require
  a new schema/version.
- Run a dense stress leg after every three completed milestones and before each
  release candidate.
- A stable claim requires no `stage1 limitation` path in the supported release
  corpus.
- Stable diagnostics carry truthful phase-specific codes, categories, source
  spans, and remediation data rather than a generic stage1 envelope.
- Release work has explicit time and peak-memory budgets. A passing but
  unbounded selfhost/proof path is a release defect.

## Milestone Sequence

### M52: Stable Contract And Agent Operating Gate

- install the repository-level multi-agent protocol;
- define terminal and application completeness without claiming broad GUI or
  ecosystem parity;
- lock the dependency-ordered release path and acceptance gates.
- restore executable metadata for every directly invoked Linux gate so CI can
  establish a real green baseline from a clean checkout.

### M53: Release Truth And Foundational Values

- add stable `help` and `version` behavior;
- replace generic/null-span stage1 diagnostics with truthful stable diagnostic
  identity and locations;
- add a byte-buffer type and one width-safe integer/duration representation
  before filesystem sizes, timestamps, or binary APIs depend on them;
- define and implement deterministic reclamation for owned strings, lists,
  bytes, file contents, and process output before adding long-running tasks;
- record and enforce initial compiler/test/proof time and peak-memory budgets;
- require a green clean-checkout Linux CI run before M54 begins.

### M54: Linux Input And Filesystem Foundation

- add current-directory, environment lookup, standard-input, path status,
  directory iteration, text/binary file, temporary-path, and atomic-replace
  primitives over the M53 value foundations;
- expose fixed checked IO evidence for each authority-bearing operation;
- provide pure Nauqtype path/filesystem modules and a real terminal-tool corpus.

### M55: Structured Process, Time, And Cancellation

- replace the narrow toolchain-only process call with a structured process
  contract supporting environment overrides, stdin, capture/inherit modes,
  timeout, and explicit termination;
- add wall time, monotonic time, and sleep/deadline primitives;
- prove deterministic cleanup and failure behavior on Linux.

### M56: Generic Reuse Foundation

- design one explicit generic model for functions and user types;
- lower deterministic monomorphized instances through checked handoff, IR, and
  C emission;
- avoid traits, implicit constraints, overload resolution, and method-driven
  dispatch in the first form.

### M57: Collections And Data Interchange

- build reusable map/set facilities on M56 with an explicit, checked key
  strategy;
- add a complete deterministic JSON value/parser/writer module;
- graduate helpers only through real terminal and application fixtures.

### M58: Native Library And Linux ABI Boundary

- define explicit C imports/exports, ownership at the FFI boundary, library
  search inputs, and link declarations;
- build both executables and reusable libraries;
- add one real Linux platform binding without making unchecked FFI ordinary
  Nauqtype code.

### M59: Bounded Applications And Daily Tooling

- add explicit task start/join/cancel and channel-style communication;
- keep scheduling authority visible and avoid an implicit global async runtime;
- prove shutdown, cancellation, and resource bounds in a service fixture.
- add comment-preserving formatter write mode;
- add editor diagnostics, definitions, references, and rename over the existing
  stable semantic identities;
- make Nauqtype-owned tests ergonomic for workspace authors;
- generate API documentation from checked declarations and audit contracts.
- enforce compilation, test, proof, service-memory, and editor-latency budgets.

### M60: Linux Packaging And Compatibility Freeze

- produce versioned archives and a conservative Linux package/install path;
- define supported host compiler/libc/platform ranges and upgrade behavior;
- verify clean installation, relocation, uninstall, and rollback outside the
  repository.
- add release checksums/signatures plus sanitizer and focused fuzz gates for
  runtime, parser, manifest, JSON, and FFI boundaries.

### M61: v1.0 Stable Linux Gate

- run seed bootstrap, selfhost proof, full owned tests, terminal/app corpus,
  copied release, ABI/FFI fixtures, stress leg, schema compatibility, install,
  upgrade, and rollback independently;
- freeze the supported source, runtime, evidence, workspace, and release
  contracts;
- publish only when the release has no known critical correctness or data-loss
  issue and no unsupported path is presented as stable.

## Release Evidence

Ordinary development uses the layered gates in `VERIFICATION.md`. Every release
candidate additionally requires independent runs of:

- `scripts/check_seed_bootstrap.sh`;
- `bin/nauqc test`;
- `bin/nauqc prove`;
- `scripts/check_linux_alpha.sh` or its stable successor;
- `scripts/run_stress_leg.sh`;
- the clean-checkout Linux CI workflow;
- diagnostics schema/code/span compatibility checks;
- terminal-tool and application-workspace compatibility matrices introduced by
  M53-M59;
- installation and relocation checks introduced by M60.

Agent summaries are not proof. The checked artifacts and exact command results
are the release record.
