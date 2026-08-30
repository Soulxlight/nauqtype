# NQType Libraries: Upstream Response

Status: frozen M54 upstream contract from the Nauqtype compiler/runtime
workspace to the NQType Libraries workspace. All executable gates and the
required independent mixed-model audit are green.

This response distinguishes implemented contracts from the bundled-resolution
work that remains explicitly deferred. Nothing here transfers library-owned
implementation work into this repository.

## 1. Standard Library Identity And Resolution

### Active contract

- The intended official library workspace identity is `nauqtype.std`.
- `std` is a conventional dependency alias, not a reserved name and not a
  hidden prelude. A consumer must declare it explicitly.
- The initial manifest and lock use the existing `workspace/v1` and
  `workspace-lock/v1` path-dependency forms:

```json
{
  "version": "workspace/v1",
  "workspace": {
    "name": "example.tool",
    "source_roots": ["src"]
  },
  "dependencies": [
    {
      "alias": "std",
      "path": "vendor/std",
      "workspace": "nauqtype.std"
    }
  ]
}
```

- The canonical source spelling is explicit, for example `use std::path;`.
- `manifest_sha256` and `source_sha256` in
  `nauqtype.workspace.lock.json` are the exact dependency identity. Facts v3
  exports the same alias, workspace identity, path, and hashes.
- There is no semantic package-version field or automatic package fetch in
  M54. Adding one requires a versioned workspace/lock contract rather than a
  silent change to v1.

### Deferred bundled-resolution contract

The first proof uses an ordinary vendored path dependency at `vendor/std`.
The copied compiler release does not provide ambient or implicit library
resolution. A compiler-bundled source location and package-version contract
remain deferred to the installation/package milestone; NQType Libraries must
not freeze an API around an assumed release path yet.

## 2. `str`, `bytes`, UTF-8, And Linux Paths

### Active contract

- `str` is an immutable, length-carrying byte string with copy semantics. It
  is not guaranteed to contain valid UTF-8.
- `str_len`, `str_get`, and `str_slice` use byte offsets. `str_get` returns the
  byte value as `i32`; `str_slice` does not claim Unicode-boundary validation.
- `bytes` is an owned, move-only mutable-capacity buffer. Binary filesystem
  and stream primitives return or borrow `bytes` so ownership remains visible.
- UTF-8 validation, decoding, code-point traversal, and validated text wrappers
  belong to NQType Libraries. Runtime text-named primitives do not silently
  replace malformed data.
- Linux paths use `str` and therefore preserve arbitrary non-NUL path bytes.
  Every OS-bound path, program, environment-name, and prefix parameter rejects
  an embedded NUL with `io_err` kind `invalid_input`; truncation is never
  permitted.
- The public Linux lexical path library recognizes `/` only. Backslash has no
  separator meaning.

## 3. M54 Primitive Contract

The signatures below are implemented and have passed the executable M54 gate.
Existing builtins remain source-compatible.

```nauq
fn stdin_read() -> result<str, io_err>
fn stdin_read_bytes() -> result<bytes, io_err>
fn stdin_read_line() -> result<option<str>, io_err>
fn stdout_write(data: str) -> result<unit, io_err>
fn stdout_write_bytes(data: ref bytes) -> result<unit, io_err>
fn stderr_write(data: str) -> result<unit, io_err>
fn stderr_write_bytes(data: ref bytes) -> result<unit, io_err>
fn stdout_flush() -> result<unit, io_err>
fn stderr_flush() -> result<unit, io_err>

fn arg_count() -> i32
fn arg_get(index: i32) -> option<str>
fn env_get(name: str) -> result<option<str>, io_err>
fn current_dir() -> result<str, io_err>

fn read_file(path: str) -> result<str, io_err>
fn read_file_bytes(path: str) -> result<bytes, io_err>
fn write_file(path: str, data: str) -> result<unit, io_err>
fn write_file_bytes(path: str, data: ref bytes) -> result<unit, io_err>
fn path_metadata(path: str, follow_symlinks: bool) -> result<path_metadata, io_err>
fn read_dir(path: str) -> result<list<str>, io_err>
fn create_dir(path: str) -> result<unit, io_err>
fn create_dir_all(path: str) -> result<unit, io_err>
fn create_file_new(path: str) -> result<unit, io_err>
fn remove_file(path: str) -> result<unit, io_err>
fn remove_dir(path: str) -> result<unit, io_err>
fn rename_path(source: str, target: str) -> result<unit, io_err>
fn create_temp_file(directory: str, prefix: str) -> result<str, io_err>
fn create_temp_dir(directory: str, prefix: str) -> result<str, io_err>
fn atomic_write_file(path: str, data: ref bytes) -> result<unit, io_err>

fn str_from_bytes(data: ref bytes) -> str
```

