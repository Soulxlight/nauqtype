from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from tests.test_support import ROOT


class VerificationScriptTests(unittest.TestCase):
    def _script(self, name: str) -> Path:
        return ROOT / "scripts" / name

    def test_verification_scripts_are_shell_valid(self) -> None:
        for name in [
            "check_fast.sh",
            "check_milestone.sh",
            "check_seed_bootstrap.sh",
            "check_linux_alpha.sh",
            "check_organizational_alpha.sh",
            "performance_budgets.sh",
            "run_budgeted.sh",
            "check_m53_ownership.sh",
            "run_stress_leg.sh",
            "stage1_cache.sh",
        ]:
            result = subprocess.run(
                ["bash", "-n", str(self._script(name))],
                cwd=ROOT,
                capture_output=True,
                text=True,
                timeout=30,
            )
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_verification_scripts_document_reuse_contracts(self) -> None:
        expected = {
            "check_fast.sh": "active Nauqtype-owned",
            "check_milestone.sh": "without repeating the same selfhost proof",
            "check_seed_bootstrap.sh": "--reuse-stage1",
            "check_linux_alpha.sh": "--reuse-stage1",
            "check_organizational_alpha.sh": "outside the",
            "run_budgeted.sh": "GNU timeout and /usr/bin/time",
            "check_m53_ownership.sh": "address and leak sanitizers",
            "run_stress_leg.sh": "--release-root",
            "stage1_cache.sh": "missing, stale, or modified",
        }
        for name, expected_text in expected.items():
            result = subprocess.run(
                ["bash", str(self._script(name)), "--help"],
                cwd=ROOT,
                capture_output=True,
                text=True,
                timeout=30,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(expected_text, result.stdout)

    def _run_budgeted(
        self,
        result_path: Path,
        *,
        wall_seconds: int,
        rss_kib: int,
        command: list[str],
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                str(self._script("run_budgeted.sh")),
                "--id",
                "synthetic.phase",
                "--wall-seconds",
                str(wall_seconds),
                "--rss-kib",
                str(rss_kib),
                "--result",
                str(result_path),
                "--",
                *command,
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=15,
        )

    def test_budget_runner_records_success_without_hiding_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            result_path = Path(temp_dir) / "result.json"
            result = self._run_budgeted(
                result_path,
                wall_seconds=5,
                rss_kib=262144,
                command=["sh", "-c", "printf budget-ok"],
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, "budget-ok")
            evidence = json.loads(result_path.read_text(encoding="utf-8"))
            self.assertEqual(evidence["version"], 1)
            self.assertEqual(evidence["status"], "ok")
            self.assertEqual(evidence["failure"], "none")
            self.assertLessEqual(evidence["peak_rss_kib"], 262144)

    def test_budget_runner_fails_closed_on_wall_time(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            result_path = Path(temp_dir) / "result.json"
            result = self._run_budgeted(
                result_path,
                wall_seconds=1,
                rss_kib=262144,
                command=["sh", "-c", "sleep 2"],
            )
            self.assertEqual(result.returncode, 124, result.stderr)
            evidence = json.loads(result_path.read_text(encoding="utf-8"))
            self.assertEqual(evidence["status"], "failed")
            self.assertEqual(evidence["failure"], "wall_time")
            self.assertIn("ran longer than 1s", result.stderr)

    def test_budget_runner_fails_closed_on_peak_rss(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            result_path = Path(temp_dir) / "result.json"
            result = self._run_budgeted(
                result_path,
                wall_seconds=5,
                rss_kib=1024,
                command=[
                    "dd",
                    "if=/dev/zero",
                    "of=/dev/null",
                    "bs=16M",
                    "count=1",
                    "status=none",
                ],
            )
            self.assertEqual(result.returncode, 97, result.stderr)
            evidence = json.loads(result_path.read_text(encoding="utf-8"))
            self.assertEqual(evidence["status"], "failed")
            self.assertEqual(evidence["failure"], "peak_rss")
            self.assertGreater(evidence["peak_rss_kib"], 1024)

    def test_milestone_gate_has_one_budgeted_invocation_per_phase(self) -> None:
        milestone = self._script("check_milestone.sh").read_text(encoding="utf-8")
        for phase_id in [
            "seed_bootstrap",
            "stage1.driver",
            "proof",
            "linux_alpha",
            "stress_leg",
            "owned_tests",
            "ownership_sanitizers",
        ]:
            self.assertEqual(milestone.count(f"run_phase {phase_id} "), 1)
        self.assertIn("performance-summary.json", milestone)
        self.assertLess(
            milestone.index("run_phase stage1.driver"),
            milestone.index("run_phase seed_bootstrap"),
        )
        self.assertIn(
            "run_phase seed_bootstrap scripts/check_seed_bootstrap.sh --reuse-stage1",
            milestone,
        )

        full_workflow = (ROOT / ".github" / "workflows" / "linux-alpha.yml").read_text(
            encoding="utf-8"
        )
        quick_workflow = (ROOT / ".github" / "workflows" / "quick.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("run: scripts/check_milestone.sh", full_workflow)
        self.assertNotIn("pull_request:", full_workflow)
        self.assertIn("workflow_dispatch:", full_workflow)
        self.assertIn("schedule:", full_workflow)
        self.assertIn("tags: ['v*']", full_workflow)
        self.assertIn("name: quick", quick_workflow)
        self.assertIn("pull_request:", quick_workflow)
        self.assertIn("cancel-in-progress: true", quick_workflow)
        self.assertIn("run: scripts/check_fast.sh", quick_workflow)
        self.assertNotIn("check_milestone.sh", quick_workflow)

    def test_stage1_cache_binds_inputs_and_built_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "scripts").mkdir()
            (root / "selfhost" / "build").mkdir(parents=True)
            (root / "bootstrap" / "seed").mkdir(parents=True)
            (root / "build" / "seed").mkdir(parents=True)
            cache_script = root / "scripts" / "stage1_cache.sh"
            shutil.copy2(self._script("stage1_cache.sh"), cache_script)

            (root / "VERSION").write_text("0.test\n", encoding="utf-8")
            (root / "selfhost" / "main.nq").write_text(
                "fn main() -> i32 { return 0; }\n", encoding="utf-8"
            )
            for name in [
                "SHA256SUMS",
                "manifest.json",
                "nauqc-seed.c",
                "runtime.c",
                "runtime.h",
            ]:
                (root / "bootstrap" / "seed" / name).write_text(
                    f"{name}\n", encoding="utf-8"
                )
            (root / "scripts" / "bootstrap_seed.sh").write_text(
                "bootstrap\n", encoding="utf-8"
            )
            (root / "scripts" / "build_stage1_from_seed.sh").write_text(
                "build\n", encoding="utf-8"
            )
            stage1_c = root / "build" / "seed" / "stage1.c"
            stage1_c.write_text("generated C\n", encoding="utf-8")
            stage1_exe = root / "selfhost" / "build" / "nauqc"
            stage1_exe.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            stage1_exe.chmod(0o755)

            env = {
                **os.environ,
                "NAUQTYPE_REPO_ROOT": "/definitely/not/the/cache/root",
            }

            def run_cache(command: str) -> subprocess.CompletedProcess[str]:
                return subprocess.run(
                    [str(cache_script), command],
                    cwd=root,
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=30,
                )

            recorded = run_cache("record")
            self.assertEqual(recorded.returncode, 0, recorded.stderr)
            self.assertEqual(run_cache("check").returncode, 0)
            fingerprint = run_cache("fingerprint")
            self.assertEqual(fingerprint.returncode, 0, fingerprint.stderr)
            self.assertRegex(fingerprint.stdout.strip(), r"^[0-9a-f]{64}$")

            source = root / "selfhost" / "main.nq"
            original_source = source.read_text(encoding="utf-8")
            source.write_text(original_source + "// stale\n", encoding="utf-8")
            self.assertNotEqual(run_cache("check").returncode, 0)
            source.write_text(original_source, encoding="utf-8")
            self.assertEqual(run_cache("record").returncode, 0)

            cache_manifest = root / "build" / "seed" / "stage1-cache-v1.txt"
            manifest_before_missing_input = cache_manifest.read_text(encoding="utf-8")
            seed_manifest = root / "bootstrap" / "seed" / "manifest.json"
            seed_manifest_text = seed_manifest.read_text(encoding="utf-8")
            seed_manifest.unlink()
            missing_record = run_cache("record")
            self.assertNotEqual(missing_record.returncode, 0)
            self.assertIn("input is missing", missing_record.stderr)
            self.assertNotEqual(run_cache("check").returncode, 0)
            self.assertEqual(
                cache_manifest.read_text(encoding="utf-8"),
                manifest_before_missing_input,
            )
            seed_manifest.write_text(seed_manifest_text, encoding="utf-8")
            self.assertEqual(run_cache("record").returncode, 0)

            stage1_c.write_text("modified generated C\n", encoding="utf-8")
            self.assertNotEqual(run_cache("check").returncode, 0)
            stage1_c.write_text("generated C\n", encoding="utf-8")
            self.assertEqual(run_cache("record").returncode, 0)

            stage1_exe.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
            stage1_exe.chmod(0o755)
            required = run_cache("require")
            self.assertNotEqual(required.returncode, 0)
            self.assertIn("missing, stale, or modified", required.stderr)

    def test_stage1_build_publishes_artifacts_before_cache_marker(self) -> None:
        build = self._script("build_stage1_from_seed.sh").read_text(encoding="utf-8")
        self.assertIn("temp_build_dir=", build)
        self.assertLess(build.index('mv -f "$temp_stage1_c"'), build.index("stage1_cache.sh\" record"))
        self.assertLess(build.index('mv -f "$temp_stage1_exe"'), build.index("stage1_cache.sh\" record"))

    def test_corpus_uses_one_direct_compile_per_case_and_three_route_smokes(self) -> None:
        proof = (ROOT / "selfhost" / "proof.nq").read_text(encoding="utf-8")
        route_body = re.search(
            r"fn corpus_routes_driver_commands\(case_name: str\) -> bool \{(?P<body>.*?)\n\}",
            proof,
            re.S,
        )
        self.assertIsNotNone(route_body)
        route_ids = re.findall(r'case_name == "([^"]+)"', route_body.group("body"))
        self.assertEqual(route_ids, ["hello", "multi_file_main", "m53_ownership_values"])
        corpus_body = re.search(
            r"fn run_corpus_case\(.*?\) -> bool \{(?P<body>.*?)\n\}\n\nfn run_example_corpus_inner",
            proof,
            re.S,
        )
        self.assertIsNotNone(corpus_body)
        body = corpus_body.group("body")
        self.assertEqual(body.count("run_driver_emit_c("), 1)
        self.assertEqual(body.count("compile_host_c_program("), 1)
        self.assertEqual(body.count("run_corpus_program("), 1)
        self.assertEqual(body.count("run_driver_build("), 1)
        self.assertEqual(body.count("run_driver_run("), 1)

    def test_milestone_gate_writes_separate_performance_summary(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            scripts = root / "scripts"
            bin_dir = root / "bin"
            scripts.mkdir()
            bin_dir.mkdir()
            for name in [
                "check_milestone.sh",
                "performance_budgets.sh",
                "run_budgeted.sh",
            ]:
                shutil.copy2(self._script(name), scripts / name)

            stub = "#!/usr/bin/env bash\nexit 0\n"
            for name in [
                "check_seed_bootstrap.sh",
                "build_stage1_from_seed.sh",
                "check_linux_alpha.sh",
                "run_stress_leg.sh",
                "check_fast.sh",
                "check_m53_ownership.sh",
            ]:
                path = scripts / name
                path.write_text(stub, encoding="utf-8")
                path.chmod(0o755)
            driver = bin_dir / "nauqc"
            driver.write_text(stub, encoding="utf-8")
            driver.chmod(0o755)

            result = subprocess.run(
                ["bash", str(scripts / "check_milestone.sh")],
                cwd=root,
                capture_output=True,
                text=True,
                timeout=30,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("milestone verification ok:", result.stdout)

            verification = root / "build" / "verification"
            milestone = json.loads(
                (verification / "milestone-summary.json").read_text(encoding="utf-8")
            )
            performance = json.loads(
                (verification / "performance-summary.json").read_text(encoding="utf-8")
            )
            self.assertEqual(milestone["version"], 1)
            self.assertEqual(performance["version"], 1)
            self.assertEqual(performance["status"], "ok")
            self.assertIsNone(performance["failed_phase"])
            self.assertEqual(
                [phase["id"] for phase in performance["phases"]],
                [
                    "stage1.driver",
                    "seed_bootstrap",
                    "proof",
                    "linux_alpha",
                    "stress_leg",
                    "owned_tests",
                    "ownership_sanitizers",
                ],
            )
            self.assertTrue(all(phase["status"] == "ok" for phase in performance["phases"]))


if __name__ == "__main__":
    unittest.main()
