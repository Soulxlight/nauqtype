# PRE-M56 E1: Explicit Borrowed Text Assembly

Status: implemented and focused-evidenced 2026-10-01. Gate A and repair reviews
are independent and mixed-model. The measurements below establish a text
assembly improvement, not a representative compiler/gate speedup. Final
candidate audit/gate closure is recorded in `ROADMAP.md`.

## Pressure And Contract

P0 measured a 2520.62s cold gate, ~81s direct seed comparisons, and
304.23s/308.99s full-tree checks, versus 4.749s for source capture.
`proof.normalize_line` repeatedly concatenates characters; `text.lines_text`
concatenates rendered chunks into a growing output. Existing immutable string
operations cannot express a single exact-size output allocation in Nauqtype.

```nauq
fn str_join(parts: ref list<str>) -> str;
```

- Sole new builtin; no grammar, user generics, methods, traits, or schema bump.
- Ordered concatenation without a separator; empty input yields empty text.
  Preserve bytes, including embedded NUL; no conversion/normalization.
- Explicit read-only borrow, unchanged inputs, independently owned result.
  Forwarding an existing borrowed parameter preserves its pointer and checked
  value-use/IR borrow identity; it does not introduce an implicit owned borrow.
  Empty/singleton calls also allocate a fresh payload and existing owner.
- Exactly two successful runtime allocations per call. Check total length and
  allocation bounds before payload allocation; preserve `str_concat` fatal
  size/OOM behavior and free payload on owner-allocation failure.
- Pure, no mutation or IO/effect kind; existing argument-evaluation rules.
- Concrete `ref list<str>` signature; named parameter `parts`; stable IDs
  `builtin:str_join` and `builtin-param:str_join::parts`, with builtin evidence.
- Existing facts/review/refactor/policy machinery must represent or
  conservatively reject it as other modeled builtins. No command expansion.
- Linear runtime work in part count plus bytes. No timing claim from design.

This meets `SYNTAX_IDENTITY.md`: concise value flow, visible `ref` authority,
specified allocation/failure behavior, and checked identity/type/effect facts.
Teaching includes positive borrowed parts and negative type/borrow/arity/label
cases. Formatter uses existing call syntax. Mutable strings, stored refs,
implicit rewrites, callbacks, separator helpers, and generic maps are rejected
for this slice. Ordinary helpers remain library-owned; no consumer repo edits.

## Acceptance Order

1. Add builtin/runtime support without calls in reachable selfhost sources;
   old seed emits/compiles a builtin-aware bridge.
2. Test empty/singleton, NUL/shared-owner slices, unchanged input, independent
   drop lifetimes, checked size, separate payload/owner OOM, concrete typing,
   named args, pure evidence, formatter, and emitted-C execution.
3. Switch only normalizer line assembly and final rendered-chunk assembly.
   Preserve identifier recognition, first-seen mapping, whitespace, and
   line-by-line streaming. Both direct seed comparisons stay mandatory.
4. Compare old frozen/new normalizer verdicts on identical positive remaps and
   negative names/operators/control-flow/order pairs, whitespace/final-line
   cases, and real retained P0 C. Any mismatch blocks Stage B/seed promotion.
5. Measure concat versus join on identical native inputs and compare normalizer
   work on identical C. Disclose rebuild/setup/RSS and repeatability limits;
   timings cannot establish the complete checkpoint goal.
6. Old seed -> no-call bridge -> final-source C -> compile that C -> re-emit
   final sources. Require exact input/output C SHA-256 equality before seed
   promotion. Record actual final generator/source snapshot/runtime/CC/flags,
   never relabel bridge provenance or manually edit generated seed C.
7. Trailing mixed-model audit before one frozen seven-phase final gate, retaining
   release independence, sanitizers, full owned tests, and attestation.

P1-P4, their goals, and full M56 generics remain open. No stage3/stage4 proof,
broader borrow model, external API, or Python implementation is authorized.

## Measured Result

Same Ubuntu 24.04 WSL2/ext4 host and GCC 13.3.0 as P0, with unchanged C flags.
Sources were transferred as small deltas into one retained native workspace.
No full repository recapture was used for the paired measurements. Absence
of concurrent Linux compiler work is an operator observation, not an
independently monitored interval. GNU time reports hundredths of a second.

`tests/fixtures/str_join/benchmark.nq` verifies every byte of 160,000-byte
output. Each row below is a batch of 500 separate executions, including
process startup and internal byte verification plus exact stdout, empty
stderr, and success-exit assertions for every execution. The join path also constructs its list.
Both modes use the same candidate executable and identical text parts.

