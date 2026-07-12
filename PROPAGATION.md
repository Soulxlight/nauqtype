# Nauqtype Propagation Design

This note packages the accepted design direction for `?` support. The goal is not to clone Rust. Nauqtype should make fallible code less wordy while increasing compiler-visible evidence for human supervisors and agent pairs.

Current implementation status: statement-boundary `let name = result_expr?;`, optional `?[context_label]` provenance labels, exact error typing, C emission, `propagates(E)` audit validation, versioned facts/review/change-report evidence, and explicit local `try` boundaries with expression-position propagation are implemented.

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
    let text = read_file(path)?[config_read];
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

## Function-Boundary Rules

- Allow `?` only in `let name = result_expr?;`.
- Require `result_expr` to have type `result<T, E>`.
- Require the enclosing function to return `result<U, E>` with the exact same `E`.
- Bind the `Ok` payload to the left-hand local.
- Return `Err(err)` unchanged on failure.
- Require or infer `propagates(E)` through the audit contract.
- Permit an optional bare identifier label as `?[context_label]`.
- Treat the label as checked evidence only; it does not affect error typing, audit inference, lowering, or runtime control flow.
- Reject implicit error conversion.
- Reject traits, custom propagation protocols, and overloads.
- Reject expression-position `?`, including call arguments, binary expressions, conditions, and `return Ok(expr?);`.
- Reject `option<T>?` in the first version.

## Local Try-Boundary Rules

M50 adds a separate local capture form:

```nauq
let measured: result<i32, io_err> = try {
    str_len(read_file(path)?[config_read])
};
```

- The boundary must be the direct initializer of an explicitly annotated `result<T, E>` local.
- Each `?` operand must be a direct function call returning `result<U, E>` with the exact boundary error type.
- Failure assigns `Err(error)` to the local and exits only the visible boundary; it never returns from the function.
- Success sites are unwrapped depth-first and left-to-right, then the final value expression is wrapped in `Ok(...)`.
- Local sites remain visible in facts v2 and review v2 but do not contribute to inferred function `propagates(...)`.
- Short-circuit logic, match success expressions, multi-statement bodies, function-scoped expression propagation, and implicit conversion remain rejected.

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

Do not silently change default or unversioned JSON behavior. Propagation evidence lives on explicit machine-readable surfaces: facts v2 exports checked propagation-site references, review v2 exports propagation contracts/sites, and change-report v1 reports added/removed propagation contracts. Labeled sites include an optional `context` string in facts/review v2, and label-only changes are visible as changed functions in review-diff/change-report. Future incompatible shape changes still require a new version.

A checked propagation site should carry at least:

- stable propagation id, for example `prop:config::load@123`
- containing function identity
- source expression or call-site identity when available
- operator span
- result carrier
- success payload type
- propagated error type
- enclosing return type
- optional context label
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
  "context": "config_read",
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

Deterministic local-boundary diagnostics:

- `NQ-TRY-001`: missing explicit `result<T, E>` boundary type
- `NQ-TRY-002`: missing value expression or a `?` operand that is not a direct call in V1
- `NQ-TRY-003`: success expression does not match the boundary payload type
- `NQ-TRY-004`: propagation would cross short-circuit `and` / `or`
- `NQ-TRY-005`: a match expression requires control-flow lowering not supported by V1
- `NQ-TRY-006`: `try` appears outside a direct annotated-local initializer

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

- Policy rules requiring labels for public APIs or `effects(io)` functions.
- `option<T>?` inside functions returning `option<U>`.
- Function-scoped expression `?` without a visible local boundary.
- Multi-statement `try { ... }` blocks and general block expressions.
- Short-circuit or match-expression propagation inside a local boundary.
- Explicit error mapping syntax.

## Rejected For This Path

- Rust-style implicit `From` conversion.
- Panic/unwrap operators.
- Fallback operators that hide error handling.
- User-defined propagation protocols.
- Treating `?` as invisible pure desugaring with no facts/review evidence.
