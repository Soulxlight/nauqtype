# Compiler Implementation Map

> Inspection scope: 2026-10-19. This map adds no new executable evidence.
> It describes the inspected working tree and does not claim that unrun checks
> pass.

## Purpose And Authority
This is a compact implementation-facing navigation map.
It is not a language specification, release contract, or architecture decision.

- [ARCHITECTURE.md](../ARCHITECTURE.md) is the authority for compiler layers.
- [SPEC.md](../SPEC.md) and [GRAMMAR.md](../GRAMMAR.md) define language behavior.
- [SELFHOST_HANDOFF.md](../SELFHOST_HANDOFF.md) defines the checked boundary.
- [VERIFICATION.md](../VERIFICATION.md) defines verification commands and scope.
- [BOOTSTRAP_RETIREMENT.md](../BOOTSTRAP_RETIREMENT.md) defines bootstrap ownership.
- [DECISIONS.md](../DECISIONS.md) records accepted compatibility decisions.

Use this file to find code and likely seams, then consult those authorities
before changing behavior or a public contract.

## Repository Surfaces
| Surface | Status | Implementation role |
| --- | --- | --- |
| [selfhost/](../selfhost/) | Active source | Compiler, driver, evidence, and owned test/proof runner. |
| [stdlib/](../stdlib/) | Active source | Narrow C runtime and ABI-owned helpers. |
| [bin/nauqc](../bin/nauqc) | Active launcher | Repository and copied-release command entry. |
| [scripts/](../scripts/) | Active host integration | Bootstrap, budgets, release copies, provenance, sanitizers, and attestations. |
| [schemas/](../schemas/) | Active contracts | Versioned machine-readable evidence schemas. |
| [examples/](../examples/) | Active examples | Teaching and executable corpus inputs. |
| [tests/fixtures/](../tests/fixtures/) | Active fixtures | Compiler, runtime, evidence, ownership, and host-integration cases. |
| [tests/golden/](../tests/golden/) | Active expected output | CLI, diagnostics, facts, review, policy, and schema output. |
| [compiler/](../compiler/) | Archived reference | Frozen Python bootstrap compiler; not an active implementation lane. |
| Python suites under [tests/](../tests/) | Archived reference | Historical claims mapped into the Nauqtype-owned runner. |
| [bootstrap/python-reference.json](../bootstrap/python-reference.json) | Archive manifest | Records the Python reference boundary and replacements. |
| [bootstrap/seed/](../bootstrap/seed/) | Checked-in generated bootstrap | Versioned seed C, runtime copies, source snapshot, manifest, flags, and checksums. |
| `build/` and `selfhost/build/` | Generated output | Local compilers, C output, proof summaries, releases, profiles, and receipts. |

Do not hand-edit generated seed material as an ordinary source refactor.
Seed promotion follows the bootstrap contract and regenerates linked artifacts.
File presence alone does not prove source, compiler, or receipt identity.

## Active Pipeline

The active path is `workspace capture -> source loading -> lex and flat parser
facts -> resolve and typecheck -> checked handoff -> checked source contracts
-> type properties and value-use plan -> borrow validation -> typed IR
-> C emission -> host C`.

The front end remains fact-oriented.
Backend work starts from the structured checked handoff, not raw parser facts.

## Driver And Workspace
- [selfhost/main.nq](../selfhost/main.nq) owns CLI parsing, command dispatch,
  module-graph loading, phase assembly, and command-specific output behavior.
- `parse_driver_request` maps arguments into a private `driver_request`.
- `dispatch_driver_request` routes that decoded request; the historical
  `main` entrypoint remains parse-then-dispatch.
- `assemble_frontend` shares the borrowed semantic sequence across four
  readiness paths. `assemble_source_contracts` preserves original and
  validated summaries without taking ownership of project collections.
- `run_pipeline` assembles the compile/check/emit path.
- `run_facts`, `collect_facts_ready_project`, and
  `collect_review_ready_project` assemble evidence-oriented paths.
- `run_build_command` invokes emission and host compilation for build/run.
- [selfhost/workspace.nq](../selfhost/workspace.nq) provides
  `resolve_workspace_entry`, `capture_workspace`,
  `resolve_captured_workspace_module`, and captured identity helpers.
- [selfhost/files.nq](../selfhost/files.nq) holds narrow path/file helpers.
- [selfhost/source.nq](../selfhost/source.nq) defines source-file records.
- [selfhost/build_info.nq](../selfhost/build_info.nq) owns version/build facts.
- [selfhost/host_c.nq](../selfhost/host_c.nq) exposes
  `compile_host_c_program` for the explicit host-C boundary.
- In `proof.nq`, the existing build/check/run entry wrappers share only their
  identical two-argument invocation through `run_driver_entry_command`.
  Output-specific wrappers and distinct receipt publishers remain separate.

## Lex, Parse, Resolve, And Typecheck

