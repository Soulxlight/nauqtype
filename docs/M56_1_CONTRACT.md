# M56.1: Generic-Aware Facts And Review

Status: Gate A passed, 2026-10-31 (revision 3). Not implemented. Base:
`bec86b0`. Sequencing approved by the owner on 2026-10-30 (ROADMAP M56.1);
this scope is proposed by the compiler lead. The independent Gate A reviewer
(gpt-5.6-sol xhigh) required changes on revisions 1 and 2 and approved
revision 3 with no findings. Closing evidence will be
recorded in AUDIT_REMEDIATION, not here.

## Problem And Pressure

M56 lets programs declare generic functions, products, and enums, but every
evidence command rejects a generic source graph with NQ-GENERIC-008. A
supervisor gets no facts or review output for any program that uses generics,
and M57 cannot ship generic collections that its own evidence surfaces can
describe. M56.1 adds one new version of `facts` and one of `review` that
describe generic code truthfully. Nothing else changes.

## Surface

- `nauqc facts <path> --format v5` and `nauqc review <path> --format v5`.
- No source syntax, audit clause, or runtime change. Two diagnostics gain the
  exact meanings below (NQ-GENERIC-009 widened, NQ-GENERIC-010 new).
- Unchanged and still rejecting generic graphs with NQ-GENERIC-008:
  `facts` v1-v4, `review` v1-v4, `review-diff` (all formats),
  `change-report` (all formats), `policy-check`, and `refactor-rename`.
- facts v5 extends facts v4 (workspace scheme, captured provenance; no
  references array is added). review v5 extends review v4. Identity schemes
  become `nauqtype.workspace.v2` (facts v5) and `nauqtype.semantic.v2`
  (review v5). A v2 scheme only adds the instance forms defined below; every
  identity expressible in v1 is byte-identical in v2.

## Rendering Grammar

All type arguments in public output use one recursive grammar. Source `int`
canonicalizes to `i32`; no spaces are emitted.

```text
args      := "<" arg ("," arg)* ">"
arg       := atom | container | nominal | nominal_instance
atom      := "bool" | "i32" | "i64" | "f64" | "str" | "unit" | "bytes" | "io_err"
           | "process_result" | "path_metadata" | "duration" | "instant"
           | "process" | "process_outcome"
container := "list<" arg ">" | "option<" arg ">" | "result<" arg "," arg ">"
nominal   := the type or enum identity of a nongeneric nominal in the
             output's scheme (e.g. "type:app::Name",
             "workspace:org.tool::module:app::enum:Mode")
nominal_instance := the identity of a generic nominal template in the
             output's scheme, followed by args
```

The atom list is the checked builtin set in `selfhost/handoff.nq`
(`canonical_type_origin_module`) of the accepting compiler. Adding a builtin
type to that set adds an atom without a format change, provided every source
that mentions the new name was a hard error before (so no output for any
previously accepted input changes) and the name contains no `:` (so the
injectivity argument below is unchanged). This sentence was amended by M56.2,
which added `f64` under that rule (D067); `i64` (M53) is the precedent.
Injectivity: atoms and container heads contain no `:`; every nominal begins
with `type:`, `enum:`, or `workspace:`; source identifiers cannot contain
`<`, `>`, `,`, `:`, or `@`. Parsing is therefore unambiguous left to right.

**Bound.** Every newly constructed generic identity (an instance identity,
a site identity inside an instance, or a rendered `type_arguments` entry) is
at most 32768 bytes. The emitter computes the length before building the
string; exceeding the bound fails closed with NQ-GENERIC-005 and empty
stdout. Identities that v4 can already express (all nongeneric items and
templates) are not capped, so the nongeneric oracle below holds for every
input v4 accepts. The existing M56 internal bounds (4096-byte nominal keys,
16384-byte function keys) are unchanged and apply first.

## Identity Forms

| Item | Semantic scheme (review v5) | Workspace scheme (facts v5) |
| --- | --- | --- |
| Generic function template | `fn:m::name` (ordinary v1 form) | `workspace:w::module:m::fn:name` |
| Function instance | `fn:m::name` + args | `workspace:w::module:m::fn:name` + args |
| Generic product/enum template | `type:m::N` / `enum:m::N` | `...::type:N` / `...::enum:N` |
| Product/enum instance | template identity + args | template identity + args |
| Variant of an enum instance | `variant:m::E` + args + `::V` | `workspace:w::module:m::enum:E` + args + `::variant:V` |
| Site inside an instance (call, reference, propagation) | v1 site prefix with the enclosing instance identity, `@` original offset, e.g. `call:m::get<str,i32>@412` | same rule over the workspace identity |

Templates are reported once at their ordinary source identity; type
parameters are listed in a separate field. Generated names (`__nqg_...`),
hex-encoded keys, and internal `f|`/`t|`/`v|` keys never appear in any
output field. In a generic graph M56 also renames nongeneric nominal types
and their variants; v5 decodes every such name back to its source identity.

