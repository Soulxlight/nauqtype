# M56.1: Generic-Aware Facts And Review

Status: draft for Gate A review, 2026-10-31. Not implemented. Base: `e34d459`.
Sequencing approved by the owner on 2026-10-30 (ROADMAP M56.1); this draft
scope is proposed by the compiler lead and pending Gate A. Closing evidence
will be recorded in AUDIT_REMEDIATION, not here.

## Problem And Pressure

M56 lets programs declare generic functions, products, and enums, but every
evidence command rejects a generic source graph with NQ-GENERIC-008. A
supervisor therefore gets no facts or review output for any program that uses
generics, and M57 cannot ship generic collections that its own evidence
surfaces can describe. M56.1 adds one new version of `facts` and one of
`review` that describe generic code truthfully. Nothing else changes.

## Surface

- `nauqc facts <path> --format v5` and `nauqc review <path> --format v5`.
- No source syntax, audit clause, diagnostic code renumbering, or runtime
  change.
- Unchanged and still rejecting generic graphs with NQ-GENERIC-008:
  `facts` v1-v4, `review` v1-v4, `review-diff` (all formats),
  `change-report` (all formats), `policy-check`, and `refactor-rename`.
- On nongeneric input, v5 output equals the corresponding v4 output except
  for `version`, `identity_scheme`, and the added generic sections, which are
  empty arrays. This is a locked oracle (see Tests).

Base formats: facts v5 extends facts v4 (workspace scheme, captured
provenance); review v5 extends review v4 (checked call-aware may-write
coverage). The identity schemes become `nauqtype.workspace.v2` (facts v5) and
`nauqtype.semantic.v2` (review v5). A v2 scheme adds template and instance
identity forms only; every identity a v1 scheme can express is byte-identical
in v2.

## Identity Rules

1. **Templates are source declarations.** A generic function, product, or
   enum is reported once, at its ordinary source identity in the scheme
   (`fn:collections::assoc_get`,
   `workspace:app::module:collections::fn:assoc_get`). Type parameters are
   listed separately, never folded into the template identity.
2. **Instances get their own identity.** An instance identity is its template
   identity followed by the rendered type-argument list in angle brackets:
   `fn:collections::assoc_get<str,i32>`. Arguments render as:
   builtin scalars by canonical name (`i32`, `i64`, `bool`, `str`, `unit`,
   `bytes`); builtin containers as `list<A>`, `option<A>`, `result<A,E>`;
   nominal types by their full type identity in the same scheme
   (`type:app::Name`); generic nominal instances recursively by their instance
   identity. No spaces. The existing 16384-byte key bound applies to the
   rendered list; exceeding it fails closed (NQ-GENERIC-005).
3. **Generated names never appear.** No output field may contain a `__nqg_`
   name, a hex-encoded key, or an internal `f|`/`t|`/`v|` key. In a generic
   graph every elaborated nominal name (including nongeneric types, which M56
   also renames) is decoded back to its source identity.
4. **Positions are original source.** Every `span.start` and every `@<at>`
   suffix is a byte offset into the original source file, obtained through
   the M56 origin map. Positions inside an instance body point at the template
   text. Site identities stay unique because they are prefixed by the
   instance identity: `call:collections::assoc_get<str,i32>@412`.
5. **Fail closed.** If any reported item cannot be mapped to an original span
   and source identity, the command emits no stdout and fails with
   NQ-GENERIC-009 (invalid origin) or a new NQ-GENERIC-010 (generated item
   has no source identity). There is no partial output.
6. **Determinism.** Arrays are ordered by identity string (bytewise), then by
   original offset. Output must not depend on instance discovery order,
   worklist counters, or host paths.

## New Sections

### `generic_templates` (facts v5 and review v5)

One entry per generic declaration in the analyzed graph, used or unused:
`id`, `kind` (`function`, `type`, `enum`), `module`, `name`, `public`,
`type_parameters` (ordered names), `span`, `instances` (sorted instance
identities, possibly empty), and `evidence: "declared"`. Review v5 adds the
declared `audit` for function templates exactly as written. Templates have
no `inferred` field: template bodies are only structurally validated, not
type-checked, so no truthful template-level inference exists.

### `generic_instances` (facts v5) and instance entries (review v5)

