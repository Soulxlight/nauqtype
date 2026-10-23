# M56: Bounded Host-Compiler Memory Profile

Status: both independent supplemental Gate A reviews passed,2026-10-23.
The final producer, fault-fixture and milestone results are recorded separately
in AUDIT_REMEDIATION. M56's512MiB driver ceiling remains unchanged.

## Observed Blocker

The development M56 compiler C grows6.41% relative to P1-P4. GCC13.3.0 with
the unchanged C11/O2 recipe peaks at559888KiB (48.15s compilation), above the
524288KiB ceiling. This is development evidence, not a milestone pass.

A diagnostic compilation of the exact same C/runtime with
`--param=ggc-min-expand=20 --param=ggc-min-heapsize=32768` peaks at363896KiB
in49.87s. Its ELF is byte-for-byte identical and accepts the imported generic
composition. These are a single diagnostic pair, not an overall gate speedup.
GCC's queried defaults on this host are100/131072. The proposal changes host
compiler collection policy, not optimization level, Nauqtype semantics, runtime,
generated C, proof coverage, or resource ceilings.

## Narrow Producer Change

- Probe the already selected, identity-checked C compiler with
  `-Q --help=params`. Choose the fixed profile only on successful, clean output
  explicitly listing both parameters. Otherwise use the existing portable
  recipe. Do not make GCC-specific flags mandatory for other C11 compilers.
  Bound the probe to3s (TERM then1s KILL), accepting at most64KiB per stream
  within a68KiB bounded capture, independent of Bash's POSIX file-limit units.
  This guard space makes handled write overflow
  independently detectable, even if the compiler exits1/2. Recognize
  exactly one complete row for each parameter; duplicates/malformed rows are
  unsupported, not guessed capability. Exit1/2 or successful unsupported output
  selects portable; timeout/signal, failed capture/readback, or changed compiler
  identity is an error, not portable fallback. GCC selection requires empty
  stderr. Do not retry or downgrade a failed selected-profile postcheck.
- Freeze the selected profile once per build invocation. Only `portable` and
  `gcc-20-32768` are valid frozen values. Append exactly those two flags after
  the existing eight argv items for the GCC profile; never accept arbitrary
  flags, shell fragments, or a new public compiler command.
- The stage1 builder passes its frozen profile to the captured seed builder
  through one validated internal environment value. Both seed and stage1 argv
  and the existing flags digest derive from that same frozen value, not new
  independent capability guesses. Direct seed builds choose/freeze their own
  profile. Reject a changed capability profile before publishing artifacts.
  The private transport is `NQ_BOOTSTRAP_CC_GC_PROFILE`, scoped only to the
  captured child invocation. If inherited, including an empty value, validate
  it and require equality with fresh selection for the pinned compiler;
  malformed/mismatched values fail. It is not an override. Cache, profiling and
  attestation always select freshly, ignoring the transport. Profiling display,
  execution recipes and digest share one invocation-frozen profile.
- The flags digest retains its existing framed argv encoding. Cache validation
  freshly derives the selected profile and digest from the current compiler.
  A changed profile invalidates reuse. Record the actual argv profile, not an
  assumption about what a child selected.
- Materialize each argv producer through a checked file before compilation.
  Validate producer exit status, exact item count, and complete NUL framing;
  execution and hashing must consume the same validated bytes. A producer
  failing after the portable eight-item prefix, truncated framing, or a
  parent/child profile mismatch must fail before publication. Do not use
  unchecked `mapfile ... < <(producer)` for these recipes.
  Pin argv hashes and the recipe digest in parent-shell scalars before
  execution, verify the loaded execution array against that pin, and reject
  persistent spool drift before publication. Never derive an executed recipe
  retrospectively from bytes a compiler process could have changed.
- Strict historical seed flag validation accepts the old exact eight-item
  recipe and the exact ten-item recipe with the two fixed appended flags.
  Unknown, altered, reordered, missing or extra flags remain failures. Manifest
  JSON shape/version and source/ELF/C/toolchain identity checks stay unchanged.
  An unchanged historical eight-item seed must verify positively while the
  current producer selects ten items: recorded history is not today's profile.
  Historical generator input/output paths retain the previous safe-relative
  validation rules; do not hardcode today's producer paths in their verifier.
- No change to stage1's generated-program compile/run flags or runtime API.

## Required Evidence

Before adoption, independent mixed review must approve the producer/cache/seed
boundary. Focused host fixtures must cover portable fallback, both exact argv
recipes, malformed profiles/flags, profile-change cache rejection and original
seed/provenance failure paths. Keep them explicitly synthetic; they are not
Linux compiler evidence.

Measure the final M56 compiler under the selected profile and preserve exact
source/C/runtime/toolchain/argv identities. Confirm the unchanged O2 level and
both seed comparisons. The existing final seven-phase milestone gate, with
all current wall/RSS ceilings, is still required after the complete candidate
and seed are reviewed. Do not trade a passing component measurement for that
gate or relax the512MiB limit.