## Positions

Every `span.start` and every `@<at>` suffix is a byte offset into the
original source file, mapped through the M56 origin map. Positions inside an
instance body point at the template text; uniqueness comes from the instance
prefix. A template declaration's span is its name token, as for nongeneric
declarations in v4.

## Field Mapping (v4 to v5)

Nongeneric items in a generic graph keep exactly their v4 fields and values,
with names decoded. Generic items map as follows.

**review v5 top level:** v4 fields unchanged; one new array
`generic_templates`, emitted on its own line immediately after the
`identity_scheme` line.

**`generic_templates[]` (review v5 and facts v5):** `id` (template identity),
`kind` (`function`, `type`, `enum`), `module`, `name`, `public`,
`type_parameters` (ordered names), `span`, `instances` (sorted instance
identities; empty for unused templates), `evidence: "declared"`. review v5
adds `audit` (declared audit as written, with type-parameter names in
`propagates`) and `audit_evidence` (`declared` or `absent`). No `inferred`
field: template bodies are only structurally validated.

**review v5 `functions[]` instance entries:** `id` = instance identity;
`kind` = `function_instance`; `qualified_name` = `m::name` + args;
`module`, `name`, `public` = the template's; `span` = template name token;
`audit` = template audit after M56's `propagates(E)` substitution;
`evidence.audit` = template's; `inferred` and `mutation_coverage` = computed
on the checked instance as for any v4 function; plus `instance_of`,
`type_arguments` (rendered `arg` list), `application_sites`, and
`audit_source: "template"`. Instances of one template may differ in inferred
facts; v5 reports each and never merges them.

**Calls, `references[]`, `call_graph[]`:** every v4 field is kept. `from`,
`caller`, `callee`, `call_site`, `id`, and `target_id` use instance
identities where the endpoint is an instance. `target_kind` gains
`function_instance` and `variant_instance`; such records also carry
`target_instance_of` (the template function identity, or the template
variant identity `variant:m::E::V`). `target_module` and `name` are the
template's source module and source name.

**Propagated errors (`audit.propagates`, `inferred.propagates`,
`propagation_sites[]`):** for a builtin atom or nongeneric nominal error, the
spelling, `target_kind`, and `target_id` follow the v4 rule, decoded. For a
generic nominal instance error (M56 admits one substituted for `E`), the
error is spelled with its public instance rendering (the `nominal_instance`
form of the grammar), `target_kind` is `type_instance` or `enum_instance`,
`target_id` is the instance identity, and the record adds
`target_instance_of` (the template identity). Propagation-site `id` and
`function` use the enclosing instance identity. Generated text never
appears.

**facts v5:** v4 top level unchanged plus `generic_templates` and
`generic_instances`, each on its own line immediately after the
`identity_scheme` line. `summary` keys and meanings are unchanged (export and
call-edge counts include generic items naturally). `exports[]` adds public
templates with kinds `function_template`, `type_template`, `enum_template`,
a `type_parameters` field, `legacy_id` = the semantic-scheme template
identity, and `evidence: "declared"` (never `"checked"`: template bodies are
only structurally validated). The schema ties template kinds to
`"declared"`. Instances are never exports. `call_graph[]` endpoints use instance
identities. `generic_instances[]`: `id`, `instance_of`, `kind`
(`function`, `type`, `enum`), `type_arguments`, `application_sites`,
`evidence: "checked"`.

