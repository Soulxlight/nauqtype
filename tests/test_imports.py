from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class ImportTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[1]

    def run_cli(self, command: str, entry: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-m", "compiler.main", command, str(entry)],
            cwd=self.root,
            capture_output=True,
            text=True,
        )

    def test_multi_file_build_runs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            (tmp / "main.nq").write_text(
                "use helper;\n\nfn main() -> i32 {\n    return read_value();\n}\n",
                encoding="utf-8",
            )
            (tmp / "helper.nq").write_text(
                "pub fn read_value() -> i32\n"
                "audit {\n"
                "    intent(\"Return a fixed value\");\n"
                "    mutates();\n"
                "    effects();\n"
                "}\n"
                "{\n"
                "    return 7;\n"
                "}\n",
                encoding="utf-8",
            )
            result = self.run_cli("run", tmp / "main.nq")
            self.assertEqual(result.returncode, 7, result.stderr)

    def test_missing_module_reports_diagnostic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            (tmp / "main.nq").write_text("use helper;\n\nfn main() -> i32 { return 0; }\n", encoding="utf-8")
            result = self.run_cli("check", tmp / "main.nq")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("NQ-IMPORT-001", result.stderr)

    def test_import_cycle_reports_diagnostic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            (tmp / "main.nq").write_text("use helper;\n\nfn main() -> i32 { return 0; }\n", encoding="utf-8")
            (tmp / "helper.nq").write_text("use main;\n\npub fn read_value() -> i32 { return 1; }\n", encoding="utf-8")
            result = self.run_cli("check", tmp / "main.nq")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("NQ-IMPORT-003", result.stderr)

    def test_duplicate_imported_symbol_reports_diagnostic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            (tmp / "main.nq").write_text(
                "use left;\nuse right;\n\nfn main() -> i32 { return value(); }\n",
                encoding="utf-8",
            )
            body = (
                "pub fn value() -> i32\n"
                "audit {\n"
                "    intent(\"Return a value\");\n"
                "    mutates();\n"
                "    effects();\n"
                "}\n"
                "{\n"
                "    return 1;\n"
                "}\n"
            )
            (tmp / "left.nq").write_text(body, encoding="utf-8")
            (tmp / "right.nq").write_text(body.replace("return 1;", "return 2;"), encoding="utf-8")
            result = self.run_cli("check", tmp / "main.nq")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("NQ-IMPORT-004", result.stderr)

    def test_non_pub_import_access_reports_diagnostic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            (tmp / "main.nq").write_text("use helper;\n\nfn main() -> i32 { return secret(); }\n", encoding="utf-8")
            (tmp / "helper.nq").write_text("fn secret() -> i32 { return 1; }\n", encoding="utf-8")
            result = self.run_cli("check", tmp / "main.nq")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("NQ-IMPORT-005", result.stderr)

    def test_review_infers_transitive_print_across_imports(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            (tmp / "main.nq").write_text(
                "use helper;\n\n"
                "pub fn main() -> i32\n"
                "audit {\n"
                "    intent(\"Run helper\");\n"
                "    mutates();\n"
                "    effects(print);\n"
                "}\n"
                "{\n"
                "    helper();\n"
                "    return 0;\n"
                "}\n",
                encoding="utf-8",
            )
            (tmp / "helper.nq").write_text(
                "pub fn helper() -> unit\n"
                "audit {\n"
                "    intent(\"Print a line\");\n"
                "    mutates();\n"
                "    effects(print);\n"
                "}\n"
                "{\n"
                "    print_line(\"hi\");\n"
                "    return;\n"
                "}\n",
                encoding="utf-8",
            )
            result = self.run_cli("review", tmp / "main.nq")
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["functions"][0]["inferred"]["effects"], ["print"])


if __name__ == "__main__":
    unittest.main()
