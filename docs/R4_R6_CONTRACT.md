# R4-R6 Execution Contract

Status: independently approved execution contract, 2026-10-19. Base: `b7baf76`.
Owner: compiler repository only; adjacent libraries and missing AI/ML work
are outside this run. This is behavior-preserving maintenance, not M56,
new source syntax, runtime authority, evidence versions, or a stable release.
Completion belongs in [TODO](../TODO.md#current-refactor-checkpoint).

## R4: Shared Assembly Without An Owned Aggregate

Four driver paths repeat the same semantic phases and source-contract checks:
`run_pipeline`, `run_facts`, `collect_facts_ready_project`, and
`collect_review_ready_project`. Keep these identity-bearing functions and
their signatures in `selfhost/main.nq`. Keep parsing, source capture/loading,
rendering, command-specific entry requirements, and failure envelopes intact.

Add private, explicitly borrowed helpers in the same module:

- Front-end assembly calls resolve modules/types/bodies, module typechecking,
  constant typechecking, recursive value typechecking, and resolved binding
  collection in exactly their current order. Run all existing phase calls
  before the existing error boundary; do not drop diagnostics with a new early
  return. Forward `entry_module` and `require_entry` truthfully.
- Source-contract assembly retains checked call-target replacement, declared
  contract collection, and checked mutation validation in that order. Borrow
  the existing caller-owned lists; return both original and validated summaries
  in a small copy-only record so review's existing failure-count composition
  remains unchanged. Mutation/coverage outputs stay explicitly `mutref`.
- Separate dispatch from argument decoding by retaining `main` and
  `parse_driver_request` and routing the unchanged mode match through one
  private dispatch function. Preserve mode order, every literal argument,
  output stream, exit, legacy no-argument behavior, and build/run paths.

Do not introduce an owned `checked_project`, stored references, a service
framework, new borrow rules, or a public command. Caller-owned lists and
their current explicit early-release assignments remain in place. No
aggregate is being adopted, so no aggregate-copy or zero-copy claim is made.
Inspect generated helper parameter/body handling and compare actual RSS;
indirection alone is not evidence of lower allocation or faster checking.

## R5: Reviewed Intentional Type Ownership

The required review distinguishes data flow from vocabulary imports:

- `ir.nq` legitimately consumes checked handoff records, type properties, and
  value-use plans. That is the required lowering boundary, not flat facts.
- `c_emit.nq` accepts only IR collections. Its `handoff` and `value_plan`
  imports supply shared kind enums, not checked project collections.
- Keep existing enum definitions, variant order, nominal/source identities,
  IR record field types, and checked type/use truth in their current owners.
  A second neutral enum would duplicate truth; primitive tags weaken checking;
  predicate wrappers merely hide the same exhaustive backend knowledge.

R5 closes as an independently audited retention decision, not an invented
definition relocation. Record that disposition and its import/record evidence
in the refactor notes. No edits to handoff, value-plan, IR, or C-emitter types
are authorized by this slice. Preserve missing identity/type/child failures.
Existing arithmetic, ordered-match, field-borrow, and cleanup examples must
retain byte-identical user C and runtime behavior under the integrated driver.
IR/backend preservation evidence is static equality of the unchanged
`handoff.nq`, `value_plan.nq`, `ir.nq`, and `c_emit.nq`, including their
identity/type/child failure guards, plus the exact user-C/runtime comparisons.
There is no direct serialized-IR comparison or new malformed-IR oracle in this
slice. `probe_checked_coverage.nq` tests type/use-count coverage failures only;
it must not be reported as a missing-child/identity/type-ID injection test.

## R6: Narrow Host Mechanism And Final Documentation

In `selfhost/proof.nq`, retain the private names/signatures of
`run_driver_build`, `run_driver_check`, and `run_driver_run`. Delegate only
their identical `[command, entry_path]` construction and
`run_process(driver_path, ref args, ".")` invocation to one private helper.
Each wrapper supplies its unchanged literal command. Do not catch, rewrite,
cache, or reinterpret the process result. Keep all other argument shapes,
`*_output` wrappers, explicit cwd choices, and their call sites unchanged.

Do not unify proof-summary, profile-summary, attestation, or builder receipt
publication. Their validation, stale-output handling, signal/finalization,
capture, and provenance policies differ. Keeping those mechanisms independent
is an explicit R6 outcome, not unfinished generic-publisher work.

Reconcile refactor notes, roadmap/TODO/coordination, and navigation only where
current wording changes. Preserve all seven gate phases, independent release
gates, budgets, artifact roles, proof summaries, both direct seed comparisons,
and archived assets. No new shell publication framework or Python work.

## Ownership And Required Review

The lead owns contract/fixture selection, routing, integration, generated-code
inspection, measurement, actual seed promotion, final docs, and Git operations.
A Sol High worker implements only the approved R4 changes in `main.nq`.
A Luna Medium worker implements only the R6 helper and three wrapper bodies
in `proof.nq`; the lead edits proof registration only after that handoff.
All existing function names and public signatures are retained.

Allowed tracked writes are exactly `selfhost/main.nq`, `selfhost/proof.nq`,
`AGENT_ROUTING.md`, `docs/R4_R6_CONTRACT.md`, `docs/R4_R6_MATRIX.txt`,
`docs/R4_R6_RESULTS.md`, `docs/REFACTOR_PLAN.md`, `docs/COMPILER_MAP.md`,
`docs/README.md`, `TODO.md`, `ROADMAP.md`, `NAUQTYPE_COORDINATION.md`, and the
actual generated `bootstrap/seed/` family. No new fixture, golden, schema,
runtime, host-script, archived source, or teaching source is planned. Local
measurement/capture recipes and raw receipts remain ignored build artifacts.
Only `TODO.md`, `ROADMAP.md`, and `NAUQTYPE_COORDINATION.md` may receive the
reviewed completion-only delta after the full gate; every other path freezes
before trailing review and acceptance. New compiler-private definitions/call
edges may appear in selfhost facts; user-program IDs and goldens stay stable.

Independent pre-implementation and trailing audits use `gpt-5.6-sol` xhigh and
`gpt-6-astra` xhigh, the explicit fallback because GPT-5.5 is unavailable.
Neither auditor sees the other's verdict before reaching its own. Workers do
not audit their own work, commit, push, or spawn descendants. No paid service.

## Compatibility, Measurement, And Close

Freeze the exact command matrix before collecting reference outputs. Cover
help/version aliases, invalid options, success/warning/error diagnostics,
library-only and workspace routes, facts/review formats, diff/change/policy/
rename, and user IR/C/runtime fixtures. Compare exits/stdout/stderr and emitted
C bytes, retain NUL-framed argv, and hash/recheck all fixture inputs. Report
commands use no source writes; generated outputs stay in isolated build dirs.
No golden updates are authorized to hide a regression.
The exact rows are [R4_R6_MATRIX.txt](R4_R6_MATRIX.txt). IR-related rows exercise
lowering through observable C/runtime output, not a separately dumped IR.
Keep `<native-campaign>/compatibility/{before,after}/<id>.stdout`, `.stderr`,
`.exit`, `.cwd`, and NUL-framed `.argv`; retain/read back receipts under
`build/verification/refactor-r4-r6-20261019/` in the canonical checkout.

Each selected valid-shape `emit-c` row uses a fresh side-specific `<id>.c`
path. The no-argument
legacy row runs from `tests/fixtures/facts/`; remove only its fixed ignored
`build/main.c` before each run, require successful fresh emission, and retain
it as the side-specific `legacy_no_args.c`. Byte-compare every present C
artifact and its presence marker. A failed emission, including library-only
`emit-c`, must retain an explicit absent marker and no stale output; never
turn missing C into a successful comparison or accept an earlier artifact.
Append output arguments only to the explicitly selected `c_*` and
`library_emit_missing_entry` rows. Invalid-option rows retain their literal
argv, so a changed argument count cannot mask the intended validation branch.
The 82 rows include frontend and source-contract failures through both policy
and rename, not just their successful shared-readiness paths.

Reuse the verified R2/R3 reference capture/executable without changing its
gated worktree. Capture one new native-ext4 candidate and transfer only changed
files thereafter. Its initial cache may be copied only with unchanged complete
fingerprint/derivation/artifact/toolchain verification, never manually blessed.

R4's comparison target is the already retained 74-file current-source profile
input from R2/R3. Its two ordinary reference checks are 289.82s/289.36s,
104436/104564 KiB, executable SHA-256
`d766e07e4621ad399fb022b37958594604f6693200be06f2511f9d868f4796ab`.
Recheck the retained inputs and executable before reusing that evidence; run
two candidate checks on those exact inputs, serially with production flags.
Disclose that the reference pair predates this run. Spread above 10% is
inconclusive; material wall/RSS regressions require investigation before close.
Keep cache/build/copy/hash costs separate. No cold A/B or campaign goal is
claimed from maintenance, historical timings, or synthetic checks.

Before executable close: focused CLI/diagnostic/evidence/backend cases, existing
coverage-failure probes, static identity/import checks, and the existing budget,
provenance, attestation, profile, and interruption fixture suites as relevant.
Build the integrated compiler through the existing checked seed, re-emit and
promote only exact compiler-produced C with complete snapshot/inventory,
predecessor, generator, flags, physical compiler identities, and rollback.
Never hand-edit generated C.

Freeze the integrated candidate and obtain both independent trailing approvals;
repair findings with affected focused checks only. Then run one complete
`scripts/check_milestone.sh`, retaining all seven phase wall/RSS results,
proof/release/sanitizer coverage, and exact attestation. A later executable
change requires fresh acceptance. Only the specifically selected completion
documents may change afterward; bind the reviewed final tree in the closing
receipt. Commit only reviewed work; do not infer GitHub publication from a
local commit. R0-R6 closure does not close the wider PRE-M56 campaign or
M56-M61, adopt the authoring-kit prototype, or migrate a downstream pin.
