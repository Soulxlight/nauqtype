# Nauqtype Refactor Program

Status: R0/R1 documentation checkpoints accepted; bounded R2/R3 source work
implemented and undergoing acceptance. Current acceptance results
are recorded in [TODO](../TODO.md#current-refactor-checkpoint).
Inspection date: 2026-10-09. This is staged behavior-preserving work, not a
compiler rewrite or a new feature milestone. It does not renumber M56-M61
or displace the PRE-M56 efficiency campaign.

## Purpose

An older model having written code is not evidence that it needs replacing.
The actual pressures are repeated phase assembly and builtin knowledge,
expensive scans/copies, coupled internal type ownership, and documentation
mixing historical milestones with current instructions.

Keep the current flat semantic front end and structured checked downstream
boundary. Do not invent a universal AST, service framework, new runtime helper,
or more ownership authority to simplify a cleanup. Each code slice must earn
its place through concrete maintenance or measured performance benefit.

## Protected Baseline

- Incoming checkout: `main` at `f289fd6`, with substantial uncommitted docs,
  source, runtime, fixtures, performance, and generated-seed work. Do not reset,
  regenerate, stage, or publish it incidentally.
- Recorded P2 candidate: `36e68e791d3ec2bb3b068fbabd69894a01913803`, not a newly
  committed baseline. Its one cold gate took 2485.30 seconds; the overall
  campaign goal remains open. See [Performance Mapping](../PERFORMANCE_MAPPING.md).
- Record incoming file content and staged-content state. The raw `.git/index`
  hash can change during metadata refresh without staged-content changes.
- Keep seed C, historical source snapshot, runtime, manifests, generator
  identity, and checksums intact. Generated C is never a manual refactor target.
- Preserve other project ownership/dirty work. Missing AIML workspaces or
  documents are not permission to recreate or adopt their APIs.

## Compatibility Lock

| Surface | Preserve or explicitly migrate |
| --- | --- |
| Source | Accept/reject behavior, evaluation order, exact type/error rules |
| Commands | Names, aliases, defaults, options, paths, exits, stdout/stderr, no-mutation guarantees |
| Evidence | Format meanings, stable IDs, spans, ordering, schemas, failure envelopes, null artifacts |
| Values | Binding IDs, type origins, copy/move/borrow plans, cleanup timing/authority |
| Backend | Checked handoff -> value/borrow -> IR -> C; no downstream token/flat-fact fallback |
| Proof | Both direct seed comparisons, copied-selfhost proof, corpus/tooling/release/sanitizer coverage |
| Runtime | ABI, integer/allocation behavior, filesystem/process authority and failures |

Moving compiler functions changes their source semantic IDs. Keep
identity-bearing entrypoints in place, or explicitly review affected policy
and evidence migrations; do not silently update goldens to conceal changes.
Named arguments still evaluate in canonical parameter order, not label order.

## Checkpoint Sequence

### R0: Documentation Foundation

Implemented: complete [documentation index](README.md), descriptive
[compiler map](COMPILER_MAP.md), and narrow repairs to architecture,
verification, syntax-status, roadmap, TODO, and coordination. History,
packaged README, all executable inputs, and campaign goals are preserved.

Acceptance: exact write set, protected-content equality, relative links,
document coverage, whitespace checks, and independent documentation audit.
No new compiler, benchmark, release, or stable gate is claimed. P2's earlier
attestation still applies only to its original candidate.

### R1: Baseline Checkpoint And Packaged Documentation

Baseline checkpoint completed before code restructuring:

- `0564a32` commits exactly the reviewed P0/E1/P2 completed-document tree
  `beb60b56fc31906b36d742156f641dd83a6a8e00`, separately from R0/R1.
- Its verified P2 closing receipt discloses only the three allowlisted
  completion-document changes from the earlier gated candidate. It does not
  attest R0/R1 or claim a fresh performance result or publication.

The accepted R1 candidate rewrites the packaged README around the current Linux quick
start, evidence versions, limitations, and authoritative links rather than
milestone history. It removes stale stage0/Zig-first instructions and
v3-as-newest review guidance. Source-only guides remain distinct from installed
docs; adding packaged guides would require an explicit manifest/assembler
change and is not part of R1.

README is a release artifact. Its rewrite received a separately reviewed
candidate and the executable close in [Verification](../VERIFICATION.md).
Do not fold it into P2's completion-doc allowlist. Commit/push ownership stays
with the lead; this plan does not claim publication. Freeze README, this plan,
the documentation index, and routing before the trailing audits and gate;
record the later acceptance result only in allowlisted completion documents.

### R2: Narrow Feedback And Compiler-Scan Attribution

Bounded implementation, still PRE-M56; acceptance remains candidate-specific:

The combined R2/R3 run follows the revised [execution contract](R2_R3_CONTRACT.md):
phase-owned immutable module-run ranges, retained public wrappers, direct
oracle/table probes, exact fixture comparisons, real seed promotion, and one
reviewed full gate. Current results remain in TODO; the contract is not closure.
The ordinary timing/compatibility record is [R2/R3 Results](R2_R3_RESULTS.md).

- measure fixture startup, cache validation, captures/hashes, and actual
  compiler work separately on one retained native-Linux candidate;
- attribute one dominant scan before choosing an index. Candidate seams are
  handoff function slices, borrow function collections, and C-emitter
  expression/field/arm/block adjacency;
- add private stable ranges only where measured cost warrants them. Preserve
  source order, ambiguity, origins, early exit, and fail-closed missing truth;
- prefer existing focused probes. `nauqc test` has no suite selector; adding
  one is an explicit tooling-interface decision, not an existing flag.

Acceptance: identical diagnostics/evidence and user-program C for selected
fixtures, spec-derived runtime/negative cases, two comparable ordinary
measurements with RSS/setup costs, required audits, actual seed promotion
when needed, then one frozen full gate. Profiles are attribution, not release
timings. Faster inner checks do not close the broader P1-P4 goals.

### R3: Shared Builtin Truth

The R2/R3 candidate extracts the identical IO-subkind and propagation-error
tables in facts/review, retaining their wrappers and checked-builtin guards.
The wider inventory below is not a mandate to consolidate every phase:

- inventory repeated names, signatures, argument labels, borrowing, effects,
  and runtime mappings across resolve/typecheck/handoff/value-plan/borrow/
  facts/review/C emission;
- move one pure identical family into a compiler-owned Nauqtype module;
  migrate consumers incrementally rather than creating a giant abstraction;
- keep ABI spelling/type policy distinct from evidence rendering. Neither
  the runtime nor a model becomes the semantic authority.

Acceptance: filesystem/process/`str_join`/propagation fixtures, negative arity/
label/ref/mutation cases, exact facts/review/diagnostic goldens, audited
executable gate and actual seed procedure. No new builtin or effect atom.

### R4: Driver And Checked-Project Assembly

Proposed, not a license to bundle every list into a context:

- separate argument decoding, routing, phase readiness, and rendering while
  retaining identity-bearing entrypoints where possible;
- unify repeated checked-phase assembly without erasing command-specific
  entry requirements, diagnostics, legacy formats, or fail-fast boundaries;
- prototype any owned `checked_project` aggregate first. Move-only lists,
  field-mutation limits, borrow forwarding, copies, and cleanup can make a
  convenient-looking abstraction invalid or expensive.

Acceptance: exact help/version/invalid-option behavior and success/warning/
failure/workspace goldens across routes; no mutation from report commands;
checked coverage/fail-fast cases; memory comparison; full seed/proof/release
close. No zero-copy claim without generated-code and runtime evidence, and
no new reference/lifetime authority to make aggregation work.

### R5: Backend Type Ownership

Proposed dependency cleanup:

- distinguish valid IR-only data flow from shared checked-enum imports in
  IR/C emission;
- consider a neutral vocabulary only if it reduces coupling without duplicating
  type truth; preserve variants/order, IDs, record semantics and type origins;
- review nominal-origin, policy, and selfhost-evidence consequences of moving
  a definition instead of treating it as an invisible file move.

Acceptance: static import checks, identical user-program IR/C and runtime
behavior for arithmetic, ordered match, field borrows and cleanup, retained
missing-identity/type/child failures, and normal executable acceptance.
No richer AST or backend rewrite.

### R6: Proof/Host Integration And Final Documentation

Proposed only where focused evidence justifies it:

- share identical receipt publication/failure cleanup, not proof policy,
  independent captures, invocation provenance, or authority;
- preserve all seven phases, independent release gates, budgets, artifact
  roles, signal/failure handling, and mandatory comparisons;
- reduce every composition finding to a focused fixture;
- reconcile source, evidence, teaching and release documentation per slice,
  without copying new histories into every entrypoint.

Acceptance: shell syntax plus existing budget/provenance/attestation tamper,
failure and interruption probes, independent audits and frozen executable
close. Archived Python, tracked probes, and benchmark/history assets stay
unless a separate ownership/manifest audit proves deletion safe.

## Working Method And Completion

The lead owns scope/integration; workers get disjoint files and bounded tasks.
Independent auditors review actual diffs and exact concise evidence under
[AGENTS](../AGENTS.md) and [routing](../AGENT_ROUTING.md). Wait fully for audits.
No paid model call or optional authoring pilot is required.

Source changes follow focused checks -> freeze -> audits -> repairs/affected
checks -> one full milestone gate. Do not duplicate or weaken that gate.
New active compiler/tooling/teaching work remains Nauqtype, narrow host shell
integration remains intentional, and Python remains archived.

The complete refactor is not done when this plan is written. Source slices
remain open until behavior, identities, evidence, resources, seed lineage and
gates pass. R0 is documentation only. M56-M61 stay in the
[existing release sequence](../STABLE_RELEASE.md) after the efficiency
checkpoint, not hidden inside this refactor.
