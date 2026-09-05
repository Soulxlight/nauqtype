# Nauqtype AI Contracts

## Purpose

AI Contracts are Nauqtype's first explicitly AI-first language feature.

They are designed to make AI-authored code easier to supervise by attaching a small, fixed-shape, compiler-checked review surface to functions.

## Alpha Surface

Current syntax:

```nauq
pub fn bump(value: mutref i32) -> unit
audit {
    intent("Increment a counter in place");
    mutates(value);
    effects();
    propagates();
}
{
    value = value + 1;
    return;
}
```

## Alpha Rules

- Clause order is fixed: `intent`, then `mutates`, then `effects`, then optional `propagates`.
- `intent("...")` is required and must be non-empty.
- `mutates(...)` may list only `mutref` parameters.
- `effects(...)` currently supports the fixed atoms `print` and `io`.
- `propagates(...)` may list exact error types forwarded unchanged by statement-boundary `?`.
- Public functions without `audit` are allowed in this phase, but they emit a warning.
- Compilation and evidence commands share source-contract validation. An
  invalid declaration is not accepted merely because the command is `facts`,
  `build`, or `policy-check`; policy sidecars remain advisory and separate.
- Malformed fixed clause grammar reports `NQ-CONTRACT-002`. Duplicate list
  entries report `NQ-CONTRACT-010`; unresolved or non-type propagation names
  report `NQ-PROPAGATE-006`. A trailing comma is allowed, an empty entry is not.

## Compiler Inference

- Mutation validation uses checked binding identities for direct assignments,
  `list_push`, and resolved local/imported calls. Argument mapping follows
  canonical parameter indexes, including reordered named arguments.
- A finite fixed point propagates parameter may-writes through recursive
  calls. Shadowing locals remain separate bindings. Owned-local field writes
  are outside the outward mutable-parameter contract.
- `print` is inferred directly from `print_line(...)` / `eprint_line(...)` calls and transitively through checked calls.
- `io` is inferred directly from authority-bearing argument, environment, cwd, stream, filesystem, and process builtins and transitively through checked calls.
- Facts v2 and review v2 expose checked IO evidence in canonical order as `read`, `write`, `create_dir`, `process`, `arguments`, `environment`, `cwd`, `stdin`, `stdout`, `stderr`, `metadata`, `traversal`, `create_file`, `temporary`, `remove`, `rename`, and `atomic_replace`; these subkinds are descriptive evidence, not new audit atoms.
- Propagation is inferred from accepted `let name = result_expr?;` sites and checked against exact `propagates(E)` entries.
- Missing inferred facts are errors.
- Overdeclared facts are warnings.
- Known parameter writes omitted from `mutates(...)` are errors, even when
  coverage is partial. An overdeclaration warning requires complete coverage.
  Every current builtin has a mutation summary; an unmodeled future builtin
  makes its caller and transitive callers partial rather than pure.

## Review Output

`nauqc review <file>` emits deterministic JSON containing:

- module name
- function name
- visibility
- declared audit data
- compiler-inferred mutation, effect, and propagation facts

`nauqc review <file> --format v2` keeps the same contract validation behavior and emits the first richer AI-first review surface:

- stable function identities
- stable call-site identities
- call references with resolved target identity where available
- call graph edges
- propagation contracts and checked propagation sites
- legacy evidence fields; v2 incorrectly labels absent audits as declared

`nauqc review <file> --format v3` is the first explicit provenance migration.
It preserves the v2 identities and successful-output structure, but makes
`evidence.audit` exactly `absent` for `audit: null`, otherwise `declared`.
`inferred.mutates` now comes from checked assignment target/binding/parameter
IDs, with names deduplicated in parameter-index order. A shadowing local is
not the parameter it happens to share a name with.

Every v3 function has this fixed capability-level evidence:

```json
"mutation_coverage": {
  "interpretation": "lower_bound",
  "scope": "direct_mutref_parameter_assignments",
  "completeness": "partial",
  "uncovered": ["builtin_call_writes", "local_call_writes", "imported_call_writes"]
}
```

This object is inside `evidence`, alongside `audit` and `inferred`.
It describes syntactically observed writes, not path feasibility. Empty
`mutates` does not prove purity or a complete footprint, even for a call-free
function. Owned-local field writes are outside this parameter contract.
Effects, IO kinds, and propagation retain their existing analysis.
M54.8's final correction now validates source contracts using the shared
call-aware analysis in every command/version. v3's successful evidence stays
direct-only and partial for compatibility; use v4 for the broader footprint.