**`application_sites[]`:** sorted, deduplicated `{module, span}` records
from the M56 `A` records. A site inside another instance adds
`enclosing_instance` (that instance's identity); one template site
instantiated under two enclosing instances therefore appears twice, once per
enclosing instance.

## Retention And Metadata Validation

The elaborator must retain, and v5 must validate before emitting anything:

- exactly one template record per generic declaration, used or unused, with
  kind, visibility, ordered parameter names, declaration and name ranges,
  and (for functions) the audit block range;
- the existing instance (`I`), application (`A`), generated-declaration
  (`D`), nongeneric-nominal (`N`), and variant (`V`) records, parsed by one
  checked reader.

Required invariants: template, `I`, `D`, `N`, and `V` keys are unique within
their record kind. `A` is a relation, not a keyed record: many `A` records may
name the same instance; only the complete
`(instance, module, start, end, parent)` tuple is deduplicated (during
retention or checked parsing). Every `I` names an existing template of the
same kind and arity; every `A` names an existing `I`, and a nonempty parent
names an existing `I`; every generated declaration
corresponds to exactly one `I`, `N`, or `V`; every `V` names an existing enum
key; every offset lies inside its original file; no orphaned records.

- NQ-GENERIC-009: metadata is malformed or violates an invariant.
- NQ-GENERIC-010: metadata is valid but a generated item reached the emitter
  with no source identity.
- Both print a diagnostic, produce empty stdout, and exit 1. No partial
  output.

## Determinism And Compatibility

Arrays are ordered by identity string (bytewise), then original offset.
Output must not depend on instance discovery order, worklist counters, or
host paths.

**Nongeneric oracle (bytewise).** For every input that produces facts v4 or
review v4 output today, take the v5 bytes; replace `"version": 5` with
`"version": 4`; replace the v2 `identity_scheme` value with the v1 value;
delete exactly the line(s) `  "generic_templates": [],` and (facts)
`  "generic_instances": [],`. The result must equal the v4 bytes exactly,
including counts, ordering, workspace capture, and `legacy_id`.

## Write Set And Audit Classification

- `selfhost/main.nq`: v5 `--format` parsing, driver modes,
  `allow_generics=true` only for the two v5 routes, usage text.
- `selfhost/generic.nq`, `selfhost/generic_auth.nq`: template records,
  checked metadata reader, invariants, 009/010.
- `selfhost/generic_names.nq`: the shared argument renderer and bound check.
- `selfhost/facts.nq`, `selfhost/review.nq`: v5 emitters.
- `selfhost/build_info.nq`, `tests/golden/cli/help.txt`: help text.
- `schemas/facts-v5.schema.json`, `schemas/review-v5.schema.json` (bounded
  profile; sorting, uniqueness and cross-record integrity are emitter tests,
  not schema claims), registered in `schema_profile_tests.nq` and
  `EVIDENCE_SCHEMA_PROFILE.md`.
- Tests and fixtures as below; docs: AI_CONTRACTS, README/SPEC evidence
  summaries, DECISIONS entry, DEFERRED, ROADMAP/TODO status lines.

No new `.nq` module and no change to `push_selfhost_modules` or the seed
inventory rules. The seed is regenerated by unchanged machinery, so under
AGENTS.md this is a routine milestone with one independent trailing auditor.
If implementation needs a new module or any inventory/bootstrap change, stop,
record it, and reclassify as bootstrap-boundary with the mixed audit.

## Tests And Acceptance Fixture

Fixture `tests/fixtures/m56_1_evidence/`: a manifest workspace with a
provisional map/set-shaped module of the kind M57 will ship (generic
`Assoc<K, V>` product over `list<K>`/`list<V>`; generic new/put/get/len; a
generic `Bag<T>`) used from a separate application module, plus a locked
local dependency. It must cover:

- two instances of one template with different builtin arguments;
- the same instance applied at multiple sites;
- one template site instantiated under two enclosing instances;
- a generic enum with payload and zero-payload variants, used in
  constructors and `match` patterns;
- a template that calls another template; a cross-module application;
- opaque builtin arguments (e.g. `io_err`, `duration`) and source `int`
  rendered as `i32`;
- nongeneric, dependency, and nested generic nominal arguments;
- a nongeneric product and enum in the same graph (decoded identities);
- a `propagates(E)` template with substituted error types, including one
  instantiated with a generic nominal error (e.g. `Failure<str>`);
- the same nominal instance appearing twice within one explicit argument
  list;
- an unused public template (exported as `"declared"`, never `"checked"`).

Required Nauqtype-owned checks (in `nauqc test`):

- v5 goldens for the fixture, valid against the new schemas; repeat run
  byte-identical.
- No `__nqg_` generated name and no decoded internal generic key
  (`f|`, `t|`, `v|` forms) in any v5 output. Legitimate hexadecimal evidence
  inherited from v4 (e.g. SHA-256 provenance) is unaffected.
- Every `span.start` lies inside the named original file on the expected
  token.
- The bytewise nongeneric oracle over every existing facts v4 and review v4
  golden input.
- Existing goldens for all formats byte-identical; `m56_legacy` refusals
  unchanged; the same refusal for `review-diff`, `change-report`,
  `policy-check`, and `refactor-rename` on the fixture.
- Renderer unit cases: every atom, nested containers, `int`, nested nominal
  instances; an identity of exactly 32768 bytes accepted and 32769 rejected
  with NQ-GENERIC-005.
- Metadata negatives with exact codes and empty stdout: malformed framing,
  duplicate keys, orphaned `I`/`A`/`V`, cross-linked records (instance
  pointing at a template of another kind or arity), out-of-file offsets
  (009); a valid generated item with no source identity (010).
- Forged `__nqg_` source still fails with NQ-GENERIC-006.

Close: Gate A re-check of this revision; implementation with focused checks;
one independent trailing audit; seed regeneration through unchanged
machinery; one full `scripts/check_milestone.sh` on the frozen candidate.

## Out Of Scope

Generic-aware `review-diff`, `change-report`, `policy-check`, or
`refactor-rename`; a facts references array; template-level inferred facts
or merged instance summaries; type-argument inference; constraints or traits;
any change to existing formats.

## Input For M57

Template bodies are checked only per concrete instance, so a generic map's
key comparison (`key == candidate`) type-checks for any instance whose key
type supports `==` and fails only when instantiated with one that does not.
M57's "explicit checked key strategy" must decide whether that per-instance
checking is acceptable or whether a declared key requirement is needed.
