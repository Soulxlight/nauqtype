from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

from tests.test_support import ROOT, built_stage1_driver, normalize_structural_c


class Stage1DriverTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root = ROOT
        cls._driver_ctx = built_stage1_driver(timeout=240)
        cls.driver_workspace, cls.driver_exe = cls._driver_ctx.__enter__()

    @classmethod
    def tearDownClass(cls) -> None:
        cls._driver_ctx.__exit__(None, None, None)

    def _write_project(self, tmp: Path, files: dict[str, str]) -> None:
        for name, content in files.items():
            (tmp / name).write_text(textwrap.dedent(content).strip() + "\n", encoding="utf-8")

    def test_stage1_driver_preserves_legacy_no_arg_selfhost_mode(self) -> None:
        result = subprocess.run(
            [str(self.driver_exe)],
            cwd=self.driver_workspace,
            capture_output=True,
            text=True,
            timeout=240,
        )
        combined = result.stdout + result.stderr
        self.assertEqual(result.returncode, 0, combined)
        self.assertEqual(result.stdout, "stage1 front-end ok\n")
        self.assertEqual(result.stderr, "")
        self.assertNotIn("stage1 limitation", combined)
        self.assertTrue((self.driver_workspace / "build" / "main.c").exists())

    def test_stage1_driver_prove_runs_owned_transition_gate(self) -> None:
        result = subprocess.run(
            [str(self.driver_exe), "prove"],
            cwd=self.root,
            capture_output=True,
            text=True,
            timeout=1200,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stdout, "selfhost proof ok\nexample corpus ok\nnauqtype proof ok\n")
        self.assertEqual(result.stderr, "")

    def test_stage1_driver_check_handles_project_relative_entry_and_imports(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            self._write_project(
                tmp,
                {
                    "main.nq": """
                    use helper;

                    fn main() -> i32 {
                        return read_value();
                    }
                    """,
                    "helper.nq": """
                    pub fn read_value() -> i32 {
                        return 7;
                    }
                    """,
                },
            )
            result = subprocess.run(
                [str(self.driver_exe), "check", "main.nq"],
                cwd=tmp,
                capture_output=True,
                text=True,
                timeout=240,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(result.stdout, "")
            self.assertEqual(result.stderr, "")

    def test_stage1_driver_emit_c_creates_parent_dirs_and_matches_stage0_structurally(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            self._write_project(
                tmp,
                {
                    "main.nq": """
                    use helper;

                    fn main() -> i32 {
                        let value = pair { left: 20, right: read_value() };
                        return value.left + value.right;
                    }
                    """,
                    "helper.nq": """
                    pub type pair {
                        left: i32,
                        right: i32,
                    }

                    pub fn read_value() -> i32 {
                        return 22;
                    }
                    """,
                },
            )

            stage0_out = tmp / "stage0.c"
            stage0_result = subprocess.run(
                [sys.executable, "-m", "compiler.main", "emit-c", str(tmp / "main.nq"), "-o", str(stage0_out)],
                cwd=self.root,
                capture_output=True,
                text=True,
                timeout=240,
            )
            self.assertEqual(stage0_result.returncode, 0, stage0_result.stdout + stage0_result.stderr)

            relative_out = Path("nested") / "stage1.c"
            stage1_result = subprocess.run(
                [str(self.driver_exe), "emit-c", "main.nq", "-o", str(relative_out)],
                cwd=tmp,
                capture_output=True,
                text=True,
                timeout=240,
            )
            self.assertEqual(stage1_result.returncode, 0, stage1_result.stdout + stage1_result.stderr)
            emitted = tmp / relative_out
            self.assertTrue(emitted.exists(), f"missing emitted C at {emitted}")

            stage0_c = stage0_out.read_text(encoding="utf-8")
            stage1_c = emitted.read_text(encoding="utf-8")
            self.assertEqual(normalize_structural_c(stage1_c), normalize_structural_c(stage0_c))

    def test_stage1_driver_review_matches_stage0_golden(self) -> None:
        example = self.root / "examples" / "review_contracts.nq"
        golden = self.root / "tests" / "golden" / "review" / "review_contracts.json"
        result = subprocess.run(
            [str(self.driver_exe), "review", str(example)],
            cwd=self.root,
            capture_output=True,
            text=True,
            timeout=240,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stderr, "")
        self.assertEqual(result.stdout.rstrip("\n"), golden.read_text(encoding="utf-8").rstrip("\n"))

    def test_stage1_driver_review_warns_for_missing_audit_and_keeps_json_clean(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            self._write_project(
                tmp,
                {
                    "warning_review.nq": """
                    pub fn greet() -> unit {
                        return;
                    }
                    """,
                },
            )
            result = subprocess.run(
                [str(self.driver_exe), "review", "warning_review.nq"],
                cwd=tmp,
                capture_output=True,
                text=True,
                timeout=240,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn('"module": "warning_review"', result.stdout)
            self.assertIn('"audit": null', result.stdout)
            self.assertIn("warning[NQ-CONTRACT-001]", result.stderr)

    def test_stage1_driver_review_infers_transitive_print_across_imports(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            self._write_project(
                tmp,
                {
                    "main.nq": """
                    use helper;

                    pub fn main() -> i32
                    audit {
                        intent("Run helper");
                        mutates();
                        effects(print);
                    }
                    {
                        helper();
                        return 0;
                    }
                    """,
                    "helper.nq": """
                    pub fn helper() -> unit
                    audit {
                        intent("Print a line");
                        mutates();
                        effects(print);
                    }
                    {
                        print_line("hi");
                        return;
                    }
                    """,
                },
            )
            result = subprocess.run(
                [str(self.driver_exe), "review", "main.nq"],
                cwd=tmp,
                capture_output=True,
                text=True,
                timeout=240,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(result.stderr, "")
            payload = json.loads(result.stdout)
            self.assertEqual(payload["functions"][0]["inferred"]["effects"], ["print"])

    def test_stage1_driver_review_v2_exports_semantic_identities(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            self._write_project(
                tmp,
                {
                    "main.nq": """
                    use helper;

                    pub fn main() -> i32
                    audit {
                        intent("Run helper");
                        mutates();
                        effects(print);
                    }
                    {
                        helper();
                        return 0;
                    }
                    """,
                    "helper.nq": """
                    pub fn helper() -> unit
                    audit {
                        intent("Print a line");
                        mutates();
                        effects(print);
                    }
                    {
                        print_line("hi");
                        return;
                    }
                    """,
                },
            )
            result = subprocess.run(
                [str(self.driver_exe), "review", "main.nq", "--format", "v2"],
                cwd=tmp,
                capture_output=True,
                text=True,
                timeout=240,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(result.stderr, "")
            payload = json.loads(result.stdout)
            self.assertEqual(payload["version"], 2)
            self.assertEqual(payload["identity_scheme"], "nauqtype.semantic.v1")
            function_ids = {entry["id"] for entry in payload["functions"]}
            self.assertIn("fn:main::main", function_ids)
            self.assertIn("fn:helper::helper", function_ids)
            self.assertTrue(
                any(
                    entry["kind"] == "call"
                    and entry["from"] == "fn:main::main"
                    and entry["target_id"] == "fn:helper::helper"
                    for entry in payload["references"]
                )
            )
            self.assertTrue(
                any(
                    edge["caller"] == "fn:main::main"
                    and edge["callee"] == "fn:helper::helper"
                    for edge in payload["call_graph"]
                )
            )

    def test_stage1_driver_facts_exports_defs_refs_and_call_graph(self) -> None:
        fixture = self.root / "tests" / "fixtures" / "facts" / "main.nq"
        golden = self.root / "tests" / "golden" / "facts" / "main.json"
        result = subprocess.run(
            [str(self.driver_exe), "facts", str(fixture)],
            cwd=self.root,
            capture_output=True,
            text=True,
            timeout=240,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stderr, "")
        payload = json.loads(result.stdout)
        expected = json.loads(golden.read_text(encoding="utf-8"))
        self.assertEqual(payload, expected)

        schema = json.loads((self.root / "schemas" / "facts-v1.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(schema["$id"], "https://nauqtype.dev/schemas/facts-v1.schema.json")
        self.assertEqual(schema["properties"]["version"]["const"], 1)
        self.assertEqual(schema["properties"]["command"]["const"], "facts")
        self.assertEqual(schema["properties"]["identity_scheme"]["const"], "nauqtype.semantic.v1")
        self.assertEqual(
            schema["required"],
            ["version", "command", "module", "identity_scheme", "summary", "modules", "definitions", "references", "call_graph"],
        )

    def test_stage1_driver_facts_exports_selfhost_module_without_limitations(self) -> None:
        result = subprocess.run(
            [str(self.driver_exe), "facts", str(self.root / "selfhost" / "source.nq")],
            cwd=self.root,
            capture_output=True,
            text=True,
            timeout=240,
        )
        combined = result.stdout + result.stderr
        self.assertEqual(result.returncode, 0, combined)
        self.assertEqual(result.stderr, "")
        self.assertNotIn("stage1 limitation", combined)
        self.assertNotIn("stage1 c error", combined)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["command"], "facts")
        self.assertEqual(payload["identity_scheme"], "nauqtype.semantic.v1")
        self.assertEqual(payload["module"], "source")
        self.assertGreaterEqual(payload["summary"]["definitions"], 2)
        self.assertGreaterEqual(payload["summary"]["references"], 1)

    def test_stage1_driver_review_diff_reports_semantic_changes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            before = tmp / "before"
            after = tmp / "after"
            before.mkdir()
            after.mkdir()
            self._write_project(
                before,
                {
                    "main.nq": """
                    pub fn helper() -> unit
                    audit {
                        intent("Return without output");
                        mutates();
                        effects();
                    }
                    {
                        return;
                    }

                    pub fn main() -> i32
                    audit {
                        intent("Return zero");
                        mutates();
                        effects();
                    }
                    {
                        return 0;
                    }
                    """,
                },
            )
            self._write_project(
                after,
                {
                    "main.nq": """
                    pub fn helper() -> unit
                    audit {
                        intent("Print helper");
                        mutates();
                        effects(print);
                    }
                    {
                        print_line("hi");
                        return;
                    }

                    pub fn main() -> i32
                    audit {
                        intent("Call helper");
                        mutates();
                        effects(print);
                    }
                    {
                        helper();
                        return 0;
                    }
                    """,
                },
            )
            result = subprocess.run(
                [str(self.driver_exe), "review-diff", str(before / "main.nq"), str(after / "main.nq")],
                cwd=self.root,
                capture_output=True,
                text=True,
                timeout=240,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(result.stderr, "")
            payload = json.loads(result.stdout)
            self.assertEqual(payload["version"], 1)
            self.assertEqual(payload["command"], "review-diff")
            self.assertEqual(payload["identity_scheme"], "nauqtype.semantic.v1")
            self.assertEqual(payload["summary"]["added_functions"], 0)
            self.assertEqual(payload["summary"]["removed_functions"], 0)
            self.assertEqual(payload["summary"]["changed_functions"], 2)
            self.assertEqual(payload["changes"]["changed_functions"], ["fn:main::helper", "fn:main::main"])
            self.assertEqual(
                payload["changes"]["added_call_edges"],
                ["fn:main::helper -> builtin:print_line", "fn:main::main -> fn:main::helper"],
            )

    def test_stage1_driver_review_rejects_borrow_errors_before_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            self._write_project(
                tmp,
                {
                    "main.nq": """
                    type Bucket {
                        items: list<i32>,
                    }

                    fn take(bucket: Bucket) -> i32 {
                        return 0;
                    }

                    fn inspect(bucket: ref Bucket) -> i32 {
                        return 0;
                    }

                    pub fn main() -> i32
                    audit {
                        intent("Reject unsafe review input");
                        mutates();
                        effects();
                    }
                    {
                        let mut items: list<i32> = list();
                        list_push(mutref items, 1);
                        let bucket = Bucket { items: items };
                        take(bucket);
                        return inspect(ref bucket);
                    }
                    """,
                },
            )
            result = subprocess.run(
                [str(self.driver_exe), "review", "main.nq"],
                cwd=tmp,
                capture_output=True,
                text=True,
                timeout=240,
            )
            combined = result.stdout + result.stderr
            self.assertNotEqual(result.returncode, 0, combined)
            self.assertIn("cannot borrow moved value `bucket`", combined)
            self.assertNotIn('"functions"', result.stdout)

    def test_stage1_driver_build_creates_default_c_and_exe_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            self._write_project(
                tmp,
                {
                    "main.nq": """
                    fn main() -> i32 {
                        return 7;
                    }
                    """,
                },
            )
            result = subprocess.run(
                [str(self.driver_exe), "build", str(tmp / "main.nq")],
                cwd=self.root,
                capture_output=True,
                text=True,
                timeout=240,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(result.stdout, "")
            self.assertEqual(result.stderr, "")
            self.assertTrue((tmp / "build" / "main.c").exists())
            self.assertTrue((tmp / "build" / "main.exe").exists())

    def test_stage1_driver_run_executes_with_source_directory_cwd(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            self._write_project(
                tmp,
                {
                    "main.nq": """
                    fn main() -> i32 {
                        let data = read_file("input.txt");
                        match data {
                            Ok(text) => {
                                print_line(text);
                                return 0;
                            },
                            Err(err) => {
                                print_line(io_err_text(err));
                                return 1;
                            },
                        }
                    }
                    """,
                },
            )
            (tmp / "input.txt").write_text("hello", encoding="utf-8")
            result = subprocess.run(
                [str(self.driver_exe), "run", str(tmp / "main.nq")],
                cwd=self.root,
                capture_output=True,
                text=True,
                timeout=240,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(result.stdout, "hello\n")
            self.assertEqual(result.stderr, "")


if __name__ == "__main__":
    unittest.main()
