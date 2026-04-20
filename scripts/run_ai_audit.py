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
    ("hello_function", "hello_function.nq", "hello_function.py"),
    ("arithmetic_helper", "arithmetic_helper.nq", "arithmetic_helper.py"),
    ("record_field_read", "record_field_read.nq", "record_field_read.py"),
    ("enum_branching", "enum_branching.nq", "enum_branching.py"),
    ("explicit_result", "explicit_result.nq", "explicit_result.py"),
    ("visible_mutation", "visible_mutation.nq", "visible_mutation.py"),
]

QUALITATIVE_RUBRIC = {
    "declaration_regularity": {
        "prompt": "How few declaration templates must an AI remember for common definitions?",
        "nauqtype": {"score": 5, "summary": "Core declarations are regular and keyword-led: `fn`, `type`, `enum`, `let`."},
        "python": {"score": 3, "summary": "Definitions are readable, but common program state also relies on plain assignment and decorator-driven structure."},
    },
    "mutation_visibility": {
        "prompt": "How obvious is mutation to a human reviewer glancing at the code?",
        "nauqtype": {"score": 5, "summary": "Mutation is surfaced with `let mut`, assignment, and `mutref`."},
        "python": {"score": 2, "summary": "Assignment is visible, but mutability is ambient and alias-sensitive operations have no dedicated marker."},
    },
    "fallibility_visibility": {
        "prompt": "How obvious are fallible paths from function signatures and call sites?",
        "nauqtype": {"score": 5, "summary": "Fallibility is type-level through `result<T, E>` and handled explicitly with `match`."},
        "python": {"score": 2, "summary": "Exception-based fallibility is common, but signatures usually do not advertise it."},
    },
    "control_flow_explicitness": {
        "prompt": "How directly does the source expose control-flow boundaries and branch shapes?",
        "nauqtype": {"score": 5, "summary": "Braces, explicit `return`, and block-armed `match` keep branch shapes very regular."},
        "python": {"score": 3, "summary": "Indentation and `match` are readable, but truthiness and implicit exception flow reduce explicitness."},
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


def conclusion(total_ratio: float, nauqtype_rubric: float, python_rubric: float) -> str:
    if total_ratio <= 1.15 and nauqtype_rubric > python_rubric:
        return "Nauqtype is close to Python on raw token count while being structurally more explicit. The current syntax is working well for its AI-first goals."
    if total_ratio <= 1.35 and nauqtype_rubric > python_rubric:
        return "Nauqtype pays a moderate token premium versus Python, but the explicit structure appears justified by stronger regularity, mutation visibility, and fallibility visibility."
    return "Nauqtype is not yet token-competitive with Python on raw source size. Its current value proposition is structural regularity and auditability rather than absolute brevity."


def main() -> int:
    root = project_root()
    audit_root = root / "audit"
    nq_root = audit_root / "benchmarks" / "nauqtype"
    py_root = audit_root / "benchmarks" / "python"
    result_dir = audit_root / "results"
    result_dir.mkdir(parents=True, exist_ok=True)

    encoding = tiktoken.get_encoding("o200k_base")

    rows: list[dict[str, object]] = []
    for name, nq_file, py_file in BENCHMARKS:
        nauqtype_text = load_text(nq_root / nq_file)
        python_text = load_text(py_root / py_file)
        nauq_tokens = token_count(encoding, nauqtype_text)
        python_tokens = token_count(encoding, python_text)
        rows.append(
            {
                "name": name,
                "nauqtype": {
                    "path": f"audit/benchmarks/nauqtype/{nq_file}",
                    "tokens": nauq_tokens,
                    "chars": len(nauqtype_text),
                    "lines": len(nauqtype_text.rstrip().splitlines()),
                    "punctuation_density": round(punctuation_density(nauqtype_text), 4),
                },
                "python": {
                    "path": f"audit/benchmarks/python/{py_file}",
                    "tokens": python_tokens,
                    "chars": len(python_text),
                    "lines": len(python_text.rstrip().splitlines()),
                    "punctuation_density": round(punctuation_density(python_text), 4),
                },
                "token_ratio_nauqtype_to_python": round(nauq_tokens / python_tokens, 3),
            }
        )

    total_nauqtype_tokens = sum(row["nauqtype"]["tokens"] for row in rows)
    total_python_tokens = sum(row["python"]["tokens"] for row in rows)
    average_ratio = round(total_nauqtype_tokens / total_python_tokens, 3)
    nauqtype_rubric = language_rubric_average("nauqtype")
    python_rubric = language_rubric_average("python")

    payload = {
        "tokenizer": "o200k_base",
        "benchmark_count": len(rows),
        "benchmarks": rows,
        "totals": {
            "nauqtype_tokens": total_nauqtype_tokens,
            "python_tokens": total_python_tokens,
            "token_ratio_nauqtype_to_python": average_ratio,
            "average_nauqtype_punctuation_density": round(
                sum(row["nauqtype"]["punctuation_density"] for row in rows) / len(rows), 4
            ),
            "average_python_punctuation_density": round(
                sum(row["python"]["punctuation_density"] for row in rows) / len(rows), 4
            ),
        },
        "qualitative_rubric": QUALITATIVE_RUBRIC,
        "rubric_averages": {
            "nauqtype": nauqtype_rubric,
            "python": python_rubric,
        },
        "conclusion": conclusion(average_ratio, nauqtype_rubric, python_rubric),
    }

    json_path = result_dir / "ai_audit.json"
    json_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    report_lines = [
        "# Nauqtype AI Audit",
        "",
        "This report compares Nauqtype against plain idiomatic Python 3 on a small general-programming benchmark set.",
        "",
        "## Method",
        "",
        "- Tokenizer: `o200k_base` via `tiktoken`",
        "- Benchmarks: hello function, arithmetic helper, record field read, enum branching, explicit fallible result, visible mutation",
        "- Quantitative metrics: raw token count, character count, line count, punctuation density",
        "- Qualitative rubric: declaration regularity, mutation visibility, fallibility visibility, control-flow explicitness",
        "",
        "## Token Results",
        "",
        "| Benchmark | Nauqtype tokens | Python tokens | Ratio |",
        "| --- | ---: | ---: | ---: |",
    ]

    for row in rows:
        report_lines.append(
            f"| {row['name']} | {row['nauqtype']['tokens']} | {row['python']['tokens']} | {row['token_ratio_nauqtype_to_python']:.3f} |"
        )

    report_lines.extend(
        [
            "",
            f"- Total Nauqtype tokens: `{total_nauqtype_tokens}`",
            f"- Total Python tokens: `{total_python_tokens}`",
            f"- Overall Nauqtype/Python token ratio: `{average_ratio:.3f}`",
            f"- Average Nauqtype punctuation density: `{payload['totals']['average_nauqtype_punctuation_density']:.4f}`",
            f"- Average Python punctuation density: `{payload['totals']['average_python_punctuation_density']:.4f}`",
            "",
            "## Structural Rubric",
            "",
            "| Criterion | Nauqtype | Python |",
            "| --- | --- | --- |",
        ]
    )

    for criterion, entry in QUALITATIVE_RUBRIC.items():
        report_lines.append(
            f"| {criterion.replace('_', ' ')} | {entry['nauqtype']['score']}/5 - {entry['nauqtype']['summary']} | {entry['python']['score']}/5 - {entry['python']['summary']} |"
        )

    report_lines.extend(
        [
            "",
            f"- Average Nauqtype rubric score: `{nauqtype_rubric:.2f}`",
            f"- Average Python rubric score: `{python_rubric:.2f}`",
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
