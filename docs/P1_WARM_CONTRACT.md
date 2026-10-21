# P1 Warm-Tier Amendment

Proposed for independent pre-implementation review, 2026-10-19. This amends
[P1-P4](P1_P4_CONTRACT.md); its coverage, authority, goals and audit rules stay.

## Measured Pressure

The serial current baseline passed: ordinary checks 291.72s/289.05s on the
same hashed inputs. Warm tier components were cache validation 2.83s, owned
fixtures 76.03s, provenance 66.20s, attestation 19.49s, and budgets 8.69s.
The complete interval is recorded separately. The provenance fixture contains
the known 30s wait; removing that wait alone cannot meet the <=60s goal.

## Two Bounded Changes

1. Coalesce redundant metadata reads in `scripts/provenance.sh`, without
   caching metadata across calls. One private helper validates the same
   readable regular file and physical parent chain, reads mode/size in one
   GNU stat operation, and emits a fixed internal pair. `prov_regular` keeps
   its existing silent success/failure contract; `prov_mode` and file framing
   use the same checked observation instead of two/three separate stat calls.
   Keep canonical framed bytes/digests, allowed modes/paths, symlink rejection,
   unreadable-bit checks, error propagation, and all mutation checks intact.
   Do not cache source digests or remove pre/post reads. Add direct old/new
   predicate, mode and framing oracles; retain every existing assertion.
2. Add a Nauqtype-owned compile-only cache for the existing integer, allocation,
   string-join and process/time fixture helpers. Cache no test result or
   compiler semantic/evidence output. Emission, native execution, diagnostics,
   expected stdout/stderr/exit checks and sanitizer runs still happen every
   time. Do not change `host_c.nq`, public build/run, proof/corpus/seed/release
   compilation, flags, macros, profiles or phase coverage.

## Fixture C Cache Contract

- Default direct `nauqc test` remains fresh. The local warm `check_fast.sh`
  opts into the private `NQ_TEST_REUSE_C=1` mode; explicit zero disables it.
  Reject unknown values. The complete milestone owned-tests invocation
  explicitly sets zero, preserving its cold/fresh compile boundary. Document
  this distinction; cached fixtures are not independent release evidence.
- Only owned fixture compilation helpers call the new module. Inputs are
  captured from actual files, not timestamps or names. Bind the exact argv,
  physical cwd, producer executable, physical CC path/executable/version/
  target, relevant compiler environment, C source, all declared local includes
  (at least runtime.c/runtime.h for these helpers), and output executable bytes.
  Audit the actual fixture include sets before wiring them. Unmodeled volatile
  input or failed identity checks must never cause reuse; use a real fresh
  compilation or fail closed. No arbitrary dependency discovery engine.
  For environment identity, hash the complete inherited NUL-delimited `env -0`
  output in memory; never persist or print its raw values. Do not maintain a
  guessed list of influential variables. Bind physical cwd independently.
  Volatile date/time/timestamp macros in captured local input disable reuse.
  System headers/linker libraries remain within the disclosed stable-host
  toolchain assumption, as with the existing compiler cache.
  Use the existing M55 pipe-based `process_start`/`process_wait` route with a
  finite output cap and deadline for environment capture and SHA-256 stdin.
  Legacy `run_process` and `workspace_sha256_captured` use temporary files and
  must not receive raw environment bytes. No raw-value logging or filesystem
  fallback is permitted. Resolve the actual `cc` selected by PATH, not `$CC`.
- Use deterministic length-framed input identity and a small exact canonical
  receipt, not a general JSON/schema engine. A hit requires a regular,
  nonsymlink executable, a matching successful producer receipt, matching
  current inputs and matching output bytes. Otherwise invalidate and compile.
- Only successful empty-output compiler invocations may publish reusable
  success. Validate inputs/CC before and after compilation, verify artifact
  identity, publish atomically only on success, and never leave a valid-looking
  receipt on compiler failure or persistent input drift. Publication failure
  cannot claim reusable success. Preserve original nonzero compiler results.
- Mutable outputs stay in their existing private build directories. Do not
  share proof workspaces or let a fixture cache bless a stage1 compiler.
  Record hits/misses for the measurements without changing locked success text
  or claiming that cached C was freshly compiled. Stable-host toolchain trust
  is the same bounded assumption as the existing checked compiler cache, not
  a claim to attest the whole OS against a malicious owner.
- Tests must exercise actual helper logic for hit/miss, argv/profile/source/
  include/CC/cwd/producer invalidation, missing or modified executable,
  malformed/stale receipt, unsafe artifact shape, compiler failure,
  persistent drift and publication failure. Synthetic cases remain labeled
  unit/stub evidence; also validate the real GCC warm path and unchanged
  sanitizer/runtime behavior. Every probe executes regardless of cache hits.

## Ownership And Acceptance

### Include Closure And Replacement Decisions

The four compile helpers' complete local closure is the primary C source,
`stdlib/runtime.c`, and `stdlib/runtime.h`. Preserve each exact argv: native
allocation/string-join probes quote `runtime.c`; process probes quote
`../../../stdlib/runtime.c`; generated C quotes `runtime.h` and separately
links runtime.c. Require the expected source-local runtime.c/runtime.h
shadow to be absent for each quote-search case. Verify these absences on hits
and before/after compilation, not only their current state. Require stdlib's
entry set to remain exactly its two checked regular nonsymlink runtime files,
so a new stdlib header/subdirectory cannot shadow a system include. Tests add
earlier-search-path runtime.c/runtime.h and stdlib shadow entries.

