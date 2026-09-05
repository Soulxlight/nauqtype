# M54.9: Integer And Allocation Edges

Status: complete, 2026-09-05. Independent Sol max and GPT-5.5 xhigh final
audits passed, followed by the seven-phase reviewed frozen-candidate gate.
This closes F06/F13 only; M54.10 and M55 remain separate.

## Scope

Close Astra findings F06 and F13. This is a correction to shipped integer and
runtime operations, not new syntax, numeric types, casts, recoverable ownership,
libraries, or a new public command. M54.10 owns provenance and hash framing;
M55 and F14 remain separate.

## Integer Contract

- Ordinary `i32` and `i64` addition, subtraction, multiplication, and unary
  negation wrap modulo their width. The result is the corresponding signed
  two's-complement value, including negation of the minimum value.
- Division truncates toward zero. Zero divisors and minimum-value divided by
  `-1` fail deterministically with exit code 1 and one stderr line:
  `nauqtype runtime: integer division by zero` or
  `nauqtype runtime: integer division overflow`.
- Fatal runtime failure is not an exception or a recoverable result. No
  unwinding or cleanup execution is promised after it.
- Existing literal range checks and direct negative-minimum literals stay
  unchanged. There are no new implicit or explicit numeric conversions.
- Constants use the same arithmetic. Evaluated invalid division emits
  `NQ-TYPE-045` at the slash token, with `constant integer division by zero`
  or `constant integer division overflow`; `check` exits 1. Boolean `and` and
  `or` short-circuit, including comparisons containing constant arithmetic.

Dynamic C lowering materializes value reads left-to-right exactly once, then
uses unsigned arithmetic and range-safe signed reconstruction. Constant C
lowering folds typed IR into bounded-size strict C11 literals; it does not nest
duplicating arithmetic macros. Dead operands still validate their IR links
and types, but cannot trigger arithmetic failure during folding.
The frontend constant evaluator uses bounded byte limbs, so validating these
semantics does not depend on a host compiler's signed-overflow behavior.

## Size And Failure Contract

- Every runtime-created string, including views and imported argument,
  environment, cwd, error, and stream text, has length at most `INT32_MAX`.
- Bytes have length/capacity at most `min(INT64_MAX, SIZE_MAX)`.
- Lists have length/capacity at most `INT32_MAX`; capacity also respects
  allocation-byte limits divided by the element size.
- All addition, multiplication, growth, terminators, argv/path construction,
  Windows quoting, and native/generated container allocation is checked
  before potentially overflowing arithmetic. Growth saturates at the
  effective limit, then fails. String-owner retain counters cannot wrap.
- Infallible allocation paths exit 1 with
  `nauqtype runtime: size limit exceeded` or the existing
  `nauqtype runtime: out of memory` line.
- Fallible IO reserve paths return an existing `io_err`, without allocating
  while constructing the error: limit errors use `invalid_input`, code and
  OS code 0, text `size limit exceeded`; allocation errors use `other`, code
  and OS code `ENOMEM`, text `out of memory`. The operation is retained and
  path fields are absent.

Private native test macros are `NQ_TEST_MAX_SEQUENCE_LENGTH`,
`NQ_TEST_MAX_ALLOCATION_BYTES`, and `NQ_TEST_ALLOC_FAIL_AFTER=N`.
Exactly N successful nonzero allocations are permitted before the next fails;
size validation precedes allocation-attempt accounting. The sequence-length
test limit must be at least 128 and smaller values are compile-time errors,
so fixed fallback IO metadata remains representable. Allocation-byte limits
are independent. These macros do not enter release builds or the Nauqtype
API. Tests use small artificial limits, not huge real allocations.

## Existing Helper Repairs

`text.i32_to_str` must render `INT32_MIN` exactly. The proof's old `nqsum`
triage checksum uses bounded arithmetic, preserving every previously
nonoverflowing calculation; it is not promoted to a cryptographic identity.
M54.10 owns that migration. The structural normalizer stays unchanged.

## Acceptance Evidence

Gate A: independent Sol xhigh and GPT-5.5 xhigh reviews accepted the revised
contract, including constant short-circuit evaluation, strict C11 constants,
allocation-free IO errors, and bounded fault injection.

Required before completion:

1. Runtime-fed arithmetic at both widths under `-O0`, `-O2`, and
   `-O2 -fsanitize=undefined -fno-sanitize-recover=all`.
2. Strict C11 constant-expression probes with `-pedantic-errors`, source
   diagnostics with exact division spans, nested wrap-before-division,
   evaluated failures, and unreachable short-circuit counterparts.
3. Native and generated list/bytes/string boundaries, injected size/OOM
   behavior, and the minimum signed integer text conversion.
4. Nauqtype-owned focused tests and the existing corpus; generated seed
   refresh only through recorded predecessor/generator/source/runtime lineage.
5. Sol xhigh primary plus independent GPT-5.5 xhigh adversarial Gate B PASS,
   followed by one full gate on the reviewed frozen candidate.

Development results and final artifact identities are recorded below only
after the commands actually run.

### Development And Rejected Candidate

