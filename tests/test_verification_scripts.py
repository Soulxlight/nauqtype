from __future__ import annotations

import json
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

        workflow = (ROOT / ".github" / "workflows" / "linux-alpha.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("run: scripts/check_milestone.sh", workflow)
        self.assertNotIn("run: scripts/check_linux_alpha.sh", workflow)

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
