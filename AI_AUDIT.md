# Nauqtype AI Audit

This report compares Nauqtype against plain idiomatic Python 3 on a small general-programming benchmark set.

## Method

- Tokenizer: `o200k_base` via `tiktoken`
- Benchmarks: hello function, arithmetic helper, record field read, enum branching, explicit fallible result, visible mutation
- Quantitative metrics: raw token count, character count, line count, punctuation density
- Qualitative rubric: declaration regularity, mutation visibility, fallibility visibility, control-flow explicitness

## Token Results

| Benchmark | Nauqtype tokens | Python tokens | Ratio |
| --- | ---: | ---: | ---: |
| hello_function | 16 | 8 | 2.000 |
| arithmetic_helper | 23 | 12 | 1.917 |
| record_field_read | 33 | 33 | 1.000 |
| enum_branching | 49 | 53 | 0.925 |
| explicit_result | 41 | 24 | 1.708 |
| visible_mutation | 24 | 29 | 0.828 |

- Total Nauqtype tokens: `186`
- Total Python tokens: `159`
- Overall Nauqtype/Python token ratio: `1.170`
- Average Nauqtype punctuation density: `0.2546`
- Average Python punctuation density: `0.1683`

## Structural Rubric

| Criterion | Nauqtype | Python |
| --- | --- | --- |
| declaration regularity | 5/5 - Core declarations are regular and keyword-led: `fn`, `type`, `enum`, `let`. | 3/5 - Definitions are readable, but common program state also relies on plain assignment and decorator-driven structure. |
| mutation visibility | 5/5 - Mutation is surfaced with `let mut`, assignment, and `mutref`. | 2/5 - Assignment is visible, but mutability is ambient and alias-sensitive operations have no dedicated marker. |
| fallibility visibility | 5/5 - Fallibility is type-level through `result<T, E>` and handled explicitly with `match`. | 2/5 - Exception-based fallibility is common, but signatures usually do not advertise it. |
| control flow explicitness | 5/5 - Braces, explicit `return`, and block-armed `match` keep branch shapes very regular. | 3/5 - Indentation and `match` are readable, but truthiness and implicit exception flow reduce explicitness. |

- Average Nauqtype rubric score: `5.00`
- Average Python rubric score: `2.50`

## Conclusion

Nauqtype pays a moderate token premium versus Python, but the explicit structure appears justified by stronger regularity, mutation visibility, and fallibility visibility.

## Raw Results

- Machine-readable data: `audit\results\ai_audit.json`
