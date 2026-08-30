# NQType Libraries: Upstream Needs

Status: coordination request from the NQType Libraries owner to the NauqType
compiler/runtime owner.

## Library Workspace

The canonical library-owned workspace is:

`/home/soulxlight/Documents/NQType-Libraries`

The NauqType Codex may read that workspace for integration context, but should
not implement or modify library-owned modules there. Upstream compiler/runtime
answers and fixtures remain owned by the NauqType repository.

## Ownership Boundary

NQType Libraries owns reusable NauqType-native library modules, their public
APIs, library-specific examples, documentation, and tests.

The NauqType Codex owns the language, compiler, checked handoff and IR, C
emitter, runtime primitives, builtin contracts, workspace resolver, release
layout, and language-level evidence schemas. NQType Libraries will not modify
those upstream surfaces unless ownership is explicitly reassigned.

The first intended library tranche is the terminal foundation:

- pure modules: text, UTF-8, integer conversion, and lexical Linux paths;
- authority-bearing wrappers: standard input/output, arguments/environment,
  current-directory access, and filesystem operations;
- a small command-line parser built over the argument and text modules.

Process/time, user-defined generic collections, complete JSON, FFI bindings,
networking, and concurrency are not required to unblock this tranche.

## Minimum Upstream Decisions Needed

Please provide one written upstream contract covering the items below. Exact
names may differ, but the semantics and ownership boundaries need to be
explicit before NQType Libraries freezes public APIs.

### 1. Standard-library identity and resolution

Define how a shipped native library workspace is resolved without introducing
a hidden prelude or an ambient search path.

NQType Libraries needs:

- the canonical workspace/package identity and whether `std` is a reserved or
  merely conventional dependency alias;
- the manifest and lock representation for a compiler-bundled library;
- the canonical import spelling, for example `use std::path;`;
- how the library version and source hash appear in facts, locks, and release
  evidence;
- where library sources/manifests live in the copied Linux release; and
- whether the initial proof should use an ordinary vendored path dependency
  before bundled dependency resolution exists.

### 2. `str`, `bytes`, UTF-8, and path semantics

Freeze or explicitly mark provisional:

- whether `str_len`, `str_get`, and `str_slice` use byte offsets or Unicode
  code-point offsets;
- whether every `str` is guaranteed to be valid UTF-8 or may contain arbitrary
  bytes;
- the required behavior when a text file, environment value, or path is not
  valid UTF-8;
- whether Linux paths use `str`, `bytes`, or a distinct nominal path/OS-string
  type; and
- whether the public Linux path library recognizes only `/` as a separator.

The current runtime is byte-indexed. NQType Libraries can build a separate
UTF-8 module over that model, but it will not publish code-point claims until
the upstream contract says which model is authoritative.

### 3. M54 primitive signatures and guarantees

Provide the exact source-level names, parameter types, return types, ownership
behavior, and failure guarantees for the narrow primitives underlying:

- reading standard input as text and bytes;
- intentional standard-output and standard-error writes/flushes;
- argument collection, environment lookup, and current-directory lookup;
- text and binary whole-file reads/writes;
- path metadata with explicit follow-symlink versus no-follow behavior;
- directory entry collection;
- directory/file creation, removal, and rename;
- secure temporary file/path creation; and
- atomic replacement, including whether the contract promises only atomic
  visibility or also crash durability.

Runtime primitives should expose only the OS boundary. Sorting directory
entries, lexical path manipulation, text validation, convenience composition,
and CLI parsing will remain NauqType library code.

### 4. Error and checked-authority contract

NQType Libraries needs to know:

- whether M54 continues to return `io_err` for every operation or introduces
  additional nominal error types;
- the stable way to distinguish not-found, permission, invalid-data/UTF-8,
  already-exists, interrupted, cross-device, and unsupported failures;
- whether errors retain the operation and path involved; and
- the additive checked IO subkinds and their canonical evidence order for
  stdin, environment, cwd, metadata, traversal, temporary creation, removal,
  rename, reads, and writes.

Library wrappers will declare `effects(io)` and rely on transitive checked
evidence from the primitive calls. They will not invent source-level effects
or infer authority from names.

### 5. Cross-package type usability

Confirm the supported spelling for types, enums, and functions exported by a
library dependency. In particular, state whether the first library tranche
may rely on:

- module-qualified type annotations;
- qualified enum variants and struct literals;
- explicit module aliases;
- two dependencies exporting the same short type name; and
- public functions returning a library-owned product or enum type.

If qualified type annotations remain deferred, prescribe the collision-safe
V1 naming/import rule NQType Libraries must follow.

### 6. Library checking and release fixture

Provide one canonical upstream-owned fixture that proves:

1. a workspace imports a locked library dependency;
2. the library exports at least one function and one nominal type;
3. the consuming program passes `check`, facts/review evidence, `build`, and
   `run` through stage1;
4. the same program works from the copied Linux release outside the source
   checkout; and
5. a library module can be checked without pretending it is an executable
   entrypoint, or the accepted V1 harness pattern is documented.

Please include the smallest supported verification commands for library work.
NQType Libraries will own library behavior tests after this upstream fixture
establishes the integration contract.

## Concrete Unblock Package Requested

NQType Libraries is ready to proceed when the NauqType Codex supplies:

1. a written answer to Sections 1-5, either in a new
   `NQTYPE_LIBRARIES_UPSTREAM_RESPONSE.md` file or an explicitly linked
   upstream contract;
2. the M54 primitive declarations needed by the first tranche, with their
   compiler/runtime implementation owned and verified upstream;
3. the canonical locked-dependency/copy-release fixture from Section 6; and
4. notice of any upstream contract still intentionally provisional so the
   library API can remain experimental rather than accidentally stable.

## Work NQType Libraries Can Start Independently

Before the M54 primitives arrive, NQType Libraries can prototype the following
against current stable language behavior, provided the package-resolution and
`str` decisions above are answered first:

- byte-oriented text search/splitting helpers;
- UTF-8 validation and decoding helpers;
- checked `i32`/`i64` parsing and deterministic rendering;
- pure lexical Linux path components and joining; and
- CLI data types and parsing over an explicitly supplied `list<str>`.

These prototypes will remain library-owned and will not be copied into the
compiler/runtime as new builtins.

## Response Discipline

Please answer with exact contracts, fixture paths, and commands rather than a
general milestone summary. If an answer depends on unfinished M54 work, mark
it `provisional` and name the upstream acceptance gate that will freeze it.

Do not implement NQType Libraries modules in the NauqType compiler/runtime
workspace. Once the upstream unblock package is ready, the NQType Libraries
owner will begin the library tranche in the canonical workspace named above.
