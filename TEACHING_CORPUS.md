# Nauqtype Teaching Corpus

This document organizes the canonical Nauqtype examples found in the `examples/` directory into a teaching corpus for future humans and AI models.

## Beginner Lessons

These examples introduce the core structure, syntax, and flow control of Nauqtype.

- [hello.nq](examples/hello.nq): Minimal program that prints a string to stdout.
- [simple_add.nq](examples/simple_add.nq): Demonstrates function calls, local variables, and basic arithmetic.
- [while_counter.nq](examples/while_counter.nq): Introduces `while` loops and the `bool` type.
- [fibonacci.nq](examples/fibonacci.nq): Combines functions, mutable locals (`mut`), and `while` loops.
- [mutate_counter.nq](examples/mutate_counter.nq): Demonstrates explicit `mutref` passing for mutable references.
- [user_record.nq](examples/user_record.nq): Introduces product types (`type`) and structural instantiation.
- [list_sum.nq](examples/list_sum.nq): Demonstrates iterating over a builtin `list<T>` using `list_len` and `list_get`.

## Language Feature Lessons

These examples cover specific semantic features of Nauqtype.

- [generic_reuse.nq](examples/generic_reuse.nq): Explicit imported function,
  product/enum specializations, n-ary/nested arguments, named call labels and
  borrowed lists. [generic_values.nq](examples/generic_values.nq) supplies the
  templates; no inference, traits, or hidden ownership rules. Legacy evidence
  commands deliberately reject generic graphs until a versioned export exists.

- [string_join.nq](examples/string_join.nq): Pure ordered byte assembly with an
  explicit borrowed `list<str>`, a named argument, and unchanged input ownership.
  PRE-M56 E1 acceptance is tracked in `PERFORMANCE_ENABLEMENT.md`.

- [f64_basics.nq](examples/f64_basics.nq): Scalar `f64` (M56.2): averaging
  `i64` samples through explicit `f64_from_i64`, rendering a percentage with
  `str_from_f64`, strict parsing with `f64_from_str`, truncating back with
  `f64_trunc_i64`, and the NaN (`x != x`) and finiteness (`x - x == 0.0`)
  idioms. Every fallible conversion returns `option` and is handled visibly.

- [in_place_update.nq](examples/in_place_update.nq): In-place updates
  (M57.1): a product holding a `list` is changed through `mutref` parameters
  with `list_push(mutref shelf.items, ...)` and `shelf.count = ...`, an
  element is swapped out with `list_replace` and removed with `list_pop` (both
  hand the old value back as `option`), an `i64` is narrowed with
  `i32_from_i64` and its `None` handled, and a payload-free enum is compared
  with `==`/`!=`. Each helper's `mutates(shelf)` covers both field writes and
  call-mediated writes.

- [list_literals.nq](examples/list_literals.nq): Using square brackets to construct homogeneous `list<T>` literals.
- [for_list.nq](examples/for_list.nq): Iterating directly over `list<T>` with an immutable per-iteration binding and nearest-loop `break` / `continue`.
- [composite_field_backend.nq](examples/composite_field_backend.nq): Storing `list<T>`, `option<T>`, and `result<T, E>` values in a product type and borrowing a list field directly for a helper call.
- [enum_match.nq](examples/enum_match.nq): Using `enum` types and the statement-level `match` block.
- [match_expr_let_else.nq](examples/match_expr_let_else.nq): Using `match` as an expression to yield values, and the `let-else` guard binding.
- [record_update.nq](examples/record_update.nq): Copy-only record update using the explicit `Type { from base, field: value }` syntax.
- [record_update_nontrivial.nq](examples/record_update_nontrivial.nq): Record update performed over a computed owned base value.
- [field_assignment.nq](examples/field_assignment.nq): Updating a direct field on an owned `let mut` product local without widening mutation authority (`in_place_update.nq` shows the same write through a `mutref` parameter).
- [named_arguments.nq](examples/named_arguments.nq): Using labeled arguments in direct function calls.
- [qualified_calls.nq](examples/qualified_calls.nq): Making direct module-qualified function calls across a flat-root module boundary.
- [qualified_call_chain.nq](examples/qualified_call_chain.nq): Multi-module qualified call chains across several files.
- [qualified_data_names.nq](examples/qualified_data_names.nq): Direct module-qualified struct literals and enum constructor names.
- [import_aliases.nq](examples/import_aliases.nq): Using an explicit local module alias for functions, struct literals, and enum variants.
- [top_level_const.nq](examples/top_level_const.nq): Defining and using stage1-owned top-level constants.
- [break_continue.nq](examples/break_continue.nq): Minimal `break` and `continue` statement usage within the nearest enclosing `while` loop.
- [nested_break_continue.nq](examples/nested_break_continue.nq): Using nested `break` and `continue` inside `if` conditionals within a `while` loop.
- [nested_patterns.nq](examples/nested_patterns.nq): Matching nested `option` constructors and an integer literal with an explicit fallback arm.

