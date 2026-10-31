# M57.1: Library-Enabling Core

Status: Gate A passed, 2026-10-31 (revision 4, approved with no findings).
Compiler lead. Implemented 2026-10-31; closing evidence in AUDIT_REMEDIATION. Base:
`675819b`. Planning context: [M57 plan](M57_PLAN.md). The independent Gate A
reviewer (gpt-5.6-sol xhigh) required changes on revision 1 (six blocking,
two should-fix, one nit), revision 2 (four blocking, three should-fix,
one nit) and revision 3 (one blocking, one should-fix); all are addressed
below.
Closing evidence will be recorded in AUDIT_REMEDIATION, not here.

This is the implementation contract and the `SYNTAX_IDENTITY.md` decision
record for the feature set. No new syntax is added; every change widens or
narrows the meaning of existing syntax, or adds builtins.

## Problem And Real Usage Pressure

M57.2-M57.4 ship maps, sets and JSON as ordinary Nauqtype modules
(STABLE_RELEASE engineering rules). Probes against `675819b` show that no
user-written data structure can be updated in place today:

- `fn insert(m: mutref Map, ...)` cannot touch `m.items`: `mutref m.items` is
  rejected and field assignment rejects `mutref` parameters.
- A list element can only be appended or copied out (`list_get` needs a copy
  element type). Nothing replaces or removes an element, so neither a hash
  table nor removal can be written, and a move-only value can never be taken
  back out of a list.
- `i32` and `i64` cannot be converted, so an `i64` hash cannot index a list.
- Three SPEC violations make library code silently wrong or late-failing:
  assignment to a plain `let` is accepted; a statement `match` missing a
  variant compiles and falls off the end of the function; `==`/`<` on types
  the backend cannot compare (`str <`, any enum, products, containers) pass
  `check` and then fail in the C compiler.
- A type that contains itself through a `list` field fails with
  NQ-HANDOFF-002 and no source location.
- Found during Gate A: a `mutref` parameter forwarded by name to two borrow
  parameters of one call (`f(p, p)`, or `f(p, mutref p.items)`) is not
  recorded as a borrow, so two live mutable aliases of one place can exist.
  And a user function declared with a builtin's name is silently ignored in
  favour of the builtin.

## Canonical Forms

### `mutref` field places

```nauq
fn add(bag: mutref Bag, value: i32) -> unit
audit {
    intent("append a value");
    mutates(bag);
    effects();
}
{
    list_push(mutref bag.items, value);
    bag.count = bag.count + 1;
}
```

- A `mutref` borrow argument may name a field path `root.f1.f2...`, the same
  shape `ref` already accepts. The root must be mutable-capable: a `let mut`
  owned local or a `mutref` parameter (the nearest visible binding decides).
  Any other root (`ref` parameter, immutable local, owned parameter, `for`
  binding, pattern or `let-else` binding) is rejected with NQ-TYPE-012
  "cannot take `mutref` of immutable binding `<root>`", naming the root (the
  message no longer renders an empty name).
- Fields are product fields only (enum payloads have no field syntax). A
  field path through a generic product instance works the same way.
- `ref` parameters stay `const` pointers in C; nothing in this milestone
  writes through them.

### Borrow conflicts (root-based)

- Within one call, every argument that borrows under root `r` is a borrow of
  `r`: `ref r...`, `mutref r...`, and a borrow-typed parameter `r` passed by
  name to a borrow parameter (its kind is the parameter's kind: `ref` or
  `mutref`).
- A `mutref` borrow of `r` conflicts with any other borrow of `r` in the same
  call: NQ-BORROW-006 "conflicting borrows of `r` in one call" (message
  unchanged). Two `ref` borrows never conflict.
- So `f(mutref b.items, ref b.count)` and `f(p, p)` with two `mutref`
  parameters are rejected; write two statements. Field-disjoint checking is
  deferred.
- The forwarded-name case newly rejects some programs `675819b` accepted;
  they create two mutable aliases of one place, so they are unsound and the
  rejection is a repair (listed under Migration).

### Field assignment through a `mutref` parameter

