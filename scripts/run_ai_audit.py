from __future__ import annotations

import json
import string
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts._deps import bootstrap_sys_path, project_root

bootstrap_sys_path()

try:
    import tiktoken
except ModuleNotFoundError:
    print("tiktoken is not installed; run `python scripts/setup_deps.py` first", file=sys.stderr)
    raise SystemExit(1)


BENCHMARKS = [
    ("hello_function", "hello_function.nq", "hello_function.nq", "hello_function.py"),
    ("arithmetic_helper", "arithmetic_helper.nq", "arithmetic_helper.nq", "arithmetic_helper.py"),
    ("record_field_read", "record_field_read.nq", "record_field_read.nq", "record_field_read.py"),
    ("enum_branching", "enum_branching.nq", "enum_branching.nq", "enum_branching.py"),
    ("explicit_result", "explicit_result.nq", "explicit_result.nq", "explicit_result.py"),
    ("visible_mutation", "visible_mutation.nq", "visible_mutation.nq", "visible_mutation.py"),
]

QUALITATIVE_RUBRIC = {
    "declaration_regularity": {
        "prompt": "How few declaration templates must an AI remember for common definitions?",
        "nauqtype_contracts": {
            "score": 5,
            "summary": "Core declarations stay regular even with contracts: `fn`, optional `audit`, `type`, `enum`, `let`.",
        },
        "python_typed_docstring": {
            "score": 3,
            "summary": "Definitions are readable, but behavior summaries live in free-form docstrings and ordinary assignment remains structural.",
        },
    },
    "mutation_visibility": {
        "prompt": "How obvious is mutation to a human reviewer glancing at the code?",
        "nauqtype_contracts": {
            "score": 5,
            "summary": "Mutation is surfaced by `let mut`, `mutref`, assignment, and explicit `mutates(...)` declarations.",
        },
        "python_typed_docstring": {
            "score": 3,
            "summary": "Type hints and docstrings can describe mutation, but alias-sensitive writes are still convention-driven.",
        },
    },
    "fallibility_visibility": {
        "prompt": "How obvious are fallible paths from function signatures and review surfaces?",
        "nauqtype_contracts": {
            "score": 5,
            "summary": "Fallibility remains type-level through `result<T, E>` and review metadata can stay aligned with the compiler.",
        },
        "python_typed_docstring": {
            "score": 3,
            "summary": "Type hints and docstrings help explain failure, but exceptions usually remain outside the checked signature.",
        },
    },
    "control_flow_explicitness": {
        "prompt": "How directly does the source expose control-flow boundaries and branch shapes?",
        "nauqtype_contracts": {
            "score": 5,
            "summary": "Braces, explicit `return`, block-armed `match`, and fixed-shape audit blocks keep code structurally regular.",
        },
        "python_typed_docstring": {
            "score": 3,
            "summary": "Type hints do not change Python's more ambient exception and mutation model, even when the source is well documented.",
        },
    },
    "api_review_surface": {
        "prompt": "How directly can a tool or reviewer recover intent, mutation, and notable effects from the source?",
        "nauqtype_contracts": {
            "score": 5,
            "summary": "`audit` blocks and `review` output make intent, mutation, and `print` effects deterministic and machine-readable.",
        },
        "python_typed_docstring": {
            "score": 3,
            "summary": "Docstrings communicate intent, but they are not compiler-checked and can drift from actual behavior.",
        },
    },
}

PUNCTUATION = set(string.punctuation)


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip() + "\n"


def token_count(encoding, text: str) -> int:
    return len(encoding.encode(text))


def punctuation_density(text: str) -> float:
    significant = [char for char in text if not char.isspace()]
    if not significant:
        return 0.0
    punct = sum(1 for char in significant if char in PUNCTUATION)
    return punct / len(significant)


def language_rubric_average(language: str) -> float:
    scores = [entry[language]["score"] for entry in QUALITATIVE_RUBRIC.values()]
    return round(sum(scores) / len(scores), 2)


