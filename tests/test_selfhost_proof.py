from __future__ import annotations

import unittest

from tests.test_support import (
    compile_c_only,
    copied_selfhost_workspace,
    normalize_structural_c,
    run_executable,
    run_stage0_selfhost_and_capture_c,
)


class SelfhostProofTests(unittest.TestCase):
    def test_stage1_to_stage2_self_build_proof(self) -> None:
        with copied_selfhost_workspace() as workspace:
            stage1_result, stage1_c = run_stage0_selfhost_and_capture_c(workspace, timeout=240)
            stage1_output = stage1_result.stdout + stage1_result.stderr
            self.assertEqual(stage1_result.returncode, 0, stage1_output)
            self.assertEqual(stage1_result.stdout, "stage1 front-end ok\n")
            self.assertNotIn("stage1 limitation", stage1_output)
            self.assertNotIn("stage1 c error", stage1_output)

            emitted_c = workspace / "build" / "main.c"
            emitted_exe = workspace / "build" / "main.exe"
            compile_c_only(emitted_c, exe_path=emitted_exe)

            stage2_result = run_executable(emitted_exe, cwd=workspace, timeout=240)
            stage2_output = stage2_result.stdout + stage2_result.stderr
            self.assertEqual(stage2_result.returncode, 0, stage2_output)
            self.assertEqual(stage2_result.stdout, "stage1 front-end ok\n")
            self.assertEqual(stage2_result.stderr, "")
            self.assertNotIn("stage1 limitation", stage2_output)
            self.assertNotIn("stage1 c error", stage2_output)

            stage2_c = emitted_c.read_text(encoding="utf-8")
            self.assertEqual(normalize_structural_c(stage1_c), normalize_structural_c(stage2_c))


if __name__ == "__main__":
    unittest.main()