`path_metadata` is a copyable compiler-known product:

```nauq
path_metadata {
    is_file: bool,
    is_directory: bool,
    is_symlink: bool,
    size: i64,
    modified_ns: i64,
    mode: i32,
}
```

On Linux, `mode` contains the permission and special bits (`st_mode & 07777`);
file-kind truth is carried by the three boolean fields rather than packed into
that integer. `modified_ns` is checked before conversion; a filesystem
timestamp outside the representable `i64` nanosecond range returns
`invalid_data` instead of wrapping or invoking signed-overflow behavior.

Ownership and behavior are fixed as follows:

- returned `str` and `path_metadata` values are copy-semantic;
- returned `bytes` and `list<str>` values are owned and move-only;
- a `ref bytes` argument is never consumed or retained;
- `arg_count` includes the executable at index `0`; `arg_get` returns `None`
  for every negative or out-of-range index;
- `env_get` returns `None` only when the name is absent and otherwise preserves
  the value bytes; `current_dir` returns the absolute current working directory
  reported by Linux;
- `stdin_read` and `stdin_read_bytes` read all remaining standard input;
- `stdin_read_line` removes one trailing line-feed, preserves every other
  byte, returns `None` only when EOF occurs before any byte, and never closes
  standard input;
- checked output writes add no newline and do not flush implicitly;
- output is stdio-buffered, so a delivery failure such as `broken_pipe` may
  surface from the write or the subsequent explicit flush; code that requires
  delivery evidence must check both results;
- whole-file reads consume the complete file; whole-file writes create or
  truncate the destination before writing the complete supplied value;
- directory entries are immediate base names, exclude `.` and `..`, and retain
  operating-system enumeration order; sorting is library-owned;
- ordinary reads and writes follow the final symlink;
- `path_metadata(path, false)` uses no-follow semantics and reports the link
  itself, while `true` reports the final target;
- `remove_file` removes a non-directory final entry, including a symlink,
  without following it; `remove_dir` removes only an empty directory;
- `rename_path` has Linux `rename` replacement semantics and reports
  cross-device failure rather than copying;
- temporary files are created exclusively with mode `0600`; temporary
  directories use mode `0700`; both are created in the requested directory;
  `create_temp_file` returns the path after closing the creation handle, so
  later reopen-by-path is not TOCTOU-safe. Sensitive multi-step composition
  should use a returned `0700` temporary directory until a checked file-handle
  capability is introduced;
- `atomic_write_file` uses an exclusive same-directory temporary followed by
  rename, replaces the final directory entry rather than following an existing
  final symlink, and promises atomic visibility only. It does not promise
  crash durability, metadata preservation, or cross-filesystem fallback;
- M54 exposes precise operations, not a sandbox or a TOCTOU-proof authority
  system.

## 4. Error And Checked-Authority Contract

All M54 fallible primitives continue to return `io_err`. No second filesystem
error hierarchy is introduced.

The source-visible stable accessors are implemented:

```nauq
fn io_err_kind(err: ref io_err) -> str
fn io_err_operation(err: ref io_err) -> str
fn io_err_path(err: ref io_err) -> option<str>
fn io_err_other_path(err: ref io_err) -> option<str>
fn io_err_os_code(err: ref io_err) -> i32
fn io_err_text(err: io_err) -> str
```

