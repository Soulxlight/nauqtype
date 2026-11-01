# M58.1 Producer Ledger

Status: frozen inventory for [M58.1](M58_1_CONTRACT.md) rule 4 ("No reachable
stage1 limitations"). Base `4d80e70` (the producer code is identical at
`86368fc`).

This ledger lists every producer call site in production source
(`selfhost/*.nq` excluding `*_tests.nq` and `*_probe.nq`) whose diagnostic
message, at the base, began with one of the three legacy prefixes
"stage1 limitation", "stage1 ir error" or "stage1 c error". A call site is a
call to one of the legacy producer helpers (`push_borrow_limitation`,
`push_c_error`, `push_handoff_limitation`, `push_handoff_limitation_detail`,
`consume_handoff_limitation`, `consume_handoff_limitation_detail`,
`push_ir_limitation`, `push_stage1_limitation`,
`push_unsupported_question_diag`), including the calls inside those helpers,
or a direct diagnostic push whose message literal carries a prefix.

- **ID** is `<file>:<function>:<n>`: the n-th such call inside that function
  at the base. It is stable: the inventory is never regenerated.
- **Base message** is the message the site produced at the base; `<expr>`
  marks a value computed at run time.
- **Disposition** is *covered* (an earlier focused rule rejects the source
  shape; the rule column names the code and the evidence names the fixtures
  that prove it), *internal* (unreachable from accepted source; the rule
  column names the invariant below and the evidence names the phase-level test
  or probe that exercises the producer), or *removed* (the call site no longer
  exists; the evidence names what proves the cascade it produced is gone).

Totals: 246 sites; 17 covered, 227 internal, 2 removed.

After M58.1 every *internal* producer reports `internal compiler error: ...`
with its code unchanged (NQ-HANDOFF-001, NQ-BORROW-008, NQ-IR-012, NQ-C-001,
and NQ-TYPE-042 for the two type-checker invariants), and no production
source string begins with a legacy prefix.

## Checked evidence

`selfhost/integer_policy_tests.nq` (`m58c_ledger_cases`, run by
`nauqc test --suite integer-policy`) parses this file and fails unless:

- it has exactly 246 rows with unique IDs, each with a known disposition;
- every evidence path exists; `path#name` also requires `fn name(` in that
  file and `path!name` requires that `fn name(` no longer exists there;
- every covered rule code is produced by production source;
- no production source contains a string literal that begins with a legacy
  prefix.

The fixtures under `tests/fixtures/m58_1/c/` are pinned to their exact
diagnostics by `m58c_fixture_cases` in the same module.

## Invariants

- **T1** (type checker): `infer_match_expr_type_ctx` is called only from the
  `match` arm of `infer_expr_type_ctx_indexed`, so its span always starts with
  `match`. Exercised by every expression `match`, for example
  `tests/fixtures/m58_1/c/accepted.nq`.
- **T2** (type checker): `evaluate_typed_const` runs only after
  `infer_const_expr_type_ctx` accepted the initializer without a diagnostic,
  and that checker accepts only literals, parentheses and operators
  (NQ-TYPE-057 rejects the rest). Exercised by every typed constant.
- **H** (checked handoff, NQ-HANDOFF-001): `build_checked_handoff` runs only
  when load, resolve and type checking reported no error (`main.nq` gates every
  call on `diagnostics_have_errors`). Every expression it exports was inferred
  by the type checker without error (since M58.1 including expression
  statements, `validate_expression_statements`), and every name, binding,
  call target, constructor, field and type it looks up has a front-end fact.
  A nested type-shape failure reports its own diagnostic (for example
  NQ-TYPE-001) and adds no cascade.
- **B** (borrow pass, NQ-BORROW-008): the borrow pass reads only a checked
  handoff and value plan that completed without error; every block,
  expression, binding, call target and type id it reads was exported there.
- **I** (IR lowering, NQ-IR-012): lowering runs only after the borrow pass and
  value planning succeeded; every local, constant, function, block and call
  target it reads has a checked record and type id.
- **C** (C emission, NQ-C-001): emission runs only on IR lowered without
  error; every type shape, local, expression, child, block and declaration id
  it reads exists in that IR.

The family producers are exercised directly by
`handoff_internal_producer_cases`, `borrow_internal_producer_cases`,
`ir_internal_producer_cases` and `c_emit_internal_producer_cases` (the last
also drives a real emitter path, an expression id with no record), all called
by `m58c_ledger_cases`.

## Ledger

