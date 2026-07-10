from __future__ import annotations

import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


class PatternTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[1]

    def run_source(self, source: str) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "main.nq"
            path.write_text(textwrap.dedent(source).strip() + "\n", encoding="utf-8")
            return subprocess.run(
                [sys.executable, "-m", "compiler.main", "run", str(path)],
                cwd=self.root,
                capture_output=True,
                text=True,
            )

    def test_integer_literal_patterns_run_with_fallback(self) -> None:
        result = self.run_source(
            """
            fn main() -> i32 {
                let value = -1;
                match value {
                    -1 => {
                        return 42;
                    },
                    _ => {
                        return 0;
                    },
                }
            }
            """
        )
        self.assertEqual(result.returncode, 42, result.stdout + result.stderr)

    def test_nested_constructor_and_literal_patterns_run(self) -> None:
        result = self.run_source(
            """
            fn main() -> i32 {
                let value: option<option<i32>> = Some(Some(42));
                match value {
                    Some(Some(42)) => {
                        return 42;
                    },
                    _ => {
                        return 0;
                    },
                }
            }
            """
        )
        self.assertEqual(result.returncode, 42, result.stdout + result.stderr)

    def test_nested_constructor_pattern_binds_payload(self) -> None:
        result = self.run_source(
            """
            fn main() -> i32 {
                let value: option<option<i32>> = Some(Some(42));
                match value {
                    Some(Some(number)) => {
                        return number;
                    },
                    _ => {
                        return 0;
                    },
                }
            }
            """
        )
        self.assertEqual(result.returncode, 42, result.stdout + result.stderr)

    def test_literal_patterns_require_i32_scrutinee(self) -> None:
        result = self.run_source(
            """
            fn main() -> i32 {
                match true {
                    1 => {
                        return 1;
                    },
                    _ => {
                        return 0;
                    },
                }
            }
            """
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("NQ-TYPE-040", result.stdout + result.stderr)

    def test_refined_patterns_require_fallback(self) -> None:
        result = self.run_source(
            """
            fn main() -> i32 {
                let value: option<option<i32>> = Some(Some(1));
                match value {
                    Some(Some(number)) => {
                        return number;
                    },
                    None => {
                        return 0;
                    },
                }
            }
            """
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("NQ-TYPE-041", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