v3 is opt-in and successful-output-only. Errors return nonzero, empty stdout,
and diagnostics on stderr; warnings remain nonfatal and appear once.
`review-diff` still accepts only v1/v2. The strict
[review-v3 schema](schemas/review-v3.schema.json) describes audit/evidence
coherence without changing its historical partial footprint.

`nauqc review <file> --format v4` preserves those identities and audit
provenance while emitting checked call-aware may-writes. Its coverage is:

```json
"mutation_coverage": {
  "interpretation": "syntactic_may_write",
  "scope": "checked_mutref_parameters",
  "completeness": "complete",
  "uncovered": []
}
```

An unmodeled builtin instead produces `partial` with the single uncovered
category `unmodeled_builtin_summary`. Complete coverage describes this fixed
syntactic parameter analysis, not reachability, purity, effects, or every
possible ownership property. Missing required checked identities fail with
`NQ-INTERNAL-012`, never a guessed empty footprint. v4 is also opt-in and
successful-output-only; diagnostics remain on stderr and warnings are nonfatal.

`nauqc review-diff <before> <after>` consumes the same checked review facts and emits deterministic JSON for semantic changes:

- added, removed, and changed functions by stable `fn:<module>::<name>` identity
- added and removed call graph edges by caller-to-callee identity
- summary counts suitable for agent-pair review triage and human supervision

`nauqc review-diff <before> <after> --format v2` preserves the v1 change shape and adds evidence metadata for the checked before/after inputs and the semantic-identity comparison basis.

`nauqc change-report <before> <after> --format v1` combines the semantic diff basis with deterministic evidence and diagnostics for supervised change review. With `--policy <path>`, it also reports advisory policy target status without approving, repairing, or mutating code.

`nauqc change-report <before> <after> [--policy <path>] --format v3` retains
the workspace dependency/call-impact report introduced by v2 and corrects
policy truth. Absent policy has `provided: false`, no path/targets/errors, and
evidence `absent`. A valid supplied policy is `checked`. Invalid, malformed,
or unreadable supplied policy is `failed`, with nonzero errors and `ok: false`;
`malformed` is explicit. No policy becomes compiler enforcement or approval.

For review-diff v1/v2 and change-report v1/v2/v3, source/load failures now
emit [evidence-error v1](schemas/evidence-error-v1.schema.json) instead of a
success-shaped or misleading v1 fallback document. The exact fields are
`version`, `command`, `requested_format`, `ok: false`, `stage`, `code`, and
`message`. Stages distinguish before/after load/check, and exit remains 1.
Consumers must inspect this envelope before assuming the requested success
shape. Unsupported CLI formats remain ordinary argument errors.

This output is intended to be consumed by both humans and future AI tooling.

During the current Nauqtype-only toolchain transition, `facts`, `review`, `review-diff`, `change-report`, `refactor-rename`, `policy-check`, and `fmt` are now owned by the active stage1 executable driver alongside `check`, `emit-c`, `build`, `run`, and the proof/corpus gates. The frozen stage0 path remains in-repo only as bootstrap/reference code.

The broader AI-first compiler surface also includes `nauqc facts <file>`, which
exports checked definitions, references, and call graph edges. Its output is
different from `review`, but both commands require the same valid source
contracts. Review renders the already-extracted, validated declarations rather
than applying a second acceptance policy.

Legacy review v1/v2 and change-report v1/v2 success documents stay unchanged;
in particular, v2's absent-audit and absent-policy labels must not be treated
as stronger evidence. New consumers should use review v4 and change-report v3.
The Nauqtype-owned `test` and `prove` gates validate every owned schema against
mapped evidence and reject coherence-negative fixtures using
`nauqtype.evidence-schema-profile.v1`. This is an explicitly bounded fixture
validator, not full Draft 2020-12 or a general JSON library. Its supported
keywords, string/number bounds, and exclusions are documented in
[EVIDENCE_SCHEMA_PROFILE.md](EVIDENCE_SCHEMA_PROFILE.md); it does not narrow
the compiler's source language or public JSON string support.

## Supervised Workflow Alpha

