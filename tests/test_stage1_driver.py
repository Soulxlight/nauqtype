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
            target = tmp / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(textwrap.dedent(content).strip() + "\n", encoding="utf-8")

    def _run_driver(self, args: list[str], *, cwd: Path | None = None, timeout: int = 240) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [str(self.driver_exe), *args],
            cwd=cwd if cwd is not None else self.root,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

    def _schema_spec(self, schema: dict, spec: dict) -> dict:
        ref = spec.get("$ref")
        if not ref:
            return spec
        name = ref.removeprefix("#/$defs/")
        return schema["$defs"][name]

    def _assert_schema_shape(self, payload, schema: dict, spec: dict | None = None) -> None:
        spec = self._schema_spec(schema, spec if spec is not None else schema)
        if "const" in spec:
            self.assertEqual(payload, spec["const"])
        if "enum" in spec:
            self.assertIn(payload, spec["enum"])
        expected_type = spec.get("type")
        if expected_type == "object" or (isinstance(expected_type, list) and "object" in expected_type and payload is not None):
            self.assertIsInstance(payload, dict)
            for key in spec.get("required", []):
                self.assertIn(key, payload)
            if spec.get("additionalProperties") is False and "properties" in spec:
                self.assertLessEqual(set(payload), set(spec["properties"]))
            for key, child_spec in spec.get("properties", {}).items():
                if key in payload:
                    self._assert_schema_shape(payload[key], schema, child_spec)
        if expected_type == "array":
            self.assertIsInstance(payload, list)
            item_spec = spec.get("items")
            if item_spec is not None:
                for item in payload:
                    self._assert_schema_shape(item, schema, item_spec)

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

    def test_stage1_driver_top_level_const_check_emit_build_and_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            self._write_project(
                tmp,
                {
                    "main.nq": """
                    const answer: i32 = 40 + 2;
                    const greeting: str = "hello const";
                    const should_print: bool = true and not false;

                    fn main() -> i32 {
                        if should_print {
                            print_line(greeting);
                        }
                        return answer - 42;
                    }
                    """,
                },
            )

            checked = self._run_driver(["check", str(tmp / "main.nq")])
            self.assertEqual(checked.returncode, 0, checked.stdout + checked.stderr)
            self.assertEqual(checked.stdout, "")
            self.assertEqual(checked.stderr, "")

            out_c = tmp / "build" / "const_main.c"
            emitted = self._run_driver(["emit-c", str(tmp / "main.nq"), "-o", str(out_c)])
            self.assertEqual(emitted.returncode, 0, emitted.stdout + emitted.stderr)
            c_text = out_c.read_text(encoding="utf-8")
            self.assertIn("static const int32_t nqc_main__answer", c_text)
            self.assertIn("static const NQStr nqc_main__greeting", c_text)
            self.assertIn("static const bool nqc_main__should_print", c_text)
            self.assertIn("nq_print_line(nqc_main__greeting)", c_text)

            built = self._run_driver(["build", str(tmp / "main.nq")])
            self.assertEqual(built.returncode, 0, built.stdout + built.stderr)

            ran = self._run_driver(["run", str(tmp / "main.nq")])
            self.assertEqual(ran.returncode, 0, ran.stdout + ran.stderr)
            self.assertEqual(ran.stdout, "hello const\n")
            self.assertEqual(ran.stderr, "")

    def test_stage1_driver_top_level_const_imports_facts_refactor_and_policy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            self._write_project(
                tmp,
                {
                    "main.nq": """
                    use helper;

                    fn main() -> i32 {
                        return helper_value;
                    }
                    """,
                    "helper.nq": """
                    pub const helper_value: i32 = 21 * 2;

                    pub fn read_helper() -> i32 {
                        return helper_value;
                    }
                    """,
                },
            )
            before_main = (tmp / "main.nq").read_text(encoding="utf-8")
            before_helper = (tmp / "helper.nq").read_text(encoding="utf-8")

            facts = self._run_driver(["facts", str(tmp / "main.nq"), "--format", "v2"])
            self.assertEqual(facts.returncode, 0, facts.stdout + facts.stderr)
            payload = json.loads(facts.stdout)
            self.assertTrue(any(entry["id"] == "const:helper::helper_value" and entry["kind"] == "const" for entry in payload["definitions"]))
            self.assertTrue(
                any(
                    entry["kind"] == "value"
                    and entry["target_kind"] == "const"
                    and entry["target_id"] == "const:helper::helper_value"
                    and entry["from"] == "fn:main::main"
                    for entry in payload["references"]
                )
            )

            refactor = self._run_driver(["refactor-rename", str(tmp / "main.nq"), "const:helper::helper_value", "renamed_value"])
            self.assertEqual(refactor.returncode, 0, refactor.stdout + refactor.stderr)
            plan = json.loads(refactor.stdout)
            self.assertTrue(plan["ok"])
            self.assertEqual([edit["kind"] for edit in plan["edits"]], ["definition", "reference", "reference"])
            self.assertTrue(all(edit["replacement"] == "renamed_value" for edit in plan["edits"]))
            self.assertEqual((tmp / "main.nq").read_text(encoding="utf-8"), before_main)
            self.assertEqual((tmp / "helper.nq").read_text(encoding="utf-8"), before_helper)

            policy = tmp / "nauqtype.policy.json"
            policy.write_text(
                json.dumps({"version": 1, "targets": [{"target_id": "const:helper::helper_value", "owner": "human:lead", "review": "required"}]}),
                encoding="utf-8",
            )
            policy_result = self._run_driver(["policy-check", str(tmp / "main.nq"), str(policy)])
            self.assertEqual(policy_result.returncode, 0, policy_result.stdout + policy_result.stderr)
            policy_payload = json.loads(policy_result.stdout)
            self.assertTrue(policy_payload["ok"])
            self.assertTrue(policy_payload["targets"][0]["known"])

    def test_stage1_driver_top_level_const_rejects_unsupported_shapes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            self._write_project(
                tmp,
                {
                    "main.nq": """
                    const wrong_type: bool = 1 + 2;
                    const bad_initializer: i32 = print_line("nope");
                    const bad_shape: list<i32> = list();
                    const bad_string_compare: bool = "a" == "a";

                    fn main() -> i32 {
                        return 0;
                    }
                    """,
                },
            )
            result = self._run_driver(["check", str(tmp / "main.nq")])
            combined = result.stdout + result.stderr
            self.assertNotEqual(result.returncode, 0, combined)
            self.assertIn("const initializer does not match declared type", combined)
            self.assertIn("stage1 limitation: unsupported const initializer expression", combined)
            self.assertIn("top-level const supports only non-borrow i32, bool, or str in v1", combined)
            self.assertIn("const comparison operand must have integer type", combined)

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

    def test_stage1_driver_review_v2_matches_golden_and_schema_contract(self) -> None:
        fixture = self.root / "tests" / "fixtures" / "review_v2.nq"
        golden = self.root / "tests" / "golden" / "review" / "review_v2.json"
        result = self._run_driver(["review", str(fixture), "--format", "v2"])
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stderr, "")
        self.assertEqual(json.loads(result.stdout), json.loads(golden.read_text(encoding="utf-8")))
        schema = json.loads((self.root / "schemas" / "review-v2.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(schema["$id"], "https://nauqtype.dev/schemas/review-v2.schema.json")
        self.assertEqual(schema["properties"]["version"]["const"], 2)
        self.assertEqual(schema["properties"]["command"]["const"], "review")
        self._assert_schema_shape(json.loads(result.stdout), schema)

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

    def test_stage1_driver_facts_v2_exports_evidence_and_matches_golden(self) -> None:
        fixture = self.root / "tests" / "fixtures" / "facts" / "main.nq"
        golden = self.root / "tests" / "golden" / "facts" / "main-v2.json"
        result = self._run_driver(["facts", str(fixture), "--format", "v2"])
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stderr, "")
        payload = json.loads(result.stdout)
        self.assertEqual(payload, json.loads(golden.read_text(encoding="utf-8")))
        self.assertEqual({entry["evidence"] for entry in payload["references"]}, {"declared", "builtin", "checked"})
        schema = json.loads((self.root / "schemas" / "facts-v2.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(schema["$id"], "https://nauqtype.dev/schemas/facts-v2.schema.json")
        self.assertEqual(schema["properties"]["version"]["const"], 2)
        self._assert_schema_shape(payload, schema)

    def test_stage1_driver_facts_full_selfhost_is_bounded_and_valid(self) -> None:
        result = self._run_driver(["facts", str(self.root / "selfhost" / "main.nq")], timeout=240)
        combined = result.stdout + result.stderr
        self.assertEqual(result.returncode, 0, combined)
        self.assertEqual(result.stderr, "")
        self.assertNotIn("stage1 limitation", combined)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["command"], "facts")
        self.assertEqual(payload["module"], "main")
        self.assertGreater(payload["summary"]["definitions"], 100)

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

    def test_stage1_driver_review_diff_goldens_and_v2_evidence(self) -> None:
        before = self.root / "tests" / "fixtures" / "review_diff" / "before" / "main.nq"
        after = self.root / "tests" / "fixtures" / "review_diff" / "after" / "main.nq"
        v1 = self._run_driver(["review-diff", str(before), str(after)])
        self.assertEqual(v1.returncode, 0, v1.stdout + v1.stderr)
        self.assertEqual(v1.stderr, "")
        self.assertEqual(
            json.loads(v1.stdout),
            json.loads((self.root / "tests" / "golden" / "review" / "review_diff_v1.json").read_text(encoding="utf-8")),
        )
        v2 = self._run_driver(["review-diff", str(before), str(after), "--format", "v2"])
        self.assertEqual(v2.returncode, 0, v2.stdout + v2.stderr)
        self.assertEqual(v2.stderr, "")
        payload = json.loads(v2.stdout)
        self.assertEqual(
            payload,
            json.loads((self.root / "tests" / "golden" / "review" / "review_diff_v2.json").read_text(encoding="utf-8")),
        )
        self.assertEqual(payload["evidence"]["comparison"], "semantic-identities")
        self.assertEqual(
            json.loads((self.root / "schemas" / "review-diff-v1.schema.json").read_text(encoding="utf-8"))["properties"]["version"]["const"],
            1,
        )
        self.assertEqual(
            json.loads((self.root / "schemas" / "review-diff-v2.schema.json").read_text(encoding="utf-8"))["properties"]["version"]["const"],
            2,
        )
        self._assert_schema_shape(
            json.loads(v1.stdout),
            json.loads((self.root / "schemas" / "review-diff-v1.schema.json").read_text(encoding="utf-8")),
        )
        self._assert_schema_shape(
            payload,
            json.loads((self.root / "schemas" / "review-diff-v2.schema.json").read_text(encoding="utf-8")),
        )

    def test_stage1_driver_refactor_rename_plans_imported_function_without_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            self._write_project(
                tmp,
                {
                    "main.nq": """
                    use helper;

                    fn main() -> i32 {
                        let value = helper();
                        return value;
                    }
                    """,
                    "helper.nq": """
                    pub fn helper() -> i32 {
                        return 7;
                    }
                    """,
                },
            )
            before_main = (tmp / "main.nq").read_text(encoding="utf-8")
            before_helper = (tmp / "helper.nq").read_text(encoding="utf-8")
            result = self._run_driver(["refactor-rename", str(tmp / "main.nq"), "fn:helper::helper", "renamed_helper"])
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            payload = json.loads(result.stdout)
            self.assertTrue(payload["ok"])
            self.assertEqual([edit["kind"] for edit in payload["edits"]], ["definition", "reference"])
            self.assertEqual(payload["edits"][1]["module"], "main")
            self._assert_schema_shape(
                payload,
                json.loads((self.root / "schemas" / "refactor-rename-v1.schema.json").read_text(encoding="utf-8")),
            )
            self.assertEqual((tmp / "main.nq").read_text(encoding="utf-8"), before_main)
            self.assertEqual((tmp / "helper.nq").read_text(encoding="utf-8"), before_helper)

    def test_stage1_driver_refactor_rename_plans_local_binding(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            self._write_project(
                tmp,
                {
                    "main.nq": """
                    fn main() -> i32 {
                        let value = 1;
                        return value;
                    }
                    """,
                },
            )
            facts = self._run_driver(["facts", str(tmp / "main.nq"), "--format", "v2"])
            self.assertEqual(facts.returncode, 0, facts.stdout + facts.stderr)
            local_id = next(entry["id"] for entry in json.loads(facts.stdout)["definitions"] if entry["kind"] == "local")
            result = self._run_driver(["refactor-rename", str(tmp / "main.nq"), local_id, "total"])
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            payload = json.loads(result.stdout)
            self.assertTrue(payload["ok"])
            self.assertEqual(len(payload["edits"]), 2)
            self.assertTrue(all(edit["replacement"] == "total" for edit in payload["edits"]))

    def test_stage1_driver_refactor_rename_rejects_invalid_identifier_and_unknown_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            self._write_project(tmp, {"main.nq": "fn main() -> i32 {\n    return 0;\n}\n"})
            invalid = self._run_driver(["refactor-rename", str(tmp / "main.nq"), "fn:main::main", "not-valid"])
            self.assertNotEqual(invalid.returncode, 0, invalid.stdout + invalid.stderr)
            invalid_payload = json.loads(invalid.stdout)
            self.assertFalse(invalid_payload["ok"])
            self.assertEqual(invalid_payload["edits"], [])
            unknown = self._run_driver(["refactor-rename", str(tmp / "main.nq"), "fn:main::missing", "renamed"])
            self.assertNotEqual(unknown.returncode, 0, unknown.stdout + unknown.stderr)
            unknown_payload = json.loads(unknown.stdout)
            self.assertFalse(unknown_payload["ok"])
            self.assertEqual(unknown_payload["diagnostics"][0]["code"], "NQ-REFACTOR-002")

    def test_stage1_driver_refactor_rename_rejects_field_ids_until_field_uses_are_exported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            self._write_project(
                tmp,
                {
                    "main.nq": """
                    type Box {
                        value: i32,
                    }

                    fn main() -> i32 {
                        let box = Box { value: 1 };
                        return box.value;
                    }
                    """,
                },
            )
            result = self._run_driver(["refactor-rename", str(tmp / "main.nq"), "field:main::Box::value", "amount"])
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
            payload = json.loads(result.stdout)
            self.assertFalse(payload["ok"])
            self.assertEqual(payload["edits"], [])
            self.assertEqual(payload["diagnostics"][0]["code"], "NQ-REFACTOR-002")

    def test_stage1_driver_policy_check_validates_sidecar_targets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            self._write_project(tmp, {"main.nq": "fn main() -> i32 {\n    return 0;\n}\n"})
            policy = tmp / "nauqtype.policy.json"
            policy.write_text(
                json.dumps({"version": 1, "targets": [{"target_id": "fn:main::main", "owner": "human:lead", "review": "required"}]}),
                encoding="utf-8",
            )
            result = self._run_driver(["policy-check", str(tmp / "main.nq"), str(policy)])
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            payload = json.loads(result.stdout)
            self.assertTrue(payload["ok"])
            self.assertEqual(payload["summary"]["errors"], 0)
            self._assert_schema_shape(
                payload,
                json.loads((self.root / "schemas" / "policy-check-v1.schema.json").read_text(encoding="utf-8")),
            )
            self._assert_schema_shape(
                json.loads(policy.read_text(encoding="utf-8")),
                json.loads((self.root / "schemas" / "nauqtype.policy-v1.schema.json").read_text(encoding="utf-8")),
            )
            self.assertEqual(
                json.loads((self.root / "schemas" / "policy-check-v1.schema.json").read_text(encoding="utf-8"))["properties"]["command"]["const"],
                "policy-check",
            )
            self.assertEqual(
                json.loads((self.root / "schemas" / "nauqtype.policy-v1.schema.json").read_text(encoding="utf-8"))["properties"]["version"]["const"],
                1,
            )

    def test_stage1_driver_policy_check_reports_unknown_duplicate_and_invalid_values(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            self._write_project(tmp, {"main.nq": "fn main() -> i32 {\n    return 0;\n}\n"})
            policy = tmp / "nauqtype.policy.json"
            policy.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "targets": [
                            {"target_id": "fn:main::missing", "owner": "human:lead", "review": "required"},
                            {"target_id": "fn:main::main", "owner": "team", "review": "required"},
                            {"target_id": "fn:main::main", "owner": "agent:pair", "review": "block"},
                        ],
                    }
                ),
                encoding="utf-8",
            )
            result = self._run_driver(["policy-check", str(tmp / "main.nq"), str(policy)])
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
            payload = json.loads(result.stdout)
            self.assertFalse(payload["ok"])
            codes = [diag["code"] for diag in payload["diagnostics"]]
            self.assertIn("NQ-POLICY-003", codes)
            self.assertIn("NQ-POLICY-004", codes)
            self.assertIn("NQ-POLICY-005", codes)
            self.assertIn("NQ-POLICY-006", codes)

    def test_stage1_driver_policy_check_reports_malformed_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            self._write_project(tmp, {"main.nq": "fn main() -> i32 {\n    return 0;\n}\n"})
            policy = tmp / "nauqtype.policy.json"
            policy.write_text("{", encoding="utf-8")
            result = self._run_driver(["policy-check", str(tmp / "main.nq"), str(policy)])
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
            payload = json.loads(result.stdout)
            self.assertFalse(payload["ok"])
            self.assertEqual(payload["diagnostics"][0]["code"], "NQ-POLICY-002")

    def test_stage1_driver_policy_check_rejects_non_exact_policy_version(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            self._write_project(tmp, {"main.nq": "fn main() -> i32 {\n    return 0;\n}\n"})
            policy = tmp / "nauqtype.policy.json"
            policy.write_text(
                json.dumps({"version": 10, "targets": [{"target_id": "fn:main::main", "owner": "human:lead", "review": "required"}]}),
                encoding="utf-8",
            )
            result = self._run_driver(["policy-check", str(tmp / "main.nq"), str(policy)])
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
            payload = json.loads(result.stdout)
            self.assertFalse(payload["ok"])
            self.assertEqual(payload["diagnostics"][0]["code"], "NQ-POLICY-002")

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

    def test_stage1_driver_fmt_outputs_canonical_text_without_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            source = tmp / "main.nq"
            source.write_text(
                "fn main() -> i32 {\n"
                "let value = 1;\n"
                "if value == 1 {\n"
                "return 0;\n"
                "}\n"
                "return 1;\n"
                "}\n",
                encoding="utf-8",
                newline="\n",
            )
            original = source.read_text(encoding="utf-8")

            result = self._run_driver(["fmt", str(source)])

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(
                result.stdout,
                "fn main() -> i32 {\n"
                "    let value = 1;\n"
                "    if value == 1 {\n"
                "        return 0;\n"
                "    }\n"
                "    return 1;\n"
                "}\n",
            )
            self.assertEqual(result.stderr, "")
            self.assertEqual(source.read_text(encoding="utf-8"), original)

    def test_stage1_driver_fmt_check_and_fail_closed_cases(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            formatted = tmp / "formatted.nq"
            formatted.write_text(
                "fn main() -> i32 {\n"
                "    return 0;\n"
                "}\n",
                encoding="utf-8",
                newline="\n",
            )
            unformatted = tmp / "unformatted.nq"
            unformatted.write_text("fn main() -> i32 {\nreturn 0;\n}\n", encoding="utf-8", newline="\n")
            tabbed = tmp / "tabbed.nq"
            tabbed.write_text("fn main() -> i32 {\n\treturn 0;\n}\n", encoding="utf-8", newline="\n")

            ok = self._run_driver(["fmt", "--check", str(formatted)])
            self.assertEqual(ok.returncode, 0, ok.stdout + ok.stderr)
            self.assertEqual(ok.stdout, "")
            self.assertEqual(ok.stderr, "")

            changed = self._run_driver(["fmt", "--check", str(unformatted)])
            self.assertNotEqual(changed.returncode, 0)
            self.assertEqual(changed.stdout, "")
            self.assertIn("fmt check failed", changed.stderr)

            unsupported = self._run_driver(["fmt", "--check", str(tabbed)])
            self.assertNotEqual(unsupported.returncode, 0)
            self.assertEqual(unsupported.stdout, "")
            self.assertIn("formatter-lite unsupported: tabs", unsupported.stderr)

    def test_stage1_driver_fmt_check_accepts_canonical_examples(self) -> None:
        for name in ("top_level_const.nq", "list_literals.nq", "match_expr_let_else.nq"):
            with self.subTest(name=name):
                result = self._run_driver(["fmt", "--check", str(self.root / "examples" / name)])
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertEqual(result.stdout, "")
                self.assertEqual(result.stderr, "")


if __name__ == "__main__":
    unittest.main()
