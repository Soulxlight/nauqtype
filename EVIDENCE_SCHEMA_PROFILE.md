# Evidence Schema Profile

M54.8 adds `nauqtype.evidence-schema-profile.v1`, a bounded owned validator for
Nauqtype evidence schemas. It is intentionally not a full Draft 2020-12
implementation.

## Public Hooks

- `schema_profile_accepts(schema_text: str, data_text: str) -> bool` in
  `selfhost/schema_profile.nq` parses both JSON texts, rejects malformed inputs
  fail-closed, validates the schema profile everywhere, then evaluates data.
- `run_schema_profile_selftests() -> bool` in
  `selfhost/schema_profile_tests.nq` runs local positive and negative profile
  cases without filesystem fixtures.
- `run_schema_profile_gate() -> bool` in
  `selfhost/schema_profile_tests.nq` runs the selftests, enumerates
  `schemas/*.schema.json` with `read_dir`, fails any unmapped schema, and checks
  each mapped positive evidence document.

Main/proof integration should import `schema_profile_tests` and call
`run_schema_profile_gate()` from the existing proof gate.

## Accepted Profile

The schema profile accepts only these schema keywords:

- annotations: `$schema`, `$id`, `title`
- local definitions: `$defs`, `$ref`
- assertions: `type`, `const`, `enum`, `properties`, `required`,
  `additionalProperties`, `items`, `minimum`, `minItems`, `minLength`,
  `pattern`, `anyOf`, `oneOf`

`$ref` is local only and must use `#/$defs/name`. Nonlocal refs, unresolved refs,
slashes in definition names, nested `$defs`, and reference cycles reject.

Patterns are exact built-ins, not arbitrary regex:

- `^module:`
- `^[a-f0-9]{64}$`
- `^(human|agent):`

Unknown keywords reject anywhere in the schema, including unused branches.
`anyOf` requires at least one matching branch. `oneOf` requires exactly one
matching branch.

## JSON Bounds

The private JSON parser supports the evidence subset needed by owned schemas:
objects, arrays, ASCII-only strings, booleans, null, and bounded base-10
integers. It rejects duplicate object keys after escape decoding, malformed
JSON, raw non-ASCII string bytes, non-ASCII `\u` escapes, unsupported
backspace/form-feed/carriage-return escapes, excess depth above 96,
decimal/exponent numbers, and integer tokens wider than nine digits.

String escapes support only `\"`, `\\`, `\/`, `\n`, `\t`, and ASCII `\u00XX`
style escapes for printable ASCII plus LF/TAB. JSON `\b`, `\f`, `\r`, and their
Unicode control-code analogues reject because the current Nauqtype lexer does
not expose those control characters as source string literals. `minLength` is
evaluated over accepted ASCII byte length, so non-ASCII text fails closed
instead of using UTF-8 byte length as a character count. This is a profile
parser for proof evidence, not a general JSON API or CLI.

## Schema Map

`run_schema_profile_gate()` currently maps every owned schema in `schemas/`:

- `change-report-v1.schema.json` -> `tests/golden/review/change_report_v1.json`
- `change-report-v2.schema.json` ->
  `tests/golden/workspace_governance/change_report_v2.json`
- `change-report-v3.schema.json` ->
  `tests/golden/workspace_governance/change_report_v3.json`
- `change-report-v4.schema.json` ->
  `tests/golden/workspace_governance/change_report_v4.json`
- `diagnostics-v1.schema.json` -> `tests/golden/diagnostics/check_failure.json`
- `evidence-error-v1.schema.json` ->
  `tests/golden/review/evidence_error_v1.json`
