# M54.7 Specification Regressions

Every runnable case must exit `0` with empty stdout/stderr. Nonzero returns
identify assertions, not expected sample-program results. The values below
come from the grammar and first-match rule, not compiler-generated goldens.

| Source | Required behavior |
| --- | --- |
| `operators.nq` | Left-associative subtraction/division and mixed peers for i32/i64 and consts; equality below relational comparison; unary/parenthesized controls; short-circuit and left-to-right effects; list/constructor/field nesting. |
| `ordered_match.nq` | First matching enum/option/result arm wins in statement and expression positions, including fallback-first, duplicate variants, and fallback-middle/last. Copy-string and move-only list payloads, single scrutinee evaluation, return, continue, break, and normal arm cleanup are exercised repeatedly. |
| `c_names.nq` | C-keyword product fields and enum variants remain legal Nauqtype names through construction, borrowing, record update, assignment, nested patterns, and generic copy/drop. Escape-like `_u` and `_` fields remain distinct. |
| `names_workspace/src/app/main.nq` | `a::b::f` and `a::b__f`, their constants, and `a::b::Box` and `a::b__Box` stay distinct across C symbols and option/result/list carriers. Module aliases are explicit; qualified type annotations are not required. |

`selfhost/proof.nq` runs these through both the owned test suite and locked
corpus. `scripts/check_m53_ownership.sh` also runs the match and naming cases
under address/leak sanitizers. The existing negative width and move fixtures
continue to lock rejection behavior. No Python test implementation is added.
