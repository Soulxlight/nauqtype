from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

from tests.test_support import ROOT, STAGE1_DRIVER_BUILD_TIMEOUT, built_stage1_driver, normalize_structural_c


class Stage1DriverTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root = ROOT
        cls._driver_ctx = built_stage1_driver(timeout=STAGE1_DRIVER_BUILD_TIMEOUT)
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

    def _proof_summary_path(self, cwd: Path | None = None) -> Path:
        return (cwd if cwd is not None else self.root) / "build" / "proof" / "summary.json"

    def _clear_proof_summary(self, cwd: Path | None = None) -> None:
        path = self._proof_summary_path(cwd)
        if path.exists():
            path.unlink()

    def _load_proof_summary(self, cwd: Path | None = None) -> dict:
        path = self._proof_summary_path(cwd)
        self.assertTrue(path.exists(), f"missing proof summary at {path}")
        payload = json.loads(path.read_text(encoding="utf-8"))
        schema = json.loads((self.root / "schemas" / "proof-summary-v2.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(schema["$id"], "https://nauqtype.dev/schemas/proof-summary-v2.schema.json")
        self.assertEqual(schema["properties"]["version"]["const"], 2)
        self._assert_schema_shape(payload, schema)
        return payload

    def _phase_statuses(self, summary: dict) -> dict[str, str]:
        return {entry["id"]: entry["status"] for entry in summary["phases"]}

    def _phase_by_id(self, summary: dict, phase_id: str) -> dict:
        for entry in summary["phases"]:
            if entry["id"] == phase_id:
                return entry
        self.fail(f"missing phase {phase_id}")

    def _locked_corpus_entries(self) -> list[tuple[str, str]]:
        proof_source = (self.root / "selfhost" / "proof.nq").read_text(encoding="utf-8")
        entries = re.findall(r'make_corpus_case\("([^"]+)",\s*"([^"]+)",', proof_source)
        self.assertGreater(len(entries), 0)
        return entries

    def _locked_corpus_count(self) -> int:
        return len(self._locked_corpus_entries())

    def _locked_formatter_example_paths(self) -> list[str]:
        proof_source = (self.root / "selfhost" / "proof.nq").read_text(encoding="utf-8")
        match = re.search(
            r"fn push_locked_formatter_examples\(paths: mutref list<str>\) -> unit \{(?P<body>.*?)\n\}",
            proof_source,
            re.S,
        )
        self.assertIsNotNone(match)
        paths = re.findall(r'list_push\(mutref paths,\s*"([^"]+)"\)', match.group("body"))
        self.assertGreater(len(paths), 0)
        return paths

    def _all_example_paths(self) -> list[str]:
        return [path.relative_to(self.root).as_posix() for path in sorted((self.root / "examples").glob("*.nq"))]

    def _runnable_example_paths(self) -> list[str]:
        paths: list[str] = []
        for path in sorted((self.root / "examples").glob("*.nq")):
            text = path.read_text(encoding="utf-8")
            if re.search(r"\bfn\s+main\s*\(", text):
                paths.append(path.relative_to(self.root).as_posix())
        return paths

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

    def test_stage1_driver_help_aliases_match_stable_golden(self) -> None:
        expected = (self.root / "tests" / "golden" / "cli" / "help.txt").read_text(encoding="utf-8")
        for command in ("help", "--help", "-h"):
            with self.subTest(command=command):
                result = self._run_driver([command])
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertEqual(result.stdout, expected)
                self.assertEqual(result.stderr, "")

    def test_stage1_driver_version_aliases_match_version_source(self) -> None:
        expected = (self.root / "tests" / "golden" / "cli" / "version.txt").read_text(encoding="utf-8")
        version = (self.root / "VERSION").read_text(encoding="utf-8").strip()
        self.assertEqual(expected, f"nauqc {version}\n")
        for command in ("version", "--version", "-V"):
            with self.subTest(command=command):
                result = self._run_driver([command])
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertEqual(result.stdout, expected)
                self.assertEqual(result.stderr, "")

    def test_stage1_driver_prove_runs_owned_transition_gate(self) -> None:
        self._clear_proof_summary()
        result = self._run_driver(["prove"], timeout=1200)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stdout, "selfhost proof ok\nexample corpus ok\nnauqtype proof ok\n")
        self.assertEqual(result.stderr, "")
        summary = self._load_proof_summary()
        self.assertEqual(summary["version"], 2)
        self.assertEqual(summary["command"], "prove")
        self.assertTrue(summary["ok"])
        self.assertEqual(summary["failed_phase"], "")
        self.assertEqual(summary["failure"], {"phase": "", "corpus_id": "", "artifact_path": ""})
        self.assertEqual(summary["selfhost"]["status"], "passed")
        self.assertTrue(summary["selfhost"]["structural_c_equal"])
        self.assertTrue(summary["selfhost"]["artifacts"]["stage1_c"]["hash"].startswith("nqsum:"))
        self.assertEqual(
            summary["selfhost"]["artifacts"]["stage1_c"]["hash"],
            summary["selfhost"]["artifacts"]["stage2_c"]["hash"],
        )
        self.assertEqual(summary["corpus"]["status"], "passed")
        self.assertEqual(summary["corpus"]["cases"], self._locked_corpus_count())
        self.assertEqual(len(summary["corpus"]["ids"]), self._locked_corpus_count())
        self.assertIn("hello", summary["corpus"]["ids"])
        self.assertEqual(len(summary["corpus"]["artifacts"]), self._locked_corpus_count())
        hello_artifact = next(entry for entry in summary["corpus"]["artifacts"] if entry["id"] == "hello")
        self.assertTrue(hello_artifact["emit_c"]["hash"].startswith("nqsum:"))
        self.assertEqual(hello_artifact["emit_c"]["hash"], hello_artifact["build_c"]["hash"])
        self.assertEqual(hello_artifact["emit_c"]["hash"], hello_artifact["run_c"]["hash"])
        self.assertEqual(summary["tooling"]["status"], "passed")
        self.assertEqual(summary["tooling"]["groups"], ["schema_golden", "policy_check", "refactor_plan", "formatter_check"])
        self.assertEqual(self._phase_by_id(summary, "selfhost.stage1_emit_c")["ordinal"], 2)
        self.assertEqual(self._phase_by_id(summary, "tooling.schema_golden")["group"], "tooling")
        self.assertEqual(set(self._phase_statuses(summary).values()), {"passed"})

    def test_stage1_driver_test_runs_owned_fixture_suite(self) -> None:
        result = self._run_driver(["test"], timeout=1200)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stdout, "nauqtype test ok\n")
        self.assertEqual(result.stderr, "")

    def test_stage1_driver_check_diagnostics_json_is_schema_shaped(self) -> None:
        result = self._run_driver(["check", "tests/fixtures/diagnostics_failure.nq", "--diagnostics", "json"])
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertEqual(result.stderr, "")
        payload = json.loads(result.stdout)
        schema = json.loads((self.root / "schemas" / "diagnostics-v1.schema.json").read_text(encoding="utf-8"))
        self._assert_schema_shape(payload, schema)
        self.assertFalse(payload["ok"])
        self.assertEqual([entry["code"] for entry in payload["diagnostics"]], ["NQ-TYPE-042", "NQ-TYPE-042"])
        self.assertTrue(all(entry["span"] is not None for entry in payload["diagnostics"]))

    def test_stage1_driver_checks_manifest_nested_workspace(self) -> None:
        source = "tests/fixtures/workspace_nested/src/app/main.nq"
        result = self._run_driver(["check", source])
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "")
        facts = self._run_driver(["facts", source, "--format", "v2"])
        self.assertEqual(facts.returncode, 0, facts.stdout + facts.stderr)
        self.assertIn('"name": "app::main"', facts.stdout)
        self.assertIn('"name": "app::helper"', facts.stdout)
        self.assertIn('"target_id": "fn:app::helper::answer"', facts.stdout)
        self.assertIn('"call_site": "call:app::main::main@61"', facts.stdout)

    def test_stage1_driver_supports_explicit_module_aliases(self) -> None:
        source = "tests/fixtures/workspace_alias/src/app/main.nq"
        check = self._run_driver(["check", source])
        self.assertEqual(check.returncode, 0, check.stdout + check.stderr)
        self.assertEqual(check.stdout, "")
        self.assertEqual(check.stderr, "")

        run = self._run_driver(["run", source])
        self.assertEqual(run.returncode, 7, run.stdout + run.stderr)
        self.assertEqual(run.stdout, "")
        self.assertEqual(run.stderr, "")

        facts = self._run_driver(["facts", source, "--format", "v2"])
        self.assertEqual(facts.returncode, 0, facts.stdout + facts.stderr)
        self.assertIn('"kind": "import"', facts.stdout)
        self.assertIn('"name": "model"', facts.stdout)
        self.assertIn('"target_id": "module:app::model"', facts.stdout)
        self.assertIn('"target_id": "type:app::model::Box"', facts.stdout)
        self.assertIn('"target_id": "variant:app::model::Choice::Keep"', facts.stdout)

        with tempfile.TemporaryDirectory() as tmp_text:
            tmp = Path(tmp_text)
            self._write_project(
                tmp,
                {
                    "nauqtype.workspace.json": '''
                        {"version":"workspace/v1","workspace":{"name":"tests.alias_duplicate","source_roots":["src"]}}
                    ''',
                    "src/app/one.nq": "pub fn value() -> i32 { return 1; }",
                    "src/app/two.nq": "pub fn value() -> i32 { return 2; }",
                    "src/app/main.nq": '''
                        use app::one as source;
                        use app::two as source;

                        fn main() -> i32 { return 0; }
                    ''',
                },
            )
            duplicate = self._run_driver(["check", str(tmp / "src" / "app" / "main.nq")])
            self.assertEqual(duplicate.returncode, 1)
            self.assertIn("duplicate import qualifier", duplicate.stdout + duplicate.stderr)

    def test_stage1_driver_rejects_workspace_dependencies_without_lock(self) -> None:
        source = "tests/fixtures/workspace_missing_lock/src/app/main.nq"
        result = self._run_driver(["check", source])
        self.assertEqual(result.returncode, 1)
        self.assertIn("workspace dependencies require nauqtype.workspace.lock.json", result.stdout)

    def test_stage1_driver_rejects_multiple_workspace_source_roots(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_text:
            tmp = Path(tmp_text)
            self._write_project(
                tmp,
                {
                    "nauqtype.workspace.json": """
                        {
                          "version": "workspace/v1",
                          "workspace": {
                            "name": "tests.multiple_roots",
                            "source_roots": ["src", "other"]
                          }
                        }
                    """,
                    "src/main.nq": """
                        fn main() -> i32 {
                            return 0;
                        }
                    """,
                },
            )
            result = self._run_driver(["check", str(tmp / "src" / "main.nq")])
            self.assertEqual(result.returncode, 1)
            self.assertIn("workspace manifest must declare exactly one source root", result.stdout)

    def test_stage1_driver_loads_locked_local_dependency(self) -> None:
        source = "tests/fixtures/workspace_local_dependency/src/app/main.nq"
        result = self._run_driver(["check", source])
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "")
        facts = self._run_driver(["facts", source, "--format", "v2"])
        self.assertEqual(facts.returncode, 0, facts.stdout + facts.stderr)
        self.assertIn('"name": "reporting::render"', facts.stdout)
        self.assertIn('"name": "reporting::values"', facts.stdout)
        self.assertIn('"target_id": "fn:reporting::render::answer"', facts.stdout)

    def test_stage1_driver_facts_v3_exports_workspace_governance_evidence(self) -> None:
        source = "tests/fixtures/workspace_local_dependency/src/app/main.nq"
        result = self._run_driver(["facts", source, "--format", "v3"])
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        golden = self.root / "tests" / "golden" / "facts" / "workspace-local-dependency-v3.json"
        self.assertEqual(payload, json.loads(golden.read_text(encoding="utf-8")))
        schema = json.loads((self.root / "schemas" / "facts-v3.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(schema["$id"], "https://nauqtype.dev/schemas/facts-v3.schema.json")
        self._assert_schema_shape(payload, schema)
        self.assertEqual(payload["dependencies"][0]["alias"], "reporting")
        self.assertEqual(
            payload["call_graph"][1]["callee"],
            "workspace:tests.reporting::module:render::fn:answer",
        )

    def test_stage1_driver_policy_check_requires_canonical_dependency_targets(self) -> None:
        source = "tests/fixtures/workspace_local_dependency/src/app/main.nq"
        valid = self._run_driver(["policy-check", source, "tests/fixtures/workspace_local_dependency/policy.json"])
        self.assertEqual(valid.returncode, 0, valid.stdout + valid.stderr)
        valid_payload = json.loads(valid.stdout)
        self.assertTrue(valid_payload["ok"])
        self.assertTrue(all(entry["known"] for entry in valid_payload["targets"]))

        alias = self._run_driver(["policy-check", source, "tests/fixtures/workspace_local_dependency/policy_alias_rejected.json"])
        self.assertEqual(alias.returncode, 1)
        alias_payload = json.loads(alias.stdout)
        self.assertEqual(alias_payload["diagnostics"][0]["code"], "NQ-POLICY-007")

        unknown = self._run_driver(["policy-check", source, "tests/fixtures/workspace_local_dependency/policy_unknown_workspace.json"])
        self.assertEqual(unknown.returncode, 1)
        unknown_payload = json.loads(unknown.stdout)
        self.assertEqual(unknown_payload["diagnostics"][0]["code"], "NQ-POLICY-003")

        schema = json.loads((self.root / "schemas" / "policy-check-v1.schema.json").read_text(encoding="utf-8"))
        self._assert_schema_shape(valid_payload, schema)
        self._assert_schema_shape(alias_payload, schema)
        self._assert_schema_shape(unknown_payload, schema)

    def test_stage1_driver_review_tools_keep_manifest_module_identity(self) -> None:
        fixture = self.root / "tests" / "fixtures" / "workspace_local_dependency"
        with tempfile.TemporaryDirectory() as tmp_text:
            tmp = Path(tmp_text)
            before = tmp / "before"
            after = tmp / "after"
            shutil.copytree(fixture, before)
            shutil.copytree(fixture, after)
            after_main = after / "src" / "app" / "main.nq"
            after_main.write_text(after_main.read_text(encoding="utf-8").replace("return reporting::render::answer();", "return 7;"), encoding="utf-8")

            before_source = before / "src" / "app" / "main.nq"
            after_source = after / "src" / "app" / "main.nq"
            review_diff = self._run_driver(["review-diff", str(before_source), str(after_source), "--format", "v2"])
            self.assertEqual(review_diff.returncode, 0, review_diff.stdout + review_diff.stderr)
            review_payload = json.loads(review_diff.stdout)
            self.assertEqual(review_payload["before"]["module"], "app::main")
            self.assertEqual(review_payload["after"]["module"], "app::main")

            report = self._run_driver(["change-report", str(before_source), str(after_source), "--format", "v1"])
            self.assertEqual(report.returncode, 0, report.stdout + report.stderr)
            report_payload = json.loads(report.stdout)
            self.assertEqual(report_payload["before"]["module"], "app::main")
            self.assertEqual(report_payload["after"]["module"], "app::main")
            self.assertGreaterEqual(report_payload["summary"]["changed_functions"], 1)

    def test_stage1_driver_change_report_v2_reports_changed_dependency_callers(self) -> None:
        before = "tests/fixtures/workspace_impact/before/src/app/main.nq"
        after = "tests/fixtures/workspace_impact/after/src/app/main.nq"
        result = self._run_driver(["change-report", before, after, "--format", "v2"])
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        golden = self.root / "tests" / "golden" / "workspace_governance" / "change_report_v2.json"
        self.assertEqual(payload, json.loads(golden.read_text(encoding="utf-8")))
        schema = json.loads((self.root / "schemas" / "change-report-v2.schema.json").read_text(encoding="utf-8"))
        self._assert_schema_shape(payload, schema)

    def test_stage1_driver_proves_organizational_tool_evidence(self) -> None:
        source = "tests/fixtures/organizational_tool/src/app/main.nq"
        before = "tests/fixtures/organizational_tool_before/src/app/main.nq"
        policy = "tests/fixtures/organizational_tool/nauqtype.policy.json"

        check = self._run_driver(["check", source])
        self.assertEqual(check.returncode, 0, check.stdout + check.stderr)
        self.assertEqual(check.stdout, "")
        self.assertEqual(check.stderr, "")

        run = self._run_driver(["run", source])
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertEqual(run.stdout, "operations: ready\n")
        self.assertEqual(run.stderr, "")

        facts = self._run_driver(["facts", source, "--format", "v3"])
        self.assertEqual(facts.returncode, 0, facts.stdout + facts.stderr)
        facts_payload = json.loads(facts.stdout)
        facts_golden = self.root / "tests" / "golden" / "organizational_tool" / "facts_v3.json"
        self.assertEqual(facts_payload, json.loads(facts_golden.read_text(encoding="utf-8")))
        facts_schema = json.loads((self.root / "schemas" / "facts-v3.schema.json").read_text(encoding="utf-8"))
        self._assert_schema_shape(facts_payload, facts_schema)

        policy_result = self._run_driver(["policy-check", source, policy])
        self.assertEqual(policy_result.returncode, 0, policy_result.stdout + policy_result.stderr)
        policy_payload = json.loads(policy_result.stdout)
        policy_golden = self.root / "tests" / "golden" / "organizational_tool" / "policy_check_v1.json"
        self.assertEqual(policy_payload, json.loads(policy_golden.read_text(encoding="utf-8")))
        policy_schema = json.loads((self.root / "schemas" / "policy-check-v1.schema.json").read_text(encoding="utf-8"))
        self._assert_schema_shape(policy_payload, policy_schema)

        report = self._run_driver(["change-report", before, source, "--format", "v2"])
        self.assertEqual(report.returncode, 0, report.stdout + report.stderr)
        report_payload = json.loads(report.stdout)
        report_golden = self.root / "tests" / "golden" / "organizational_tool" / "change_report_v2.json"
        self.assertEqual(report_payload, json.loads(report_golden.read_text(encoding="utf-8")))
        report_schema = json.loads((self.root / "schemas" / "change-report-v2.schema.json").read_text(encoding="utf-8"))
        self._assert_schema_shape(report_payload, report_schema)
        self.assertEqual(report_payload["summary"]["changed_dependencies"], 1)
        self.assertEqual(report_payload["summary"]["impacted_local_callers"], 1)

    def test_stage1_driver_rejects_stale_local_dependency_source_hash(self) -> None:
        fixture = self.root / "tests" / "fixtures" / "workspace_local_dependency"
        with tempfile.TemporaryDirectory() as tmp_text:
            tmp = Path(tmp_text) / "workspace"
            shutil.copytree(fixture, tmp)
            source_file = tmp / "vendor" / "reporting" / "src" / "values.nq"
            source_file.write_text(source_file.read_text(encoding="utf-8") + "\n// stale lock probe\n", encoding="utf-8")
            result = self._run_driver(["check", str(tmp / "src" / "app" / "main.nq")])
            self.assertEqual(result.returncode, 1)
            self.assertIn("workspace dependency source hash is stale: reporting", result.stdout)

    def test_stage1_driver_rejects_mismatched_local_dependency_lock(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_text:
            tmp = Path(tmp_text)
            self._write_project(
                tmp,
                {
                    "nauqtype.workspace.json": """
                        {
                          "version": "workspace/v1",
                          "workspace": { "name": "tests.bad_lock", "source_roots": ["src"] },
                          "dependencies": [
                            { "alias": "reporting", "path": "vendor/reporting", "workspace": "tests.reporting" }
                          ]
                        }
                    """,
                    "nauqtype.workspace.lock.json": """
                        {
                          "version": "workspace-lock/v1",
                          "workspace": "tests.bad_lock",
                          "dependencies": [
                            {
                              "alias": "reporting",
                              "path": "vendor/reporting",
                              "workspace": "tests.wrong",
                              "manifest_sha256": "0000000000000000000000000000000000000000000000000000000000000000",
                              "source_sha256": "0000000000000000000000000000000000000000000000000000000000000000"
                            }
                          ]
                        }
                    """,
                    "src/main.nq": """
                        fn main() -> i32 {
                            return 0;
                        }
                    """,
                },
            )
            result = self._run_driver(["check", str(tmp / "src" / "main.nq")])
            self.assertEqual(result.returncode, 1)
            self.assertIn("workspace dependency lock does not match: reporting", result.stdout)

    def test_stage1_driver_rejects_noncanonical_local_dependency_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_text:
            tmp = Path(tmp_text)
            self._write_project(
                tmp,
                {
                    "nauqtype.workspace.json": """
                        {
                          "version": "workspace/v1",
                          "workspace": { "name": "tests.bad_path", "source_roots": ["src"] },
                          "dependencies": [
                            { "alias": "reporting", "path": "vendor/../reporting", "workspace": "tests.reporting" }
                          ]
                        }
                    """,
                    "nauqtype.workspace.lock.json": """
                        {
                          "version": "workspace-lock/v1",
                          "workspace": "tests.bad_path",
                          "dependencies": [
                            {
                              "alias": "reporting",
                              "path": "vendor/../reporting",
                              "workspace": "tests.reporting",
                              "manifest_sha256": "0000000000000000000000000000000000000000000000000000000000000000",
                              "source_sha256": "0000000000000000000000000000000000000000000000000000000000000000"
                            }
                          ]
                        }
                    """,
                    "src/main.nq": """
                        fn main() -> i32 {
                            return 0;
                        }
                    """,
                },
            )
            result = self._run_driver(["check", str(tmp / "src" / "main.nq")])
            self.assertEqual(result.returncode, 1)
            self.assertIn("workspace dependency requires alias, canonical relative path, and workspace identity", result.stdout)

    def test_stage1_driver_prove_selfhost_writes_summary_without_changing_stdout(self) -> None:
        self._clear_proof_summary()
        result = self._run_driver(["prove-selfhost"], timeout=900)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stdout, "selfhost proof ok\n")
        self.assertEqual(result.stderr, "")
        summary = self._load_proof_summary()
        phases = self._phase_statuses(summary)
        self.assertEqual(summary["command"], "prove-selfhost")
        self.assertTrue(summary["ok"])
        self.assertEqual(summary["failed_phase"], "")
        self.assertEqual(summary["selfhost"]["status"], "passed")
        self.assertEqual(summary["corpus"]["status"], "skipped")
        self.assertEqual(summary["tooling"]["status"], "skipped")
        self.assertEqual(phases["selfhost.copy"], "passed")
        self.assertEqual(phases["selfhost.stage1_emit_c"], "passed")
        self.assertEqual(phases["selfhost.stage2_run"], "passed")
        self.assertEqual(phases["selfhost.structural_c_compare"], "passed")
        self.assertEqual(phases["corpus.emit_c"], "skipped")
        self.assertEqual(phases["tooling.schema_golden"], "skipped")
        self.assertTrue(summary["selfhost"]["artifacts"]["workspace_main"]["hash"].startswith("nqsum:"))

    def test_stage1_driver_prove_corpus_writes_summary_without_changing_stdout(self) -> None:
        self._clear_proof_summary()
        result = self._run_driver(["prove-corpus"], timeout=900)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stdout, "example corpus ok\n")
        self.assertEqual(result.stderr, "")
        summary = self._load_proof_summary()
        phases = self._phase_statuses(summary)
        self.assertEqual(summary["command"], "prove-corpus")
        self.assertTrue(summary["ok"])
        self.assertEqual(summary["failed_phase"], "")
        self.assertEqual(summary["selfhost"]["status"], "skipped")
        self.assertEqual(summary["corpus"]["status"], "passed")
        self.assertEqual(summary["corpus"]["cases"], self._locked_corpus_count())
        self.assertEqual(summary["corpus"]["ids"][0], "break_continue")
        self.assertTrue(summary["corpus"]["artifacts"][0]["emit_c"]["hash"].startswith("nqsum:"))
        self.assertEqual(summary["tooling"]["status"], "skipped")
        self.assertEqual(phases["selfhost.copy"], "skipped")
        self.assertEqual(phases["corpus.emit_c"], "passed")
        self.assertEqual(phases["corpus.build"], "passed")
        self.assertEqual(phases["corpus.run"], "passed")
        self.assertEqual(phases["corpus.structural_c_compare"], "passed")

    def test_stage1_driver_prove_corpus_failure_writes_failed_phase_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            self._clear_proof_summary(tmp)
            result = self._run_driver(["prove-corpus"], cwd=tmp, timeout=240)
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
            summary = self._load_proof_summary(tmp)
            phases = self._phase_statuses(summary)
            self.assertEqual(summary["command"], "prove-corpus")
            self.assertFalse(summary["ok"])
            self.assertEqual(summary["failed_phase"], "corpus.emit_c")
            self.assertEqual(summary["failure"]["phase"], "corpus.emit_c")
            self.assertEqual(summary["failure"]["corpus_id"], "break_continue")
            self.assertEqual(summary["failure"]["artifact_path"], "build/corpus/break_continue/emit.c")
            self.assertEqual(summary["selfhost"]["status"], "skipped")
            self.assertEqual(summary["corpus"]["status"], "failed")
            self.assertEqual(summary["tooling"]["status"], "skipped")
            self.assertEqual(phases["corpus.emit_c"], "failed")
            self.assertEqual(phases["corpus.build"], "skipped")
            self.assertEqual(phases["tooling.schema_golden"], "skipped")

    def test_stage1_driver_locked_corpus_covers_every_runnable_example(self) -> None:
        entries = self._locked_corpus_entries()
        names = [name for name, _ in entries]
        paths = [path for _, path in entries]
        self.assertEqual(len(names), len(set(names)))
        self.assertEqual(len(paths), len(set(paths)))
        for name, path in entries:
            self.assertEqual(name, Path(path).stem)
        self.assertEqual(paths, self._runnable_example_paths())

    def test_stage1_driver_locked_formatter_examples_cover_every_example_file(self) -> None:
        paths = self._locked_formatter_example_paths()
        self.assertEqual(len(paths), len(set(paths)))
        self.assertEqual(paths, self._all_example_paths())

    def test_stage1_driver_formatter_contract_documents_lite_boundaries(self) -> None:
        text = (self.root / "FORMATTER.md").read_text(encoding="utf-8")
        self.assertIn("fmt <source>` writes formatted text to stdout only", text)
        self.assertIn("fmt --check <source>` exits successfully only when the source is already canonical", text)
        self.assertIn("Formatter-lite never mutates files", text)
        self.assertIn("Formatter write mode stays deferred", text)
        self.assertIn("Do not use tabs", text)
        self.assertIn("unbalanced closing braces", text)
        self.assertIn("locked formatter example list in `selfhost/proof.nq` includes it", text)

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

    def test_stage1_driver_review_infers_io_for_file_and_process_builtins(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            self._write_project(
                tmp,
                {
                    "main.nq": """
                    pub fn touch_tooling() -> i32
                    audit {
                        intent("Touch file and process helpers");
                        mutates();
                        effects(io);
                    }
                    {
                        let made = create_dir_all("build");
                        let written = write_file("build/out.txt", "ok");
                        let read = read_file("build/out.txt");
                        let args: list<str> = [];
                        let run = run_process("tool", ref args, ".");
                        return 0;
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
            self.assertEqual(payload["functions"][0]["inferred"]["effects"], ["io"])

    def test_stage1_driver_review_infers_transitive_io_across_imports(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            self._write_project(
                tmp,
                {
                    "main.nq": """
                    use helper;

                    pub fn main() -> i32
                    audit {
                        intent("Load through helper");
                        mutates();
                        effects(io);
                    }
                    {
                        helper();
                        return 0;
                    }
                    """,
                    "helper.nq": """
                    pub fn helper() -> unit
                    audit {
                        intent("Read a file");
                        mutates();
                        effects(io);
                    }
                    {
                        let data = read_file("input.txt");
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
            self.assertEqual(payload["functions"][0]["inferred"]["effects"], ["io"])

    def test_stage1_driver_io_subkind_evidence_is_transitive_and_diffable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            before = tmp / "before"
            after = tmp / "after"
            self._write_project(
                before,
                {
                    "main.nq": """
                    fn direct(path: str) -> unit
                    audit {
                        intent("Read a tooling file.");
                        mutates();
                        effects(io);
                    }
                    {
                        let data = read_file(path);
                        return;
                    }

                    fn through(path: str) -> unit
                    audit {
                        intent("Call the tooling helper.");
                        mutates();
                        effects(io);
                    }
                    {
                        direct(path);
                        return;
                    }

                    fn main() -> i32
                    audit {
                        intent("Run the tooling evidence fixture.");
                        mutates();
                        effects(io);
                    }
                    {
                        through("build/out.txt");
                        return 0;
                    }
                    """,
                },
            )
            self._write_project(
                after,
                {
                    "main.nq": """
                    fn direct(path: str) -> unit
                    audit {
                        intent("Use the supported tooling operations.");
                        mutates();
                        effects(io);
                    }
                    {
                        let made = create_dir_all("build");
                        let written = write_file(path, "ok");
                        let data = read_file(path);
                        let args: list<str> = [];
                        let run = run_process("tool", ref args, ".");
                        return;
                    }

                    fn through(path: str) -> unit
                    audit {
                        intent("Call the tooling helper.");
                        mutates();
                        effects(io);
                    }
                    {
                        direct(path);
                        return;
                    }

                    fn main() -> i32
                    audit {
                        intent("Run the tooling evidence fixture.");
                        mutates();
                        effects(io);
                    }
                    {
                        through("build/out.txt");
                        return 0;
                    }
                    """,
                },
            )

            review = self._run_driver(["review", "main.nq", "--format", "v2"], cwd=after)
            self.assertEqual(review.returncode, 0, review.stdout + review.stderr)
            review_payload = json.loads(review.stdout)
            expected_kinds = ["read", "write", "create_dir", "process"]
            for function_name in ["direct", "through", "main"]:
                function = next(entry for entry in review_payload["functions"] if entry["name"] == function_name)
                self.assertEqual(function["audit"]["effects"], ["io"])
                self.assertEqual(function["inferred"]["effects"], ["io"])
                self.assertEqual(function["inferred"]["io_kinds"], expected_kinds)
            direct = next(entry for entry in review_payload["functions"] if entry["name"] == "direct")
            direct_kinds = {entry["name"]: entry.get("io_kind") for entry in direct["calls"]}
            self.assertEqual(
                {name: direct_kinds[name] for name in ["read_file", "write_file", "create_dir_all", "run_process"]},
                {"read_file": "read", "write_file": "write", "create_dir_all": "create_dir", "run_process": "process"},
            )
            self._assert_schema_shape(
                review_payload,
                json.loads((self.root / "schemas" / "review-v2.schema.json").read_text(encoding="utf-8")),
            )

            facts = self._run_driver(["facts", "main.nq", "--format", "v2"], cwd=after)
            self.assertEqual(facts.returncode, 0, facts.stdout + facts.stderr)
            facts_payload = json.loads(facts.stdout)
            fact_kinds = {entry["callee"]: entry.get("io_kind") for entry in facts_payload["call_graph"]}
            self.assertEqual(
                {name: fact_kinds[f"builtin:{name}"] for name in ["read_file", "write_file", "create_dir_all", "run_process"]},
                {"read_file": "read", "write_file": "write", "create_dir_all": "create_dir", "run_process": "process"},
            )
            self._assert_schema_shape(
                facts_payload,
                json.loads((self.root / "schemas" / "facts-v2.schema.json").read_text(encoding="utf-8")),
            )

            review_diff = self._run_driver(["review-diff", str(before / "main.nq"), str(after / "main.nq"), "--format", "v2"])
            self.assertEqual(review_diff.returncode, 0, review_diff.stdout + review_diff.stderr)
            review_diff_payload = json.loads(review_diff.stdout)
            self.assertEqual(review_diff_payload["changes"]["changed_functions"], ["fn:main::direct", "fn:main::through", "fn:main::main"])

            report = self._run_driver(["change-report", str(before / "main.nq"), str(after / "main.nq"), "--format", "v1"])
            self.assertEqual(report.returncode, 0, report.stdout + report.stderr)
            report_payload = json.loads(report.stdout)
            self.assertEqual(report_payload["changes"]["changed_functions"], ["fn:main::direct", "fn:main::through", "fn:main::main"])

    def test_stage1_driver_review_requires_declared_io_effect(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            self._write_project(
                tmp,
                {
                    "main.nq": """
                    fn load() -> unit
                    audit {
                        intent("Read a file");
                        mutates();
                        effects();
                    }
                    {
                        let data = read_file("input.txt");
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
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(result.stdout, "")
            self.assertIn("error[NQ-CONTRACT-008]", result.stderr)
            self.assertIn("`io`", result.stderr)

    def test_stage1_driver_review_warns_for_overdeclared_io_effect(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            self._write_project(
                tmp,
                {
                    "main.nq": """
                    pub fn pure() -> i32
                    audit {
                        intent("Return a pure value");
                        mutates();
                        effects(io);
                    }
                    {
                        return 1;
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
            self.assertIn("warning[NQ-CONTRACT-009]", result.stderr)
            self.assertIn("`io`", result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["functions"][0]["audit"]["effects"], ["io"])
            self.assertEqual(payload["functions"][0]["inferred"]["effects"], [])

    def test_stage1_driver_question_propagates_result_error_explicitly(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            self._write_project(
                tmp,
                {
                    "main.nq": """
                    fn load_count() -> result<i32, io_err>
                    audit {
                        intent("Load a file and return its length.");
                        mutates();
                        effects(io);
                        propagates(io_err);
                    }
                    {
                        let data = read_file("input.txt")?;
                        return Ok(str_len(data));
                    }

                    fn main() -> i32
                    audit {
                        intent("Run propagation sample.");
                        mutates();
                        effects(print, io);
                    }
                    {
                        let value = load_count();
                        match value {
                            Ok(count) => {
                                print_line("ok");
                            },
                            Err(err) => {
                                print_line(io_err_text(err));
                            },
                        }
                        return 0;
                    }
                    """,
                },
            )
            check = self._run_driver(["check", "main.nq"], cwd=tmp)
            self.assertEqual(check.returncode, 0, check.stdout + check.stderr)
            review = self._run_driver(["review", "main.nq"], cwd=tmp)
            self.assertEqual(review.returncode, 0, review.stdout + review.stderr)
            self.assertEqual(review.stderr, "")

    def test_stage1_driver_m50_try_expression_captures_error_at_visible_boundary(self) -> None:
        source = self.root / "examples" / "try_expression.nq"
        result = self._run_driver(["run", str(source)])
        self.assertEqual(result.returncode, 7, result.stdout + result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "")

        with tempfile.TemporaryDirectory() as tmp_dir:
            output = Path(tmp_dir) / "try_expression.c"
            emitted = self._run_driver(["emit-c", str(source), "-o", str(output)])
            self.assertEqual(emitted.returncode, 0, emitted.stdout + emitted.stderr)
            c_text = output.read_text(encoding="utf-8")
            self.assertIn("nq_try_result_", c_text)
            self.assertIn("goto nq_try_end_", c_text)
            self.assertIn("NQ_Result__i32__io_err_Tag_Err", c_text)

    def test_stage1_driver_m50_try_expression_exports_local_propagation_evidence(self) -> None:
        source = self.root / "examples" / "try_expression.nq"
        facts_result = self._run_driver(["facts", str(source), "--format", "v2"])
        self.assertEqual(facts_result.returncode, 0, facts_result.stdout + facts_result.stderr)
        facts = json.loads(facts_result.stdout)
        site = next(entry for entry in facts["references"] if entry["kind"] == "propagation_site")
        self.assertEqual(site["name"], "io_err")
        self.assertEqual(site["context"], "read_source")
        self.assertEqual(site["evidence"], "builtin")

        review_result = self._run_driver(["review", str(source), "--format", "v2"])
        self.assertEqual(review_result.returncode, 0, review_result.stdout + review_result.stderr)
        review = json.loads(review_result.stdout)
        function = next(entry for entry in review["functions"] if entry["name"] == "main")
        self.assertEqual(function["audit"]["propagates"], [])
        self.assertEqual(function["inferred"]["propagates"], [])
        self.assertEqual(review["propagation_sites"][0]["context"], "read_source")

    def test_stage1_driver_m50_try_context_change_is_supervised(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            before = tmp / "before"
            after = tmp / "after"
            template = """
                fn main() -> i32
                audit {
                    intent("Capture one local read failure");
                    mutates();
                    effects(io);
                    propagates();
                }
                {
                    let outcome: result<str, io_err> = try {
                        read_file("missing.txt")?[%s]
                    };
                    match outcome {
                        Ok(_) => { return 0; },
                        Err(_) => { return 1; },
                    }
                }
            """
            self._write_project(before, {"main.nq": template % "config_read"})
            self._write_project(after, {"main.nq": template % "cache_read"})

            review_diff = self._run_driver(
                ["review-diff", str(before / "main.nq"), str(after / "main.nq"), "--format", "v2"]
            )
            self.assertEqual(review_diff.returncode, 0, review_diff.stdout + review_diff.stderr)
            review_payload = json.loads(review_diff.stdout)
            self.assertEqual(review_payload["changes"]["changed_functions"], ["fn:main::main"])

            report = self._run_driver(
                ["change-report", str(before / "main.nq"), str(after / "main.nq"), "--format", "v1"]
            )
            self.assertEqual(report.returncode, 0, report.stdout + report.stderr)
            report_payload = json.loads(report.stdout)
            self.assertEqual(report_payload["changes"]["changed_functions"], ["fn:main::main"])

    def test_stage1_driver_m50_try_expression_sequences_multiple_nested_sites(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            self._write_project(
                tmp,
                {
                    "main.nq": """
                    fn first() -> result<i32, io_err> {
                        return Ok(2);
                    }

                    fn second(value: i32) -> result<i32, io_err> {
                        return Ok(value + 3);
                    }

                    fn main() -> i32 {
                        let measured: result<i32, io_err> = try {
                            second(first()?[first_value])?[second_value]
                        };
                        match measured {
                            Ok(value) => { return value; },
                            Err(_) => { return 99; },
                        }
                    }
                    """,
                },
            )
            result = self._run_driver(["run", str(tmp / "main.nq")])
            self.assertEqual(result.returncode, 5, result.stdout + result.stderr)

            facts_result = self._run_driver(["facts", str(tmp / "main.nq"), "--format", "v2"])
            self.assertEqual(facts_result.returncode, 0, facts_result.stdout + facts_result.stderr)
            facts = json.loads(facts_result.stdout)
            contexts = [
                entry["context"]
                for entry in facts["references"]
                if entry["kind"] == "propagation_site"
            ]
            self.assertEqual(contexts, ["first_value", "second_value"])

    def test_stage1_driver_m50_try_expression_rejects_ambiguous_or_mismatched_boundaries(self) -> None:
        cases = {
            "unannotated": (
                "let measured = try { read_file(\"missing\")? }; return 0;",
                "NQ-TRY-001",
                "",
            ),
            "non_result": (
                "let measured: result<i32, io_err> = try { value()? }; return 0;",
                "NQ-PROPAGATE-001",
                "fn value() -> i32 { return 1; }",
            ),
            "error_mismatch": (
                "let measured: result<i32, io_err> = try { parse_value()? }; return 0;",
                "NQ-PROPAGATE-003",
                "enum ParseErr { Bad } fn parse_value() -> result<i32, ParseErr> { return Err(Bad); }",
            ),
            "success_mismatch": (
                "let measured: result<str, io_err> = try { str_len(read_file(\"missing\")?) }; return 0;",
                "NQ-TRY-003",
                "",
            ),
            "non_call_operand": (
                "let ready: result<i32, io_err> = Ok(1); let measured: result<i32, io_err> = try { ready? }; return 0;",
                "NQ-TRY-002",
                "",
            ),
            "short_circuit": (
                "let measured: result<bool, io_err> = try { false and ready()? }; return 0;",
                "NQ-TRY-004",
                "fn ready() -> result<bool, io_err> { return Ok(true); }",
            ),
            "match_success": (
                "let measured: result<i32, io_err> = try { match Some(1) { Some(value) => value, None => 0 } }; return 0;",
                "NQ-TRY-005",
                "",
            ),
            "unsupported_placement": (
                "return try { 1 };",
                "NQ-TRY-006",
                "",
            ),
        }
        for name, (body, expected, prelude) in cases.items():
            with self.subTest(name=name):
                with tempfile.TemporaryDirectory() as tmp_dir:
                    tmp = Path(tmp_dir)
                    self._write_project(
                        tmp,
                        {
                            "main.nq": f"""
                            {prelude}
                            fn main() -> i32 {{
                                {body}
                            }}
                            """,
                        },
                    )
                    result = self._run_driver(["check", str(tmp / "main.nq")])
                    combined = result.stdout + result.stderr
                    self.assertNotEqual(result.returncode, 0, combined)
                    self.assertIn(expected, combined)

    def test_stage1_driver_question_exports_propagation_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            before = tmp / "before"
            after = tmp / "after"
            self._write_project(
                before,
                {
                    "main.nq": """
                    fn load_count() -> result<i32, io_err>
                    audit {
                        intent("Return a fixed count.");
                        mutates();
                        effects();
                    }
                    {
                        return Ok(1);
                    }
                    """,
                },
            )
            self._write_project(
                after,
                {
                    "main.nq": """
                    fn load_count() -> result<i32, io_err>
                    audit {
                        intent("Load a file and return its length.");
                        mutates();
                        effects(io);
                        propagates(io_err);
                    }
                    {
                        let data = read_file("input.txt")?;
                        return Ok(str_len(data));
                    }

                    fn main() -> i32
                    audit {
                        intent("Provide a checked entrypoint.");
                        mutates();
                        effects();
                    }
                    {
                        return 0;
                    }
                    """,
                },
            )

            facts = self._run_driver(["facts", "main.nq", "--format", "v2"], cwd=after)
            self.assertEqual(facts.returncode, 0, facts.stdout + facts.stderr)
            facts_payload = json.loads(facts.stdout)
            self.assertTrue(
                any(
                    entry["kind"] == "propagation_site"
                    and entry["target_id"] == "builtin-type:io_err"
                    and entry["evidence"] == "builtin"
                    for entry in facts_payload["references"]
                )
            )

            review = self._run_driver(["review", "main.nq", "--format", "v2"], cwd=after)
            self.assertEqual(review.returncode, 0, review.stdout + review.stderr)
            review_payload = json.loads(review.stdout)
            load_fn = next(entry for entry in review_payload["functions"] if entry["name"] == "load_count")
            self.assertEqual(load_fn["audit"]["propagates"], ["io_err"])
            self.assertEqual(load_fn["inferred"]["propagates"], ["io_err"])
            self.assertEqual(len(review_payload["propagation_sites"]), 1)
            self.assertEqual(review_payload["propagation_sites"][0]["target_id"], "builtin-type:io_err")

            report = self._run_driver(["change-report", str(before / "main.nq"), str(after / "main.nq"), "--format", "v1"])
            self.assertEqual(report.returncode, 0, report.stdout + report.stderr)
            report_payload = json.loads(report.stdout)
            self.assertEqual(report_payload["summary"]["added_propagates"], 1)
            self.assertEqual(report_payload["changes"]["added_propagates"], ["fn:main::load_count -> io_err"])

    def test_stage1_driver_propagation_context_label_flows_to_evidence_and_diffs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            before = tmp / "before"
            after = tmp / "after"
            self._write_project(
                before,
                {
                    "main.nq": """
                    fn load_count() -> result<i32, io_err>
                    audit {
                        intent("Load a file and return its length.");
                        mutates();
                        effects(io);
                        propagates(io_err);
                    }
                    {
                        let data = read_file("input.txt")?;
                        return Ok(str_len(data));
                    }
                    """,
                },
            )
            self._write_project(
                after,
                {
                    "main.nq": """
                    fn load_count() -> result<i32, io_err>
                    audit {
                        intent("Load a file and return its length.");
                        mutates();
                        effects(io);
                        propagates(io_err);
                    }
                    {
                        let data = read_file("input.txt")?[config_read];
                        return Ok(str_len(data));
                    }

                    fn main() -> i32
                    audit {
                        intent("Provide a checked entrypoint.");
                        mutates();
                        effects();
                    }
                    {
                        return 0;
                    }
                    """,
                },
            )

            check = self._run_driver(["check", "main.nq"], cwd=after)
            self.assertEqual(check.returncode, 0, check.stdout + check.stderr)

            facts = self._run_driver(["facts", "main.nq", "--format", "v2"], cwd=after)
            self.assertEqual(facts.returncode, 0, facts.stdout + facts.stderr)
            facts_payload = json.loads(facts.stdout)
            propagation_ref = next(entry for entry in facts_payload["references"] if entry["kind"] == "propagation_site")
            self.assertEqual(propagation_ref["context"], "config_read")
            self._assert_schema_shape(
                facts_payload,
                json.loads((self.root / "schemas" / "facts-v2.schema.json").read_text(encoding="utf-8")),
            )

            review = self._run_driver(["review", "main.nq", "--format", "v2"], cwd=after)
            self.assertEqual(review.returncode, 0, review.stdout + review.stderr)
            review_payload = json.loads(review.stdout)
            self.assertEqual(review_payload["propagation_sites"][0]["context"], "config_read")
            self._assert_schema_shape(
                review_payload,
                json.loads((self.root / "schemas" / "review-v2.schema.json").read_text(encoding="utf-8")),
            )

            review_diff = self._run_driver(["review-diff", str(before / "main.nq"), str(after / "main.nq"), "--format", "v2"])
            self.assertEqual(review_diff.returncode, 0, review_diff.stdout + review_diff.stderr)
            review_diff_payload = json.loads(review_diff.stdout)
            self.assertEqual(review_diff_payload["changes"]["changed_functions"], ["fn:main::load_count"])

            report = self._run_driver(["change-report", str(before / "main.nq"), str(after / "main.nq"), "--format", "v1"])
            self.assertEqual(report.returncode, 0, report.stdout + report.stderr)
            report_payload = json.loads(report.stdout)
            self.assertEqual(report_payload["changes"]["changed_functions"], ["fn:main::load_count"])

    def test_stage1_driver_change_report_rejects_missing_propagation_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            before = tmp / "before"
            after = tmp / "after"
            self._write_project(
                before,
                {
                    "main.nq": """
                    fn load_count() -> result<i32, io_err>
                    audit {
                        intent("Return a fixed count.");
                        mutates();
                        effects();
                    }
                    {
                        return Ok(1);
                    }
                    """,
                },
            )
            self._write_project(
                after,
                {
                    "main.nq": """
                    fn load_count() -> result<i32, io_err>
                    audit {
                        intent("Load a file and return its length.");
                        mutates();
                        effects(io);
                    }
                    {
                        let data = read_file("input.txt")?;
                        return Ok(str_len(data));
                    }
                    """,
                },
            )

            report = self._run_driver(["change-report", str(before / "main.nq"), str(after / "main.nq"), "--format", "v1"])
            self.assertNotEqual(report.returncode, 0, report.stdout + report.stderr)
            self.assertIn("NQ-PROPAGATE-004", report.stderr)
            payload = json.loads(report.stdout)
            self.assertFalse(payload["ok"])
            self.assertEqual(payload["diagnostics"][0]["code"], "NQ-CHANGE-001")
            self.assertEqual(payload["summary"]["added_propagates"], 0)

            diff = self._run_driver(["review-diff", str(before / "main.nq"), str(after / "main.nq")])
            self.assertNotEqual(diff.returncode, 0, diff.stdout + diff.stderr)
            self.assertIn("NQ-PROPAGATE-004", diff.stderr)

    def test_stage1_driver_question_rejects_non_result_expression(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            self._write_project(
                tmp,
                {
                    "main.nq": """
                    fn bad() -> result<i32, io_err>
                    audit {
                        intent("Reject non-result propagation.");
                        mutates();
                        effects();
                        propagates(io_err);
                    }
                    {
                        let value = 1?;
                        return Ok(value);
                    }
                    """,
                },
            )
            result = self._run_driver(["check", "main.nq"], cwd=tmp)
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("NQ-PROPAGATE-001", result.stdout + result.stderr)

    def test_stage1_driver_question_requires_result_return_function(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            self._write_project(
                tmp,
                {
                    "main.nq": """
                    fn bad() -> i32
                    audit {
                        intent("Reject propagation outside result functions.");
                        mutates();
                        effects(io);
                        propagates(io_err);
                    }
                    {
                        let data = read_file("input.txt")?;
                        return str_len(data);
                    }
                    """,
                },
            )
            result = self._run_driver(["check", "main.nq"], cwd=tmp)
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("NQ-PROPAGATE-002", result.stdout + result.stderr)

    def test_stage1_driver_question_requires_exact_error_type_match(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            self._write_project(
                tmp,
                {
                    "main.nq": """
                    enum app_err {
                        Bad(unit),
                    }

                    fn bad() -> result<i32, app_err>
                    audit {
                        intent("Reject hidden error mapping.");
                        mutates();
                        effects(io);
                        propagates(io_err);
                    }
                    {
                        let data = read_file("input.txt")?;
                        return Ok(str_len(data));
                    }
                    """,
                },
            )
            result = self._run_driver(["check", "main.nq"], cwd=tmp)
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("NQ-PROPAGATE-003", result.stdout + result.stderr)
            self.assertIn("let-else", result.stdout + result.stderr)

    def test_stage1_driver_question_is_statement_boundary_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            self._write_project(
                tmp,
                {
                    "main.nq": """
                    fn bad() -> result<i32, io_err>
                    audit {
                        intent("Reject expression-position propagation.");
                        mutates();
                        effects(io);
                        propagates(io_err);
                    }
                    {
                        return Ok(str_len(read_file("input.txt")?));
                    }
                    """,
                },
            )
            result = self._run_driver(["check", "main.nq"], cwd=tmp)
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("?", result.stdout + result.stderr)

    def test_stage1_driver_review_requires_declared_propagation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            self._write_project(
                tmp,
                {
                    "main.nq": """
                    fn load_count() -> result<i32, io_err>
                    audit {
                        intent("Load a file and return its length.");
                        mutates();
                        effects(io);
                    }
                    {
                        let data = read_file("input.txt")?;
                        return Ok(str_len(data));
                    }
                    """,
                },
            )
            result = self._run_driver(["review", "main.nq"], cwd=tmp)
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(result.stdout, "")
            self.assertIn("NQ-PROPAGATE-004", result.stderr)
            self.assertIn("io_err", result.stderr)

    def test_stage1_driver_review_warns_for_overdeclared_propagation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            self._write_project(
                tmp,
                {
                    "main.nq": """
                    fn pure() -> result<i32, io_err>
                    audit {
                        intent("Return a pure result.");
                        mutates();
                        effects();
                        propagates(io_err);
                    }
                    {
                        return Ok(1);
                    }
                    """,
                },
            )
            result = self._run_driver(["review", "main.nq"], cwd=tmp)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("warning[NQ-PROPAGATE-005]", result.stderr)
            self.assertIn("io_err", result.stderr)

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
        self.assertTrue(
            any(
                entry["kind"] == "field_init"
                and entry["target_id"] == "field:helper::Box::value"
                and entry["evidence"] == "checked"
                for entry in payload["references"]
            )
        )
        self.assertTrue(
            any(
                entry["kind"] == "field_access"
                and entry["target_id"] == "field:helper::Box::value"
                and entry["evidence"] == "checked"
                for entry in payload["references"]
            )
        )
        schema = json.loads((self.root / "schemas" / "facts-v2.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(schema["$id"], "https://nauqtype.dev/schemas/facts-v2.schema.json")
        self.assertEqual(schema["properties"]["version"]["const"], 2)
        self._assert_schema_shape(payload, schema)

    def test_stage1_driver_facts_v2_exports_named_argument_label_references(self) -> None:
        fixture = self.root / "tests" / "fixtures" / "facts" / "named_args_main.nq"
        golden = self.root / "tests" / "golden" / "facts" / "named-args-v2.json"
        result = self._run_driver(["facts", str(fixture), "--format", "v2"])
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stderr, "")
        payload = json.loads(result.stdout)
        self.assertEqual(payload, json.loads(golden.read_text(encoding="utf-8")))
        labels = [entry for entry in payload["references"] if entry["kind"] == "argument_label"]
        self.assertEqual(len(labels), 5)
        self.assertTrue(
            any(
                entry["name"] == "scale"
                and entry["target_id"] == "binding:fn:named_args_helper::combine:1:scale@38"
                and entry["evidence"] == "checked"
                for entry in labels
            )
        )
        schema = json.loads((self.root / "schemas" / "facts-v2.schema.json").read_text(encoding="utf-8"))
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

    def test_stage1_driver_change_report_goldens_policy_and_schema(self) -> None:
        before = self.root / "tests" / "fixtures" / "review_diff" / "before" / "main.nq"
        after = self.root / "tests" / "fixtures" / "review_diff" / "after" / "main.nq"
        schema = json.loads((self.root / "schemas" / "change-report-v1.schema.json").read_text(encoding="utf-8"))
        result = self._run_driver(["change-report", str(before), str(after), "--format", "v1"])
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stderr, "")
        payload = json.loads(result.stdout)
        self.assertEqual(payload, json.loads((self.root / "tests" / "golden" / "review" / "change_report_v1.json").read_text(encoding="utf-8")))
        self.assertEqual(payload["command"], "change-report")
        self.assertEqual(payload["evidence"]["comparison"], "semantic-identities")
        self.assertEqual(payload["changes"]["changed_functions"], ["fn:main::helper", "fn:main::main"])
        self._assert_schema_shape(payload, schema)

        policy_result = self._run_driver(
            [
                "change-report",
                str(before),
                str(after),
                "--policy",
                "tests/fixtures/policy/change_report_policy.json",
                "--format",
                "v1",
            ]
        )
        self.assertEqual(policy_result.returncode, 0, policy_result.stdout + policy_result.stderr)
        self.assertEqual(policy_result.stderr, "")
        policy_payload = json.loads(policy_result.stdout)
        self.assertEqual(
            policy_payload,
            json.loads((self.root / "tests" / "golden" / "review" / "change_report_policy_v1.json").read_text(encoding="utf-8")),
        )
        self.assertEqual(policy_payload["evidence"]["policy"], "checked")
        self.assertEqual(policy_payload["policy"]["targets"], 1)
        self._assert_schema_shape(policy_payload, schema)

    def test_stage1_driver_change_report_reports_failing_input_as_json(self) -> None:
        after = self.root / "tests" / "fixtures" / "review_diff" / "after" / "main.nq"
        result = self._run_driver(["change-report", str(self.root / "tests" / "fixtures" / "missing_before.nq"), str(after), "--format", "v1"])
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stderr, "")
        payload = json.loads(result.stdout)
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["before"]["evidence"], "unavailable")
        self.assertEqual(payload["diagnostics"][0]["code"], "NQ-CHANGE-001")
        self._assert_schema_shape(
            payload,
            json.loads((self.root / "schemas" / "change-report-v1.schema.json").read_text(encoding="utf-8")),
        )

    def test_stage1_driver_supervised_workflow_goldens_and_schema_contracts(self) -> None:
        before = "tests/fixtures/supervised_workflow/before/main.nq"
        after = "tests/fixtures/supervised_workflow/after/main.nq"
        policy = "tests/fixtures/supervised_workflow/policy.json"
        golden_root = self.root / "tests" / "golden" / "supervised_workflow"

        check = self._run_driver(["check", after])
        self.assertEqual(check.returncode, 0, check.stdout + check.stderr)
        self.assertEqual(check.stdout, "")
        self.assertEqual(check.stderr, "")

        original_after = (self.root / after).read_text(encoding="utf-8")
        cases = [
            (
                "facts v2",
                ["facts", after, "--format", "v2"],
                golden_root / "facts_v2.json",
                self.root / "schemas" / "facts-v2.schema.json",
                "https://nauqtype.dev/schemas/facts-v2.schema.json",
                2,
                "facts",
            ),
            (
                "review v2",
                ["review", after, "--format", "v2"],
                golden_root / "review_v2.json",
                self.root / "schemas" / "review-v2.schema.json",
                "https://nauqtype.dev/schemas/review-v2.schema.json",
                2,
                "review",
            ),
            (
                "review-diff v2",
                ["review-diff", before, after, "--format", "v2"],
                golden_root / "review_diff_v2.json",
                self.root / "schemas" / "review-diff-v2.schema.json",
                "https://nauqtype.dev/schemas/review-diff-v2.schema.json",
                2,
                "review-diff",
            ),
            (
                "change-report policy v1",
                ["change-report", before, after, "--policy", policy, "--format", "v1"],
                golden_root / "change_report_policy_v1.json",
                self.root / "schemas" / "change-report-v1.schema.json",
                "https://nauqtype.dev/schemas/change-report-v1.schema.json",
                1,
                "change-report",
            ),
            (
                "policy-check v1",
                ["policy-check", after, policy],
                golden_root / "policy_check_v1.json",
                self.root / "schemas" / "policy-check-v1.schema.json",
                "https://nauqtype.dev/schemas/policy-check-v1.schema.json",
                1,
                "policy-check",
            ),
            (
                "refactor-rename v1",
                ["refactor-rename", after, "binding:fn:main::apply:1:bonus@25", "extra"],
                golden_root / "refactor_rename_v1.json",
                self.root / "schemas" / "refactor-rename-v1.schema.json",
                "https://nauqtype.dev/schemas/refactor-rename-v1.schema.json",
                1,
                "refactor-rename",
            ),
        ]

        for label, args, golden_path, schema_path, schema_id, version, command in cases:
            with self.subTest(label=label):
                result = self._run_driver(args)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertEqual(result.stderr, "")
                payload = json.loads(result.stdout)
                self.assertEqual(payload, json.loads(golden_path.read_text(encoding="utf-8")))
                schema = json.loads(schema_path.read_text(encoding="utf-8"))
                self.assertEqual(schema["$id"], schema_id)
                self.assertEqual(schema["properties"]["version"]["const"], version)
                self.assertEqual(schema["properties"]["command"]["const"], command)
                self._assert_schema_shape(payload, schema)

        policy_schema = json.loads((self.root / "schemas" / "nauqtype.policy-v1.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(policy_schema["$id"], "https://nauqtype.dev/schemas/nauqtype.policy-v1.schema.json")
        self.assertEqual(policy_schema["properties"]["version"]["const"], 1)
        self._assert_schema_shape(json.loads((self.root / policy).read_text(encoding="utf-8")), policy_schema)
        self.assertEqual((self.root / after).read_text(encoding="utf-8"), original_after)

    def test_stage1_driver_m28_evidence_parity_goldens_and_schema_contracts(self) -> None:
        before = "tests/fixtures/evidence_parity/before/main.nq"
        after = "tests/fixtures/evidence_parity/after/main.nq"
        policy = "tests/fixtures/evidence_parity/policy.json"
        golden_root = self.root / "tests" / "golden" / "evidence_parity"

        check = self._run_driver(["check", after])
        self.assertEqual(check.returncode, 0, check.stdout + check.stderr)
        self.assertEqual(check.stdout, "")
        self.assertEqual(check.stderr, "")

        run = self._run_driver(["run", after])
        self.assertEqual(run.returncode, 13, run.stdout + run.stderr)
        self.assertEqual(run.stdout, "")
        self.assertEqual(run.stderr, "")

        original_after = (self.root / after).read_text(encoding="utf-8")
        cases = [
            (
                "facts v2",
                ["facts", after, "--format", "v2"],
                golden_root / "facts_v2.json",
                self.root / "schemas" / "facts-v2.schema.json",
                "https://nauqtype.dev/schemas/facts-v2.schema.json",
                2,
                "facts",
            ),
            (
                "review v2",
                ["review", after, "--format", "v2"],
                golden_root / "review_v2.json",
                self.root / "schemas" / "review-v2.schema.json",
                "https://nauqtype.dev/schemas/review-v2.schema.json",
                2,
                "review",
            ),
            (
                "review-diff v2",
                ["review-diff", before, after, "--format", "v2"],
                golden_root / "review_diff_v2.json",
                self.root / "schemas" / "review-diff-v2.schema.json",
                "https://nauqtype.dev/schemas/review-diff-v2.schema.json",
                2,
                "review-diff",
            ),
            (
                "change-report policy v1",
                ["change-report", before, after, "--policy", policy, "--format", "v1"],
                golden_root / "change_report_policy_v1.json",
                self.root / "schemas" / "change-report-v1.schema.json",
                "https://nauqtype.dev/schemas/change-report-v1.schema.json",
                1,
                "change-report",
            ),
            (
                "policy-check v1",
                ["policy-check", after, policy],
                golden_root / "policy_check_v1.json",
                self.root / "schemas" / "policy-check-v1.schema.json",
                "https://nauqtype.dev/schemas/policy-check-v1.schema.json",
                1,
                "policy-check",
            ),
            (
                "refactor field v1",
                ["refactor-rename", after, "field:helper::Box::value", "amount"],
                golden_root / "refactor_rename_field_v1.json",
                self.root / "schemas" / "refactor-rename-v1.schema.json",
                "https://nauqtype.dev/schemas/refactor-rename-v1.schema.json",
                1,
                "refactor-rename",
            ),
            (
                "refactor variant v1",
                ["refactor-rename", after, "variant:helper::Choice::Use", "Keep"],
                golden_root / "refactor_rename_variant_v1.json",
                self.root / "schemas" / "refactor-rename-v1.schema.json",
                "https://nauqtype.dev/schemas/refactor-rename-v1.schema.json",
                1,
                "refactor-rename",
            ),
            (
                "refactor const v1",
                ["refactor-rename", after, "const:helper::base_score", "starting_score"],
                golden_root / "refactor_rename_const_v1.json",
                self.root / "schemas" / "refactor-rename-v1.schema.json",
                "https://nauqtype.dev/schemas/refactor-rename-v1.schema.json",
                1,
                "refactor-rename",
            ),
        ]

        payloads: dict[str, dict] = {}
        for label, args, golden_path, schema_path, schema_id, version, command in cases:
            with self.subTest(label=label):
                result = self._run_driver(args)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertEqual(result.stderr, "")
                self.assertNotIn("unknown:", result.stdout)
                payload = json.loads(result.stdout)
                payloads[label] = payload
                self.assertEqual(payload, json.loads(golden_path.read_text(encoding="utf-8")))
                schema = json.loads(schema_path.read_text(encoding="utf-8"))
                self.assertEqual(schema["$id"], schema_id)
                self.assertEqual(schema["properties"]["version"]["const"], version)
                self.assertEqual(schema["properties"]["command"]["const"], command)
                self._assert_schema_shape(payload, schema)

        facts_refs = {(entry["kind"], entry["target_id"]) for entry in payloads["facts v2"]["references"]}
        self.assertIn(("argument_label", "binding:fn:helper::boost:1:scale@152"), facts_refs)
        self.assertIn(("call", "variant:helper::Choice::Use"), facts_refs)
        self.assertIn(("pattern_ctor", "variant:helper::Choice::Use"), facts_refs)
        self.assertIn(("record_update_inherit", "field:helper::Box::label"), facts_refs)
        self.assertIn(("propagation_site", "builtin-type:io_err"), facts_refs)
        self.assertIn("fn:main::score -> variant:helper::Choice::Use", payloads["change-report policy v1"]["changes"]["added_call_edges"])

        policy_schema = json.loads((self.root / "schemas" / "nauqtype.policy-v1.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(policy_schema["$id"], "https://nauqtype.dev/schemas/nauqtype.policy-v1.schema.json")
        self.assertEqual(policy_schema["properties"]["version"]["const"], 1)
        self._assert_schema_shape(json.loads((self.root / policy).read_text(encoding="utf-8")), policy_schema)
        self.assertEqual((self.root / after).read_text(encoding="utf-8"), original_after)

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

    def test_stage1_driver_refactor_rename_plans_field_definition_and_uses(self) -> None:
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
            before = (tmp / "main.nq").read_text(encoding="utf-8")
            result = self._run_driver(["refactor-rename", str(tmp / "main.nq"), "field:main::Box::value", "amount"])
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            payload = json.loads(result.stdout)
            self.assertTrue(payload["ok"])
            self.assertEqual([edit["kind"] for edit in payload["edits"]], ["definition", "reference", "reference"])
            self.assertEqual([edit["old_text"] for edit in payload["edits"]], ["value", "value", "value"])
            self.assertTrue(all(edit["replacement"] == "amount" for edit in payload["edits"]))
            self.assertTrue(all(edit["target_id"] == "field:main::Box::value" for edit in payload["edits"]))
            self.assertEqual((tmp / "main.nq").read_text(encoding="utf-8"), before)

    def test_stage1_driver_field_assignment_facts_and_refactor_plan(self) -> None:
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
                        let mut box = Box { value: 1 };
                        box.value = box.value + 1;
                        return box.value;
                    }
                    """,
                },
            )
            source = tmp / "main.nq"
            before = source.read_text(encoding="utf-8")

            facts = self._run_driver(["facts", str(source), "--format", "v2"])
            self.assertEqual(facts.returncode, 0, facts.stdout + facts.stderr)
            references = json.loads(facts.stdout)["references"]
            self.assertTrue(
                any(
                    ref["kind"] == "field_assign"
                    and ref["target_id"] == "field:main::Box::value"
                    for ref in references
                )
            )

            result = self._run_driver(["refactor-rename", str(source), "field:main::Box::value", "amount"])
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            payload = json.loads(result.stdout)
            self.assertTrue(payload["ok"])
            self.assertTrue(any(edit["kind"] == "reference" and edit["old_text"] == "value" for edit in payload["edits"]))
            self.assertTrue(all(edit["replacement"] == "amount" for edit in payload["edits"]))
            self.assertEqual(source.read_text(encoding="utf-8"), before)

    def test_stage1_driver_refactor_rename_updates_named_argument_labels(self) -> None:
        fixture = self.root / "tests" / "fixtures" / "facts" / "named_args_main.nq"
        before_main = fixture.read_text(encoding="utf-8")
        before_helper = (self.root / "tests" / "fixtures" / "facts" / "named_args_helper.nq").read_text(encoding="utf-8")

        imported = self._run_driver(
            ["refactor-rename", str(fixture), "binding:fn:named_args_helper::combine:1:scale@38", "multiplier"]
        )
        self.assertEqual(imported.returncode, 0, imported.stdout + imported.stderr)
        imported_payload = json.loads(imported.stdout)
        self.assertTrue(imported_payload["ok"])
        self.assertEqual([edit["kind"] for edit in imported_payload["edits"]], ["definition", "reference", "reference"])
        self.assertEqual(imported_payload["edits"][2]["span"]["start"], 176)
        self.assertEqual(imported_payload["edits"][2]["old_text"], "scale")
        self.assertEqual(imported_payload["edits"][2]["replacement"], "multiplier")

        local = self._run_driver(
            ["refactor-rename", str(fixture), "binding:fn:named_args_main::local:1:left@33", "first_value"]
        )
        self.assertEqual(local.returncode, 0, local.stdout + local.stderr)
        local_payload = json.loads(local.stdout)
        self.assertTrue(local_payload["ok"])
        self.assertEqual([edit["kind"] for edit in local_payload["edits"]], ["definition", "reference", "reference"])
        self.assertEqual(local_payload["edits"][2]["span"]["start"], 147)
        self.assertEqual(local_payload["edits"][2]["old_text"], "left")
        self.assertEqual(local_payload["edits"][2]["replacement"], "first_value")

        self.assertEqual(fixture.read_text(encoding="utf-8"), before_main)
        self.assertEqual((self.root / "tests" / "fixtures" / "facts" / "named_args_helper.nq").read_text(encoding="utf-8"), before_helper)

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
            self.assertTrue((tmp / "build" / "main").exists())

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

    def test_stage1_driver_batch_b_named_arguments_example_runs(self) -> None:
        result = self._run_driver(["run", str(self.root / "examples" / "named_arguments.nq")])
        self.assertEqual(result.returncode, 42, result.stdout + result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "")

    def test_stage1_driver_batch_b_qualified_calls_example_runs(self) -> None:
        result = self._run_driver(["run", str(self.root / "examples" / "qualified_calls.nq")])
        self.assertEqual(result.returncode, 42, result.stdout + result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "")

    def test_stage1_driver_batch_c_qualified_data_names_example_runs(self) -> None:
        result = self._run_driver(["run", str(self.root / "examples" / "qualified_data_names.nq")])
        self.assertEqual(result.returncode, 42, result.stdout + result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "")
        facts = self._run_driver(["facts", str(self.root / "examples" / "qualified_data_names.nq"), "--format", "v2"])
        self.assertEqual(facts.returncode, 0, facts.stdout + facts.stderr)
        payload = json.loads(facts.stdout)
        refs = {(entry["kind"], entry["target_id"]) for entry in payload["references"]}
        self.assertIn(("struct_type", "type:qualified_data_helper::Box"), refs)
        self.assertIn(("call", "variant:qualified_data_helper::Choice::Score"), refs)
        self.assertIn(("pattern_ctor", "variant:qualified_data_helper::Choice::Empty"), refs)

    def test_stage1_driver_m22_refactor_rename_plans_qualified_variant_constructor(self) -> None:
        main_source = self.root / "examples" / "qualified_data_names.nq"
        helper_source = self.root / "examples" / "qualified_data_helper.nq"
        before_main = main_source.read_text(encoding="utf-8")
        before_helper = helper_source.read_text(encoding="utf-8")

        result = self._run_driver(
            ["refactor-rename", str(main_source), "variant:qualified_data_helper::Choice::Score", "Points"]
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["ok"])
        self.assertEqual([edit["kind"] for edit in payload["edits"]], ["definition", "reference", "reference"])
        self.assertTrue(all(edit["old_text"] == "Score" for edit in payload["edits"]))
        self.assertTrue(all(edit["replacement"] == "Points" for edit in payload["edits"]))
        for edit in payload["edits"]:
            path = self.root / edit["path"]
            source_text = path.read_text(encoding="utf-8")
            self.assertEqual(source_text[edit["span"]["start"]:edit["span"]["end"]], "Score")
        self.assertEqual(main_source.read_text(encoding="utf-8"), before_main)
        self.assertEqual(helper_source.read_text(encoding="utf-8"), before_helper)

    def test_stage1_driver_batch_c_qualified_data_names_require_direct_import(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            self._write_project(
                tmp,
                {
                    "main.nq": """
                    fn main() -> i32 {
                        let box = helper::Box { value: 1 };
                        return box.value;
                    }
                    """,
                    "helper.nq": """
                    pub type Box {
                        value: i32,
                    }
                    """,
                },
            )
            result = self._run_driver(["check", str(tmp / "main.nq")])
            combined = result.stdout + result.stderr
            self.assertNotEqual(result.returncode, 0, combined)
            self.assertIn("unknown qualified struct literal type", combined)

    def test_stage1_driver_batch_d_record_update_example_runs(self) -> None:
        result = self._run_driver(["run", str(self.root / "examples" / "record_update.nq")])
        self.assertEqual(result.returncode, 42, result.stdout + result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "")

    def test_stage1_driver_m47_composite_field_generics_compile_and_borrow_the_field(self) -> None:
        source = self.root / "examples" / "composite_field_backend.nq"
        result = self._run_driver(["run", str(source)])
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "")

        with tempfile.TemporaryDirectory() as tmp_dir:
            output = Path(tmp_dir) / "composite.c"
            emitted = self._run_driver(["emit-c", str(source), "-o", str(output)])
            self.assertEqual(emitted.returncode, 0, emitted.stdout + emitted.stderr)
            c_text = output.read_text(encoding="utf-8")
            bundle_at = c_text.index("typedef struct NQ_composite_field_backend__Bundle")
            for declaration in (
                "typedef struct NQ_Option__bool",
                "typedef struct NQ_Option__composite_field_backend__Marker",
                "typedef struct NQ_Result__composite_field_backend__Marker__io_err",
                "typedef struct NQ_List__composite_field_backend__Marker",
            ):
                self.assertLess(c_text.index(declaration), bundle_at)
            self.assertRegex(
                c_text,
                r"values_len\(&\(\(\(nqv_\d+_bundle\)\)\.values\)\);",
            )

    def test_stage1_driver_m48_list_for_runs_and_emits_single_evaluation_loop(self) -> None:
        source = self.root / "examples" / "for_list.nq"
        result = self._run_driver(["run", str(source)])
        self.assertEqual(result.returncode, 35, result.stdout + result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "")

        with tempfile.TemporaryDirectory() as tmp_dir:
            output = Path(tmp_dir) / "for_list.c"
            emitted = self._run_driver(["emit-c", str(source), "-o", str(output)])
            self.assertEqual(emitted.returncode, 0, emitted.stdout + emitted.stderr)
            c_text = output.read_text(encoding="utf-8")
            self.assertEqual(c_text.count("NQ_List__i32 nq_for_items_"), 1)
            self.assertRegex(c_text, r"for \(int32_t nq_for_index_\d+ = 0;")
            self.assertRegex(c_text, r"nq_list__i32_get\(&nq_for_items_\d+, nq_for_index_\d+\)\.data\.Some\._0")

    def test_stage1_driver_m48_list_for_exports_stable_binding_evidence(self) -> None:
        source = self.root / "examples" / "for_list.nq"
        result = self._run_driver(["facts", str(source), "--format", "v2"])
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        loop_definition = next(
            entry
            for entry in payload["definitions"]
            if entry["kind"] == "local" and entry["name"] == "value"
        )
        self.assertGreater(loop_definition["scope_id"], 1)
        self.assertEqual(loop_definition["evidence"], "checked")
        self.assertTrue(
            any(
                entry["name"] == "value"
                and entry["target_id"] == loop_definition["id"]
                and entry["evidence"] == "checked"
                for entry in payload["references"]
            )
        )

    def test_stage1_driver_m48_list_for_rejects_non_list_and_immutable_assignment(self) -> None:
        cases = {
            "non_list": (
                "for value in 42 { return value; } return 0;",
                "`for` iterable must have type `list<T>`",
            ),
            "immutable": (
                "let values: list<i32> = [1]; for value in values { value = 2; } return 0;",
                "`for` loop bindings are immutable",
            ),
            "out_of_scope": (
                "let values: list<i32> = [1]; for value in values { } return value;",
                "unknown name in function body",
            ),
        }
        for name, (body, expected) in cases.items():
            with self.subTest(name=name):
                with tempfile.TemporaryDirectory() as tmp_dir:
                    tmp = Path(tmp_dir)
                    self._write_project(
                        tmp,
                        {
                            "main.nq": f"""
                            fn main() -> i32 {{
                                {body}
                            }}
                            """,
                        },
                    )
                    result = self._run_driver(["check", str(tmp / "main.nq")])
                    combined = result.stdout + result.stderr
                    self.assertNotEqual(result.returncode, 0, combined)
                    self.assertIn(expected, combined)

    def test_stage1_driver_batch_d_record_update_facts_v2_matches_golden(self) -> None:
        result = self._run_driver(["facts", str(self.root / "examples" / "record_update.nq"), "--format", "v2"])
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        golden = json.loads((self.root / "tests" / "golden" / "facts" / "record_update_v2.json").read_text(encoding="utf-8"))
        self.assertEqual(payload, golden)
        self._assert_schema_shape(
            payload,
            json.loads((self.root / "schemas" / "facts-v2.schema.json").read_text(encoding="utf-8")),
        )

    def test_stage1_driver_m22_record_update_facts_expose_override_and_inherit(self) -> None:
        source = self.root / "examples" / "record_update.nq"
        text = source.read_text(encoding="utf-8")
        override_at = text.index("x: next_x")
        base_at = text.index("from point") + len("from ")

        result = self._run_driver(["facts", str(source), "--format", "v2"])
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        refs = json.loads(result.stdout)["references"]

        self.assertTrue(
            any(
                ref["kind"] == "field_init"
                and ref["target_id"] == "field:record_update::Point::x"
                and ref["span"]["start"] == override_at
                for ref in refs
            )
        )
        self.assertTrue(
            any(
                ref["kind"] == "record_update_inherit"
                and ref["target_id"] == "field:record_update::Point::y"
                and ref["span"]["start"] == base_at
                for ref in refs
            )
        )
        self.assertFalse(
            any(
                ref["kind"] == "field_access"
                and ref["from"] == "fn:record_update::shift_x"
                and ref["target_id"] == "field:record_update::Point::y"
                for ref in refs
            )
        )

    def test_stage1_driver_m22_record_update_refactor_skips_inherited_fields(self) -> None:
        source = self.root / "examples" / "record_update.nq"
        original = source.read_text(encoding="utf-8")
        base_at = original.index("from point") + len("from ")

        result = self._run_driver(["refactor-rename", str(source), "field:record_update::Point::y", "height"])
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["ok"])
        self.assertEqual([edit["kind"] for edit in payload["edits"]], ["definition", "reference", "reference"])
        self.assertNotIn(base_at, [edit["span"]["start"] for edit in payload["edits"]])
        for edit in payload["edits"]:
            path = self.root / edit["path"]
            source_text = path.read_text(encoding="utf-8")
            start = edit["span"]["start"]
            end = edit["span"]["end"]
            self.assertEqual(source_text[start:end], edit["old_text"])
            self.assertEqual(edit["old_text"], "y")
            self.assertEqual(edit["replacement"], "height")
        self.assertEqual(source.read_text(encoding="utf-8"), original)

    def test_stage1_driver_batch_d_record_update_rejects_non_name_base(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            self._write_project(
                tmp,
                {
                    "main.nq": """
                    type Point {
                        x: i32,
                        y: i32,
                    }

                    fn make_point() -> Point {
                        return Point { x: 1, y: 2 };
                    }

                    fn main() -> i32 {
                        let changed = Point { from make_point(), x: 3 };
                        return changed.x;
                    }
                    """,
                },
            )
            result = self._run_driver(["check", str(tmp / "main.nq")])
            combined = result.stdout + result.stderr
            self.assertNotEqual(result.returncode, 0, combined)
            self.assertIn("record update base must be a simple local, parameter, pattern binding, or visible const name", combined)

    def test_stage1_driver_batch_d_record_update_reuses_existing_field_move_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            self._write_project(
                tmp,
                {
                    "main.nq": """
                    type Bucket {
                        items: list<i32>,
                        count: i32,
                    }

                    fn main() -> i32 {
                        let mut items: list<i32> = list();
                        list_push(mutref items, 1);
                        let bucket = Bucket { items: items, count: 1 };
                        let changed = Bucket { from bucket, count: 2 };
                        return changed.count;
                    }
                    """,
                },
            )
            result = self._run_driver(["check", str(tmp / "main.nq")])
            combined = result.stdout + result.stderr
            self.assertNotEqual(result.returncode, 0, combined)
            self.assertIn("moving out of fields is not supported in v0.1", combined)

    def test_stage1_driver_batch_b_break_continue_example_runs(self) -> None:
        result = self._run_driver(["run", str(self.root / "examples" / "break_continue.nq")])
        self.assertEqual(result.returncode, 42, result.stdout + result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "")

    def test_stage1_driver_batch_b_named_argument_validation(self) -> None:
        invalid_cases = {
            "mixed": (
                "return add(1, right: 2);",
                "cannot mix positional and named arguments",
            ),
            "duplicate": (
                "return add(left: 1, left: 2);",
                "duplicate named argument",
            ),
            "unknown": (
                "return add(left: 1, extra: 2);",
                "unknown named argument",
            ),
            "missing": (
                "return add(left: 1);",
                "missing named argument for parameter",
            ),
            "constructor": (
                "let maybe: option<i32> = Some(value: 1); return 0;",
                "named arguments are only supported for function calls",
            ),
        }
        for name, (body, expected) in invalid_cases.items():
            with self.subTest(name=name):
                with tempfile.TemporaryDirectory() as tmp_dir:
                    tmp = Path(tmp_dir)
                    self._write_project(
                        tmp,
                        {
                            "main.nq": f"""
                            fn add(left: i32, right: i32) -> i32 {{
                                return left + right;
                            }}

                            fn main() -> i32 {{
                                {body}
                            }}
                            """,
                        },
                    )
                    result = self._run_driver(["check", str(tmp / "main.nq")])
                    combined = result.stdout + result.stderr
                    self.assertNotEqual(result.returncode, 0, combined)
                    self.assertIn(expected, combined)

    def test_stage1_driver_batch_b_qualified_call_requires_direct_import(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            self._write_project(
                tmp,
                {
                    "main.nq": """
                    fn main() -> i32 {
                        return helper::add_pair(left: 40, right: 2);
                    }
                    """,
                    "helper.nq": """
                    pub fn add_pair(left: i32, right: i32) -> i32 {
                        return left + right;
                    }
                    """,
                },
            )
            result = self._run_driver(["check", str(tmp / "main.nq")])
            combined = result.stdout + result.stderr
            self.assertNotEqual(result.returncode, 0, combined)
            self.assertIn("unknown qualified function or data constructor target", combined)

    def test_stage1_driver_batch_b_break_continue_restricted_to_while(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            self._write_project(
                tmp,
                {
                    "main.nq": """
                    fn main() -> i32 {
                        break;
                        return 0;
                    }
                    """,
                },
            )
            result = self._run_driver(["check", str(tmp / "main.nq")])
            combined = result.stdout + result.stderr
            self.assertNotEqual(result.returncode, 0, combined)
            self.assertIn("`break` is only valid inside a loop", combined)

    def test_stage1_driver_batch_b_facts_see_qualified_call_target(self) -> None:
        result = self._run_driver(["facts", str(self.root / "examples" / "qualified_calls.nq"), "--format", "v2"])
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        self.assertTrue(
            any(
                edge["caller"] == "fn:qualified_calls::main"
                and edge["callee"] == "fn:batch_b_helper::add_pair"
                for edge in payload["call_graph"]
            )
        )

    def test_stage1_driver_m27_qualified_variant_match_expression_is_exhaustive(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            self._write_project(
                tmp,
                {
                    "helper.nq": """
                    pub enum Outcome {
                        Keep(i32),
                        Boost(i32),
                        Stop(i32),
                    }

                    pub fn decide(value: i32) -> Outcome {
                        if value > 10 {
                            return Boost(value);
                        } else {
                            if value == 0 {
                                return Stop(value);
                            } else {
                                return Keep(value);
                            }
                        }
                    }
                    """,
                    "main.nq": """
                    use helper;

                    fn main() -> i32 {
                        let outcome = helper::decide(2);
                        let score = match outcome {
                            helper::Keep(value) => value,
                            helper::Boost(value) => value + 10,
                            helper::Stop(value) => value + 20,
                        };
                        return score;
                    }
                    """,
                },
            )
            result = self._run_driver(["check", "main.nq"], cwd=tmp)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(result.stdout, "")
            self.assertNotIn("match expression must be exhaustive", result.stdout + result.stderr)

    def test_stage1_driver_m36_nested_patterns_run_and_export_constructor_evidence(self) -> None:
        source = self.root / "examples" / "nested_patterns.nq"
        checked = self._run_driver(["check", str(source)])
        self.assertEqual(checked.returncode, 0, checked.stdout + checked.stderr)
        self.assertEqual(checked.stdout, "")
        self.assertEqual(checked.stderr, "")

        facts = self._run_driver(["facts", str(source), "--format", "v2"])
        self.assertEqual(facts.returncode, 0, facts.stdout + facts.stderr)
        payload = json.loads(facts.stdout)
        pattern_refs = [
            ref
            for ref in payload["references"]
            if ref["kind"] == "pattern_ctor" and ref["name"] == "Some" and ref["evidence"] == "builtin"
        ]
        self.assertEqual(len(pattern_refs), 2)

        result = self._run_driver(["run", str(source)])
        self.assertEqual(result.returncode, 42, result.stdout + result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "")

    def test_stage1_driver_m27_nested_qualified_call_argument_stays_positional(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            self._write_project(
                tmp,
                {
                    "helper.nq": """
                    pub fn make(value: i32) -> result<i32, str> {
                        return Ok(value);
                    }
                    """,
                    "main.nq": """
                    use helper;

                    fn unwrap(value: result<i32, str>) -> i32 {
                        let Ok(score) = value else {
                            return 0;
                        };
                        return score;
                    }

                    fn main() -> i32 {
                        return unwrap(helper::make(7));
                    }
                    """,
                },
            )
            result = self._run_driver(["check", "main.nq"], cwd=tmp)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertNotIn("unknown named argument", result.stdout + result.stderr)
            self.assertNotIn("missing named argument", result.stdout + result.stderr)
            self.assertNotIn("stage1 limitation", result.stdout + result.stderr)

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

    def test_stage1_driver_fmt_ignores_braces_inside_line_comments(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            source = tmp / "main.nq"
            source.write_text(
                "fn main() -> i32 { // }}} should not close the function\n"
                "return 0; // {{{ should not keep the function open\n"
                "}\n",
                encoding="utf-8",
                newline="\n",
            )

            result = self._run_driver(["fmt", str(source)])

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(
                result.stdout,
                "fn main() -> i32 { // }}} should not close the function\n"
                "    return 0; // {{{ should not keep the function open\n"
                "}\n",
            )
            self.assertEqual(result.stderr, "")

    def test_stage1_driver_fmt_keeps_canonical_closing_forms(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            source = tmp / "main.nq"
            source.write_text(
                "fn main() -> i32 {\n"
                "if true {\n"
                "return 0;\n"
                "} else {\n"
                "let value: option<i32> = None;\n"
                "match value {\n"
                "Some(n) => {\n"
                "return n;\n"
                "},\n"
                "None => {\n"
                "return 1;\n"
                "},\n"
                "}\n"
                "}\n"
                "}\n",
                encoding="utf-8",
                newline="\n",
            )

            result = self._run_driver(["fmt", str(source)])

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(
                result.stdout,
                "fn main() -> i32 {\n"
                "    if true {\n"
                "        return 0;\n"
                "    } else {\n"
                "        let value: option<i32> = None;\n"
                "        match value {\n"
                "            Some(n) => {\n"
                "                return n;\n"
                "            },\n"
                "            None => {\n"
                "                return 1;\n"
                "            },\n"
                "        }\n"
                "    }\n"
                "}\n",
            )
            self.assertEqual(result.stderr, "")

    def test_stage1_driver_fmt_normalizes_input_newlines(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            crlf_source = tmp / "crlf.nq"
            crlf_source.write_bytes(b"fn main() -> i32 {\r\nreturn 0;\r\n}\r\n")
            no_final_newline_source = tmp / "no_final_newline.nq"
            no_final_newline_source.write_text("fn main() -> i32 {\nreturn 0;\n}", encoding="utf-8", newline="\n")

            crlf = self._run_driver(["fmt", str(crlf_source)])
            self.assertEqual(crlf.returncode, 0, crlf.stdout + crlf.stderr)
            self.assertEqual(crlf.stdout, "fn main() -> i32 {\n    return 0;\n}\n")
            self.assertEqual(crlf.stderr, "")

            no_final_newline = self._run_driver(["fmt", str(no_final_newline_source)])
            self.assertEqual(no_final_newline.returncode, 0, no_final_newline.stdout + no_final_newline.stderr)
            self.assertEqual(no_final_newline.stdout, "fn main() -> i32 {\n    return 0;\n}\n")
            self.assertEqual(no_final_newline.stderr, "")

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
        for source in sorted((self.root / "examples").glob("*.nq")):
            with self.subTest(name=source.name):
                result = self._run_driver(["fmt", "--check", str(source)])
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertEqual(result.stdout, "")
                self.assertEqual(result.stderr, "")


if __name__ == "__main__":
    unittest.main()