- [selfhost/token.nq](../selfhost/token.nq) defines token kinds and spans.
- [selfhost/lexer.nq](../selfhost/lexer.nq) exposes `lex`.
- [selfhost/parser.nq](../selfhost/parser.nq) exposes `parse_file`,
  `collect_typecheck_facts`, `collect_value_type_facts`, and
  `collect_stmt_facts`.
- [selfhost/ast.nq](../selfhost/ast.nq) defines flat front-end records; its name
  does not imply a universal recursive expression AST.
- [selfhost/resolve.nq](../selfhost/resolve.nq) exposes `resolve_modules`,
  `resolve_types`, and `resolve_bodies`.
- [selfhost/typecheck.nq](../selfhost/typecheck.nq) exposes
  `typecheck_modules_for_entry`, `typecheck_const_facts`,
  `typecheck_value_facts_with_stmt_facts`, and
  `collect_resolved_binding_facts`.
- R2's immutable `visibility_index` stores source-order module runs. Semantic
  phase entries and handoff own an index; recursive indexed operations borrow
  it, while historical public entrypoints remain compatibility wrappers.
- [selfhost/type_text.nq](../selfhost/type_text.nq) provides shared type text
  rendering and parsing helpers.
- Some expression families are reconstructed from token spans in typecheck and
  handoff. Refactors must preserve grouping and diagnostic identity.

## Checked Boundary And Backend
- [selfhost/handoff.nq](../selfhost/handoff.nq) exposes
  `build_checked_handoff` and defines checked modules, declarations, bindings,
  blocks, statements, patterns, expressions, children, and type shapes.
- [selfhost/value_plan.nq](../selfhost/value_plan.nq) exposes
  `build_checked_type_properties` and `plan_checked_value_uses`.
- [selfhost/borrow.nq](../selfhost/borrow.nq) exposes
  `check_checked_handoff_borrows_with_value_plan` for the canonical path and
  retains `check_checked_handoff_borrows` as a compatibility helper.
- [selfhost/ir.nq](../selfhost/ir.nq) exposes
  `build_ir_program_for_entry_with_value_plan`,
  `build_ir_program_for_entry`, and `build_ir_program`.
- [selfhost/c_emit.nq](../selfhost/c_emit.nq) exposes `emit_c_program` and
  accepts IR collections rather than raw parser-fact collections.

The data-flow boundary is stronger than the current source-import boundary.
IR records still use `checked_binding_kind`, `checked_value_use_kind`, and
`checked_type_shape_kind`; consequently `ir.nq` and `c_emit.nq` retain imports
from checked/value-plan modules. Do not describe the import graph as completely
clean or the backend as representation-independent.

Missing checked truth is expected to fail closed through diagnostics.
Do not add name, source-offset, or raw-token guessing in borrow, IR, or C emit.

## Evidence, Formatting, And Proof

- [selfhost/builtin_evidence.nq](../selfhost/builtin_evidence.nq) owns the
  shared pure builtin IO-kind and propagation-error classifications. Facts
  and review retain their consumer guards and identity-bearing delegates;
  this is the bounded 2026-10-19 R3 extraction, not a universal builtin registry.
- [selfhost/facts.nq](../selfhost/facts.nq) exposes `emit_facts_format`,
  `emit_workspace_facts`, `validate_policy_summary`, `emit_policy_check`, and
  the plan-only `emit_refactor_rename_plan`.
- [selfhost/review.nq](../selfhost/review.nq) exposes versioned review emitters,
  `emit_review_diff_format`, and `emit_change_report`. Shared acceptance uses
  `build_source_contracts` and `validate_checked_mutation_contracts`.
- [selfhost/diag.nq](../selfhost/diag.nq) owns producer diagnostics and JSON.
- [selfhost/fmt.nq](../selfhost/fmt.nq) exposes `format_text` and `run_fmt`;
  this is formatter-lite, not an AST rewrite or general write-mode framework.
- [selfhost/proof.nq](../selfhost/proof.nq) exposes `run_nauq_tests`,
  `run_selfhost_proof`, and `run_all_proofs`.
- [selfhost/proof_artifacts.nq](../selfhost/proof_artifacts.nq) tracks produced
  proof artifacts and their digests.
- Focused owned test modules include contract evidence, schema profiles,
  integer/allocation policy, process behavior, workspace capture/evidence,
  proof artifacts, and string joining under [selfhost/](../selfhost/).

## Command Reach And Readiness

