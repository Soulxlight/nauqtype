from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from tests.test_support import ROOT


class M54LibraryDependencyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root = ROOT
        cls.driver = ROOT / "bin" / "nauqc"
        cls.fixture = ROOT / "tests" / "fixtures" / "m54_library_dependency"
        cls.app_source = cls.fixture / "src" / "app" / "main.nq"
        cls.library_source = cls.fixture / "vendor" / "std" / "src" / "status.nq"

    def _run(self, args: list[str], *, timeout: int = 120) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [str(self.driver), *args],
            cwd=self.root,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

    def _assert_clean(self, result: subprocess.CompletedProcess[str]) -> None:
        output = result.stdout + result.stderr
        self.assertEqual(result.returncode, 0, output)
        self.assertNotIn("stage1 limitation", output)
        self.assertNotIn("stage1 c error", output)

    def test_library_module_checks_without_an_entrypoint(self) -> None:
        result = self._run(["check", str(self.library_source)])
        self._assert_clean(result)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "")

    def test_locked_std_dependency_exports_checked_authority_evidence(self) -> None:
        checked = self._run(["check", str(self.app_source)])
        self._assert_clean(checked)
        self.assertEqual(checked.stdout, "")
        self.assertEqual(checked.stderr, "")

        facts = self._run(["facts", str(self.app_source), "--format", "v3"])
        self._assert_clean(facts)
        facts_payload = json.loads(facts.stdout)
        self.assertEqual(facts_payload["version"], 3)
        self.assertEqual(facts_payload["command"], "facts")
        self.assertEqual(facts_payload["identity_scheme"], "nauqtype.workspace.v1")
        self.assertEqual(facts_payload["workspace"]["name"], "tests.m54.library_app")
        self.assertEqual(len(facts_payload["dependencies"]), 1)
        dependency = facts_payload["dependencies"][0]
        lock_payload = json.loads(
            (self.fixture / "nauqtype.workspace.lock.json").read_text(encoding="utf-8")
        )
        self.assertEqual(dependency, lock_payload["dependencies"][0])
        self.assertEqual(dependency["alias"], "std")
        self.assertEqual(dependency["workspace"], "nauqtype.std")
        self.assertEqual(dependency["path"], "vendor/std")
        self.assertRegex(dependency["manifest_sha256"], r"^[0-9a-f]{64}$")
        self.assertRegex(dependency["source_sha256"], r"^[0-9a-f]{64}$")
        self.assertIn(
            {
                "id": "workspace:nauqtype.std::module:status",
                "workspace": "nauqtype.std",
                "module": "status",
                "source_module": "std::status",
                "evidence": "checked",
            },
            facts_payload["modules"],
        )
        exports = {entry["id"]: entry for entry in facts_payload["exports"]}
        self.assertEqual(exports["workspace:nauqtype.std::module:status::type:NqStatus"]["evidence"], "checked")
        self.assertEqual(exports["workspace:nauqtype.std::module:status::fn:ready_status"]["evidence"], "checked")
        call_edges = facts_payload["call_graph"]
        self.assertTrue(
            any(
                edge["callee"] == "workspace:nauqtype.std::module:status::fn:ready_status"
                and edge["evidence"] == "checked"
                for edge in call_edges
            ),
            call_edges,
        )
        self.assertTrue(
            any(
                edge["callee"] == "builtin:print_line" and edge["evidence"] == "builtin"
                for edge in call_edges
            ),
            call_edges,
        )

        review = self._run(["review", str(self.app_source), "--format", "v2"])
        self._assert_clean(review)
        review_payload = json.loads(review.stdout)
        self.assertEqual(review_payload["version"], 2)
        self.assertEqual(review_payload["command"], "review")
        functions = {entry["qualified_name"]: entry for entry in review_payload["functions"]}
        library_function = functions["std::status::ready_status"]
        self.assertTrue(library_function["public"])
        self.assertEqual(library_function["evidence"], {"audit": "declared", "inferred": "checked"})
        app_function = functions["app::main::main"]
        self.assertEqual(app_function["audit"]["effects"], ["print"])
        self.assertEqual(app_function["inferred"]["effects"], ["print"])
        self.assertTrue(
            any(
                reference["target_id"] == "fn:std::status::ready_status"
                and reference["evidence"] == "checked"
                for reference in review_payload["references"]
            ),
            review_payload["references"],
        )
        self.assertTrue(
            any(
                reference["target_id"] == "builtin:print_line"
                and reference["evidence"] == "builtin"
                for reference in review_payload["references"]
            ),
            review_payload["references"],
        )

    def test_locked_std_dependency_builds_and_runs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_text:
            workspace = Path(tmp_text) / "workspace"
            shutil.copytree(self.fixture, workspace)
            app_source = workspace / "src" / "app" / "main.nq"
            executable = Path(tmp_text) / "m54-library-app"
            built = self._run(["build", str(app_source), "-o", str(executable)])
            self._assert_clean(built)
            self.assertTrue(executable.is_file())

            ran = self._run(["run", str(app_source)])
            self._assert_clean(ran)
            self.assertEqual(ran.stdout, "m54 library ready\n")
            self.assertEqual(ran.stderr, "")


if __name__ == "__main__":
    unittest.main()
