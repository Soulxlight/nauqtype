from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.test_support import ROOT


class ReviewTests(unittest.TestCase):
    def test_review_output_matches_golden(self) -> None:
        example = ROOT / "examples" / "review_contracts.nq"
        golden = ROOT / "tests" / "golden" / "review" / "review_contracts.json"
        result = subprocess.run(
            [sys.executable, "-m", "compiler.main", "review", str(example)],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")
        self.assertEqual(result.stdout.rstrip("\n"), golden.read_text(encoding="utf-8").rstrip("\n"))

    def test_review_emits_json_on_warning(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source_path = Path(temp_dir) / "warning_review.nq"
            source_path.write_text(
                """
pub fn greet() -> unit {
    return;
}
""".strip()
                + "\n",
                encoding="utf-8",
            )
            result = subprocess.run(
                [sys.executable, "-m", "compiler.main", "review", str(source_path)],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('"module": "warning_review"', result.stdout)
        self.assertIn('"audit": null', result.stdout)
        self.assertIn("warning[NQ-CONTRACT-001]", result.stderr)


if __name__ == "__main__":
    unittest.main()
