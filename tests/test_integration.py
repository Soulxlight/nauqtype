from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


class IntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[1]

    def run_example(self, name: str) -> subprocess.CompletedProcess[str]:
        example = self.root / "examples" / name
        return subprocess.run(
            [sys.executable, "-m", "compiler.main", "run", str(example)],
            cwd=self.root,
            capture_output=True,
            text=True,
        )

    def test_hello_runs(self) -> None:
        result = self.run_example("hello.nq")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "Hello, Nauqtype!\n")

    def test_result_program_runs(self) -> None:
        result = self.run_example("result_handling.nq")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_mutation_program_runs(self) -> None:
        result = self.run_example("mutate_counter.nq")
        self.assertEqual(result.returncode, 42, result.stderr)

    def test_while_program_runs(self) -> None:
        result = self.run_example("while_counter.nq")
        self.assertEqual(result.returncode, 5, result.stderr)

    def test_review_contracts_program_runs(self) -> None:
        result = self.run_example("review_contracts.nq")
        self.assertEqual(result.returncode, 42, result.stderr)
        self.assertEqual(result.stdout, "Hello, contracts!\n")

    def test_list_program_runs(self) -> None:
        result = self.run_example("list_sum.nq")
        self.assertEqual(result.returncode, 42, result.stderr)

    def test_read_file_program_runs(self) -> None:
        result = self.run_example("read_file_len.nq")
        self.assertEqual(result.returncode, 6, result.stderr)

    def test_multi_file_program_runs(self) -> None:
        result = self.run_example("multi_file_main.nq")
        self.assertEqual(result.returncode, 7, result.stderr)

    def test_selfhost_stage1_runs(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "compiler.main", "run", str(self.root / "selfhost" / "main.nq")],
            cwd=self.root,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "stage1 front-end ok\n")


if __name__ == "__main__":
    unittest.main()