## AI and Evidence Workflow Demos

These examples demonstrate Nauqtype's unique AI supervision surfaces, contract enforcement, and fallibility handling.

- [review_contracts.nq](examples/review_contracts.nq): Using `audit` blocks with `intent`, `mutates`, and `effects` to declare human-readable AI contracts.
- [fallible_function.nq](examples/fallible_function.nq): Writing functions that return `result<T, E>`.
- [result_handling.nq](examples/result_handling.nq): Handling `Ok` and `Err` branches using `match`.
- [read_file_len.nq](examples/read_file_len.nq): Reading files and demonstrating the inferred `effects(io)` audit atom.
- [propagation_question.nq](examples/propagation_question.nq): Statement-boundary `?` operator usage with a `?[context_label]` provenance label and required `propagates(...)` audit evidence.
- [try_expression.nq](examples/try_expression.nq): Expression-position `?` captured at an explicitly typed local `try` boundary, with local evidence but no function-level propagation claim.
- [process_deadline.nq](examples/process_deadline.nq): Absolute executable provenance, bounded capture, a nominal monotonic deadline, and consuming child wait with explicit outcome handling.

## Multi-File Entrypoints

Runnable examples that act as the `main` entrypoint for multi-file operations.

- [multi_file_main.nq](examples/multi_file_main.nq): Simple multi-file entrypoint using `use` to import another module.

---

## Runnable Corpus Entries

The following runnable `.nq` examples make up the core locked corpus. They participate in the `prove-corpus` check, which guarantees they successfully undergo semantic checking, C emission, building, and runtime execution with the expected output:

- `break_continue.nq`
- `composite_field_backend.nq`
- `enum_match.nq`
- `f64_basics.nq`
- `fallible_function.nq`
- `fibonacci.nq`
- `field_assignment.nq`
- `for_list.nq`
- `generic_reuse.nq`
- `hello.nq`
- `import_aliases.nq`
- `in_place_update.nq`
- `list_literals.nq`
- `list_sum.nq`
- `match_expr_let_else.nq`
- `multi_file_main.nq`
- `mutate_counter.nq`
- `named_arguments.nq`
- `nested_break_continue.nq`
- `nested_patterns.nq`
- `propagation_question.nq`
- `process_deadline.nq`
- `qualified_call_chain.nq`
- `qualified_calls.nq`
- `qualified_data_names.nq`
- `read_file_len.nq`
- `record_update.nq`
- `string_join.nq`
- `record_update_nontrivial.nq`
- `result_handling.nq`
- `review_contracts.nq`
- `simple_add.nq`
- `top_level_const.nq`
- `try_expression.nq`
- `user_record.nq`
- `while_counter.nq`

## Helper-Only Modules (Formatter Gated)

These examples provide imported definitions for the runnable examples above. They are not directly runnable entrypoints, but they are guaranteed to pass `fmt --check` formatting checks via the `prove` gate to remain canonically structured:

- [batch_b_helper.nq](examples/batch_b_helper.nq)
- [generic_values.nq](examples/generic_values.nq)
- [multi_file_helper.nq](examples/multi_file_helper.nq)
- [qualified_call_chain_math.nq](examples/qualified_call_chain_math.nq)
- [qualified_call_chain_mid.nq](examples/qualified_call_chain_mid.nq)
- [qualified_data_helper.nq](examples/qualified_data_helper.nq)
- [import_aliases_helper.nq](examples/import_aliases_helper.nq)

## Negative Diagnostics (Supervised Failure)

Rather than maintaining explicitly broken source files that fail `prove-corpus`, we use the canonical examples above to demonstrate negative diagnostics.

To teach supervised failure to a model:
1. **Unpropagated Errors:** Remove the `propagates(io_err)` clause from `examples/propagation_question.nq` and run `bin/nauqc check` to see `NQ-PROPAGATE-004`.
2. **Undeclared Mutation:** Remove the `mutates()` clause from `examples/mutate_counter.nq` to see the compiler infer the `mutref` and demand the contract.
3. **Invalid Exact Error:** Try using `?` on an `io_err` inside a function returning `result<str, parse_err>` in `examples/fallible_function.nq` to see the exact matching rules reject the code (`NQ-PROPAGATE-003`).
4. **Restricted Field Mutation:** Remove `mut` from `score` in `examples/field_assignment.nq`, or change `shelf: mutref Shelf` to `shelf: ref Shelf` in `examples/in_place_update.nq`, to see field writes rejected outside owned mutable product locals and `mutref` parameters.
5. **Refined Pattern Fallback:** Remove the `_` arm from `examples/nested_patterns.nq` to see refined patterns rejected until their fallback path is explicit.
6. **Ambiguous Try Boundary:** Remove the `result<i32, io_err>` annotation from `measured` in `examples/try_expression.nq` to see `NQ-TRY-001` require explicit boundary truth.
7. **Unsafe Try Control Flow:** Put a propagated call on the right side of `and` inside `try` to see `NQ-TRY-004` preserve short-circuit semantics rather than hoisting the call.
8. **Explicit Generic Arguments:** The owned `tests/fixtures/m56_generics/`
   probes pair valid values with arity, visibility, parameter-capture,
   ownership, recursion/bounds and original-source diagnostic failures. Use
   `identity::<i32>(7)`, not inferred `identity(7)`. An unused template is not a
   universal proof that its operations work for every possible type.
9. **No Implicit Numeric Conversion:** `let total: f64 = count;` with
   `count: i64` (`tests/fixtures/m56_2_f64/teaching_negative.nq`) is rejected
   with `NQ-TYPE-042` "annotated local initializer does not match declared
   type" and the help "use `f64_from_i64(count)` — Nauqtype never converts
   numbers implicitly". Write `let Some(total) = f64_from_i64(count) else {
   ... };` and handle the `None` case (an `i64` that is not exactly
   representable). The `integer-policy` suite pins this exact diagnostic.
10. **M57.1 Library-Core Rules:** `tests/fixtures/m57_1_core/teaching_negative.nq`
    shows an enum variant named like a builtin (`NQ-RESOLVE-010`), a statement
    `match` missing a variant (`NQ-TYPE-051`), assignment to a plain `let`
    (`NQ-TYPE-007`), and `str <` (`NQ-TYPE-050`). Later-phase codes need a
    clean front end, so they have companion files: `teaching_negative_place.nq`
    (`mutref` through a `ref` parameter's field, `NQ-TYPE-012`),
    `teaching_negative_layout.nq` (a type containing itself through a `list`,
    `NQ-TYPE-052`), and `teaching_negative_borrow.nq` (a forwarded `mutref`
    parameter beside `mutref` of its own field in one call, `NQ-BORROW-006`).
    The `integer-policy` suite pins each exact diagnostic.