The alpha workflow is deliberately command-composed instead of hidden behind a new orchestration command:

1. `check` proves the changed program is accepted.
2. `facts --format v2` exports checked definitions, references, call graph edges, and evidence.
3. `review --format v2` exports function-level contract and call evidence.
4. `review-diff --format v2` compares before/after checked semantic identities.
5. `change-report --policy --format v1` combines semantic changes with advisory policy status.
6. `policy-check` validates ownership/review sidecars against checked facts.
7. `refactor-rename` emits deterministic edit plans only; it does not mutate files.

The canonical fixture for this loop lives under `tests/fixtures/supervised_workflow`, and the stage1-owned `prove` gate checks its goldens. This is the intended human-supervision model: agents can propose and explain, but the review substrate is deterministic compiler evidence.

## Compatibility Rules

- Existing v1 outputs remain stable unless a new version is explicitly introduced.
- Additive evidence belongs in v2-style surfaces, not by silently changing v1 shapes.
- Schema `$id`, `version`, `command`, and `identity_scheme` values are compatibility anchors.
- Policy sidecars are advisory metadata; `check`, `build`, and `run` do not enforce them.
- Refactor output remains plan-only until an explicit apply/write milestone is accepted.

## Propagation Contract

Statement-boundary `?` and explicit local `try` boundaries extend the same compiler-evidence model, not hidden Rust-style control flow.

- `let name = result_expr?;` forwards unchanged `result<T, E>` errors only when the enclosing function returns `result<_, E>`.
- Accepted `?` sites infer exact error-type propagation into `propagates(...)`.
- `let value: result<T, E> = try { expression }` captures failure locally; its sites remain checked evidence but do not inflate function-level `propagates(...)`.
- Local-boundary propagation order is deterministic, depth-first, and left-to-right. The boundary is visible in source rather than silently targeting an enclosing function.
- Propagation evidence uses explicit versioned facts/review/change-report surfaces instead of silently changing locked schemas.
- Function-scoped expression `?`, multi-statement `try`, `option<T>?`, implicit error conversion, and custom propagation protocols remain deferred.

See [PROPAGATION.md](PROPAGATION.md) for the locked design direction.

## Semantic Facts v1 Contract

`facts` output is versioned and locked by `schemas/facts-v1.schema.json`.

- `version` is `1`, and `identity_scheme` is `nauqtype.semantic.v1`.
- Definitions use stable prefixes such as `module:`, `fn:`, `type:`, `enum:`, `variant:`, `const:`, `field:`, and `binding:`.
- References include imports, type references, name references, resolved target kind, resolved target id, and source span.
- Call graph entries use stable caller/callee identities plus a call-site id.
- The command runs only after the checked stage1 front-end and borrow safety path succeeds, so agents can distinguish checked facts from unchecked text.

## Semantic Facts v2 Contract

`facts <file> --format v2` preserves the v1 shape and adds explicit evidence fields.

- Definitions use `declared` for source declarations and `checked` for compiler-confirmed binding identities.
- References and call edges use `checked` for resolved semantic targets, `builtin` for builtin targets, `declared` for imports, and `unresolved` when a retained boundary prevents target proof.
- Copy-only record update uses checked field references for both explicit overrides and inherited fields. `record_update_inherit` is evidence-only: it proves the inherited field target but does not imply there is a source field label to edit.
- Full-tree `facts selfhost/main.nq` is a standing bounded-performance gate on Windows.

## Plan-Only Refactors And Policy Sidecars

`refactor-rename <source> <stable-id> <new-name>` emits a deterministic JSON edit plan for supported function, type/enum, variant constructor, top-level const, field, and local/param/pattern binding identities. It never mutates files. Field renames are driven by checked editable field definition/use references in the facts surface; inherited record-update evidence is intentionally not editable. Parameter renames also update checked named-argument labels.

`policy-check <source> <policy-path>` validates `nauqtype.policy.json` v1 sidecars against checked facts. The sidecar is advisory metadata for owners and review expectations; `check`, `build`, and `run` do not enforce it yet.

## Explicit Non-Goals For Alpha

- NLP validation of `intent(...)`
- Rich or user-defined effect taxonomies
- Cross-file contract propagation
- Typed holes or repair obligations
- Strong transitive mutation inference
- Semantic language-feature expansion inside the AI tooling spine

Those remain future work until the alpha proves its value.