| Command family | Main reach | Important boundary |
| --- | --- | --- |
| `check` | Front end, handoff, value plan, borrow, and IR validation | Does not compile or execute host C. |
| `emit-c` | `check` path plus C emission and file output | Does not establish host compile/runtime success. |
| `build` | Emit C plus `compile_host_c_program` | Produces an executable; does not run it. |
| `run` | Build plus process execution | Runtime success is input-specific evidence only. |
| `facts` | Checked front end plus safety pass and versioned facts | Not equivalent to a whole-program release gate. |
| `review` | Checked contracts, mutation coverage, safety pass, review output | Format versions expose different evidence. |
| `review-diff` | Two reviewed inputs and comparison | Comparison depends on stable identities. |
| `change-report` | Review/facts comparison plus optional policy evidence | Policy errors affect report success. |
| `policy-check` | Captured workspace facts against a policy sidecar | Validates named targets, not all compiler behavior. |
| `refactor-rename` | Checked evidence and a plan-only result | Must not modify source. |
| `fmt --check` | Formatter-lite comparison | Not semantic compilation evidence. |
| `test` | `run_nauq_tests` fixture/tooling suite | Owned regression evidence, not the full release gate. |
| `prove-selfhost` | Copied-selfhost fixed-point path | Narrow selfhost proof, not semantic completeness. |
| `prove-corpus` | Locked example corpus | Corpus-bounded behavior only. |
| `prove` | Combined proof orchestration and summary | Still distinct from host release/sanitizer gates. |
| `prove-seed` | Structural C comparison | A self-consistent compiler may still miscompile. |

Help/version and the preserved no-argument proof route have compatibility value.
Exact text, stream selection, exit status, aliases, and argument order matter.

## List-Backed Data And Identity Caveats

Most phase state is carried as parallel `list<T>` collections.
`list<T>` is move-only, while products derive copy/drop behavior from fields.
Passing `ref aggregate.list_field` is exercised by current fixtures.
Moving a non-copy value out of a field is rejected by borrow checking.
No inspected example establishes `mutref aggregate.list_field` as a supported
collector pattern.

Therefore a proposed `checked_project` aggregate is not assumed zero-copy or
effective. Before adoption, a focused prototype must collect into owned local
lists, move them once into a small returned product, borrow multiple fields
immutably at consumers, and inspect emitted C, cleanup, temporary, allocation,
and drop behavior.

Until then, keep aggregate work proposed and do not claim reduced copying.
Parallel lists also encode ordering and positional relationships; regrouping
must not change IDs, first-match order, source order, or diagnostics.

Function stable IDs are module-qualified as `fn:<module>::<name>`.
Moving a function between modules changes its facts/review identity even when
CLI bytes remain unchanged. The root policy currently protects
`fn:main::main` and `fn:main::run_change_report` in
[nauqtype.policy.json](../nauqtype.policy.json).

Driver decomposition therefore needs an explicit compatibility decision:
retain policy-protected wrappers in `main`, or perform a reviewed identity
migration with policy, golden, and downstream stable-ID updates. Moving other
helpers can still change call-edge and review evidence.

## Verification Locations
- Narrow source fixtures: [tests/fixtures/](../tests/fixtures/).
- Locked expected JSON/text: [tests/golden/](../tests/golden/).
- Evidence schemas: [schemas/](../schemas/).
- Compiler-owned suites and proof routing: [selfhost/proof.nq](../selfhost/proof.nq).
- Complete owned fixture/tooling tier, with verified warm reuse when valid:
  [scripts/check_fast.sh](../scripts/check_fast.sh). It is not a suite selector.
- Seed fixed-point proof: [scripts/check_seed_bootstrap.sh](../scripts/check_seed_bootstrap.sh).
- Ownership sanitizers: [scripts/check_m53_ownership.sh](../scripts/check_m53_ownership.sh).
- Linux copied-release gate: [scripts/check_linux_alpha.sh](../scripts/check_linux_alpha.sh).
- Release construction/verification: [scripts/make_linux_release.sh](../scripts/make_linux_release.sh)
  and [scripts/verify_linux_release.sh](../scripts/verify_linux_release.sh).
- Full milestone close: [scripts/check_milestone.sh](../scripts/check_milestone.sh).
- Stable release requirements: [STABLE_RELEASE.md](../STABLE_RELEASE.md).

Choose the smallest focused evidence while iterating.
Do not substitute a focused check for a required audited milestone/release gate.

## First Refactor Seams

These are candidate seams, not implemented or approved changes. The grouping
below is not execution order; [REFACTOR_PLAN.md](REFACTOR_PLAN.md) keeps
PRE-M56 attribution/efficiency first.

1. Split CLI parsing/dispatch while preserving protected stable IDs and exact
   CLI observations.
2. Prototype common checked-project assembly before replacing duplicated
   command pipelines; prove ownership and cleanup behavior first.
3. Consolidate builtin arity/type/borrow/effect/runtime-name facts after the
   current builtin work is frozen, preserving builtin priority and evidence.
4. Move shared checked/value enums only with an explicit backend-contract
   decision; preserve enum members, ordering, records, and generated C.
5. Add private stable range/index helpers for repeated handoff, borrow, and C
   emission scans, preserving source order and diagnostic order.
6. Share host evidence-publication mechanics only if schemas, paths, signals,
   budgets, failure cleanup, attestations, and mandatory proof edges remain
   unchanged.

Any performance claim requires measurement on a frozen candidate.
Any source or seed change requires the repository's normal audit and gate order.
