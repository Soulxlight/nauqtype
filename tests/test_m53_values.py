from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from tests.test_support import ROOT, compile_c_only, run_executable


class M53ValueAndResourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.driver = ROOT / "selfhost" / "build" / "nauqc"
        if not cls.driver.is_file():
            raise AssertionError(
                "M53 value tests require the active stage1 driver; "
                "run scripts/build_stage1_from_seed.sh first"
            )
        cls.fixtures = ROOT / "tests" / "fixtures" / "m53_values"

    def _fixture(self, name: str) -> Path:
        path = self.fixtures / name
        self.assertTrue(path.is_file(), f"missing M53 fixture: {path}")
        return path

    def _run_driver(
        self,
        args: list[str],
        *,
        cwd: Path = ROOT,
        timeout: int = 120,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [str(self.driver), *args],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

    def _emit_compile_run(self, fixture_name: str) -> tuple[str, subprocess.CompletedProcess[str]]:
        source = self._fixture(fixture_name)
        with tempfile.TemporaryDirectory() as tmp_text:
            tmp = Path(tmp_text)
            emitted_c = tmp / "main.c"
            emitted = self._run_driver(["emit-c", str(source), "-o", str(emitted_c)])
            self.assertEqual(emitted.returncode, 0, emitted.stdout + emitted.stderr)
            self.assertEqual(emitted.stdout, "")
            self.assertEqual(emitted.stderr, "")
            c_text = emitted_c.read_text(encoding="utf-8")
            executable = compile_c_only(emitted_c, exe_path=tmp / "program")
            result = run_executable(executable, cwd=source.parent, timeout=120)
            return c_text, result

    def _check_json(self, fixture_name: str) -> tuple[subprocess.CompletedProcess[str], dict[str, object]]:
        source = self._fixture(fixture_name).resolve()
        result = self._run_driver(["check", str(source), "--diagnostics", "json"])
        self.assertEqual(result.stderr, "")
        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            self.fail(f"stage1 diagnostics were not valid JSON: {exc}\n{result.stdout}")
        self.assertEqual(payload["version"], "diagnostics/v1")
        self.assertEqual(payload["command"], "check")
        return result, payload

    def _assert_rejected_by_family(self, fixture_name: str, family: str, category: str) -> None:
        result, payload = self._check_json(fixture_name)
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertFalse(payload["ok"])
        diagnostics = payload["diagnostics"]
        self.assertGreater(len(diagnostics), 0)
        self.assertTrue(
            any(entry["code"].startswith(family) and entry["category"] == category for entry in diagnostics),
            diagnostics,
        )
        self.assertFalse(any(entry["code"] in {"NQ-STAGE1-001", "NQ-INTERNAL-001"} for entry in diagnostics))
        self.assertNotIn("stage1 limitation", result.stdout)

    def test_i64_exact_values_emit_compile_and_run(self) -> None:
        c_text, result = self._emit_compile_run("i64_exact.nq")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "")
        self.assertIn("int64_t", c_text)
        self.assertIn("9223372036854775807", c_text)
        self.assertRegex(c_text, r"nq_[A-Za-z0-9_]*list[A-Za-z0-9_]*drop")

    def test_i64_rejects_implicit_assignment_and_mixed_arithmetic(self) -> None:
        for fixture in ("i64_assign_from_i32.nq", "i64_mixed_arithmetic.nq"):
            with self.subTest(fixture=fixture):
                self._assert_rejected_by_family(fixture, "NQ-TYPE-", "TYPE")

    def test_list_indices_remain_exact_i32(self) -> None:
        for fixture in ("i64_list_index.nq", "i32_list_index_overflow.nq"):
            with self.subTest(fixture=fixture):
                self._assert_rejected_by_family(fixture, "NQ-TYPE-", "TYPE")

    def test_json_diagnostic_has_truthful_type_identity_and_utf8_byte_span(self) -> None:
        source = self._fixture("diagnostics_type_utf8.nq").resolve()
        result, payload = self._check_json(source.name)
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertFalse(payload["ok"])
        diagnostics = payload["diagnostics"]
        self.assertGreater(len(diagnostics), 0)
        entry = next(item for item in diagnostics if item["code"].startswith("NQ-TYPE-"))
        self.assertEqual(entry["category"], "TYPE")
        self.assertEqual(entry["severity"], "error")
        self.assertNotIn(entry["code"], {"NQ-STAGE1-001", "NQ-INTERNAL-001"})

        span = entry["span"]
        self.assertIsNotNone(span)
        self.assertEqual(Path(span["path"]), source)
        start = span["start"]
        end = span["end"]
        self.assertGreater(end["offset"], start["offset"])
        source_bytes = source.read_bytes()
        self.assertLessEqual(end["offset"], len(source_bytes))
        self.assertEqual(source_bytes[start["offset"] : end["offset"]], b'"bad"')

        before = source_bytes[: start["offset"]]
        expected_line = before.count(b"\n") + 1
        expected_column = len(before.rsplit(b"\n", 1)[-1]) + 1
        self.assertEqual(start["line"], expected_line)
        self.assertEqual(start["column"], expected_column)
        self.assertGreaterEqual(end["line"], start["line"])
        self.assertGreaterEqual(end["column"], 1)

    def test_warning_diagnostic_is_truthful_and_nonfatal(self) -> None:
        warning_source = (ROOT / "tests" / "fixtures" / "diagnostics_warning.nq").resolve()
        result = self._run_driver(["check", str(warning_source), "--diagnostics", "json"])
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stderr, "")
        payload = json.loads(result.stdout)
        self.assertTrue(payload["ok"])
        self.assertEqual(len(payload["diagnostics"]), 1)
        warning = payload["diagnostics"][0]
        self.assertEqual(warning["code"], "NQ-CONTRACT-001")
        self.assertEqual(warning["category"], "CONTRACT")
        self.assertEqual(warning["severity"], "warning")
        self.assertEqual(Path(warning["span"]["path"]), warning_source)

    def test_heap_strings_and_aggregates_retain_values(self) -> None:
        c_text, result = self._emit_compile_run("ownership_values.nq")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "")
        self.assertIn("nq_str_clone", c_text)
        self.assertIn("nq_str_drop", c_text)
        self.assertRegex(c_text, r"nq_str_drop\(&nqv_\d+_source\)")

    def test_cleanup_is_emitted_before_loop_control_and_returns(self) -> None:
        c_text, result = self._emit_compile_run("cleanup_control_flow.nq")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "")
        for binding in ("loop_text", "arm_text", "prefix"):
            with self.subTest(binding=binding):
                self.assertRegex(c_text, rf"nq_str_drop\(&nqv_\d+_{binding}\)")

    def test_generated_cleanup_passes_address_and_leak_sanitizers(self) -> None:
        compiler = shutil.which("cc")
        if compiler is None:
            self.skipTest("M53 sanitizer proof requires a C compiler named cc")

        source = self._fixture("cleanup_control_flow.nq")
        with tempfile.TemporaryDirectory() as tmp_text:
            tmp = Path(tmp_text)
            sanitizer_probe = subprocess.run(
                [
                    compiler,
                    "-x",
                    "c",
                    "-",
                    "-fno-omit-frame-pointer",
                    "-fsanitize=address",
                    "-o",
                    str(tmp / "sanitizer-probe"),
                ],
                input="int main(void) { return 0; }\n",
                cwd=ROOT,
                capture_output=True,
                text=True,
                timeout=30,
            )
            if sanitizer_probe.returncode != 0:
                self.skipTest("host C compiler does not support the M53 address/leak sanitizer gate")

            emitted_c = tmp / "main.c"
            emitted = self._run_driver(["emit-c", str(source), "-o", str(emitted_c)])
            self.assertEqual(emitted.returncode, 0, emitted.stdout + emitted.stderr)

            executable = tmp / "program-sanitized"
            compiled = subprocess.run(
                [
                    compiler,
                    "-std=c11",
                    "-D_POSIX_C_SOURCE=200809L",
                    "-fno-omit-frame-pointer",
                    "-fsanitize=address",
                    "-I",
                    str(ROOT / "stdlib"),
                    str(emitted_c),
                    str(ROOT / "stdlib" / "runtime.c"),
                    "-o",
                    str(executable),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                timeout=120,
            )
            self.assertEqual(compiled.returncode, 0, compiled.stdout + compiled.stderr)

            env = os.environ.copy()
            env["ASAN_OPTIONS"] = "detect_leaks=1:halt_on_error=1"
            env["LSAN_OPTIONS"] = "exitcode=23"
            result = subprocess.run(
                [str(executable)],
                cwd=source.parent,
                capture_output=True,
                text=True,
                timeout=120,
                env=env,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(result.stderr, "")

    def test_lists_are_move_only(self) -> None:
        self._assert_rejected_by_family("list_use_after_move.nq", "NQ-BORROW-", "BORROW")

    def test_bytes_emit_compile_and_run(self) -> None:
        c_text, result = self._emit_compile_run("bytes_exact.nq")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "")
        self.assertIn("nq_bytes_drop", c_text)
        self.assertRegex(c_text, r"nq_bytes_(from_str|len|get)")

    def test_bytes_are_move_only_and_have_no_literal(self) -> None:
        self._assert_rejected_by_family("bytes_use_after_move.nq", "NQ-BORROW-", "BORROW")
        self._assert_rejected_by_family("bytes_literal_rejected.nq", "NQ-TYPE-", "TYPE")


if __name__ == "__main__":
    unittest.main()
