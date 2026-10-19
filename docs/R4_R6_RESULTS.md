# R4-R6 Maintenance And Compatibility

Measured 2026-10-19 on Ubuntu 24.04 WSL2, native ext4, GCC 13.3.0,
`x86_64-linux-gnu`, ordinary production flags. This report records focused
evidence, not final milestone acceptance or a stable release. Final
acceptance belongs in [TODO](../TODO.md#current-refactor-checkpoint).
The [execution contract](R4_R6_CONTRACT.md) and exact
[82-row matrix](R4_R6_MATRIX.txt) remain the comparison authority.

## Implemented Boundary

R4 shares the existing front-end and source-contract sequences across four
driver paths through explicitly borrowed private helpers in `main.nq`.
Caller-owned collections, phase order, entry requirements, failure boundaries,
and early-release assignments remain. A copy-only pair returns both original
and validated review summaries, preserving review failure-count composition.
The unchanged mode match is separated from decoding, while historical
entrypoints and signatures stay in place. No owned project aggregate or new
reference authority is introduced.

R5 closes as an intentional type-ownership retention decision, not a new
backend layer. IR legitimately consumes checked records and value plans.
C emission accepts IR collections; its checked/value-plan imports supply
shared kind vocabulary. Relocation would change nominal/source identities;
neutral duplicates, primitive tags, or wrappers would not reduce the actual
semantic dependency. Keep those canonical definitions and exhaustive uses.

R6 shares only the identical `[command, entry_path]` process invocation used
by the three private build/check/run proof wrappers. Their names, signatures,
literal commands, cwd, and unmodified process results remain. Output-specific
wrappers and all other proof bodies remain separate. Proof/profile/attestation/
builder publishers retain their distinct policies; no generic publisher is
adopted. No host script, runtime, schema, fixture, golden, archived Python,
teaching source, downstream checkout, or consumer pin changes.

## Compatibility And Generated-Code Inspection

All 82 reference/candidate cases match exits, stdout, stderr, and cwd bytes.
All 11 present user C artifacts match byte-for-byte: ten selected emit cases
plus fresh legacy no-argument emission. Library-only emission fails with no
stale output. Literal invalid-option argv remains unmodified. Retained
NUL-framed argv differs only where the executable/output paths must differ;
it is not falsely compared as identical. Fixture/golden/example hashes are
rechecked, and no golden is rewritten.

Static comparison preserves 192 historical function signatures across main
and proof, all 148 proof function bodies outside the three approved wrappers,
eight protected driver declarations, and the exact old mode-match body.
The four backend owners (`handoff.nq`, `value_plan.nq`, `ir.nq`, `c_emit.nq`)
are raw-byte identical to the base. This preserves their identity/type/child
failure guards, but is not a new malformed-IR test. The existing coverage
probe checks type/use-count failures (`NQ-INTERNAL-010` / `NQ-INTERNAL-011`) only.

Generated C inspection confirms list inputs become const pointers, mutable
outputs become pointers, and forwarded borrowed parameters are not copied
into an owned project record. The source-contract helper replaces call facts
through the existing explicit drop/move sequence. Its returned pair contains
only two four-integer review summaries. Normal string clone/drop and small
record copies still exist; no zero-copy, allocation reduction, or speedup is
claimed from helper extraction alone.

The existing profile-harness suite passes all 20 stub-based shell checks.
Those are harness contracts, not a production compiler baseline. The actual
predecessor-seed construction passes in 498.39s / 437308 KiB; its input,
derivation, and artifact cache are verified. That build cost is separate
from the ordinary checks and the later seven-phase gate.

## Measurement And Seed Record

The comparison uses the retained R2/R3 current-source profile inputs, not a
fresh reference run or cold-gate A/B experiment. Their source/executable,
toolchain, flags, host, and successful timing receipts are revalidated before
two new serial candidate checks. The reference profile began at 14:51 UTC;
the candidate measurements began at 17:52 UTC the same day. No compiler build
ran alongside the measurements. This is not a randomized performance study.

| Ordinary check on identical inputs | Wall seconds | Peak RSS KiB | Wall spread |
| --- | --- | --- | --- |
| Reused R2/R3 reference | 289.82, 289.36 | 104436, 104564 | 0.159% |
| R4/R6 candidate | 296.87, 297.02 | 104984, 104828 | 0.051% |

Means are 289.590s and 296.945s: the candidate's observed wall time is
**2.54% higher**, and its maximum RSS is 0.40% higher. Both pairs meet the
10% repeatability bound. The result supports bounded maintenance cost, not
a speedup; the older reference and unpinned scheduling/frequency conditions
limit causal attribution. No cold/warm/focused campaign target closes here.

Costs are kept separate: one native clone took 15.27s / 15700 KiB; changed
source/document transfer took 2.345s / 302915 bytes; cache validation took
2.85s / 3988 KiB; pre/post measurement hash validation took 1.969s / 3.508s.
The 498.39s compiler construction above is not part of either check sample.
No new source-input clone/copy was needed for the two matched checks.
Seed changed-file copy and full byte readback took 13.586s, transferring
11098704 bytes excluding the checksum file; that interval excludes the
separate predecessor backup and native pre-copy verification.

- Base revision: `b7baf76a59292f2ff96acd562dcf6eee134998c5`.
- Construction index tree: `1dd1e20cc4955cec955498d01160c3a9cb6621a8`.
- Common input fingerprint: `626c2e23bfda4b7cf48aa02d15ffc9fbb9961c4d5700cdf81856a449f0ef79f5`.
- Reference input source SHA-256: `0e7d7046570cf99b704b7f8f9b4d2c92a73cf5b9ce0ce19e0afb1d3153d16a85`.
- Reference executable SHA-256: `d766e07e4621ad399fb022b37958594604f6693200be06f2511f9d868f4796ab`.
- Candidate/generator executable SHA-256: `ad28b1b9c1cc71cb7da1f6798db8ee383cfbf55f37c1175612bbcaa7a76cdb47`.
- Predecessor seed C SHA-256: `1d3a29919dd5a44a61732096ce2071311b86b97d658b1c49e178e35f913223e2`.
- Builder-produced generator input C SHA-256: `568c6fa4afb65f3275d197b4bbfe9bab2a947f67daae3e11be14f25bd3aa55ee`.
- Actual re-emitted output and promoted seed C SHA-256: `568c6fa4afb65f3275d197b4bbfe9bab2a947f67daae3e11be14f25bd3aa55ee`.
- Current 74-file source SHA-256: `e9d3abd2123635aad8ce9da83f5562c19431832166b79212cce39f13147931ad`.
- Strict source inventory SHA-256: `719cf06151e20bdd919a7766f33afc8ea8b7b0725effdf252ca018afea71d26f`.
- Matrix SHA-256: `acc126b9863ac57bf8c682bf6beeeecd6b855b5e781f3dd6702c5e5defb55f4c`.

Actual exact self-emission passes in 390.56s / 108412 KiB. The promoted seed
is compiler-produced, not manually edited. Strict manifest, inventory,
checksums, predecessor, generator input/output, runtime, physical CC, flags,
and pre/post-install identities are verified with catchable-failure rollback
remaining active through post-install validation. No failed promotion attempt
occurred in this run. Copy-back retains a predecessor backup and full
byte readback; native-ext4 inventory/mode checks remain authoritative rather
than claiming Linux mode certification from NTFS.

## Retained Receipts And Remaining Goals

Local evidence lives under `build/verification/refactor-r4-r6-20261019/`.
The one native-ext4 candidate and prior retained inputs are reused; only
changed files are transferred after capture. Original reference artifacts
remain untouched. Raw timings, argv, outputs, identity checks, construction,
seed promotion/readback, and final gate/closing receipts are kept locally,
not promoted into tracked release artifacts.

R0-R6 maintenance closure does not close the wider PRE-M56 campaign: focused
feedback <=10s, warm complete fixtures <=60s, >=50% faster cold gates with a
<=10-minute working target remain open. No budgets, proof comparisons,
coverage, independent release gates, or required audits are removed.
M56-M61, the staged authoring-kit evaluation, and downstream adoption remain
separate.