| ID | Code | Base message | Disposition | Rule or invariant | Evidence |
| --- | --- | --- | --- | --- | --- |
| `borrow.nq:push_borrow_limitation:1` | NQ-BORROW-008 | stage1 limitation: checked borrow pass <detail> | internal | B | `selfhost/borrow.nq#borrow_internal_producer_cases` |
| `borrow.nq:set_moved_or_limit:1` | NQ-BORROW-008 | stage1 limitation: checked borrow pass is missing binding move state | internal | B | `selfhost/borrow.nq#borrow_internal_producer_cases` |
| `borrow.nq:set_moved_or_limit:2` | NQ-BORROW-008 | stage1 limitation: checked borrow pass could not update binding move state | internal | B | `selfhost/borrow.nq#borrow_internal_producer_cases` |
| `borrow.nq:is_copy_type:1` | NQ-BORROW-008 | stage1 limitation: checked borrow pass is missing a checked type name | internal | B | `selfhost/borrow.nq#borrow_internal_producer_cases` |
| `borrow.nq:is_copy_type:2` | NQ-BORROW-008 | stage1 limitation: checked borrow pass cannot classify copyability for checked type `<type_name>` | internal | B | `selfhost/borrow.nq#borrow_internal_producer_cases` |
| `borrow.nq:is_copy_type:3` | NQ-BORROW-008 | stage1 limitation: checked borrow pass found ambiguous checked declarations for `<type_name>` | internal | B | `selfhost/borrow.nq#borrow_internal_producer_cases` |
| `borrow.nq:planned_value_use_kind:1` | NQ-BORROW-008 | stage1 limitation: checked borrow pass is missing checked value-use plan for expression <expr.id> | internal | B | `selfhost/borrow.nq#borrow_internal_producer_cases` |
| `borrow.nq:type_id_is_copy_or_limit:1` | NQ-BORROW-008 | stage1 limitation: checked borrow pass is missing canonical checked type identity for copy classification | internal | B | `selfhost/borrow.nq#borrow_internal_producer_cases` |
| `borrow.nq:type_id_is_copy_or_limit:2` | NQ-BORROW-008 | stage1 limitation: checked borrow pass is missing canonical checked type properties for type <type_id> | internal | B | `selfhost/borrow.nq#borrow_internal_producer_cases` |
| `borrow.nq:walk_expr:1` | NQ-BORROW-008 | stage1 limitation: checked borrow pass is missing a binding id for checked name expression | internal | B | `selfhost/borrow.nq#borrow_internal_producer_cases` |
| `borrow.nq:walk_expr:2` | NQ-BORROW-008 | stage1 limitation: checked borrow pass could not look up checked binding for name expression | internal | B | `selfhost/borrow.nq#borrow_internal_producer_cases` |
| `borrow.nq:walk_expr:3` | NQ-BORROW-008 | stage1 limitation: checked borrow pass is missing a binding id for checked ref expression | internal | B | `selfhost/borrow.nq#borrow_internal_producer_cases` |
| `borrow.nq:walk_expr:4` | NQ-BORROW-008 | stage1 limitation: checked borrow pass is missing a binding id for checked mutref expression | internal | B | `selfhost/borrow.nq#borrow_internal_producer_cases` |
| `borrow.nq:walk_expr:5` | NQ-BORROW-008 | stage1 limitation: checked borrow pass is missing a child for unary not | internal | B | `selfhost/borrow.nq#borrow_internal_producer_cases` |
| `borrow.nq:walk_expr:6` | NQ-BORROW-008 | stage1 limitation: checked borrow pass is missing a child for unary negation | internal | B | `selfhost/borrow.nq#borrow_internal_producer_cases` |
| `borrow.nq:walk_expr:7` | NQ-BORROW-008 | stage1 limitation: checked borrow pass is missing a scrutinee child for checked match expression | internal | B | `selfhost/borrow.nq#borrow_internal_producer_cases` |
| `borrow.nq:walk_expr:8` | NQ-BORROW-008 | stage1 limitation: checked borrow pass is missing an owning statement for checked match expression | internal | B | `selfhost/borrow.nq#borrow_internal_producer_cases` |
| `borrow.nq:walk_expr:9` | NQ-BORROW-008 | stage1 limitation: checked borrow pass could not resolve checked match-expression scrutinee binding | internal | B | `selfhost/borrow.nq#borrow_internal_producer_cases` |
| `borrow.nq:walk_expr:10` | NQ-BORROW-008 | stage1 limitation: checked borrow pass could not load checked match-expression scrutinee expression | internal | B | `selfhost/borrow.nq#borrow_internal_producer_cases` |
| `borrow.nq:walk_expr:11` | NQ-BORROW-008 | stage1 limitation: checked borrow pass is missing a checked match-expression arm result | internal | B | `selfhost/borrow.nq#borrow_internal_producer_cases` |
| `borrow.nq:walk_expr:12` | NQ-BORROW-008 | stage1 limitation: checked borrow pass is missing checked match-expression arms | internal | B | `selfhost/borrow.nq#borrow_internal_producer_cases` |
| `borrow.nq:walk_expr:13` | NQ-BORROW-008 | stage1 limitation: checked borrow pass is missing a value child for checked try expression | internal | B | `selfhost/borrow.nq#borrow_internal_producer_cases` |
| `borrow.nq:walk_expr:14` | NQ-BORROW-008 | stage1 limitation: checked borrow pass is missing an operand child for checked expression propagation | internal | B | `selfhost/borrow.nq#borrow_internal_producer_cases` |
| `borrow.nq:walk_expr:15` | NQ-BORROW-008 | stage1 limitation: checked borrow pass is missing a child for a checked binary expression | internal | B | `selfhost/borrow.nq#borrow_internal_producer_cases` |
| `borrow.nq:walk_expr:16` | NQ-BORROW-008 | stage1 limitation: checked borrow pass is missing a base expression for checked field access | internal | B | `selfhost/borrow.nq#borrow_internal_producer_cases` |
| `borrow.nq:walk_expr:17` | NQ-BORROW-008 | stage1 limitation: checked borrow pass is missing a child for checked list literal | internal | B | `selfhost/borrow.nq#borrow_internal_producer_cases` |
| `borrow.nq:walk_expr:18` | NQ-BORROW-008 | stage1 limitation: checked borrow pass cannot resolve checked call target `<expr.name>` | internal | B | `selfhost/borrow.nq#borrow_internal_producer_cases` |
| `borrow.nq:walk_expr:19` | NQ-BORROW-008 | stage1 limitation: checked borrow pass cannot determine checked parameter shape for `<expr.name>` | internal | B | `selfhost/borrow.nq#borrow_internal_producer_cases` |
| `borrow.nq:walk_expr:20` | NQ-BORROW-008 | stage1 limitation: checked borrow pass is missing a checked call argument expression | internal | B | `selfhost/borrow.nq#borrow_internal_producer_cases` |
| `borrow.nq:walk_expr:21` | NQ-BORROW-008 | stage1 limitation: checked borrow pass cannot resolve checked function target `<expr.name>` | internal | B | `selfhost/borrow.nq#borrow_internal_producer_cases` |
| `borrow.nq:walk_expr:22` | NQ-BORROW-008 | stage1 limitation: checked borrow pass could not load checked call argument expression | internal | B | `selfhost/borrow.nq#borrow_internal_producer_cases` |
| `borrow.nq:walk_expr:23` | NQ-BORROW-008 | stage1 limitation: checked borrow pass is missing a constructor payload expression | internal | B | `selfhost/borrow.nq#borrow_internal_producer_cases` |
| `borrow.nq:walk_expr:24` | NQ-BORROW-008 | stage1 limitation: checked borrow pass could not load a checked expression by id | internal | B | `selfhost/borrow.nq#borrow_internal_producer_cases` |
| `borrow.nq:check_block:1` | NQ-BORROW-008 | stage1 limitation: checked borrow pass is missing a checked statement expression | internal | B | `selfhost/borrow.nq#borrow_internal_producer_cases` |
| `borrow.nq:check_block:2` | NQ-BORROW-008 | stage1 limitation: checked borrow pass is missing a checked local target binding | internal | B | `selfhost/borrow.nq#borrow_internal_producer_cases` |
| `borrow.nq:check_block:3` | NQ-BORROW-008 | stage1 limitation: checked borrow pass is missing a checked let-else block | internal | B | `selfhost/borrow.nq#borrow_internal_producer_cases` |
| `borrow.nq:check_block:4` | NQ-BORROW-008 | stage1 limitation: checked borrow pass is missing a checked let-else target binding | internal | B | `selfhost/borrow.nq#borrow_internal_producer_cases` |
| `borrow.nq:check_block:5` | NQ-BORROW-008 | stage1 limitation: checked borrow pass is missing a checked assignment target binding | internal | B | `selfhost/borrow.nq#borrow_internal_producer_cases` |
| `borrow.nq:check_block:6` | NQ-BORROW-008 | stage1 limitation: checked borrow pass is missing a checked field-assignment target binding | internal | B | `selfhost/borrow.nq#borrow_internal_producer_cases` |
| `borrow.nq:check_block:7` | NQ-BORROW-008 | stage1 limitation: checked borrow pass is missing a checked if block | internal | B | `selfhost/borrow.nq#borrow_internal_producer_cases` |
| `borrow.nq:check_block:8` | NQ-BORROW-008 | stage1 limitation: checked borrow pass is missing a checked loop block | internal | B | `selfhost/borrow.nq#borrow_internal_producer_cases` |
| `borrow.nq:check_block:9` | NQ-BORROW-008 | stage1 limitation: checked borrow pass is missing a checked for-loop binding | internal | B | `selfhost/borrow.nq#borrow_internal_producer_cases` |
| `borrow.nq:check_block:10` | NQ-BORROW-008 | stage1 limitation: checked borrow pass could not resolve checked scrutinee binding | internal | B | `selfhost/borrow.nq#borrow_internal_producer_cases` |
| `borrow.nq:check_block:11` | NQ-BORROW-008 | stage1 limitation: checked borrow pass could not load checked scrutinee expression | internal | B | `selfhost/borrow.nq#borrow_internal_producer_cases` |
| `borrow.nq:check_block:12` | NQ-BORROW-008 | stage1 limitation: checked borrow pass is missing checked match arms | internal | B | `selfhost/borrow.nq#borrow_internal_producer_cases` |
| `borrow.nq:check_checked_handoff_borrows_impl:1` | NQ-BORROW-008 | stage1 limitation: checked borrow pass is missing the checked root block for `<function.name>` | internal | B | `selfhost/borrow.nq#borrow_internal_producer_cases` |
| `c_emit.nq:push_c_error:1` | NQ-C-001 | stage1 c error: <detail> | internal | C | `selfhost/c_emit.nq#c_emit_internal_producer_cases` |
| `c_emit.nq:expression_field_name:1` | NQ-C-001 | stage1 c error: missing field base type during C naming | internal | C | `selfhost/c_emit.nq#c_emit_internal_producer_cases` |
| `c_emit.nq:emit_expr_discard_cleanup:1` | NQ-C-001 | stage1 c error: missing expression for owned discard cleanup | internal | C | `selfhost/c_emit.nq#c_emit_internal_producer_cases` |
| `c_emit.nq:emit_ordered_declarations:1` | NQ-C-001 | stage1 c error: cyclic by-value declaration dependencies cannot be emitted | internal | C | `selfhost/c_emit.nq#c_emit_internal_producer_cases` |
| `c_emit.nq:integer_operation_text:1` | NQ-C-001 | stage1 c error: missing f64 operation truth | internal | C | `selfhost/c_emit.nq#c_emit_internal_producer_cases` |
| `c_emit.nq:integer_operation_text:2` | NQ-C-001 | stage1 c error: missing integer operation type truth | internal | C | `selfhost/c_emit.nq#c_emit_internal_producer_cases` |
| `c_emit.nq:invalid_c_const:1` | NQ-C-001 | stage1 c error: invalid constant IR type, structure, or evaluated division during C emission | internal | C | `selfhost/c_emit.nq#c_emit_internal_producer_cases` |
| `c_emit.nq:emit_f64_const_expr:1` | NQ-C-001 | stage1 c error: invalid f64 constant IR during C emission | internal | C | `selfhost/c_emit.nq#c_emit_internal_producer_cases` |
| `c_emit.nq:emit_const_decl:1` | NQ-C-001 | stage1 c error: missing const initializer expression during C emission: <const_decl.name> | internal | C | `selfhost/c_emit.nq#c_emit_internal_producer_cases` |
| `c_emit.nq:emit_borrow_expr:1` | NQ-C-001 | stage1 c error: borrow expression requires one binding child | internal | C | `selfhost/c_emit.nq#c_emit_internal_producer_cases` |
| `c_emit.nq:emit_borrow_expr:2` | NQ-C-001 | stage1 c error: borrow expression requires a binding or field path | internal | C | `selfhost/c_emit.nq#c_emit_internal_producer_cases` |
| `c_emit.nq:emit_borrow_expr:3` | NQ-C-001 | stage1 c error: missing local identity for borrow expression | internal | C | `selfhost/c_emit.nq#c_emit_internal_producer_cases` |
| `c_emit.nq:emit_borrow_expr:4` | NQ-C-001 | stage1 c error: borrow expression requires a binding or field path | internal | C | `selfhost/c_emit.nq#c_emit_internal_producer_cases` |
| `c_emit.nq:emit_borrow_expr:5` | NQ-C-001 | stage1 c error: missing borrow child expression | internal | C | `selfhost/c_emit.nq#c_emit_internal_producer_cases` |
| `c_emit.nq:emit_borrow_expr:6` | NQ-C-001 | stage1 c error: missing borrow child expression | internal | C | `selfhost/c_emit.nq#c_emit_internal_producer_cases` |
| `c_emit.nq:emit_list_first_argument:1` | NQ-C-001 | stage1 c error: missing local identity for list argument | internal | C | `selfhost/c_emit.nq#c_emit_internal_producer_cases` |
| `c_emit.nq:emit_list_first_argument:2` | NQ-C-001 | stage1 c error: missing list argument expression | internal | C | `selfhost/c_emit.nq#c_emit_internal_producer_cases` |
| `c_emit.nq:emit_expr:1` | NQ-C-001 | stage1 c error: missing local identity for name expression | internal | C | `selfhost/c_emit.nq#c_emit_internal_producer_cases` |
| `c_emit.nq:emit_expr:2` | NQ-C-001 | stage1 c error: missing unary child expression | internal | C | `selfhost/c_emit.nq#c_emit_internal_producer_cases` |
| `c_emit.nq:emit_expr:3` | NQ-C-001 | stage1 c error: missing unary child expression | internal | C | `selfhost/c_emit.nq#c_emit_internal_producer_cases` |
| `c_emit.nq:emit_expr:4` | NQ-C-001 | stage1 c error: missing binary child expression | internal | C | `selfhost/c_emit.nq#c_emit_internal_producer_cases` |
| `c_emit.nq:emit_expr:5` | NQ-C-001 | stage1 c error: missing binary child expression | internal | C | `selfhost/c_emit.nq#c_emit_internal_producer_cases` |
| `c_emit.nq:emit_expr:6` | NQ-C-001 | stage1 c error: missing binary child expression | internal | C | `selfhost/c_emit.nq#c_emit_internal_producer_cases` |
| `c_emit.nq:emit_expr:7` | NQ-C-001 | stage1 c error: missing binary child expression | internal | C | `selfhost/c_emit.nq#c_emit_internal_producer_cases` |
| `c_emit.nq:emit_expr:8` | NQ-C-001 | stage1 c error: missing binary child expression | internal | C | `selfhost/c_emit.nq#c_emit_internal_producer_cases` |
| `c_emit.nq:emit_expr:9` | NQ-C-001 | stage1 c error: missing binary child expression | internal | C | `selfhost/c_emit.nq#c_emit_internal_producer_cases` |
| `c_emit.nq:emit_expr:10` | NQ-C-001 | stage1 c error: missing binary child expression | internal | C | `selfhost/c_emit.nq#c_emit_internal_producer_cases` |
| `c_emit.nq:emit_expr:11` | NQ-C-001 | stage1 c error: missing binary child expression | internal | C | `selfhost/c_emit.nq#c_emit_internal_producer_cases` |
| `c_emit.nq:emit_expr:12` | NQ-C-001 | stage1 c error: missing binary child expression | internal | C | `selfhost/c_emit.nq#c_emit_internal_producer_cases` |
| `c_emit.nq:emit_expr:13` | NQ-C-001 | stage1 c error: missing binary child expression | internal | C | `selfhost/c_emit.nq#c_emit_internal_producer_cases` |
| `c_emit.nq:emit_expr:14` | NQ-C-001 | stage1 c error: missing binary child expression | internal | C | `selfhost/c_emit.nq#c_emit_internal_producer_cases` |
| `c_emit.nq:emit_expr:15` | NQ-C-001 | stage1 c error: missing binary child expression | internal | C | `selfhost/c_emit.nq#c_emit_internal_producer_cases` |
| `c_emit.nq:emit_expr:16` | NQ-C-001 | stage1 c error: match expression requires statement lowering before C expression emission | internal | C | `selfhost/c_emit.nq#c_emit_internal_producer_cases` |
| `c_emit.nq:emit_expr:17` | NQ-C-001 | stage1 c error: try expression requires local-statement lowering before C expression emission | internal | C | `selfhost/c_emit.nq#c_emit_internal_producer_cases` |
| `c_emit.nq:emit_expr:18` | NQ-C-001 | stage1 c error: missing list literal type truth | internal | C | `selfhost/c_emit.nq#c_emit_internal_producer_cases` |
| `c_emit.nq:emit_expr:19` | NQ-C-001 | stage1 c error: missing list helper type truth | internal | C | `selfhost/c_emit.nq#c_emit_internal_producer_cases` |
| `c_emit.nq:emit_expr:20` | NQ-C-001 | stage1 c error: missing field base expression | internal | C | `selfhost/c_emit.nq#c_emit_internal_producer_cases` |
| `c_emit.nq:emit_expr:21` | NQ-C-001 | stage1 c error: missing struct literal type truth | internal | C | `selfhost/c_emit.nq#c_emit_internal_producer_cases` |
| `c_emit.nq:emit_expr:22` | NQ-C-001 | stage1 c error: missing expression record during C emission | internal | C | `selfhost/c_emit.nq#c_emit_internal_producer_cases` |
| `c_emit.nq:apply_planned_lvalue_use:1` | NQ-C-001 | stage1 c error: move-only value use requires a binding-backed lvalue | internal | C | `selfhost/c_emit.nq#c_emit_internal_producer_cases` |
| `c_emit.nq:lower_planned_borrow_argument:1` | NQ-C-001 | stage1 c error: planned borrow argument is missing local identity | internal | C | `selfhost/c_emit.nq#c_emit_internal_producer_cases` |
| `c_emit.nq:lower_planned_borrow_argument:2` | NQ-C-001 | stage1 c error: planned borrow argument requires a direct borrow or borrowed parameter | internal | C | `selfhost/c_emit.nq#c_emit_internal_producer_cases` |
| `c_emit.nq:lower_planned_borrow_argument:3` | NQ-C-001 | stage1 c error: planned borrow argument is missing expression truth | internal | C | `selfhost/c_emit.nq#c_emit_internal_producer_cases` |
| `c_emit.nq:lower_expr_value:1` | NQ-C-001 | stage1 c error: missing local identity for ordered name expression | internal | C | `selfhost/c_emit.nq#c_emit_internal_producer_cases` |
| `c_emit.nq:lower_expr_value:2` | NQ-C-001 | stage1 c error: missing call argument expression during ordered lowering | internal | C | `selfhost/c_emit.nq#c_emit_internal_producer_cases` |
| `c_emit.nq:lower_expr_value:3` | NQ-C-001 | stage1 c error: missing ordered call target truth | internal | C | `selfhost/c_emit.nq#c_emit_internal_producer_cases` |
| `c_emit.nq:lower_expr_value:4` | NQ-C-001 | stage1 c error: cannot detach a move-only field from an owned temporary | internal | C | `selfhost/c_emit.nq#c_emit_internal_producer_cases` |
| `c_emit.nq:lower_expr_value:5` | NQ-C-001 | stage1 c error: missing ordered struct type truth | internal | C | `selfhost/c_emit.nq#c_emit_internal_producer_cases` |
| `c_emit.nq:lower_expr_value:6` | NQ-C-001 | stage1 c error: missing ordered list type truth | internal | C | `selfhost/c_emit.nq#c_emit_internal_producer_cases` |
| `c_emit.nq:lower_expr_value:7` | NQ-C-001 | stage1 c error: match expression requires statement-boundary ordered lowering | internal | C | `selfhost/c_emit.nq#c_emit_internal_producer_cases` |
| `c_emit.nq:lower_expr_value:8` | NQ-C-001 | stage1 c error: try expression requires statement-boundary ordered lowering | internal | C | `selfhost/c_emit.nq#c_emit_internal_producer_cases` |
| `c_emit.nq:lower_expr_value:9` | NQ-C-001 | stage1 c error: unsupported ordered expression kind | internal | C | `selfhost/c_emit.nq#c_emit_internal_producer_cases` |
| `c_emit.nq:lower_expr_value:10` | NQ-C-001 | stage1 c error: missing expression during ordered C lowering | internal | C | `selfhost/c_emit.nq#c_emit_internal_producer_cases` |
| `c_emit.nq:lower_expr_transfer_value:1` | NQ-C-001 | stage1 c error: owned transfer cannot move from a ref parameter | internal | C | `selfhost/c_emit.nq#c_emit_internal_producer_cases` |
| `c_emit.nq:lower_expr_transfer_value:2` | NQ-C-001 | stage1 c error: owned transfer is missing binding identity | internal | C | `selfhost/c_emit.nq#c_emit_internal_producer_cases` |
| `c_emit.nq:lower_expr_transfer_value:3` | NQ-C-001 | stage1 c error: owned transfer requires copy or move value truth | internal | C | `selfhost/c_emit.nq#c_emit_internal_producer_cases` |
| `c_emit.nq:lower_expr_transfer_value:4` | NQ-C-001 | stage1 c error: missing expression during owned transfer lowering | internal | C | `selfhost/c_emit.nq#c_emit_internal_producer_cases` |
| `c_emit.nq:require_type_shape:1` | NQ-C-001 | stage1 c error: <detail> | internal | C | `selfhost/c_emit.nq#c_emit_internal_producer_cases` |
| `c_emit.nq:require_type_shape:2` | NQ-C-001 | stage1 c error: <detail> | internal | C | `selfhost/c_emit.nq#c_emit_internal_producer_cases` |
| `c_emit.nq:emit_pattern_bindings:1` | NQ-C-001 | stage1 c error: missing local identity for bind pattern | internal | C | `selfhost/c_emit.nq#c_emit_internal_producer_cases` |
| `c_emit.nq:emit_pattern_bindings:2` | NQ-C-001 | stage1 c error: missing payload type truth for nested pattern binding | internal | C | `selfhost/c_emit.nq#c_emit_internal_producer_cases` |
| `c_emit.nq:emit_pattern_bindings:3` | NQ-C-001 | stage1 c error: missing pattern record during C emission | internal | C | `selfhost/c_emit.nq#c_emit_internal_producer_cases` |
| `c_emit.nq:pattern_condition:1` | NQ-C-001 | stage1 c error: missing payload type truth for pattern condition | internal | C | `selfhost/c_emit.nq#c_emit_internal_producer_cases` |
| `c_emit.nq:pattern_condition:2` | NQ-C-001 | stage1 c error: missing pattern record for condition | internal | C | `selfhost/c_emit.nq#c_emit_internal_producer_cases` |
| `c_emit.nq:emit_match_stmt:1` | NQ-C-001 | stage1 c error: refined match requires a wildcard or binding fallback arm | internal | C | `selfhost/c_emit.nq#c_emit_internal_producer_cases` |
| `c_emit.nq:emit_match_stmt:2` | NQ-C-001 | stage1 c error: missing match scrutinee expression | internal | C | `selfhost/c_emit.nq#c_emit_internal_producer_cases` |
| `c_emit.nq:emit_match_expr_assignment:1` | NQ-C-001 | stage1 c error: match expression must be exhaustive | internal | C | `selfhost/c_emit.nq#c_emit_internal_producer_cases` |
| `c_emit.nq:emit_match_expr_assignment:2` | NQ-C-001 | stage1 c error: refined match requires a wildcard or binding fallback arm | internal | C | `selfhost/c_emit.nq#c_emit_internal_producer_cases` |
| `c_emit.nq:emit_match_expr_assignment:3` | NQ-C-001 | stage1 c error: missing match-expression scrutinee expression | internal | C | `selfhost/c_emit.nq#c_emit_internal_producer_cases` |
| `c_emit.nq:emit_match_expr_assignment:4` | NQ-C-001 | stage1 c error: missing match-expression scrutinee child | internal | C | `selfhost/c_emit.nq#c_emit_internal_producer_cases` |
| `c_emit.nq:emit_match_expr_assignment:5` | NQ-C-001 | stage1 c error: missing match expression for lowering | internal | C | `selfhost/c_emit.nq#c_emit_internal_producer_cases` |
| `c_emit.nq:emit_let_else_stmt:1` | NQ-C-001 | stage1 c error: let-else scrutinee must be option or result | internal | C | `selfhost/c_emit.nq#c_emit_internal_producer_cases` |
| `c_emit.nq:emit_let_else_stmt:2` | NQ-C-001 | stage1 c error: missing let-else scrutinee expression | internal | C | `selfhost/c_emit.nq#c_emit_internal_producer_cases` |
| `c_emit.nq:emit_let_else_stmt:3` | NQ-C-001 | stage1 c error: missing local identity for let-else statement | internal | C | `selfhost/c_emit.nq#c_emit_internal_producer_cases` |
| `c_emit.nq:emit_propagate_stmt:1` | NQ-C-001 | stage1 c error: missing function return type for propagation statement | internal | C | `selfhost/c_emit.nq#c_emit_internal_producer_cases` |
| `c_emit.nq:emit_propagate_stmt:2` | NQ-C-001 | stage1 c error: propagation scrutinee must be result | internal | C | `selfhost/c_emit.nq#c_emit_internal_producer_cases` |
| `c_emit.nq:emit_propagate_stmt:3` | NQ-C-001 | stage1 c error: missing propagation err payload type | internal | C | `selfhost/c_emit.nq#c_emit_internal_producer_cases` |
| `c_emit.nq:emit_propagate_stmt:4` | NQ-C-001 | stage1 c error: missing propagation scrutinee expression | internal | C | `selfhost/c_emit.nq#c_emit_internal_producer_cases` |
| `c_emit.nq:emit_propagate_stmt:5` | NQ-C-001 | stage1 c error: missing local identity for propagation statement | internal | C | `selfhost/c_emit.nq#c_emit_internal_producer_cases` |
| `c_emit.nq:emit_try_propagation_preludes:1` | NQ-C-001 | stage1 c error: try propagation operand must have result type | internal | C | `selfhost/c_emit.nq#c_emit_internal_producer_cases` |
| `c_emit.nq:emit_try_propagation_preludes:2` | NQ-C-001 | stage1 c error: missing try propagation err payload type | internal | C | `selfhost/c_emit.nq#c_emit_internal_producer_cases` |
| `c_emit.nq:emit_try_propagation_preludes:3` | NQ-C-001 | stage1 c error: missing try propagation operand expression | internal | C | `selfhost/c_emit.nq#c_emit_internal_producer_cases` |
| `c_emit.nq:emit_try_propagation_preludes:4` | NQ-C-001 | stage1 c error: missing try propagation operand child | internal | C | `selfhost/c_emit.nq#c_emit_internal_producer_cases` |
| `c_emit.nq:emit_try_propagation_preludes:5` | NQ-C-001 | stage1 c error: missing expression during try propagation lowering | internal | C | `selfhost/c_emit.nq#c_emit_internal_producer_cases` |
| `c_emit.nq:emit_try_expr_assignment:1` | NQ-C-001 | stage1 c error: missing try success expression child | internal | C | `selfhost/c_emit.nq#c_emit_internal_producer_cases` |
| `c_emit.nq:emit_try_expr_assignment:2` | NQ-C-001 | stage1 c error: try boundary must have result type | internal | C | `selfhost/c_emit.nq#c_emit_internal_producer_cases` |
| `c_emit.nq:emit_try_expr_assignment:3` | NQ-C-001 | stage1 c error: missing try expression for lowering | internal | C | `selfhost/c_emit.nq#c_emit_internal_producer_cases` |
| `c_emit.nq:emit_stmt:1` | NQ-C-001 | stage1 c error: missing local identity for let statement | internal | C | `selfhost/c_emit.nq#c_emit_internal_producer_cases` |
| `c_emit.nq:emit_stmt:2` | NQ-C-001 | stage1 c error: missing local identity for assignment | internal | C | `selfhost/c_emit.nq#c_emit_internal_producer_cases` |
| `c_emit.nq:emit_stmt:3` | NQ-C-001 | stage1 c error: field assignment cannot target a ref parameter | internal | C | `selfhost/c_emit.nq#c_emit_internal_producer_cases` |
| `c_emit.nq:emit_stmt:4` | NQ-C-001 | stage1 c error: field assignment is missing a resolved field name | internal | C | `selfhost/c_emit.nq#c_emit_internal_producer_cases` |
| `c_emit.nq:emit_stmt:5` | NQ-C-001 | stage1 c error: field assignment is missing field type truth | internal | C | `selfhost/c_emit.nq#c_emit_internal_producer_cases` |
| `c_emit.nq:emit_stmt:6` | NQ-C-001 | stage1 c error: missing local identity for field assignment | internal | C | `selfhost/c_emit.nq#c_emit_internal_producer_cases` |
| `c_emit.nq:emit_stmt:7` | NQ-C-001 | stage1 c error: missing local identity for for-loop binding | internal | C | `selfhost/c_emit.nq#c_emit_internal_producer_cases` |
| `c_emit.nq:emit_stmt:8` | NQ-C-001 | stage1 c error: for-loop iterable IR type is not a list | internal | C | `selfhost/c_emit.nq#c_emit_internal_producer_cases` |
| `c_emit.nq:emit_stmt:9` | NQ-C-001 | stage1 c error: missing for-loop iterable type truth | internal | C | `selfhost/c_emit.nq#c_emit_internal_producer_cases` |
| `c_emit.nq:emit_stmt:10` | NQ-C-001 | stage1 c error: missing for-loop iterable expression | internal | C | `selfhost/c_emit.nq#c_emit_internal_producer_cases` |
| `c_emit.nq:emit_c_program:1` | NQ-C-001 | stage1 c error: missing program entry metadata during C emission | internal | C | `selfhost/c_emit.nq#c_emit_internal_producer_cases` |
| `handoff.nq:push_handoff_limitation:1` | NQ-HANDOFF-001 | stage1 limitation: checked handoff could not export the current expression or binding shape | internal | H | `selfhost/handoff.nq#handoff_internal_producer_cases` |
| `handoff.nq:push_handoff_limitation_detail:1` | NQ-HANDOFF-001 | stage1 limitation: <detail> | internal | H | `selfhost/handoff.nq#handoff_internal_producer_cases` |
| `handoff.nq:consume_handoff_limitation:1` | NQ-HANDOFF-001 | stage1 limitation: checked handoff could not export the current expression or binding shape | internal | H | `selfhost/handoff.nq#handoff_internal_producer_cases` |
| `handoff.nq:consume_handoff_limitation_detail:1` | NQ-HANDOFF-001 | stage1 limitation: <detail> | internal | H | `selfhost/handoff.nq#handoff_internal_producer_cases` |
| `handoff.nq:intern_checked_type_id:1` | NQ-HANDOFF-001 | stage1 limitation: missing inner type shape for checked borrow type | internal | H | `selfhost/handoff.nq#handoff_internal_producer_cases` |
| `handoff.nq:intern_checked_type_id:2` | NQ-HANDOFF-001 | stage1 limitation: missing checked type information | internal | H | `selfhost/handoff.nq#handoff_internal_producer_cases` |
| `handoff.nq:intern_checked_type_id:3` | NQ-HANDOFF-001 | stage1 limitation: missing list element type in checked handoff | internal | H | `selfhost/handoff.nq#handoff_internal_producer_cases` |
| `handoff.nq:intern_checked_type_id:4` | NQ-HANDOFF-001 | stage1 limitation: missing option payload type in checked handoff | internal | H | `selfhost/handoff.nq#handoff_internal_producer_cases` |
| `handoff.nq:intern_checked_type_id:5` | NQ-HANDOFF-001 | stage1 limitation: missing result payload type in checked handoff | internal | H | `selfhost/handoff.nq#handoff_internal_producer_cases` |
| `handoff.nq:intern_checked_type_id:6` | NQ-HANDOFF-001 | stage1 limitation: missing result argument type shapes in checked handoff | removed |  | `tests/fixtures/m55_process/compiler_type_arguments.nq`, `selfhost/process_tests.nq#process_time_gate_impl` |
| `handoff.nq:build_expr_tree:1` | NQ-HANDOFF-001 | stage1 limitation: unsupported checked handoff expression type context | internal | H | `selfhost/handoff.nq#handoff_internal_producer_cases` |
| `handoff.nq:build_expr_tree:2` | NQ-HANDOFF-001 | stage1 limitation: missing checked try-boundary value expression | internal | H | `selfhost/handoff.nq#handoff_internal_producer_cases` |
| `handoff.nq:build_expr_tree:3` | NQ-HANDOFF-001 | stage1 limitation: missing checked expression-propagation operand | internal | H | `selfhost/handoff.nq#handoff_internal_producer_cases` |
| `handoff.nq:build_expr_tree:4` | NQ-HANDOFF-001 | stage1 limitation: missing match-expression scrutinee | internal | H | `selfhost/handoff.nq#handoff_internal_producer_cases` |
| `handoff.nq:build_expr_tree:5` | NQ-HANDOFF-001 | stage1 limitation: missing child expression for logical or | internal | H | `selfhost/handoff.nq#handoff_internal_producer_cases` |
| `handoff.nq:build_expr_tree:6` | NQ-HANDOFF-001 | stage1 limitation: missing child expression for logical and | internal | H | `selfhost/handoff.nq#handoff_internal_producer_cases` |
| `handoff.nq:build_expr_tree:7` | NQ-HANDOFF-001 | stage1 limitation: missing child expression for comparison | internal | H | `selfhost/handoff.nq#handoff_internal_producer_cases` |
| `handoff.nq:build_expr_tree:8` | NQ-HANDOFF-001 | stage1 limitation: missing child expression for additive operator | internal | H | `selfhost/handoff.nq#handoff_internal_producer_cases` |
| `handoff.nq:build_expr_tree:9` | NQ-HANDOFF-001 | stage1 limitation: missing child expression for multiplicative operator | internal | H | `selfhost/handoff.nq#handoff_internal_producer_cases` |
| `handoff.nq:build_expr_tree:10` | NQ-HANDOFF-001 | stage1 limitation: missing borrowed binding or child for ref expression: <token_at(ref tokens, root_index).text> | internal | H | `selfhost/handoff.nq#handoff_internal_producer_cases` |
| `handoff.nq:build_expr_tree:11` | NQ-HANDOFF-001 | stage1 limitation: missing borrowed binding or child for mutref expression: <token_at(ref tokens, root_index).text> | internal | H | `selfhost/handoff.nq#handoff_internal_producer_cases` |
| `handoff.nq:build_expr_tree:12` | NQ-HANDOFF-001 | stage1 limitation: missing child for unary not expression | internal | H | `selfhost/handoff.nq#handoff_internal_producer_cases` |
| `handoff.nq:build_expr_tree:13` | NQ-HANDOFF-001 | stage1 limitation: missing child for unary negation expression | internal | H | `selfhost/handoff.nq#handoff_internal_producer_cases` |
| `handoff.nq:build_expr_tree:14` | NQ-HANDOFF-001 | stage1 limitation: missing child expression for list literal | internal | H | `selfhost/handoff.nq#handoff_internal_producer_cases` |
| `handoff.nq:build_expr_tree:15` | NQ-HANDOFF-001 | stage1 limitation: missing base expression for field access: <field_token.text> | internal | H | `selfhost/handoff.nq#handoff_internal_producer_cases` |
| `handoff.nq:build_expr_tree:16` | NQ-HANDOFF-001 | stage1 limitation: unresolved qualified call or constructor target: <head.text> | internal | H | `selfhost/handoff.nq#handoff_internal_producer_cases` |
| `handoff.nq:build_expr_tree:17` | NQ-HANDOFF-001 | stage1 limitation: named constructor arguments are outside the checked handoff subset | internal | H | `selfhost/handoff.nq#handoff_internal_producer_cases` |
| `handoff.nq:build_expr_tree:18` | NQ-HANDOFF-001 | stage1 limitation: missing exported named call argument: <param_name> | internal | H | `selfhost/handoff.nq#handoff_internal_producer_cases` |
| `handoff.nq:build_expr_tree:19` | NQ-HANDOFF-001 | stage1 limitation: missing exported named call argument expression for call: <head.text> | internal | H | `selfhost/handoff.nq#handoff_internal_producer_cases` |
| `handoff.nq:build_expr_tree:20` | NQ-HANDOFF-001 | stage1 limitation: missing exported call argument expression for call: <head.text> | internal | H | `selfhost/handoff.nq#handoff_internal_producer_cases` |
| `handoff.nq:build_expr_tree:21` | NQ-HANDOFF-001 | stage1 limitation: unresolved qualified struct literal type: <type_token.text> | internal | H | `selfhost/handoff.nq#handoff_internal_producer_cases` |
| `handoff.nq:build_expr_tree:22` | NQ-HANDOFF-001 | stage1 limitation: unsupported record update base expression | internal | H | `selfhost/handoff.nq#handoff_internal_producer_cases` |
| `handoff.nq:build_expr_tree:23` | NQ-HANDOFF-001 | stage1 limitation: missing record update base expression | internal | H | `selfhost/handoff.nq#handoff_internal_producer_cases` |
| `handoff.nq:build_expr_tree:24` | NQ-HANDOFF-001 | stage1 limitation: missing exported record update field value expression: <field_fact.name> | internal | H | `selfhost/handoff.nq#handoff_internal_producer_cases` |
| `handoff.nq:build_expr_tree:25` | NQ-HANDOFF-001 | stage1 limitation: missing exported struct field value expression: <field_token.text> | internal | H | `selfhost/handoff.nq#handoff_internal_producer_cases` |
| `handoff.nq:build_expr_tree:26` | NQ-HANDOFF-001 | stage1 limitation: missing resolved binding id for checked name expression: <name_token.text> | internal | H | `selfhost/handoff.nq#handoff_internal_producer_cases` |
| `handoff.nq:build_expr_tree:27` | NQ-HANDOFF-001 | stage1 limitation: unsupported checked handoff expression shape | internal | H | `selfhost/handoff.nq#handoff_internal_producer_cases` |
| `handoff.nq:append_const_decls:1` | NQ-HANDOFF-001 | stage1 limitation: missing checked const initializer for: <value.name> | internal | H | `selfhost/handoff.nq#handoff_internal_producer_cases` |
| `handoff.nq:append_bindings:1` | NQ-HANDOFF-001 | stage1 limitation: missing unique source for checked declaration identity | internal | H | `selfhost/handoff.nq#handoff_internal_producer_cases` |
| `handoff.nq:append_bindings:2` | NQ-HANDOFF-001 | stage1 limitation: missing exact local declaration name span | internal | H | `selfhost/handoff.nq#handoff_internal_producer_cases` |
| `handoff.nq:append_bindings:3` | NQ-HANDOFF-001 | stage1 limitation: missing resolved local binding type for checked handoff: <current.name> | internal | H | `selfhost/handoff.nq#handoff_internal_producer_cases` |
| `handoff.nq:append_bindings:4` | NQ-HANDOFF-001 | stage1 limitation: missing resolved pattern binding type for checked handoff: <current.name> | internal | H | `selfhost/handoff.nq#handoff_internal_producer_cases` |
| `handoff.nq:append_params:1` | NQ-HANDOFF-001 | stage1 limitation: missing parameter binding id in checked handoff: <param.name> | internal | H | `selfhost/handoff.nq#handoff_internal_producer_cases` |
| `handoff.nq:append_statements_for_source:1` | NQ-HANDOFF-001 | stage1 limitation: missing exported statement expression in checked handoff | internal | H | `selfhost/handoff.nq#handoff_internal_producer_cases` |
| `handoff.nq:append_statements_for_source:2` | NQ-HANDOFF-001 | stage1 limitation: missing local target binding id in checked handoff: <current.name> | internal | H | `selfhost/handoff.nq#handoff_internal_producer_cases` |
| `handoff.nq:append_statements_for_source:3` | NQ-HANDOFF-001 | stage1 limitation: missing let-else target binding id in checked handoff: <current.name> | internal | H | `selfhost/handoff.nq#handoff_internal_producer_cases` |
| `handoff.nq:append_statements_for_source:4` | NQ-HANDOFF-001 | stage1 limitation: missing else block id for checked let-else statement | internal | H | `selfhost/handoff.nq#handoff_internal_producer_cases` |
| `handoff.nq:append_statements_for_source:5` | NQ-HANDOFF-001 | stage1 limitation: missing propagation target binding id in checked handoff: <current.name> | internal | H | `selfhost/handoff.nq#handoff_internal_producer_cases` |
| `handoff.nq:append_statements_for_source:6` | NQ-HANDOFF-001 | stage1 limitation: missing result return type for checked propagation statement | internal | H | `selfhost/handoff.nq#handoff_internal_producer_cases` |
| `handoff.nq:append_statements_for_source:7` | NQ-HANDOFF-001 | stage1 limitation: missing assignment target binding id in checked handoff: <current.name> | internal | H | `selfhost/handoff.nq#handoff_internal_producer_cases` |
| `handoff.nq:append_statements_for_source:8` | NQ-HANDOFF-001 | stage1 limitation: missing field-assignment target binding id in checked handoff: <current.name> | internal | H | `selfhost/handoff.nq#handoff_internal_producer_cases` |
| `handoff.nq:append_statements_for_source:9` | NQ-HANDOFF-001 | stage1 limitation: missing resolved owned-local field target in checked handoff | internal | H | `selfhost/handoff.nq#handoff_internal_producer_cases` |
| `handoff.nq:append_statements_for_source:10` | NQ-HANDOFF-001 | stage1 limitation: missing child block id for checked if statement | internal | H | `selfhost/handoff.nq#handoff_internal_producer_cases` |
| `handoff.nq:append_statements_for_source:11` | NQ-HANDOFF-001 | stage1 limitation: missing alternate block id for checked if statement | internal | H | `selfhost/handoff.nq#handoff_internal_producer_cases` |
| `handoff.nq:append_statements_for_source:12` | NQ-HANDOFF-001 | stage1 limitation: missing child block id for checked while statement | internal | H | `selfhost/handoff.nq#handoff_internal_producer_cases` |
| `handoff.nq:append_statements_for_source:13` | NQ-HANDOFF-001 | stage1 limitation: missing for-loop target binding id in checked handoff: <current.name> | internal | H | `selfhost/handoff.nq#handoff_internal_producer_cases` |
| `handoff.nq:append_statements_for_source:14` | NQ-HANDOFF-001 | stage1 limitation: missing child block id for checked for statement | internal | H | `selfhost/handoff.nq#handoff_internal_producer_cases` |
| `handoff.nq:build_checked_pattern_tree:1` | NQ-HANDOFF-001 | stage1 limitation: missing checked pattern span | internal | H | `selfhost/handoff.nq#handoff_internal_producer_cases` |
| `handoff.nq:build_checked_pattern_tree:2` | NQ-HANDOFF-001 | stage1 limitation: missing resolved constructor for checked pattern: <ctor.text> | internal | H | `selfhost/handoff.nq#handoff_internal_producer_cases` |
| `handoff.nq:build_checked_pattern_tree:3` | NQ-HANDOFF-001 | stage1 limitation: missing checked child pattern for constructor: <ctor.text> | internal | H | `selfhost/handoff.nq#handoff_internal_producer_cases` |
| `handoff.nq:build_checked_pattern_tree:4` | NQ-HANDOFF-001 | stage1 limitation: missing resolved constructor for checked pattern: <name_token.text> | internal | H | `selfhost/handoff.nq#handoff_internal_producer_cases` |
| `handoff.nq:build_checked_pattern_tree:5` | NQ-HANDOFF-001 | stage1 limitation: missing checked binding id for pattern binding: <current.text> | internal | H | `selfhost/handoff.nq#handoff_internal_producer_cases` |
| `handoff.nq:build_checked_pattern_tree:6` | NQ-HANDOFF-001 | stage1 limitation: unsupported checked pattern shape | internal | H | `selfhost/handoff.nq#handoff_internal_producer_cases` |
| `handoff.nq:append_match_arms_for_source:1` | NQ-HANDOFF-001 | stage1 limitation: missing checked match arm owner ids | internal | H | `selfhost/handoff.nq#handoff_internal_producer_cases` |
| `handoff.nq:append_match_arms_for_source:2` | NQ-HANDOFF-001 | stage1 limitation: missing match-expression arm result expression | internal | H | `selfhost/handoff.nq#handoff_internal_producer_cases` |
| `handoff.nq:append_match_arms_for_source:3` | NQ-HANDOFF-001 | stage1 limitation: missing checked pattern binding id | internal | H | `selfhost/handoff.nq#handoff_internal_producer_cases` |
| `ir.nq:push_ir_limitation:1` | NQ-IR-012 | stage1 ir error: <detail> | internal | I | `selfhost/ir.nq#ir_internal_producer_cases` |
| `ir.nq:checked_type_property_or_default:1` | NQ-IR-012 | stage1 ir error: missing canonical value properties for IR type | internal | I | `selfhost/ir.nq#ir_internal_producer_cases` |
| `ir.nq:checked_value_use_or_default:1` | NQ-IR-012 | stage1 ir error: missing explicit value-use plan for IR expression | internal | I | `selfhost/ir.nq#ir_internal_producer_cases` |
| `ir.nq:build_ir_program_for_entry_with_value_plan:1` | NQ-IR-012 | stage1 ir error: missing field type id in checked handoff | internal | I | `selfhost/ir.nq#ir_internal_producer_cases` |
| `ir.nq:build_ir_program_for_entry_with_value_plan:2` | NQ-IR-012 | stage1 ir error: missing variant payload type id in checked handoff | internal | I | `selfhost/ir.nq#ir_internal_producer_cases` |
| `ir.nq:build_ir_program_for_entry_with_value_plan:3` | NQ-IR-012 | stage1 ir error: missing local type id for binding `<value.name>` | internal | I | `selfhost/ir.nq#ir_internal_producer_cases` |
| `ir.nq:build_ir_program_for_entry_with_value_plan:4` | NQ-IR-012 | stage1 ir error: missing const type or initializer id for `<value.name>` | internal | I | `selfhost/ir.nq#ir_internal_producer_cases` |
| `ir.nq:build_ir_program_for_entry_with_value_plan:5` | NQ-IR-012 | stage1 ir error: missing function return type id for `<value.name>` | internal | I | `selfhost/ir.nq#ir_internal_producer_cases` |
| `ir.nq:build_ir_program_for_entry_with_value_plan:6` | NQ-IR-012 | stage1 ir error: missing lowered root block for `<value.name>` | internal | I | `selfhost/ir.nq#ir_internal_producer_cases` |
| `ir.nq:build_ir_program_for_entry_with_value_plan:7` | NQ-IR-012 | stage1 ir error: missing expression type id in checked handoff | internal | I | `selfhost/ir.nq#ir_internal_producer_cases` |
| `ir.nq:build_ir_program_for_entry_with_value_plan:8` | NQ-IR-012 | stage1 ir error: missing resolved call target in checked handoff: <value.name> | internal | I | `selfhost/ir.nq#ir_internal_producer_cases` |
| `ir.nq:build_ir_program_for_entry_with_value_plan:9` | NQ-IR-012 | stage1 ir error: missing statement expression id in checked handoff | internal | I | `selfhost/ir.nq#ir_internal_producer_cases` |
| `ir.nq:build_ir_program_for_entry_with_value_plan:10` | NQ-IR-012 | stage1 ir error: missing loop cleanup target for loop-control statement | internal | I | `selfhost/ir.nq#ir_internal_producer_cases` |
| `ir.nq:build_ir_program_for_entry_with_value_plan:11` | NQ-IR-012 | stage1 ir error: missing checked pattern root for match arm | internal | I | `selfhost/ir.nq#ir_internal_producer_cases` |
| `ir.nq:build_ir_program_for_entry_with_value_plan:12` | NQ-IR-012 | stage1 ir error: missing pattern binding identity in checked handoff | internal | I | `selfhost/ir.nq#ir_internal_producer_cases` |
| `ir.nq:build_ir_program_for_entry_with_value_plan:13` | NQ-IR-012 | stage1 ir error: missing lowered entry function | internal | I | `selfhost/ir.nq#ir_internal_producer_cases` |
| `parser.nq:push_unsupported_question_diag:1` | NQ-PARSE-003 | stage1 limitation: `?` is only supported in `let name = result_expr?;` | covered | NQ-PROPAGATE-007 | `tests/fixtures/m58_1/c/propagate_call_argument.nq` |
| `parser.nq:parse_stmt:1` | NQ-PARSE-003 | stage1 limitation: `?` is only supported in `let name = result_expr?;` | covered | NQ-PROPAGATE-007 | `tests/fixtures/m58_1/c/propagate_let_operand.nq` |
| `parser.nq:parse_stmt:2` | NQ-PARSE-003 | stage1 limitation: `?` is only supported in `let name = result_expr?;` | covered | NQ-PROPAGATE-007 | `tests/fixtures/m58_1/c/propagate_if_condition.nq` |
| `parser.nq:parse_stmt:3` | NQ-PARSE-003 | stage1 limitation: `?` is only supported in `let name = result_expr?;` | covered | NQ-PROPAGATE-007 | `tests/fixtures/m58_1/c/propagate_while_condition.nq` |
| `parser.nq:parse_stmt:4` | NQ-PARSE-003 | stage1 limitation: `?` is only supported in `let name = result_expr?;` | covered | NQ-PROPAGATE-007 | `tests/fixtures/m58_1/c/propagate_for_iterable.nq` |
| `parser.nq:parse_stmt:5` | NQ-PARSE-003 | stage1 limitation: `?` is only supported in `let name = result_expr?;` | covered | NQ-PROPAGATE-007 | `tests/fixtures/m58_1/c/propagate_return.nq` |
| `parser.nq:parse_stmt:6` | NQ-PARSE-003 | stage1 limitation: `?` is only supported in `let name = result_expr?;` | covered | NQ-PROPAGATE-007 | `tests/fixtures/m58_1/c/propagate_field_assign.nq` |
| `parser.nq:parse_stmt:7` | NQ-PARSE-003 | stage1 limitation: `?` is only supported in `let name = result_expr?;` | covered | NQ-PROPAGATE-007 | `tests/fixtures/m58_1/c/propagate_assign.nq` |
| `parser.nq:parse_stmt:8` | NQ-PARSE-003 | stage1 limitation: `?` is only supported in `let name = result_expr?;` | covered | NQ-PROPAGATE-007 | `tests/fixtures/m58_1/c/propagate_expr_stmt.nq` |
| `typecheck.nq:push_stage1_limitation:1` | NQ-TYPE-042 | stage1 limitation: unsupported expression shape in recursive type checker | removed |  | `selfhost/typecheck.nq!push_stage1_limitation` |
| `typecheck.nq:infer_struct_expr_type_ctx:1` | NQ-TYPE-042 | stage1 limitation: unsupported expression shape in recursive type checker | covered | NQ-TYPE-055 | `tests/fixtures/m58_1/c/struct_field_positional.nq`, `tests/fixtures/m58_1/c/struct_field_shorthand.nq` |
| `typecheck.nq:infer_struct_expr_type_ctx:2` | NQ-TYPE-042 | stage1 limitation: unsupported expression shape in recursive type checker | covered | NQ-TYPE-055 | `tests/fixtures/m58_1/c/struct_field_string_key.nq` |
| `typecheck.nq:infer_match_expr_type_ctx:1` | NQ-TYPE-042 | stage1 limitation: unsupported expression shape in recursive type checker | internal | T1 | `tests/fixtures/m58_1/c/accepted.nq` |
| `typecheck.nq:infer_expr_type_ctx_indexed:1` | NQ-TYPE-042 | stage1 limitation: unsupported expression shape in recursive type checker | covered | NQ-TYPE-058, NQ-PARSE-005 | `tests/fixtures/m58_1/c/callee_field.nq`, `tests/fixtures/m58_1/c/expression_field_number.nq` |
| `typecheck.nq:infer_expr_type_ctx_indexed:2` | NQ-TYPE-042 | stage1 limitation: unsupported expression shape in recursive type checker | covered | NQ-PARSE-004, NQ-TYPE-058, NQ-PARSE-005 | `tests/fixtures/m58_1/c/float_leading_dot.nq`, `tests/fixtures/m58_1/c/float_trailing_dot.nq`, `tests/fixtures/m58_1/c/float_exponent_lower.nq`, `tests/fixtures/m58_1/c/float_exponent_upper.nq`, `tests/fixtures/m58_1/c/float_exponent_minus.nq`, `tests/fixtures/m58_1/c/callee_parenthesized.nq`, `tests/fixtures/m58_1/c/callee_call_result.nq`, `tests/fixtures/m58_1/c/expression_malformed.nq`, `tests/fixtures/m58_1/c/expression_statement_malformed.nq` |
| `typecheck.nq:infer_const_expr_type_ctx:1` | NQ-TYPE-042 | stage1 limitation: unsupported const initializer expression | covered | NQ-TYPE-057 | `tests/fixtures/m58_1/c/const_name.nq`, `tests/fixtures/m58_1/c/const_call.nq`, `tests/fixtures/m58_1/c/const_list.nq` |
| `typecheck.nq:evaluate_typed_const:1` | NQ-TYPE-042 | stage1 limitation: missing typed constant evaluation | internal | T2 | `tests/fixtures/m54_9_arithmetic/constants.nq`, `tests/fixtures/m58_1/c/accepted.nq` |
| `typecheck.nq:typecheck_pattern_span:1` | NQ-TYPE-042 | stage1 limitation: unsupported expression shape in recursive type checker | covered | NQ-RESOLVE-010 | `tests/fixtures/m58_1/c/pattern_unknown_call.nq`, `tests/fixtures/m58_1/c/pattern_qualified_call.nq` |
| `typecheck.nq:typecheck_pattern_span:2` | NQ-TYPE-042 | stage1 limitation: unsupported expression shape in recursive type checker | covered | NQ-RESOLVE-010 | `tests/fixtures/m58_1/c/pattern_qualified_name.nq` |
| `typecheck.nq:typecheck_pattern_span:3` | NQ-TYPE-042 | stage1 limitation: unsupported expression shape in recursive type checker | covered | NQ-TYPE-056 | `tests/fixtures/m58_1/c/pattern_true.nq`, `tests/fixtures/m58_1/c/pattern_false_expression.nq`, `tests/fixtures/m58_1/c/pattern_string.nq`, `tests/fixtures/m58_1/c/pattern_negated_name.nq`, `tests/fixtures/m58_1/c/pattern_other_form.nq` |
