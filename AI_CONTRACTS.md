# Nauqtype AI Contracts

## Purpose

AI Contracts are Nauqtype's first explicitly AI-first language feature.

They are designed to make AI-authored code easier to supervise by attaching a small, fixed-shape, compiler-checked review surface to functions.

## Alpha Surface

Current syntax:

```nauq
pub fn bump(value: mutref i32) -> unit
audit {
    intent("Increment a counter in place");
    mutates(value);
    effects();
}
{
    value = value + 1;
    return;
}
```

## Alpha Rules

- Clause order is fixed: `intent`, then `mutates`, then `effects`.
- `intent("...")` is required and must be non-empty.
- `mutates(...)` may list only `mutref` parameters.
- `effects(...)` currently supports only `print`.
- Public functions without `audit` are allowed in this phase, but they emit a warning.

## Compiler Inference

- Mutation inference is direct only in this phase.
- The compiler marks a `mutref` parameter as mutated when the function writes through that parameter.
- `print` is inferred directly from `print_line(...)` calls and transitively across the single-file call graph.
- Missing inferred facts are errors.
- Overdeclared facts are warnings.

## Review Output

`nauqc review <file>` emits deterministic JSON containing:

- module name
- function name
- visibility
- declared audit data
- compiler-inferred mutation/effect facts

This output is intended to be consumed by both humans and future AI tooling.

During the current Nauqtype-only toolchain transition, `review` is now owned by the active stage1 executable driver alongside `check`, `emit-c`, `build`, and `run`. The frozen stage0 path remains in-repo only as bootstrap/reference code while the Nauqtype-owned proof/corpus runner is still being cut over.

## Explicit Non-Goals For Alpha

- NLP validation of `intent(...)`
- Rich effect taxonomies
- Cross-file contract propagation
- Typed holes or repair obligations
- Strong transitive mutation inference

Those remain future work until the alpha proves its value.
