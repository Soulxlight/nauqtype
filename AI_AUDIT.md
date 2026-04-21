# Nauqtype AI Audit

This report compares plain Nauqtype, contract-enabled Nauqtype, and Python with type hints plus docstrings on a small general-programming benchmark set.

## Method

- Tokenizer: `o200k_base` via `tiktoken`
- Benchmarks: hello function, arithmetic helper, record field read, enum branching, explicit fallible result, visible mutation
- Quantitative metrics: raw token count, character count, line count, punctuation density
- Qualitative rubric: declaration regularity, mutation visibility, fallibility visibility, control-flow explicitness, API review surface

## Token Results

| Benchmark | Nauqtype plain | Nauqtype + audit | Python hints+docs | Audit delta |
| --- | ---: | ---: | ---: | ---: |
| hello_function | 16 | 36 | 18 | 2.250x |
| arithmetic_helper | 23 | 43 | 26 | 1.870x |
| record_field_read | 33 | 55 | 48 | 1.667x |
| enum_branching | 49 | 71 | 68 | 1.449x |
| explicit_result | 41 | 63 | 40 | 1.537x |
| visible_mutation | 24 | 45 | 42 | 1.875x |

- Total Nauqtype plain tokens: `186`
- Total Nauqtype + audit tokens: `313`
- Total Python hints+docs tokens: `242`
- Overall Nauqtype plain / Python ratio: `0.769`
- Overall Nauqtype + audit / Python ratio: `1.293`
- Overall audit overhead vs plain Nauqtype: `1.683x` (`+127` tokens)
- Average Nauqtype plain punctuation density: `0.2546`
- Average Nauqtype + audit punctuation density: `0.2329`
- Average Python hints+docs punctuation density: `0.1972`

## Structural Rubric

| Criterion | Nauqtype + audit | Python hints+docs |
| --- | --- | --- |
| declaration regularity | 5/5 - Core declarations stay regular even with contracts: `fn`, optional `audit`, `type`, `enum`, `let`. | 3/5 - Definitions are readable, but behavior summaries live in free-form docstrings and ordinary assignment remains structural. |
| mutation visibility | 5/5 - Mutation is surfaced by `let mut`, `mutref`, assignment, and explicit `mutates(...)` declarations. | 3/5 - Type hints and docstrings can describe mutation, but alias-sensitive writes are still convention-driven. |
| fallibility visibility | 5/5 - Fallibility remains type-level through `result<T, E>` and review metadata can stay aligned with the compiler. | 3/5 - Type hints and docstrings help explain failure, but exceptions usually remain outside the checked signature. |
| control flow explicitness | 5/5 - Braces, explicit `return`, block-armed `match`, and fixed-shape audit blocks keep code structurally regular. | 3/5 - Type hints do not change Python's more ambient exception and mutation model, even when the source is well documented. |
| api review surface | 5/5 - `audit` blocks and `review` output make intent, mutation, and `print` effects deterministic and machine-readable. | 3/5 - Docstrings communicate intent, but they are not compiler-checked and can drift from actual behavior. |

- Average Nauqtype + audit rubric score: `5.00`
- Average Python hints+docs rubric score: `3.00`

## Conclusion

AI Contracts materially improve reviewability, but the current token overhead is noticeable. The feature still looks directionally right, though future tightening should focus on preserving the review value without letting contract syntax sprawl.

## Raw Results

- Machine-readable data: `audit\results\ai_audit.json`