| Assembly path | Run 1 seconds | Run 2 seconds | Peak RSS KiB |
| --- | ---: | ---: | ---: |
| Repeated `str_concat` | 31.24 | 31.25 | 3644 / 3720 |
| Borrowed `str_join` | 1.72 | 1.70 | 3600 / 3712 |

Batch means are 31.245s versus 1.71s: **18.3x faster** in this assembly
fixture. Wall spread is 0.03% / 1.18%. The retained runner's SHA-256 is
`6851d6602562682f80180ef5cb480405b6f08f8c577f89a46c2b3569b9bebbf0`;
identity receipts bind it to the executable, generated C, fixture, and runtime.
Pre-review batches are retained separately, not used for this claim.
This is not a full compiler benchmark
or an RSS improvement. Direct native probes separately verify exactly two
allocations for empty/singleton/combined output, preserved NUL bytes, shared
slices, independent ownership, checked bounds, and both OOM failpoints.

The real comparison experiment ran both drivers against the same retained
P0 C bytes, SHA-256
`2ec30ab03c77d5b113eb414e18e5b4ba52c6217d9cf3283f938eea8b150c5084`.

| Real C comparison | Run 1 seconds | Run 2 seconds | Peak RSS KiB |
| --- | ---: | ---: | ---: |
| Frozen P0 driver | 80.55 | 81.86 | 26308 / 26176 |
| E1 candidate | 81.24 | 79.55 | 26008 / 26252 |

The intervals overlap. The roughly 1% mean difference is **inconclusive**;
neither representative comparison speed nor memory improvement is claimed.
P2 should now prioritize measured mapping/visibility/membership work rather
than assuming text concatenation dominates the compiler.

## Correctness And Bootstrap Evidence

- The focused gate executed, rather than merely parsed, the checked-value/IR
  probe, positional/named borrowed-parameter forwarding, native sanitizers,
  bounds/OOM cases, precise negative diagnostics, and scoped pure evidence.
  It passed in 83.99s, peak RSS 336152 KiB. This does not meet the <=10s
  focused-feedback goal.
- Frozen/new normalizer verdicts and stdout/stderr agree on all 15 positive
  and negative pairs, including leading-zero IDs, long lines, whitespace,
  mapping reuse, and final-newline behavior. The same retained-C comparison
  passed twice per driver; both seed-bootstrap comparisons remain mandatory
  in the closing gate.
- A no-call builtin bridge was emitted from the predecessor seed before
  reachable selfhost sources used `str_join`; its build took 482.56s,
  peak RSS 433584 KiB. Final C emission took 409.54s, peak RSS 104384 KiB;
  the actual compiled generator re-emitted it in 408.26s / 104524 KiB.
  No emission-speed claim is established.
- Exact input/re-emitted/promoted C SHA-256:
  `73ee8c354d3241dbcce9da003708a8ff6b3c5e0e903fe8c425c3aad7e0ec55de`.
  Actual generator SHA-256:
  `cd922f48ef4e90d19c1eb7f7a14060ddb82d49c4c6551a3e3174bb8c07dedb11`.
  Source SHA-256:
  `317fcc1aa4d2415493700e406ba41368d328043adfebbbdca7c74bd4991b5e2f`.
  Generating index: `70edaa2b6913006f5026fd23e82e20288fc08e16`, dirty
  against base `f289fd6b785c7983b003810b48fccf02f67e413f`.
- The strict seed manifest records actual input/output, flags, runtime, and
  compiler identities captured before use and rechecked through publication.
  Private seed verification preceded promotion. Six synthetic recovery cases
  exercised the actual cleanup handler; catchable signals/failures restore
  the predecessor, but SIGKILL/power-loss atomicity is not claimed.
- The successful final generation/measurement/promotion workflow took
  1270.66s, peak RSS 435592 KiB. This excludes the earlier bridge build,
  assembly batches, and two rejected pre-promotion attempts: one exposed the
  audit-rejected value-plan omission; one caught an incorrect test expectation.
  Their setup/work is not hidden in a speedup claim.

Raw receipts stay ignored under `build/verification/`; source and seed are
portable. Candidate closure still requires the audited seven-phase gate;
normalizer timings and microbenchmarks cannot replace it. Ordinary tests and
compiler behavior remain Nauqtype-owned, with no Python feature work.