Stable kinds are `not_found`, `permission_denied`, `invalid_data`,
`already_exists`, `interrupted`, `cross_device`, `unsupported`,
`invalid_input`, `broken_pipe`, and `other`. M54 also maps narrow Linux
distinctions including `not_directory`, `is_directory`, and
`directory_not_empty`; these names may not be reused for a different class
later. Checked output writes and flushes suppress `SIGPIPE` only around their
own OS-facing operation so they can return `broken_pipe`, then restore the
previous process disposition; legacy print helpers and external processes are
not silently reconfigured. This relies on the current single-threaded runtime
and is not a future concurrency contract. `io_err_text` is human-facing and may
include host wording. Kind, operation, paths, and OS code are the machine-facing
contract.

No M54 text primitive validates UTF-8, so malformed byte sequences do not emit
`invalid_data`. The kind is used only when an operation explicitly checks
external data, including an unrepresentable `path_metadata.modified_ns`, and
never to silently reclassify arbitrary `str` bytes.

The source-level authority declaration remains `effects(io)`. Facts v2 and
review v2 extend their existing fixed evidence enum without changing source
effects or adding user-defined atoms. Existing kind order is preserved, then
new kinds are appended:

```text
read, write, create_dir, process, arguments, environment, cwd, stdin,
stdout, stderr, metadata, traversal, create_file, temporary, remove, rename,
atomic_replace
```

## 5. Cross-Package Type Usability

### Active contract

- Directly imported functions, struct literals, enum variants, and patterns
  may use explicit module qualification.
- Import aliases are module aliases only.
- Public functions may accept and return dependency-owned product or enum
  types. Inferred values, field access, matching, and qualified constructors
  retain their checked origin.
- Type annotations currently use an unqualified type name. `module::Type` in
  a type position is not implemented and must not be taught as active syntax.
- Two visible modules exporting the same short nominal type name are rejected;
  the compiler never guesses by use site.

The collision-safe V1 rule is therefore that official library public nominal
types use a globally distinctive `Nq` prefix, for example `NqPath` and
`NqFileMetadata`. Qualified type annotations and qualification-only imports
remain a separate language milestone because parsing `module::Type` alone
would not fix today's unqualified-import collision.

## 6. Library Checking And Release Fixture

M54 owns a fixture at `tests/fixtures/m54_library_dependency/`. Its vendored
`std` dependency must export at least one function and one `Nq`-prefixed
nominal type. The consuming application must pass `check`, facts v3, review
v2, `build`, and `run`, then repeat from a copied Linux compiler release and a
copied workspace outside the source checkout.

M54 also changes `check` so a library module does not need a `main` function.
`emit-c`, `build`, and `run` continue to require an executable entrypoint.

The smallest supported library-work commands are:

```bash
bin/nauqc check tests/fixtures/m54_library_dependency/vendor/std/src/status.nq
bin/nauqc check tests/fixtures/m54_library_dependency/src/app/main.nq
bin/nauqc facts tests/fixtures/m54_library_dependency/src/app/main.nq --format v3
bin/nauqc review tests/fixtures/m54_library_dependency/src/app/main.nq --format v2
bin/nauqc build tests/fixtures/m54_library_dependency/src/app/main.nq -o build/m54-library
bin/nauqc run tests/fixtures/m54_library_dependency/src/app/main.nq
```

## Freeze Gate

The executable portion of the M54 freeze gate is green:

- `python3 -m unittest tests.test_m54_runtime tests.test_m54_library_dependency -v`
  passes all nine focused runtime, ownership, evidence, and dependency tests,
  including explicit-borrow, forwarded-borrow, forbidden borrow-storage,
  owned-call rejection, borrowed-to-owned move rejection, mutable-source
  enforcement, safe copy reads through borrows, mutable-borrow forwarding, and
  timestamp-boundary regressions;
- strict C11 `-Wall -Wextra -Werror -pedantic` runtime compilation passes;
- `scripts/check_fast.sh` prints `nauqtype test ok`;
- `scripts/check_milestone.sh` passes stage1 rebuild, seed fixed point, full
  proof, copied Linux release, stress leg, owned tests, and address/leak
  sanitizers in 2,128 seconds, with every checked wall/RSS budget green;
- the copied-release phase runs both `m54_runtime.nq` and the locked vendored
  `nauqtype.std` application outside the checkout.

The primitive names, error accessors, evidence additions, and fixture are
frozen. The required independent GPT-5.6 primary and GPT-5.5 adversarial M54
audits both returned `PASS` on the tree that produced this gate evidence.