- `facts-v1.schema.json` -> `tests/golden/facts/main.json`
- `facts-v2.schema.json` -> `tests/golden/facts/main-v2.json`
- `facts-v3.schema.json` -> `tests/golden/organizational_tool/facts_v3.json`
- `facts-v4.schema.json` -> `tests/golden/organizational_tool/facts_v4.json`
- `facts-v5.schema.json` -> `tests/golden/schema_profile/facts-v5-positive.json`
- `nauqtype.policy-v1.schema.json` ->
  `tests/fixtures/workspace_local_dependency/policy.json`
- `nauqtype.workspace-lock-v1.schema.json` ->
  `tests/golden/schema_profile/workspace-lock-v1-positive.json`
- `nauqtype.workspace-lock-v2.schema.json` ->
  `tests/fixtures/workspace_local_dependency/nauqtype.workspace.lock.json`
- `policy-check-v1.schema.json` ->
  `tests/golden/evidence_parity/policy_check_v1.json`
- `proof-summary-v1.schema.json` ->
  `tests/golden/schema_profile/proof-summary-v1-positive.json`
- `proof-summary-v2.schema.json` ->
  `tests/golden/schema_profile/proof-summary-v2-positive.json`
- `proof-summary-v3.schema.json` ->
  `tests/golden/schema_profile/proof-summary-v3-success.json`, with separate
  skipped, failed, and mismatch positives
- `refactor-rename-v1.schema.json` ->
  `tests/golden/supervised_workflow/refactor_rename_v1.json`
- `review-diff-v1.schema.json` -> `tests/golden/review/review_diff_v1.json`
- `review-diff-v2.schema.json` -> `tests/golden/review/review_diff_v2.json`
- `review-v2.schema.json` -> `tests/golden/review/review_v2.json`
- `review-v3.schema.json` -> `tests/golden/review/review_v3.json`
- `review-v4.schema.json` -> `tests/golden/review/review_v4.json`
- `review-v5.schema.json` -> `tests/golden/schema_profile/review-v5-positive.json`

If a new schema appears without a mapping, the gate fails closed.

## Focused Evidence

Focused checks run for this slice:

- `selfhost/build/nauqc check selfhost/schema_profile.nq`
- `selfhost/build/nauqc check selfhost/schema_profile_tests.nq`
- copied probe build/run with `selfhost/build/nauqc` calling
  `run_schema_profile_selftests()`
- copied probe build/run with `selfhost/build/nauqc` calling
  `run_schema_profile_gate()`

The gate also includes real-schema negative coherence checks against
`review-v3.schema.json`, `review-v4.schema.json`, and
`change-report-v3.schema.json` for audit/evidence mismatches, v4 mutation
coverage contradictions, and policy branch contradictions.

M56.1 adds `facts-v5.schema.json` and `review-v5.schema.json`. Their positive
documents are real `facts --format v5` / `review --format v5` output for the
`tests/fixtures/m56_1_evidence` workspace, and their coherence negatives live
beside them as
`tests/golden/schema_profile/{facts,review}-v5-negative-*.json`. The gate
requires each negative to parse as a JSON object (so it cannot pass by being
malformed) and to be rejected by the real v5 schema. The v5 schemas tie
template export kinds to `evidence: "declared"`, ordinary export kinds to
`"checked"`, generic instances to `"checked"`, instance function entries to
the instance-only fields, and instance target kinds to `target_instance_of`
using separate `$defs` joined by `anyOf`.

Profile limits for v5 (no `not`, no uniqueness, no ordering, no cross-record
references): the schemas cannot say that a plain call/reference/propagation
`target_kind` is not one of the four instance kinds without a
`target_instance_of` (plain `target_kind` stays an open string, as in v4);
that arrays are sorted or unique; that `instance_of`, `instances`,
`type_arguments`, and `enclosing_instance` refer to real records; or that
identity strings follow the rendering grammar. These are emitter tests, not
schema claims.

Schema validation stays inside the owned `test`/`prove` gates: M56.1 adds no
schema-validation command, broad JSON API, or edit to an existing v1-v4
schema or golden. The only new CLI surface is the `--format v5` choice for
`facts` and `review`.
