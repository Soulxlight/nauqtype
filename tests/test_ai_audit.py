from __future__ import annotations

import json
import subprocess
import sys
import unittest

from tests.test_support import ROOT, ensure_bootstrap_deps


class AIAuditTests(unittest.TestCase):
    def test_audit_runner_emits_results(self) -> None:
        ensure_bootstrap_deps()
        result = subprocess.run(
            [sys.executable, "scripts/run_ai_audit.py"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

        report_path = ROOT / "AI_AUDIT.md"
        json_path = ROOT / "audit" / "results" / "ai_audit.json"
        self.assertTrue(report_path.exists(), "missing AI audit report")
        self.assertTrue(json_path.exists(), "missing machine-readable AI audit results")

        payload = json.loads(json_path.read_text(encoding="utf-8"))
        self.assertEqual(payload["tokenizer"], "o200k_base")
        self.assertEqual(payload["benchmark_count"], 6)
        benchmark_names = {entry["name"] for entry in payload["benchmarks"]}
        self.assertEqual(
            benchmark_names,
            {
                "hello_function",
                "arithmetic_helper",
                "record_field_read",
                "enum_branching",
                "explicit_result",
                "visible_mutation",
            },
        )
        self.assertIn("Nauqtype", report_path.read_text(encoding="utf-8"))
        self.assertIn("Python", report_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()