- `p.field = value;` is accepted when `p` (nearest visible binding) is a
  `mutref` parameter of a user-defined product type, including a concrete
  generic product instance, in addition to the existing owned `let mut`
  local. It writes through the borrow and lowers to `(*p).member`. The
  overwritten field value is dropped exactly as for the owned case (the
  existing replace-then-drop path).
- Still rejected with the existing messages: nested field paths
  (`p.a.b = v`), `ref` parameters, owned non-`mut` locals and parameters,
  enum values, list elements.

### List builtins

```nauq
fn list_replace(items: mutref list<T>, index: i32, value: T) -> option<T>;
fn list_pop(items: mutref list<T>) -> option<T>;
```

- `list_replace`: when `0 <= index < list_len`, stores `value` at `index`
  and returns `Some(old)`, moving the old element out (exactly one owner:
  the result). Otherwise the list is unchanged, `value` is dropped once, and
  the result is `None`.
- `list_pop`: removes the last element and returns it as `Some`, moving it
  out (the list no longer owns it, so dropping the list later does not drop
  it), or returns `None` when empty.
- Neither requires a copy element type (they move, unlike `list_get`).
- Both mutate argument 0 for audit purposes (like `list_push`), have no
  effects, and are O(1). Capacity is not shrunk.

### Integer conversions

```nauq
fn i64_from_i32(value: i32) -> i64;
fn i32_from_i64(value: i64) -> option<i32>;
```

- `i64_from_i32` is exact. `i32_from_i64` returns `None` outside
  `[-2147483648, 2147483647]`.
- No implicit conversion is added. Unsuffixed literal rules (D055) are
  unchanged.

### Builtin names are reserved

- A top-level function, type, enum, enum variant or constant whose name is a builtin
  callable name (the full `is_builtin_name` set, old and new: builtin
  functions plus the builtin constructors `list`, `Some`, `None`, `Ok`,
  `Err`) is rejected at its declaration with NQ-RESOLVE-010 "builtin
  callable names cannot be redeclared", the same code and producer as the
  existing process/time
  type-name rule. Today such a declaration is silently ignored in favour of
  the builtin; this is a repair, listed under Migration.

### Comparison typing (runtime expressions)

After M57.1, `check` accepts exactly these operand types for runtime
comparison expressions (both sides identical):

| Operators | Operand type |
| --- | --- |
| `==`, `!=` | `i32`, `i64`, `f64`, `bool`, `str`, payload-free enums |
| `<`, `<=`, `>`, `>=` | `i32`, `i64`, `f64` |

- A payload-free enum is a non-generic user enum, or a concrete instance of
  a generic user enum, whose declared variants all have no payload
  (decided from the variant declarations, after instantiation). `==`
  compares variants; lowering compares tags, `((a).tag == (b).tag)` for `==`
  and `((a).tag != (b).tag)` for `!=`, in both C lowering paths (`emit_expr`
  and `lower_expr_value`); tests cover both operators on both paths.
- `bool` ordering is rejected (frozen at Gate A; no meaningful order, and no
  use was found in the compiler, examples or fixtures; a self-build failure
  would reopen this contract, not be patched at Gate B).
- Constant expressions are out of scope: `const` comparisons keep their
  existing integer-only checker, evaluator and messages unchanged.
- Diagnostic precedence for a runtime comparison: unknown operand types
  produce nothing new; mismatched types keep NQ-TYPE-042 "comparison
  operands must have matching types" with its existing help; duration,
  instant, process or process_outcome keep NQ-TYPE-042 "process and time
  values do not support comparison operators"; when both apply (mismatched
  operands where one side is a process/time type) both NQ-TYPE-042
  diagnostics are still emitted, mismatch first, exactly as today; any
  other identical type not in the table gets NQ-TYPE-050 (exact text in the
  diagnostics matrix), and NQ-TYPE-050 never accompanies a mismatch.

### Assignment mutability

- **NQ-TYPE-007** rejects `name = value;` unless the nearest visible binding
  of `name` is a `let mut` local or a `mutref` parameter. This covers plain
  `let`, owned parameters, `ref` parameters, `let-else` and pattern
  bindings. `for` bindings keep their existing message and code. Shadowing
  is respected in both directions (a `let mut` shadowed by a plain `let` is
  immutable, and the reverse is mutable).

