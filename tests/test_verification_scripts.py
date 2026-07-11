from __future__ import annotations

import subprocess
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
            "check_linux_alpha.sh",
            "check_organizational_alpha.sh",
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
            "check_linux_alpha.sh": "--reuse-stage1",
            "check_organizational_alpha.sh": "outside the",
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


if __name__ == "__main__":
    unittest.main()
