from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


class IntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[1]

    def run_program(self, path: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-m", "compiler.main", "run", str(path)],
            cwd=self.root,
            capture_output=True,
            text=True,
        )

    def run_example(self, name: str) -> subprocess.CompletedProcess[str]:
        return self.run_program(self.root / "examples" / name)

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

    def test_fibonacci_program_runs(self) -> None:
        result = self.run_example("fibonacci.nq")
        self.assertEqual(result.returncode, 55, result.stderr)

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
        result = self.run_program(self.root / "selfhost" / "main.nq")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "stage1 front-end ok\n")

    def test_selfhost_resolve_probe_runs(self) -> None:
        result = self.run_program(self.root / "selfhost" / "resolve_probe.nq")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_selfhost_resolve_collision_probe_reports_error(self) -> None:
        result = self.run_program(self.root / "selfhost" / "resolve_collision_probe.nq")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_selfhost_body_resolve_probe_runs(self) -> None:
        result = self.run_program(self.root / "selfhost" / "body_resolve_probe.nq")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_selfhost_body_resolve_error_probe_reports_error(self) -> None:
        result = self.run_program(self.root / "selfhost" / "body_resolve_error_probe.nq")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_selfhost_pattern_resolve_probe_runs(self) -> None:
        result = self.run_program(self.root / "selfhost" / "pattern_resolve_probe.nq")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_selfhost_pattern_resolve_error_probe_reports_error(self) -> None:
        result = self.run_program(self.root / "selfhost" / "pattern_resolve_error_probe.nq")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_selfhost_hidden_import_body_error_probe_reports_error(self) -> None:
        result = self.run_program(self.root / "selfhost" / "hidden_import_body_error_probe.nq")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_selfhost_hidden_import_pattern_error_probe_reports_error(self) -> None:
        result = self.run_program(self.root / "selfhost" / "hidden_import_pattern_error_probe.nq")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_selfhost_expression_resolve_error_probe_reports_error(self) -> None:
        result = self.run_program(self.root / "selfhost" / "expression_resolve_error_probe.nq")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_selfhost_call_value_class_error_probe_reports_error(self) -> None:
        result = self.run_program(self.root / "selfhost" / "call_value_class_error_probe.nq")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_selfhost_hidden_import_struct_literal_error_probe_reports_error(self) -> None:
        result = self.run_program(self.root / "selfhost" / "hidden_import_struct_literal_error_probe.nq")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_selfhost_type_resolve_probe_runs(self) -> None:
        result = self.run_program(self.root / "selfhost" / "type_resolve_probe.nq")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_selfhost_unknown_type_error_probe_reports_error(self) -> None:
        result = self.run_program(self.root / "selfhost" / "unknown_type_error_probe.nq")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_selfhost_hidden_import_type_error_probe_reports_error(self) -> None:
        result = self.run_program(self.root / "selfhost" / "hidden_import_type_error_probe.nq")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_selfhost_typecheck_probe_runs(self) -> None:
        result = self.run_program(self.root / "selfhost" / "typecheck_probe.nq")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_selfhost_call_arity_typecheck_error_probe_reports_error(self) -> None:
        result = self.run_program(self.root / "selfhost" / "call_arity_typecheck_error_probe.nq")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_selfhost_pattern_arity_typecheck_error_probe_reports_error(self) -> None:
        result = self.run_program(self.root / "selfhost" / "pattern_arity_typecheck_error_probe.nq")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_selfhost_main_signature_typecheck_error_probe_reports_error(self) -> None:
        result = self.run_program(self.root / "selfhost" / "main_signature_typecheck_error_probe.nq")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_selfhost_value_flow_typecheck_probe_runs(self) -> None:
        result = self.run_program(self.root / "selfhost" / "value_flow_typecheck_probe.nq")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_selfhost_annotated_local_typecheck_error_probe_reports_error(self) -> None:
        result = self.run_program(self.root / "selfhost" / "annotated_local_typecheck_error_probe.nq")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_selfhost_return_typecheck_error_probe_reports_error(self) -> None:
        result = self.run_program(self.root / "selfhost" / "return_typecheck_error_probe.nq")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_selfhost_if_condition_typecheck_error_probe_reports_error(self) -> None:
        result = self.run_program(self.root / "selfhost" / "if_condition_typecheck_error_probe.nq")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_selfhost_while_condition_typecheck_error_probe_reports_error(self) -> None:
        result = self.run_program(self.root / "selfhost" / "while_condition_typecheck_error_probe.nq")
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
