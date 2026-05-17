# Nauqtype Propagation Design

This note packages the accepted design direction for `?` support. The goal is not to clone Rust. Nauqtype should make fallible code less wordy while increasing compiler-visible evidence for human supervisors and agent pairs.

Current implementation status: statement-boundary `let name = result_expr?;`, exact error typing, C emission, `propagates(E)` audit validation, and the versioned facts/review/change-report evidence surface are implemented.

## Core Decision

`?` is a checked propagation operator. It is not just syntax that disappears into an early `return`.

Every accepted `?` site must become:

- a typed control-flow edge in the compiler
- a checked propagation fact in machine-readable output
- an inferred audit-contract fact compared against `propagates(...)`
- a diffable semantic change in review/report tooling

The source gets shorter, but the review surface gets richer.

## First Implementation Shape

M25 implements statement-boundary `result` propagation only:

```nauq
fn read_len(path: str) -> result<i32, io_err>
audit {
    intent("Read a file and return its length");
    mutates();
    effects(io);
    propagates(io_err);
}
{
    let text = read_file(path)?;
    return Ok(str_len(text));
}
```

This is equivalent to:

```nauq
match read_file(path) {
    Ok(text) => {
    },
    Err(err) => {
        return Err(err);
    },
}
```

but it must remain visible as a propagation site in facts/review/change-report outputs.

## V1 Rules

- Allow `?` only in `let name = result_expr?;`.
- Require `result_expr` to have type `result<T, E>`.
- Require the enclosing function to return `result<U, E>` with the exact same `E`.
- Bind the `Ok` payload to the left-hand local.
- Return `Err(err)` unchanged on failure.
- Require or infer `propagates(E)` through the audit contract.
- Reject implicit error conversion.
- Reject traits, custom propagation protocols, and overloads.
- Reject expression-position `?`, including call arguments, binary expressions, conditions, and `return Ok(expr?);`.
- Reject `option<T>?` in the first version.

The teaching rule is simple: use `?` when this function forwards the same error unchanged; use `match` or `let-else` when the function handles, maps, logs, or explains the error locally.

## Audit Contract

The audit block supports a fourth fixed clause after `effects(...)`:

```nauq
audit {
    intent("...");
    mutates(...);
    effects(...);
    propagates(...);
}
```

Compiler behavior mirrors the existing contract pattern:

- inferred propagation missing from `propagates(...)` is an error
- overdeclared propagation is a warning
- duplicate entries are rejected
- public functions expose propagation in review output

`propagates(...)` lists exact error types that can leave the function unchanged through `?`. It does not list converted source errors unless the function return type is exactly that error type.

## Evidence Surface

Do not silently change default or unversioned JSON behavior. Propagation evidence lives on explicit machine-readable surfaces: facts v2 exports checked propagation-site references, review v2 exports propagation contracts/sites, and change-report v1 reports added/removed propagation contracts. Future incompatible shape changes still require a new version.

A checked propagation site should carry at least:

- stable propagation id, for example `prop:config::load@123`
- containing function identity
- source expression or call-site identity when available
- operator span
- result carrier
- success payload type
- propagated error type
- enclosing return type
- optional context label when that extension is accepted
- checked evidence marker

Example shape:

```json
{
  "id": "prop:config::load@123",
  "kind": "propagation",
  "function": "fn:config::load",
  "source_expr": "call:config::load@112",
  "operator_span": { "start": 123 },
  "carrier": "result",
  "ok_type": "str",
  "err_type": "io_err",
  "return_type": "result<i32, io_err>",
  "context": "",
  "evidence": "checked"
}
```

Review and change-report summarize propagation contract changes so a human supervisor can see changed failure behavior without reading every branch.

## Diagnostics

Deterministic propagation diagnostics:

- `NQ-PROPAGATE-001`: `?` on a non-`result` expression
- `NQ-PROPAGATE-002`: `?` inside a function that does not return `result`
- `NQ-PROPAGATE-003`: propagated error type does not exactly match the enclosing return error type
- `NQ-PROPAGATE-004`: inferred propagation missing from `propagates(...)`
- `NQ-PROPAGATE-005`: overdeclared propagation in `propagates(...)`

Diagnostics should point users toward explicit `match` or `let-else` when propagation is not the right tool.

`NQ-PROPAGATE-003` is especially important for teaching. When a function returns `result<_, BuildError>` but the propagated expression has type `result<_, LexError>`, the diagnostic should say there is no implicit conversion and point users toward explicit handling, for example:

```nauq
let value = read_lexed(path) else {
    Err(err) => {
        return Err(map_lex_error(err));
    },
};
```

That lack of an escape hatch is intentional. Nauqtype should make unchanged propagation concise, while keeping transformed errors explicit and reviewable.

## Implementation Notes

- Existing selfhost audit blocks did not need a `propagates(...)` backfill when M25 landed because current selfhost sources do not use `?`.
- The current stress-leg and stage1-driver checks include negative coverage for `?` without a matching `propagates(...)` clause and expect `NQ-PROPAGATE-004`.
- Propagation evidence should reuse the current evidence vocabulary where possible: `declared`, `checked`, `builtin`, and `unresolved`.
- The implementation should avoid creating a second evidence taxonomy just for propagation sites.

## Deferred Extensions

- Optional propagation labels such as `read_file(path)?[read_config]`.
- Policy rules requiring labels for public APIs or `effects(io)` functions.
- `option<T>?` inside functions returning `option<U>`.
- Expression-position `?`.
- `try { ... }` blocks to bound propagation scope before expression-position `?` grows.
- Explicit error mapping syntax.

## Rejected For This Path

- Rust-style implicit `From` conversion.
- Panic/unwrap operators.
- Fallback operators that hide error handling.
- User-defined propagation protocols.
- Treating `?` as invisible pure desugaring with no facts/review evidence.