Also require source-local `runtime.c.gch` and `runtime.h.gch` to be absent
on initial capture AND every confirmation, including the validated-digest
path. Files, directories and symlinks all decline reuse. GCC can consume a
PCH even without the ordinary source-local header; stdlib's exact-entry check
also excludes its sidecars. Test actual valid PCH introduction/removal with
changed program behavior, plus explicitly labeled manual completion faults.
Keep the v2 identity domain and fresh-compile fallback unchanged. The private
allocation test defines accept only optional-minus digit strings, captured
verbatim; volatile macros or expressions are not modeled fixture arguments.

Decline reuse for unknown quoted includes/include-next/volatile macros or
unrecognized argv options. Also decline it whenever CPATH, C_INCLUDE_PATH,
CPLUS_INCLUDE_PATH, OBJC_INCLUDE_PATH, LIBRARY_PATH, COMPILER_PATH,
GCC_EXEC_PREFIX, CFLAGS, CPPFLAGS or LDFLAGS is present, even empty; hashing a
search-directory name does not capture files in that directory. Fresh real
compilation remains available. Do not attempt arbitrary include discovery.
Also decline reuse for `LD_PRELOAD`, `LD_LIBRARY_PATH`, `LD_AUDIT`,
`DEPENDENCIES_OUTPUT`, `SUNPRO_DEPENDENCIES`, and any `GCC_`, `COLLECT_`,
`CCACHE_` or `DISTCC_` environment key. This covers dynamic-loader inputs,
extra compiler outputs and unmodeled compiler configuration such as
`GCC_COMPARE_DEBUG`; add direct refusal cases. Do not cache an unsupported
compiler wrapper/configuration by assuming its environment is inert.

Implementation restriction: warm reuse currently supports only the packaged
Ubuntu24.04 x86-64 GCC13 driver at `/usr/bin/x86_64-linux-gnu-gcc-13`, also
resolved from `/usr/bin/cc`. A differently located or named ELF wrapper is
not equivalent authority. Other compiler/environment configurations retain
fresh compilation. The include recognizer is deliberately conservative:
reject macro includes, alternate directive spellings, line-spliced includes,
digraphs/trigraphs, unknown directives and unlisted angle headers; only the
current literal runtime includes and fixed standard-header set are eligible.
Eligibility is LF-only: any physical CR byte declines reuse and still allows
fresh compilation. LF splicing is considered before checking directive and
volatile identifiers, while hashes continue to bind original source bytes.

Producer identity repair proposed for review: hash the running image through
the fixed Linux `/proc/self/exe` path using direct in-process byte IO, not a
child helper's self path and not only `argv[0]`'s current on-disk contents.
Keep invoked physical origin plus kernel-image bytes in the key. This narrow
kernel-owned self-image exception does not relax source/output/receipt path
checks. If unavailable, decline reuse. Test an atomic on-disk replacement
after launch: the old running image must not publish the replacement image's
identity, and the newly launched image must miss the old producer receipt.
Use new private `fixture-c-input/v2` identity framing and `fixture-c/v2`
receipt marker. A complete v1-marker receipt must reject even with otherwise
matching input/output hashes; old pathname-derived receipts cannot migrate
silently into the repaired producer-image trust domain. No public JSON
schema or command-format version changes.

Proposed invocation-local optimization: initial identity capture validates
the modeled C directive closure. Confirmation may skip repeating that parser
ONLY after freshly recapturing every key input and proving the full digest
equals that initially validated digest. Fresh source-local shadow absences,
stdlib entry membership, source/parent safety, compiler/environment/image
bytes and artifact readback remain mandatory. No cross-call/run semantic
cache or trusted receipt substitution. A newly introduced shadow header must
still invalidate completion even when every captured file byte is unchanged.

Each of the four existing public fixture gates acquires an atomic directory
lock in its existing private build directory and holds it across its entire
compile-and-run body in BOTH fresh and warm modes. Preserve its signature and
checks through a private implementation wrapper. A second writer or stale
lock fails closed; do not guess that an existing lock is stale or remove it
automatically. Always release on normal success/failure. A process crash may
require explicit operator recovery after checking no writer is active. Cache
unit probes use independently created private directories. No fixture
execution may race another producer replacing the same output.

Validate every ancestor under the physical repository root as a nonsymlink
directory, and validate source/output/receipt/lock relative paths. Reject
unsafe parents, nonregular existing artifacts and symlinks, rather than
following them. A miss invalidates the previous receipt AND removes the old
checked regular executable before invoking the unchanged compiler argv.
An exit-zero compiler that produces no new executable is a hard failure.
On compiler failure/drift no valid receipt may survive. After successful
stable-input compilation, hash/check the new executable, atomically publish
the exact receipt, and verify receipt/artifact readback while the workspace
lock is still held. Publication failure fails closed. Record only bounded
hit/miss/hash metadata, never raw environment. Add no locking runtime API.

Lead: `scripts/provenance.sh`, metadata/timeout fixtures in
`scripts/check_m54_10_provenance.sh`, `scripts/check_milestone.sh`, integration,
measurement, docs and final gate. After the feedback worker returns, the lead
adds only the private cache-mode selection to `scripts/check_fast.sh` and
registers cache tests/captured sources in `selfhost/proof.nq`.

Sol high worker, after its checked-index handoff is reviewed: new narrow
`selfhost/fixture_c.nq` (including bounded internal cache probes), plus only
the compile helpers in `selfhost/integer_policy_tests.nq`,
`selfhost/allocation_policy_tests.nq`, `selfhost/str_join_tests.nq`, and
`selfhost/process_tests.nq`. No semantic models, runtime, host build helper,
seed, schema or unrelated test changes. No commits, pushes or descendants.

Measure warm complete and cold complete separately, including validation and
publication. The cold seven-phase gate must remain fresh and follow trailing
audits; the warm result never substitutes for it. If these changes still miss
the goals, report the gap instead of renaming a partial tier complete.