def conclusion(
    plain_ratio: float,
    contract_ratio: float,
    contract_overhead_ratio: float,
    contract_rubric: float,
    python_rubric: float,
) -> str:
    if contract_ratio <= 1.35 and contract_overhead_ratio <= 1.35 and contract_rubric > python_rubric:
        return (
            "AI Contracts add a moderate token premium over plain Nauqtype, but they buy a distinctly stronger "
            "compiler-checked review surface. The current results support keeping `audit` blocks as Nauqtype's "
            "signature AI-first differentiator for public APIs."
        )
    if contract_rubric > python_rubric:
        return (
            "AI Contracts materially improve reviewability, but the current token overhead is noticeable. The feature "
            "still looks directionally right, though future tightening should focus on preserving the review value "
            "without letting contract syntax sprawl."
        )
    return (
        "AI Contracts are not yet earning their token cost strongly enough. The differentiator needs either a tighter "
        "surface or richer review value before it should expand further."
    )


def main() -> int:
    root = project_root()
    audit_root = root / "audit"
    nq_plain_root = audit_root / "benchmarks" / "nauqtype"
    nq_contract_root = audit_root / "benchmarks" / "nauqtype_contracts"
    py_root = audit_root / "benchmarks" / "python"
    result_dir = audit_root / "results"
    result_dir.mkdir(parents=True, exist_ok=True)

    encoding = tiktoken.get_encoding("o200k_base")

    rows: list[dict[str, object]] = []
    for name, nq_plain_file, nq_contract_file, py_file in BENCHMARKS:
        plain_text = load_text(nq_plain_root / nq_plain_file)
        contract_text = load_text(nq_contract_root / nq_contract_file)
        python_text = load_text(py_root / py_file)

        plain_tokens = token_count(encoding, plain_text)
        contract_tokens = token_count(encoding, contract_text)
        python_tokens = token_count(encoding, python_text)

        rows.append(
            {
                "name": name,
                "nauqtype_plain": {
                    "path": f"audit/benchmarks/nauqtype/{nq_plain_file}",
                    "tokens": plain_tokens,
                    "chars": len(plain_text),
                    "lines": len(plain_text.rstrip().splitlines()),
                    "punctuation_density": round(punctuation_density(plain_text), 4),
                },
                "nauqtype_contracts": {
                    "path": f"audit/benchmarks/nauqtype_contracts/{nq_contract_file}",
                    "tokens": contract_tokens,
                    "chars": len(contract_text),
                    "lines": len(contract_text.rstrip().splitlines()),
                    "punctuation_density": round(punctuation_density(contract_text), 4),
                },
                "python_typed_docstring": {
                    "path": f"audit/benchmarks/python/{py_file}",
                    "tokens": python_tokens,
                    "chars": len(python_text),
                    "lines": len(python_text.rstrip().splitlines()),
                    "punctuation_density": round(punctuation_density(python_text), 4),
                },
                "ratios": {
                    "plain_to_python": round(plain_tokens / python_tokens, 3),
                    "contracts_to_python": round(contract_tokens / python_tokens, 3),
                    "contracts_over_plain": round(contract_tokens / plain_tokens, 3),
                },
            }
        )

    total_plain_tokens = sum(row["nauqtype_plain"]["tokens"] for row in rows)
    total_contract_tokens = sum(row["nauqtype_contracts"]["tokens"] for row in rows)
    total_python_tokens = sum(row["python_typed_docstring"]["tokens"] for row in rows)

    total_plain_ratio = round(total_plain_tokens / total_python_tokens, 3)
    total_contract_ratio = round(total_contract_tokens / total_python_tokens, 3)
    total_contract_overhead_ratio = round(total_contract_tokens / total_plain_tokens, 3)
    total_contract_overhead_tokens = total_contract_tokens - total_plain_tokens

    contract_rubric = language_rubric_average("nauqtype_contracts")
    python_rubric = language_rubric_average("python_typed_docstring")

    payload = {
        "tokenizer": "o200k_base",
        "benchmark_count": len(rows),
        "benchmarks": rows,
        "totals": {
            "nauqtype_plain_tokens": total_plain_tokens,
            "nauqtype_contracts_tokens": total_contract_tokens,
            "python_typed_docstring_tokens": total_python_tokens,
            "plain_to_python_ratio": total_plain_ratio,
            "contracts_to_python_ratio": total_contract_ratio,
            "contracts_over_plain_ratio": total_contract_overhead_ratio,
            "contracts_over_plain_tokens": total_contract_overhead_tokens,
            "average_nauqtype_plain_punctuation_density": round(
                sum(row["nauqtype_plain"]["punctuation_density"] for row in rows) / len(rows), 4
            ),
            "average_nauqtype_contracts_punctuation_density": round(
                sum(row["nauqtype_contracts"]["punctuation_density"] for row in rows) / len(rows), 4
            ),
            "average_python_typed_docstring_punctuation_density": round(
                sum(row["python_typed_docstring"]["punctuation_density"] for row in rows) / len(rows), 4
            ),
        },
        "qualitative_rubric": QUALITATIVE_RUBRIC,
        "rubric_averages": {
            "nauqtype_contracts": contract_rubric,
            "python_typed_docstring": python_rubric,
        },
        "conclusion": conclusion(
            total_plain_ratio,
            total_contract_ratio,
            total_contract_overhead_ratio,
            contract_rubric,
            python_rubric,
        ),
    }

    json_path = result_dir / "ai_audit.json"
    json_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    report_lines = [
        "# Nauqtype AI Audit",
        "",
        "This report compares plain Nauqtype, contract-enabled Nauqtype, and Python with type hints plus docstrings on a small general-programming benchmark set.",
        "",
        "## Method",
        "",
        "- Tokenizer: `o200k_base` via `tiktoken`",
        "- Benchmarks: hello function, arithmetic helper, record field read, enum branching, explicit fallible result, visible mutation",
        "- Quantitative metrics: raw token count, character count, line count, punctuation density",
        "- Qualitative rubric: declaration regularity, mutation visibility, fallibility visibility, control-flow explicitness, API review surface",
        "",
        "## Token Results",
        "",
        "| Benchmark | Nauqtype plain | Nauqtype + audit | Python hints+docs | Audit delta |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]

    for row in rows:
        report_lines.append(
            "| "
            f"{row['name']} | "
            f"{row['nauqtype_plain']['tokens']} | "
            f"{row['nauqtype_contracts']['tokens']} | "
            f"{row['python_typed_docstring']['tokens']} | "
            f"{row['ratios']['contracts_over_plain']:.3f}x |"
        )

    report_lines.extend(
        [
            "",
            f"- Total Nauqtype plain tokens: `{total_plain_tokens}`",
            f"- Total Nauqtype + audit tokens: `{total_contract_tokens}`",
            f"- Total Python hints+docs tokens: `{total_python_tokens}`",
            f"- Overall Nauqtype plain / Python ratio: `{total_plain_ratio:.3f}`",
            f"- Overall Nauqtype + audit / Python ratio: `{total_contract_ratio:.3f}`",
            f"- Overall audit overhead vs plain Nauqtype: `{total_contract_overhead_ratio:.3f}x` (`+{total_contract_overhead_tokens}` tokens)",
            f"- Average Nauqtype plain punctuation density: `{payload['totals']['average_nauqtype_plain_punctuation_density']:.4f}`",
            f"- Average Nauqtype + audit punctuation density: `{payload['totals']['average_nauqtype_contracts_punctuation_density']:.4f}`",
            f"- Average Python hints+docs punctuation density: `{payload['totals']['average_python_typed_docstring_punctuation_density']:.4f}`",
            "",
            "## Structural Rubric",
            "",
            "| Criterion | Nauqtype + audit | Python hints+docs |",
            "| --- | --- | --- |",
        ]
    )

    for criterion, entry in QUALITATIVE_RUBRIC.items():
        report_lines.append(
            f"| {criterion.replace('_', ' ')} | "
            f"{entry['nauqtype_contracts']['score']}/5 - {entry['nauqtype_contracts']['summary']} | "
            f"{entry['python_typed_docstring']['score']}/5 - {entry['python_typed_docstring']['summary']} |"
        )

    report_lines.extend(
        [
            "",
            f"- Average Nauqtype + audit rubric score: `{contract_rubric:.2f}`",
            f"- Average Python hints+docs rubric score: `{python_rubric:.2f}`",
            "",
            "## Conclusion",
            "",
            payload["conclusion"],
            "",
            "## Raw Results",
            "",
            f"- Machine-readable data: `{json_path.relative_to(root)}`",
        ]
    )

    report_path = root / "AI_AUDIT.md"
    report_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    print(f"Wrote {json_path.relative_to(root)}")
    print(f"Wrote {report_path.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