### Statement `match` exhaustiveness

- Scope: a statement `match` whose scrutinee is a closed-domain type (a user
  enum, `option<T>` or `result<T, E>`) and whose arms contain no wildcard or
  binding fallback. Integer scrutinees and literal or nested-constructor
  patterns are already governed by the existing refined-group rule
  ("literal or nested constructor patterns require a wildcard or binding
  fallback arm", unchanged), so no new open-domain rule is added and no
  string-pattern case exists (string patterns are deferred).
- Rule: every variant of the scrutinee type must be covered by a top-level
  variant arm. Otherwise **NQ-TYPE-051**, spanning the `match` keyword.
- The check runs on the `match` statement node, not on its arm list, so a
  zero-arm statement `match` over a closed type with at least one variant is
  reported with every variant missing. A zero-arm `match` over an empty user
  enum (which the language accepts today) has no missing variant and stays
  accepted; a regression test pins this.
- Emitter backstop (compile time, not a runtime trap): if `emit_match_stmt`
  meets a closed-domain statement match without a fallback whose arms do
  not cover every variant, it emits the existing emitter diagnostic code
  NQ-C-001 with message "internal: non-exhaustive statement match reached C
  emission", spanning the `match` keyword, and generates no C for the
  function. The check is a preflight over the function's checked IR before
  any of its C is appended, so suppression is real. This is unreachable from
  source once typecheck passes; an owned IR-level emitter test supplies a
  function containing a non-covering closed statement match and asserts the
  exact code, message and span, and that the emitted C contains no
  definition of that function.
- `match` expressions keep their existing NQ-TYPE-042 "match expression must
  be exhaustive" unchanged. Missing-return analysis is not added.

### Recursive layouts

- Scope: graphs that contain no generic declarations. Graphs with generics
  keep running the existing generic layout checker with its existing
  NQ-GENERIC-005 output unchanged (it already rejects every by-value cycle
  in such graphs, generic or not).
- Graph: nodes are the user products and enums; an edge `A -> B` exists for
  each field or payload of `A` whose type mentions `B` by value directly or
  through `list`, `option` or `result` arguments, at any depth.
- Edge enumeration order (used for every tie-break): fields of a product in
  declaration order; for an enum, variants in declaration order, then each
  variant's payload types left to right; within one type expression, a
  left-to-right preorder (`list<X>` and `option<X>`: X; `result<X, Y>`: X
  then Y, each fully before the next). Each target node is enumerated at its
  first occurrence in this order; later duplicate edges to the same target
  from the same node are ignored.
- Every strongly connected component with a cycle (two or more nodes, or one
  node with a self-edge) is reported once with **NQ-TYPE-052**, at the
  declaration of its representative: the member that comes first in the
  checked module order (the order modules appear in facts output), then by
  source offset.
- The reported path is the shortest cycle from the representative back to
  itself, found by breadth-first search that expands each node's edges in
  the enumeration order above (so among equally short cycles the one using
  earlier edges wins), spelled as type names joined by `" -> "`, for example
  `Json -> Json` or `Tree -> Branch -> Tree`.
- The check runs in `check` (not only `run`). NQ-HANDOFF-002 remains as an
  internal backstop. Supporting recursion through `list` is deferred (M57
  uses arena JSON).

## Rejected Alternatives

- **A builtin `map<K, V>` type.** Rejected by STABLE_RELEASE's engineering
  rules; the same field and list gaps would still block every other library.
- **Field-disjoint borrow checking** (`f(mutref b.a, ref b.b)`). More
  precise, but needs place-aware conflict tracking in borrow, review and C
  aliasing reasoning. Deferred; the conservative rule only rejects programs.
- **Moving fields out of owned products** (destructuring). Not needed once
  fields can be mutated in place and list elements replaced; deferred.
- **`list_replace` returning `result<T, T>`** (the value back on a bad
  index). Rejected for consistency with `list_get`'s `option` and because
  `result` error types participate in propagation; index validity is the
  caller's job.
- **Fatal error on a bad index.** Rejected: list access is fallible by
  value everywhere else.
- **A `%` operator, bitwise operators.** Not needed for hashing (wrapping
  `*`/`+` and `a - (a / b) * b` suffice); separate decision if ever needed.
- **Extending constant comparisons** to `bool`, `str` or enums. No pressure;
  C constant initializers would need separate lowering.

## Authority And Evidence Impact

- Mutation is a review and contract-validation surface; facts carry no
  inferred mutation fields. Facts v1-v5 change only by listing the four new
  builtins wherever calls to builtins already appear.
- `mutref p.f...` attributes a mutation to root `p` (already true through the
  handoff's root binding id). `list_replace` and `list_pop` mutate argument
  0. Missing `mutates(p)` is NQ-CONTRACT-005 as today.
- Which surface reports which new mutation shape (each surface keeps its
  existing inference model; AI_CONTRACTS describes v3 as direct-assignment
  only):

  | Surface | Direct field assignment through `mutref p` | Call-mediated (`mutref p.f` argument, `list_replace`, `list_pop`) |
  | --- | --- | --- |
  | review v1/v2 (legacy, name-based) | yes, projected only when proven (below) | no (unchanged model) |
  | review v3 (direct assignments only) | yes | no (unchanged model) |
  | review v4/v5 and `check` contract validation | yes | yes |

- Review v1/v2 legacy inference matches names, not binding ids. A field
  write is projected into its `assignment_fact` only when the handoff proves
  the field assignment's root binding id is a `mutref` parameter of that
  function. This projection runs after handoff, so the post-handoff wiring
  in `selfhost/main.nq` (around the legacy review path) is in the write set.
  A shadowing owned local named like a parameter is never projected
  (regression test required).
- No new effect atoms. No schema version changes.
- Compatibility: output is byte-identical for every program `675819b`
  accepts, except programs M57.1 now rejects. The complete list: assignment
  to an immutable binding (NQ-TYPE-007); non-exhaustive statement `match`
  (NQ-TYPE-051); comparisons in the NQ-TYPE-050 set, including `bool`
  ordering; a forwarded borrow parameter conflicting in one call
  (NQ-BORROW-006); a top-level item or enum variant named like a builtin
  callable, such as `enum E { Some(i32) }` (NQ-RESOLVE-010);
  a non-generic recursive layout now reported at `check` as NQ-TYPE-052
  instead of NQ-HANDOFF-002 later.

## Diagnostics And Formatter Rule

Every new or changed diagnostic, exactly. Spans: the given token, `start` to
`end` of that token. All help lines appear in JSON diagnostics and in text
output wherever the existing text renderer shows help.

| Code | Span | Message | Help |
| --- | --- | --- | --- |
| NQ-TYPE-007 | assignment target name | ``cannot assign to immutable binding `<name>` `` | plain `let` or `let-else` binding: ``declare it with `let mut <name>` to allow assignment``; `ref` or owned parameter: ``parameters are immutable; take `mutref` to write through a borrow``; match-pattern binding: ``copy the value into a `let mut` local before assigning`` |
| NQ-TYPE-012 | the root name after `mutref` | ``cannot take `mutref` of immutable binding `<root>` `` | existing (none) |
| NQ-TYPE-050 | operator token | ``operator `<op>` is not defined for type `<type>` `` | `str` with `<`, `<=`, `>`, `>=`: ``compare text with a library function; `str` supports only `==` and `!=` ``; enum with payloads: ``use `match` to compare variants with payloads``; `bool` ordering: ```bool` supports only `==` and `!=` ``; otherwise: ``compare the fields or elements individually`` |
| NQ-TYPE-051 | `match` keyword | ``match statement must be exhaustive; missing `<V1>`, `<V2>` `` (variants in declaration order; `option`: `Some`, `None`; `result`: `Ok`, `Err`) | ``add an arm for each missing variant or a `_ => { ... }` fallback arm`` |
| NQ-TYPE-052 | representative declaration name | ``type `<Name>` contains itself through `<path>`; recursive data layouts are not supported`` | ``store related values in a separate list and refer to them by index`` |
| NQ-BORROW-006 | existing | existing | existing |
| NQ-RESOLVE-010 | declaration or variant name | ``builtin callable names cannot be redeclared`` | none (existing producer) |
| NQ-C-001 | `match` keyword | ``internal: non-exhaustive statement match reached C emission`` | none (existing producer; backstop, unreachable from source) |

`<type>` uses the canonical type spelling of existing diagnostics. The
formatter is unchanged (no new syntax).

## Teaching Positive And Negative Cases

- `examples/in_place_update.nq`: a product holding a `list`, updated through a
  `mutref` parameter (`list_push(mutref p.items, ...)`, `p.count = ...`),
  `list_replace`, `list_pop`, `i32_from_i64` with `match`, and payload-free
  enum `==`. Listed in TEACHING_CORPUS.
- `tests/fixtures/m57_1_core/teaching_negative.nq` cases: each new code once,
  with the exact expected diagnostics.

## Compiler Phases And Schema Effects

- Resolve: builtin names; builtin-name redeclaration rejection.
- Typecheck: borrow-place shape for `mutref`, root mutability, field
  assignment root rule, builtin tables (arity, return, parameters, expected
  argument context, option return context), comparison table, NQ-TYPE-007,
  statement exhaustiveness, recursive layout check.
- Borrow: builtin parameter tables, forwarded-borrow conflict repair.
- Value plan: builtin borrow arguments.
- Handoff: builtin parameter tables (borrow field paths already build field
  chains under the root binding id).
- Review/facts: builtin tables, mutation profile, field assignment as a
  direct mutation, legacy projection by proven root.
- C emission: `mutref` field places (expected to need no change; tested),
  field assignment target `(*p).member` for `mutref` parameters, per-element
  `_replace`/`_pop` list helpers, `nq_i64_from_i32`/`nq_i32_from_i64`, enum
  tag equality in both lowering paths, statement-match backstop.
- Runtime: `nq_list__str_replace`/`nq_list__str_pop` for the runtime-native
  `list<str>`, the two integer conversions with a runtime-native
  `NQ_Option__i32` carrier if not already present.

## Migration And Deferred Extensions

- Programs relying on the repaired defects stop compiling with the codes in
  the compatibility list above. Old-compiler/new-compiler fixtures show each
  one accepted (or failing late) at `675819b` and rejected at `check` now.
- The tutorial site's caveat snippets (`L01-assign-plain-let`,
  `L06-statement-gap`, `L03-str-lt`) are expected to flip; the site
  maintainer updates them after the push.
- Deferred and recorded in DEFERRED: recursion through containers,
  field-disjoint borrows, moving fields out, missing-return analysis, `%`,
  non-integer constant comparisons.

## Write Set And Audit Classification

- `selfhost/`: `resolve.nq`, `typecheck.nq`, `borrow.nq`, `value_plan.nq`,
  `handoff.nq`, `review.nq`, `facts.nq`, `main.nq` (post-handoff legacy
  projection wiring), `parser.nq` (only if the legacy
  projection needs a parser fact), `c_emit.nq`, `builtin_evidence.nq`, and
  the generic layout module if NQ-TYPE-052 shares its graph walk.
- `stdlib/runtime.h`, `stdlib/runtime.c`.
- Tests: a focused section in an existing selfhost test module,
  `selfhost/proof.nq` corpus entry, `tests/fixtures/m57_1_core/**`, goldens
  touched only where a builtin inventory lists builtins,
  `examples/in_place_update.nq`.
- Docs: SPEC (borrow expressions, assignment, product rules, operators,
  match, builtins, ownership), AI_CONTRACTS (mutation inference),
  TEACHING_CORPUS, DEFERRED, DECISIONS D068, ROADMAP/TODO status lines, and
  the M57 plan wording on recursive layouts.

No new `.nq` module, no `push_selfhost_modules` change, no seed change.
**Ownership milestone** under AGENTS.md (it changes mutable-place authority,
alias checking, move-only list operations and destruction): a
`gpt-5.6-sol` `xhigh` primary trailing auditor plus an independent `gpt-5.5`
`xhigh` adversarial auditor, each reaching a verdict before seeing the
other's; any unavailable-model fallback is recorded in the evidence. If the
self-build needs source repairs because the compiler relied on a repaired
defect, they are in scope and listed in the evidence; a new module or
inventory change reclassifies the milestone as bootstrap-boundary.

Suggested slices: **A** typecheck/resolve front end (places, assignment,
comparisons, exhaustiveness, layouts, builtin-name reservation); **B**
builtins end to end (tables, borrow including the forwarded-borrow repair,
value plan, handoff, c_emit, runtime); **C** evidence, tests, docs from the
merged tree.

## Tests And Acceptance

- `mutref` places: owned-local root, `mutref`-param root, two-level path,
  generic product instance, `list_push`/`list_replace`/`list_pop` through a
  field; rejected roots (`ref` param, immutable local, owned param, `for`
  binding, pattern binding) with NQ-TYPE-012 naming the root.
- Borrow conflicts: two paths under one root with one `mutref`; a forwarded
  `mutref` parameter twice (`f(p, p)`); forwarded parameter plus a field
  borrow; two `ref` borrows accepted.
- Field assignment through `mutref` params: scalar, `str`, `list` fields,
  and a generic product instance field; nested path and `ref` param still
  rejected; generated C keeps `ref` parameters `const`.
- Ownership under the ASan/UBSan owned-test leg: a successful
  `list_replace` transfers exactly one owner (old value dropped once by the
  caller, new value dropped once with the list); an out-of-range
  `list_replace` drops the incoming owned value once; `list_pop` result
  survives dropping the shortened list; a field assignment drops the old
  `list` field once; runtime-native `list<str>` reference counts balance
  across replace and pop.
- Builtins: in range, out of range (negative, `len`), empty pop, move-only
  element types (`list<list<i32>>`), `list<str>`, a generic instance;
  `i32_from_i64` at both bounds and one past each.
- Comparisons: the accepted table executes; NQ-TYPE-050 at `check` for
  `str <`, enum-with-payload `==`, product `==`, `option`, `list`, `unit`,
  `bool <`; payload-free generic enum instance accepted; mismatch and
  process/time cases keep their NQ-TYPE-042 text; `const` comparisons
  unchanged.
- NQ-TYPE-007 for each binding kind, with shadowing both ways.
- NQ-TYPE-051 for an enum, `option`, `result`, and a zero-arm statement
  `match`, with exact missing-variant lists; a zero-arm match over an empty
  enum stays accepted; exhaustive statement matches and refined-group
  behaviour unchanged; the IR-level emitter backstop test (diagnostic and
  function suppression).
- NQ-TYPE-052 for a self cycle, a `list` cycle, an `option` cycle, a
  two-type cycle, a cross-module cycle, two independent cycles (two
  diagnostics), and a tied path through `result<B, C>` where both arguments
  close equally short cycles (the `B` path is reported); with the declaration location and exact path; `check`
  fails, not only `run`; a graph with generics still reports NQ-GENERIC-005
  unchanged.
- NQ-RESOLVE-010 for a function, a type, an enum, an enum variant and a
  constant named like a builtin function (old and new, including
  `print_line`), and for declarations named like a builtin constructor
  (`fn list`, `enum E { Some(i32) }`), each with an old/new compatibility
  fixture.
- Evidence: each surface reports exactly the shapes in the mutation-surface
  table (and no others); legacy shadowing regression; facts
  list the new builtin calls; goldens unchanged for existing programs.
- Compatibility fixtures for each rejected class (old accepts or fails late,
  new rejects at `check`).
- The full corpus and self-build pass (the compiler source compiles under
  the stricter rules).

## Implementation Notes

Deviations from this contract that the compiler lead accepted during
implementation (also summarized in D068):

1. NQ-RESOLVE-010 is narrowed to enum variants only. M55 Gate B deliberately
   supports user functions named like builtins reached by qualified calls
   (`tests/fixtures/m55_process/compiler_import_provider.nq`,
   `selfhost/process_tests.nq`); an unqualified call reaches the builtin as
   before. Top-level types, functions, enums and constants named like
   builtins remain accepted.
2. The forwarded-borrow kind is the receiving parameter's kind: a `mutref`
   parameter forwarded to two `ref` parameters is accepted (two shared
   borrows).
3. A cross-module recursive cycle cannot exist, because import cycles are
   NQ-IMPORT-002. The test covers one cycle in each of two modules, ordered
   by checked module order.
4. A zero-arm statement `match` over an empty enum was not accepted at
   `675819b` (it fails with NQ-HANDOFF-002, because empty enums get no checked
   declaration). M57.1 leaves that baseline unchanged and only guarantees that
   no NQ-TYPE-051 is added.
5. The `emit_expr` equality path is unreachable from source; enum tag
   lowering on that path is covered by an IR probe
   (`selfhost/c_emit_index_probe.nq`).
6. Slice C integration choices:
   - NQ-TYPE-050 spells a concrete generic instance the way source writes it
     (`Pair<i32>`, `Holder<result<i32, str>>`, `Holder<Pair<bool>>`): the
     module-free nominal name and the `", "` separator every other comparison
     type uses, never the internal `__nqg_` name. Decoding the generated name
     needs `use generic_names;` in `selfhost/typecheck.nq`, an import edge, not
     a new module or an inventory change.
   - facts and review, in every format, run the NQ-TYPE-052 check at the same
     point `check` does (right after the checked handoff, non-generic graphs
     only), so they report the identical diagnostic and location. Generic
     graphs in facts/review v5 keep their previous behaviour.
   - The legacy name-based projection also applies to `review-diff`, which
     shares the review v1/v2 inference model.
   - The teaching negatives are four files, not one. Later-phase codes are
     only reported once earlier phases are clean, so
     `tests/fixtures/m57_1_core/teaching_negative.nq` holds NQ-RESOLVE-010,
     NQ-TYPE-051, NQ-TYPE-007 and NQ-TYPE-050, and the companion files
     `teaching_negative_place.nq` (NQ-TYPE-012), `teaching_negative_layout.nq`
     (NQ-TYPE-052) and `teaching_negative_borrow.nq` (NQ-BORROW-006) hold one
     code each.
7. Trailing-audit repairs (no rule above changes; these make the shipped
   compiler match it):
   - A qualified call `m::name(...)` never reaches a builtin, as note 1
     requires, for every builtin name including `list`, `list_push`,
     `list_len`, `list_get`, `list_replace`, `list_pop`, `str_join`,
     `i64_from_i32` and `i32_from_i64`. The call-site arity check uses only the
     qualified function or qualified variant (never an unqualified function,
     variant or builtin of the same name), list-specific argument and result
     inference applies only to unqualified calls that resolve to the builtin,
     and C lowering selects a list helper only for a `__builtin__` target
     origin.
   - The nearest visible binding (type, `let mut`, `mutref`) is the visible
     declaration with the greatest position before the use, independent of
     whether either binding is annotated or inferred. Same-scope shadowing
     stays NQ-RESOLVE-010, so this only concerns nested scopes. The type
     checker selects by position, and it publishes each function's resolved
     bindings in declaration order, so the checked handoff's statement,
     field-assignment and borrow contexts (and every later phase) see the same
     nearest binding.
   - A parenthesized borrowed place (`mutref (bag.items)`, `ref (bag.count)`)
     resolves its root binding after the same parenthesis normalization the
     type checker uses, so it passes the checked handoff and takes part in the
     root-based NQ-BORROW-006 rule.

Where the tests live: slice tests in `selfhost/integer_policy_tests.nq`
(`m57_1_a1_gate`, `m57b_gate`, `m57a2_gate`, the cross-slice `m57c_gate`, and
the trailing-audit repair `m57r_gate`) with fixtures under
`tests/fixtures/m57_1_core/{a1,a2,b,c,repair}/` (the direct `emit_expr` half
of the qualified-call repair is an IR probe in
`selfhost/c_emit_index_probe.nq`, part of `c_emit_membership_index_cases`);
the mutation surface table and the field-write contract checks in
`selfhost/contract_evidence_tests.nq`; the facts/review v5 goldens
`tests/golden/schema_profile/{facts,review}-v5-m57-1.json` in
`selfhost/m56_generics_tests.nq`; `examples/in_place_update.nq` in the locked
proof corpus and formatter list.

## Acceptance Gate

M57.1 is complete when all of the above pass in the single milestone gate,
both trailing audits have no open findings, SPEC/AI_CONTRACTS describe the
shipped rules, DECISIONS records D068, and DEFERRED lists the deferred items
above.
