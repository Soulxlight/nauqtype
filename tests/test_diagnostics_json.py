from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

from tests.test_support import ROOT


def _normalize_payload(payload: dict[str, object], source_path: Path) -> dict[str, object]:
    normalized = json.loads(json.dumps(payload))
    source_text = str(source_path)
    for diagnostic in normalized["diagnostics"]:
        span = diagnostic["span"]
        if span is not None:
            span["path"] = "<SOURCE>"
        diagnostic["rendered"] = diagnostic["rendered"].replace(source_text, "<SOURCE>")
    return normalized


class DiagnosticsJsonTests(unittest.TestCase):
    def setUp(self) -> None:
        self.warning_source = ROOT / "tests" / "fixtures" / "diagnostics_warning.nq"
        self.failure_source = ROOT / "tests" / "fixtures" / "diagnostics_failure.nq"
        self.warning_golden = ROOT / "tests" / "golden" / "diagnostics" / "check_warning.json"
        self.failure_golden = ROOT / "tests" / "golden" / "diagnostics" / "check_failure.json"
        self.schema_path = ROOT / "schemas" / "diagnostics-v1.schema.json"

    def _run_check(self, source: Path, *, mode: str) -> subprocess.CompletedProcess[str]:
        command = [sys.executable, "-m", "compiler.main", "check", str(source)]
        if mode == "json":
            command.extend(["--diagnostics", "json"])
        return subprocess.run(
            command,
            cwd=ROOT,
            capture_output=True,
            text=True,
        )

    def test_warning_json_matches_golden(self) -> None:
        result = self._run_check(self.warning_source, mode="json")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")
        payload = json.loads(result.stdout)
        normalized = _normalize_payload(payload, self.warning_source)
        expected = json.loads(self.warning_golden.read_text(encoding="utf-8"))
        self.assertEqual(normalized, expected)

    def test_failure_json_matches_golden(self) -> None:
        result = self._run_check(self.failure_source, mode="json")
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(result.stderr, "")
        payload = json.loads(result.stdout)
        normalized = _normalize_payload(payload, self.failure_source)
        expected = json.loads(self.failure_golden.read_text(encoding="utf-8"))
        self.assertEqual(normalized, expected)

    def test_json_exit_code_matches_text_mode(self) -> None:
        text_result = self._run_check(self.failure_source, mode="text")
        json_result = self._run_check(self.failure_source, mode="json")
        self.assertEqual(text_result.returncode, json_result.returncode)

    def test_schema_shape_is_versioned(self) -> None:
        schema = json.loads(self.schema_path.read_text(encoding="utf-8"))
        self.assertEqual(schema["$id"], "https://nauqtype.dev/schemas/diagnostics-v1.schema.json")
        self.assertEqual(schema["properties"]["version"]["const"], "diagnostics/v1")
        self.assertEqual(schema["properties"]["command"]["const"], "check")
        self.assertEqual(
            schema["properties"]["diagnostics"]["items"]["required"],
            ["code", "category", "severity", "message", "span", "notes", "help", "rendered"],
        )


if __name__ == "__main__":
    unittest.main()
