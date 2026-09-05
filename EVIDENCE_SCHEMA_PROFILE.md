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
- `diagnostics-v1.schema.json` -> `tests/golden/diagnostics/check_failure.json`
- `evidence-error-v1.schema.json` ->
  `tests/golden/review/evidence_error_v1.json`
- `facts-v1.schema.json` -> `tests/golden/facts/main.json`
- `facts-v2.schema.json` -> `tests/golden/facts/main-v2.json`
- `facts-v3.schema.json` -> `tests/golden/organizational_tool/facts_v3.json`
- `nauqtype.policy-v1.schema.json` ->
  `tests/fixtures/workspace_local_dependency/policy.json`
- `nauqtype.workspace-lock-v1.schema.json` ->
  `tests/fixtures/workspace_local_dependency/nauqtype.workspace.lock.json`
- `policy-check-v1.schema.json` ->
  `tests/golden/evidence_parity/policy_check_v1.json`
- `proof-summary-v1.schema.json` ->
  `tests/golden/schema_profile/proof-summary-v1-positive.json`
- `proof-summary-v2.schema.json` ->
  `tests/golden/schema_profile/proof-summary-v2-positive.json`
- `refactor-rename-v1.schema.json` ->
  `tests/golden/supervised_workflow/refactor_rename_v1.json`
- `review-diff-v1.schema.json` -> `tests/golden/review/review_diff_v1.json`
- `review-diff-v2.schema.json` -> `tests/golden/review/review_diff_v2.json`
- `review-v2.schema.json` -> `tests/golden/review/review_v2.json`
- `review-v3.schema.json` -> `tests/golden/review/review_v3.json`
- `review-v4.schema.json` -> `tests/golden/review/review_v4.json`

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

No full rebuild, full proof gate, existing schema/golden edits, broad JSON API,
or CLI was added in this slice.