The first updated-emitter candidate passed the owned `test` in 22.20s
(98,852 KiB peak RSS) and the 42-case `prove-corpus` in 27.19s (52,592 KiB).
It regenerated compiler C in 356.83s. None of that is final acceptance:
independent source reviews returned REVISE for delayed scalar/field lvalue
reads and exponential nesting of constant C macros. They also required an
enforced supported domain for the private sequence-limit test macro.

The repair captures non-dropping lvalue reads immediately, leaving borrow
targets on their existing path. Typed constant IR folds to bounded C11
literals while validating dead-operand structure. Private sequence limits
below 128 now fail compilation; allocation-byte limits remain independent.
Permanent tests add both-width local/field mutation compositions, return,
assignment, condition, call-argument and list-literal cases, depth-40 constant
chains, and an initializer-size guard before C compilation. The prior large
macro initializer was inspected but deliberately not compiled.

The repaired emitter passed a focused source check. New helpers/tests passed
formatter checks; the cap-127 native compile rejected with the intended
`NQ_TEST_MAX_SEQUENCE_LENGTH must be at least 128` diagnostic. A newly emitted
candidate must still run all repaired tests and pass fresh explicitly selected
mixed-model trailing audits. Resumed reviewers did not expose reliable serving
model metadata, so their useful findings are not certified as those formal
model-specific gates. No candidate seed has been promoted yet.

### Final Source Repair And Seed Candidate

The explicit GPT-5.5 xhigh audit found a borrow-prefixed arithmetic argument
that still reached the backend as if it were a place. The repair validates
the whole direct borrow argument, preserves existing read-only product-field
borrows, and rejects non-place C borrow IR instead of falling back to value
lowering. Eight source negatives, both-width direct/forwarded borrow positives,
and malformed/dead IR probes are permanent owned tests. The contradictory
old SPEC field-borrow sentence is corrected to match the shipped boundary.

`build/m54_9/borrow-repair test` passed in 22.62s (98,888 KiB peak RSS),
with exact `nauqtype test ok` stdout and no compiler stderr. The same driver
passed all 42 corpus cases in 27.56s (52,620 KiB), with exact
`example corpus ok` stdout. Its source emission passed in 363.20s
(98,848 KiB) and current-runtime C11/O2 compilation passed. The explicit
GPT-5.5 xhigh repair audit returned source PASS. The primary review is
escalated to Sol max under the conflicting-verdict policy, not silently
substituted for the required model.

That executable regenerated its own sources in 426.77s (97,900 KiB).
`cmp build/m54_9/borrow-repair.c build/m54_9/final-fixedpoint.c` passed;
`build/m54_9/borrow-repair prove-seed` on the same paths passed with exact
`seed structural proof ok` stdout. Both C files have SHA-256
`3ae7bc907b3f1e234127eac4be1feadd4c2fb8be405379a37cc928474b46b525`.
The normalizer is unchanged. This exact output and current runtime were
copied into the seed candidate. The v1 manifest records actual predecessor,
generator, source, runtime, and host-compiler identities; all four
`SHA256SUMS` entries pass. The strict v2 snapshot/inventory enforcement remains
M54.10, not a claimed property of this interim seed record.

### Final Audit And Frozen Gate

The final Sol max primary and GPT-5.5 xhigh adversarial source/seed audits
returned PASS. The primary escalation follows the conflicting-verdict policy;
no earlier missed finding is hidden by that final verdict. Both authorized
the exact staged diff SHA-256
`3f597478f2b541c138d0b5c146acff0c2f7a8b92828b7314a145013e2e0bdc5c`.

`scripts/check_milestone.sh` passed in 2,048 seconds on frozen tree
`756577157e6018962e938872548dc962449a40dd` in
`/tmp/nauqtype-m54-9-frozen-fKsyGN`. It exited 0 with empty stderr. The index
and raw worktree remained unchanged throughout the run. This completion-only
documentation delta changes no source, schema, fixture, runtime, script,
README, seed, or packaged artifact.

| Phase | Wall Seconds | Peak RSS KiB | Result |
| --- | ---: | ---: | --- |
| stage1.driver | 427.98 | 424312 | PASS |
| seed_bootstrap | 438.49 | 98132 | PASS |
| proof | 1148.40 | 422820 | PASS |
| linux_alpha | 4.04 | 52268 | PASS |
| stress_leg | 1.77 | 52288 | PASS |
| owned_tests | 23.29 | 98276 | PASS |
| ownership_sanitizers | 3.09 | 47388 | PASS |

The gate includes the copied-selfhost fixed point, all 42 corpus cases, Linux
release verification, the stress leg, arithmetic/allocation fixtures, and
nine ownership sanitizer cases. The historical Python suite was not run.
No native Windows or 32-bit host verification is claimed.

Exact SHA-256 evidence, retained under ignored `build/m54_9_final/`:

- milestone summary: `9a29433a830a9e589a314fdf818590ab41f3a0468b0d660ade0625eaedae5f53`
- performance summary: `1a956607dbba584b21828d654e22ad2255ac49e248091a14a42aa251b5971049`
- proof summary: `0b61f8d3587b5e1dc7481f974c362fe28b7aa4306e36ed880d54fbda70d16108`
- stage1 C: `3ae7bc907b3f1e234127eac4be1feadd4c2fb8be405379a37cc928474b46b525`
- stage1 executable: `9f591c0014cb8241d4ea560810bb772561934a6eb7e76b4dad7aa5d5156ede5e`
