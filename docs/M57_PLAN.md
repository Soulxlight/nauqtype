# M57 Plan: Collections And Data Interchange

Status: planning record, 2026-10-31, compiler lead. Base: `675819b`. Not a
contract. Each sub-milestone below gets its own contract and Gate A review.

ROADMAP M57 asks for reusable map/set facilities with an explicit, checked key
strategy, an in-repo standard library shipped with the compiler and copied
release, and a deterministic JSON value/parser/writer. STABLE_RELEASE's
engineering rules require collections and JSON to be ordinary Nauqtype
modules, adding runtime primitives only for operating-system boundaries.

## What Blocks A Pure-Nauqtype Library Today

Probed against `675819b` (2026-10-31, `nauqc run` on small programs):

| Need | Today | Effect on a library |
| --- | --- | --- |
| Mutate a list stored in a product | `mutref b.items` is rejected ("borrow expression must name a binding or field path"); field assignment rejects `mutref` parameters (SPEC Assignment) | A `Map` value cannot be updated in place by `fn insert(m: mutref Map, ...)`. The M56.1 fixture copies both lists on every `put` (O(n) per insert). |
| Move a field out of an owned product | NQ-BORROW-004 "moving out of fields is not supported" | Functional `m = insert(m, k, v)` threading cannot rebuild the product either. |
| Replace or remove a list element | Only `list()`, `list_push`, `list_len`, `list_get` (copy element types only) | No hash table, no removal, no way to take a move-only value back out. |
| Convert between `i32` and `i64` | No builtin (only the M56.2 `f64` conversions) | Hashing in `i64` cannot produce an `i32` index; JSON integers cannot meet `list_len`. |
| Compare enums | `a == b` on an enum passes `check`, then fails in the C compiler (new finding; same class as the open `str <` defect) | JSON kind checks and key comparisons cannot be written safely. |
| Recursive data through `list` | Non-generic `enum J { Arr(list<J>) }` fails with NQ-HANDOFF-002 "cyclic by-value type shape" and no location; generic recursion is NQ-GENERIC-005 | A recursive JSON tree type is not expressible. |

No traits or function values exist, so a generic `Map<K, V>` cannot call a
per-key hash or comparison. `==` type-checks per instance, but hashing does
not.

## Decisions Taken In This Plan

1. **Fix the language, not the runtime.** Close the place, field and list gaps
   as general language features (M57.1). They are needed by any user-written
   data structure, not only the standard library. No builtin `map` type.
2. **Explicit key strategy = key-specialized types.** The library ships
   `NqStrMap<V>`, `NqI64Map<V>`, `NqStrSet` and `NqI64Set`, generic only in
   the value type. The key type is visible in the type name and checked by
   ordinary typing. No trait, no hidden dispatch, no runtime hashing
   primitive (hashing is written in Nauqtype with wrapping arithmetic). Other
   key types can be added later as more specialized modules.
3. **Deterministic iteration.** Maps and sets iterate in insertion order. A
   removed key is gone from the order. Map contents never depend on hash
   seeds, addresses, or the host.
4. **JSON as an arena document, not a recursive type.** `NqJsonDoc` holds a
   list of copyable nodes addressed by `NqJsonNode` handles (an `i32` index
   product). Reading uses `list_get` on copyable nodes; building appends
   nodes. This needs none of the recursive-layout work, matches the
   compiler's own `schema_profile.nq` reader, and gives AI callers flat,
   explicit calls. Recursive non-generic types through `list` stay deferred;
   M57.1 rejects them at `check` with a located NQ-TYPE-052 instead of the
   location-less NQ-HANDOFF-002.
5. **Number rule (ROADMAP).** A JSON number whose text is an integer (no
   `.`, no exponent) and fits `i64` is an `i64`. Every other number is an
   `f64` via `f64_from_str`. An integer that overflows `i64` is a parse
   error, not a silent `f64`. Writers render `i64` in decimal and `f64` with
   `str_from_f64`. NaN and infinities are write errors.
6. **The standard library is explicit, not ambient.** D057 stands: no prelude
   and no implicit search path. M57.2 defines how a workspace declares the
   compiler-shipped library (a dependency kind that resolves to the release's
   own library tree, recorded in the lock with the compiler identity and the
   tree hash). Single-file programs without a workspace do not see it.

## Sub-milestones

| Milestone | Scope | Notes |
| --- | --- | --- |
| **M57.1** Library-enabling core | `mutref` field places on owned locals and `mutref` parameters; field assignment through `mutref` parameters; `list_replace` and `list_pop`; `i64_from_i32` and `i32_from_i64`; comparison typing repair (payload-free enum `==`/`!=` supported, every comparison that would fail in C rejected at check, including `str <`); the two SPEC-violating defects from the tutorial (assignment to a plain `let`, non-exhaustive statement `match`); located NQ-TYPE-052 recursive-layout diagnostic. | Compiler and runtime work. May need selfhost source repairs if the compiler itself relies on the defects. |
| **M57.2** In-repo standard library | Layout `stdlib/nq/` as workspace `nauqtype.std`; bundled dependency kind, lock and provenance treatment; copied-release shipping and relocation; ports of `text`, `num` and `utf8` from the dormant NQType-Libraries foundation (adding a UTF-8 encoder); library test runner wiring. | First consumer: a workspace fixture plus a teaching example. |
| **M57.3** Maps and sets | `NqStrMap<V>`, `NqI64Map<V>`, `NqStrSet`, `NqI64Set`: new, insert (returns the replaced value), get (copy values), take/remove (move values), contains, len, keys/values in insertion order. Facts/review v5 evidence. | Decide whether `review-diff`, `change-report` and `policy-check` widen to generic graphs here; today they reject any program that imports a generic library module (NQ-GENERIC-008). |
| **M57.4** JSON | `NqJsonDoc`/`NqJsonNode`; `json_parse` (RFC 8259, exact errors with byte offsets, depth limit), typed accessors, builder calls, `json_write` (compact, deterministic) and a pretty writer; the number rule above. | M60 adds fuzzing. |

Each sub-milestone closes with the usual focused checks, trailing audit and
one milestone gate. The tutorial site is updated after each push.

## Open Questions For Gate A Reviews

- M57.1: whether a `mutref` field place may coexist with a borrow of a
  different field of the same root in one call (proposed: no, conservative).
- M57.1: whether `list_replace` with an out-of-range index drops the new
  value and returns `None` (proposed) or is a fatal runtime error.
- M57.2: whether the lock records the stdlib tree hash (proposed) or only the
  compiler version.
- M57.3: the generic-graph policy for `review-diff`/`change-report`/
  `policy-check`.