Facts v5 lists each instance in a `generic_instances` array: `id`,
`instance_of` (template identity), `kind`, `type_arguments` (rendered,
ordered), `application_sites` (sorted, deduplicated `{module, span}` records
from the M56 `A` records; a site inside another instance also names that
`enclosing_instance`), and `evidence: "checked"`.

Review v5 reports each function instance as an ordinary entry in
`functions`, with the v4 fields plus `instance_of`, `type_arguments`,
`application_sites`, and `audit_source: "template"`. Its `audit` is the
template's declared audit after M56's `propagates(E)` substitution. Its
`inferred` facts and mutation coverage are computed on the checked instance,
exactly as for a nongeneric function. Instances of one template may differ in
inferred facts; v5 reports each instance and does not merge or summarize them.

### References and call edges

Calls and references from or to an instance use instance identities.
`target_kind` gains `function_instance`; such edges also carry
`target_instance_of`. Facts v5 `exports` include public templates (kinds
`function_template`, `type_template`, `enum_template`) and never instances.

## Compiler Changes (expected write set, refined at implementation)

- `selfhost/main.nq`: `--format v5` parsing for both commands, new driver
  modes, `allow_generics=true` only for the two v5 routes, usage text.
- `selfhost/generic.nq`, `selfhost/generic_auth.nq`: retain a template
  record for every generic declaration (including unused ones), and expose a
  checked parser for the existing `I`/`A`/`N`/`V` origin records. Origin
  records stay internal.
- `selfhost/facts.nq`, `selfhost/review.nq`: v5 emitters and identity
  rendering through one shared generic-identity helper (new module allowed;
  register it in `proof.nq` `push_selfhost_modules` and the seed inventory).
- `selfhost/build_info.nq`, `tests/golden/cli/help.txt`: help text.
- `schemas/facts-v5.schema.json`, `schemas/review-v5.schema.json` within the
  bounded profile in `EVIDENCE_SCHEMA_PROFILE.md`, registered in
  `schema_profile_tests.nq` (positive map, presence list, coherence
  negatives) and the profile document.
- Docs: AI_CONTRACTS, SPEC/README evidence summaries, DECISIONS entry,
  DEFERRED, ROADMAP/TODO status lines.

## Tests And Acceptance Fixture

Acceptance fixture `tests/fixtures/m56_1_evidence/`: a manifest workspace
with a provisional map/set-shaped module of the kind M57 will ship (generic
`Assoc<K, V>` product over `list<K>`/`list<V>`; generic new/put/get/len
functions; a generic `Bag<T>`), used from a separate application module.
It must cover:

- two instances of one template with different builtin arguments;
- a nominal type argument and a nested generic argument;
- a template that calls another template (an application site inside an
  instance);
- a cross-module application;
- a `propagates(E)` template with substituted error types;
- an unused public template (appears in `generic_templates` with no
  instances);
- a nongeneric type in the same graph (decoded, not mangled).

Required checks (Nauqtype-owned, in `nauqc test`):

- v5 goldens for the fixture, validated against the new schemas; repeat run
  is byte-identical.
- No `__nqg_` or internal key text anywhere in v5 output.
- Every `span.start` in fixture output lies inside the named original file
  and on the expected token.
- v4-equivalence oracle: for every existing facts v4 and review v4 golden
  input, v5 output minus the allowed differences equals the v4 golden.
- Existing goldens for all formats are byte-identical; the M56
  `m56_legacy` refusal cases still pass; the same refusal holds for
  `review-diff`, `change-report`, `policy-check`, and `refactor-rename` on
  the fixture.
- Negative cases: forged `__nqg_` source still fails with NQ-GENERIC-006;
  an exceeded rendered-argument bound fails closed.

Close: independent Gate A review of this contract; implementation with
focused checks; one independent trailing audit (schema change, routine
category under AGENTS.md); exact seed regeneration; one full
`scripts/check_milestone.sh` on the frozen candidate.

## Out Of Scope

Generic-aware `review-diff`, `change-report`, `policy-check`, or
`refactor-rename`; template-level inferred facts or merged instance
summaries; type-argument inference; constraints or traits; any change to
existing formats.

## Input For M57

Template bodies are checked only per concrete instance, so a generic map's
key comparison (`key == candidate`) type-checks for any instance whose key
type supports `==` and fails only when instantiated with one that does not.
M57's "explicit checked key strategy" must decide whether that per-instance
checking is acceptable or whether a declared key requirement is needed.
M56.1 evidence reports per-instance facts either way.
