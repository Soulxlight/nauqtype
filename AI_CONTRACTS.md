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

## Compiler Inference

- Mutation inference is direct only in this phase.
- The compiler marks a `mutref` parameter as mutated when the function writes through that parameter.
- `print` is inferred directly from `print_line(...)` / `eprint_line(...)` calls and transitively through checked calls.
- `io` is inferred directly from `read_file(...)`, `write_file(...)`, `create_dir_all(...)`, and `run_process(...)` calls and transitively through checked calls.
- Facts v2 and review v2 expose checked IO evidence as `read`, `write`, `create_dir`, or `process`; these subkinds are descriptive evidence, not new audit atoms.
- Propagation is inferred from accepted `let name = result_expr?;` sites and checked against exact `propagates(E)` entries.
- Missing inferred facts are errors.
- Overdeclared facts are warnings.

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
- evidence fields that distinguish declared audit data from checked compiler inference

`nauqc review-diff <before> <after>` consumes the same checked review facts and emits deterministic JSON for semantic changes:

- added, removed, and changed functions by stable `fn:<module>::<name>` identity
- added and removed call graph edges by caller-to-callee identity
- summary counts suitable for agent-pair review triage and human supervision

`nauqc review-diff <before> <after> --format v2` preserves the v1 change shape and adds evidence metadata for the checked before/after inputs and the semantic-identity comparison basis.

`nauqc change-report <before> <after> --format v1` combines the semantic diff basis with deterministic evidence and diagnostics for supervised change review. With `--policy <path>`, it also reports advisory policy target status without approving, repairing, or mutating code.

This output is intended to be consumed by both humans and future AI tooling.

During the current Nauqtype-only toolchain transition, `facts`, `review`, `review-diff`, `change-report`, `refactor-rename`, `policy-check`, and `fmt` are now owned by the active stage1 executable driver alongside `check`, `emit-c`, `build`, `run`, and the proof/corpus gates. The frozen stage0 path remains in-repo only as bootstrap/reference code.

The broader AI-first compiler surface now also includes `nauqc facts <file>`, which emits checked definitions, references, and call graph edges independently from audit-contract review. That separation is intentional: `facts` gives agents stable program structure, while `review` evaluates the fixed-shape human-supervision contract.

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
