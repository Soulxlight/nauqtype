from __future__ import annotations

import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


class FieldAssignmentTests(unittest.TestCase):
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

    def test_owned_mutable_local_field_assignment_runs(self) -> None:
        result = self.run_source(
            """
            type Pair {
                left: i32,
                right: i32,
            }

            fn main() -> i32 {
                let mut pair = Pair { left: 2, right: 5 };
                pair.left = 13;
                if pair.left == 13 and pair.right == 5 {
                    return 0;
                }
                return 1;
            }
            """
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_field_assignment_checks_field_type(self) -> None:
        result = self.run_source(
            """
            type Pair { left: i32 }
            fn main() -> i32 {
                let mut pair = Pair { left: 2 };
                pair.left = "wrong";
                return 0;
            }
            """
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("NQ-TYPE-029", result.stderr)

    def test_field_assignment_rejects_non_owned_or_non_product_targets(self) -> None:
        cases = [
            """
            type Pair { left: i32 }
            fn main() -> i32 {
                let pair = Pair { left: 2 };
                pair.left = 3;
                return 0;
            }
            """,
            """
            type Pair { left: i32 }
            fn change(pair: mutref Pair) -> unit {
                pair.left = 3;
                return;
            }
            fn main() -> i32 { return 0; }
            """,
            """
            enum Choice { Keep(i32) }
            fn main() -> i32 {
                let mut choice = Keep(2);
                choice.left = 3;
                return 0;
            }
            """,
            """
            fn main() -> i32 {
                let mut values: list<i32> = [1];
                values.left = 3;
                return 0;
            }
            """,
        ]
        for source in cases:
            with self.subTest(source=source):
                result = self.run_source(source)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("NQ-TYPE-038", result.stderr)

    def test_field_assignment_rejects_nested_targets(self) -> None:
        result = self.run_source(
            """
            type Inner { value: i32 }
            type Outer { inner: Inner }
            fn main() -> i32 {
                let mut outer = Outer { inner: Inner { value: 2 } };
                outer.inner.value = 3;
                return 0;
            }
            """
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("NQ-PARSE", result.stderr)

    def test_field_assignment_reports_use_after_move(self) -> None:
        result = self.run_source(
            """
            type Pair {
                left: i32,
                values: list<i32>,
            }
            fn consume(pair: Pair) -> unit { return; }
            fn main() -> i32 {
                let mut pair = Pair { left: 2, values: [1] };
                consume(pair);
                pair.left = 3;
                return 0;
            }
            """
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("NQ-BORROW-001", result.stderr)


if __name__ == "__main__":
    unittest.main()
