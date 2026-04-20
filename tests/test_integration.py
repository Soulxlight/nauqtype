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


if __name__ == "__main__":
    unittest.main()
