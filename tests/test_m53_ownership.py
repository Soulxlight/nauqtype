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


class M53OwnershipTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.driver = ROOT / "selfhost" / "build" / "nauqc"
        if not cls.driver.is_file():
            raise AssertionError(
                "M53 ownership tests require the active stage1 driver; "
                "run scripts/build_stage1_from_seed.sh first"
            )
        cls.fixtures = ROOT / "tests" / "fixtures" / "m53_ownership"

    def _fixture(self, name: str) -> Path:
        path = self.fixtures / name
        self.assertTrue(path.is_file(), f"missing M53 ownership fixture: {path}")
        return path

    def _run_driver(
        self,
        args: list[str],
        *,
        cwd: Path = ROOT,
        timeout: int = 180,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [str(self.driver), *args],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

    def _emit(self, fixture_name: str, destination: Path) -> str:
        source = self._fixture(fixture_name)
        result = self._run_driver(["emit-c", str(source), "-o", str(destination)])
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "")
        self.assertTrue(destination.is_file(), f"missing emitted C: {destination}")
        return destination.read_text(encoding="utf-8")

    def _emit_compile_run(
        self,
        fixture_name: str,
    ) -> tuple[str, subprocess.CompletedProcess[str]]:
        source = self._fixture(fixture_name)
        with tempfile.TemporaryDirectory() as tmp_text:
            tmp = Path(tmp_text)
            emitted_c = tmp / "main.c"
            c_text = self._emit(fixture_name, emitted_c)
            executable = compile_c_only(emitted_c, exe_path=tmp / "program")
            result = run_executable(executable, cwd=source.parent, timeout=180)
            return c_text, result

    def _assert_rejected(
        self,
        fixture_name: str,
        *,
        code_family: str,
        category: str,
        message_fragment: str,
    ) -> None:
        source = self._fixture(fixture_name).resolve()
        result = self._run_driver(
            ["check", str(source), "--diagnostics", "json"],
        )
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertEqual(result.stderr, "")
        payload = json.loads(result.stdout)
        self.assertEqual(payload["version"], "diagnostics/v1")
        self.assertFalse(payload["ok"])
        matching = [
            entry
            for entry in payload["diagnostics"]
            if entry["code"].startswith(code_family)
            and entry["category"] == category
            and message_fragment in entry["message"]
        ]
        self.assertGreater(len(matching), 0, payload["diagnostics"])
        self.assertFalse(
            any(entry["code"] in {"NQ-STAGE1-001", "NQ-INTERNAL-001"} for entry in payload["diagnostics"]),
            payload["diagnostics"],
        )
        self.assertNotIn("stage1 limitation", result.stdout)

    def _sanitizer_compiler(self, tmp: Path) -> str:
        compiler = shutil.which("cc")
        if compiler is None:
            self.skipTest("M53 ownership sanitizer proof requires a C compiler named cc")
        probe = subprocess.run(
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
        if probe.returncode != 0:
            self.skipTest("host C compiler does not support the M53 address/leak sanitizer gate")
        return compiler

    def test_copy_transfer_replacement_and_record_update(self) -> None:
        c_text, result = self._emit_compile_run("copy_transfer_replacement.nq")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "")
        self.assertIn("nq_str_clone", c_text)
        self.assertIn("nq_str_drop", c_text)
        self.assertRegex(c_text, r"nq_(?:value__[^\s(]*list[^\s(]*|list__str)_drop")

    def test_control_boundaries_nested_patterns_and_runtime_values(self) -> None:
        c_text, result = self._emit_compile_run("control_boundaries.nq")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "")
        self.assertIn("nq_str_drop", c_text)
        self.assertRegex(c_text, r"nq_(?:value__[^\s(]*io_err[^\s(]*|io_err)_drop")
        self.assertRegex(c_text, r"nq_(?:value__[^\s(]*process_result[^\s(]*|process_result)_drop")
        self.assertIn("nq_try_end_", c_text)

    def test_noncopy_list_get_and_for_are_rejected(self) -> None:
        for fixture in ("list_get_noncopy_rejected.nq", "for_noncopy_rejected.nq"):
            with self.subTest(fixture=fixture):
                self._assert_rejected(
                    fixture,
                    code_family="NQ-TYPE-",
                    category="TYPE",
                    message_fragment="copy",
                )

    def test_list_get_clones_copy_named_values_with_visible_prototype(self) -> None:
        c_text, result = self._emit_compile_run("list_get_copy_named.nq")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "")
        prototype = re.search(
            r"static inline NQ_[^\s]+__Label nq_value__[^\s]+__Label_clone\(NQ_[^\s]+__Label value\);",
            c_text,
        )
        list_get = re.search(r"static inline NQ_Option__[^\s]+__Label nq_list__[^\s]+__Label_get\(", c_text)
        self.assertIsNotNone(prototype, c_text)
        self.assertIsNotNone(list_get, c_text)
        assert prototype is not None
        assert list_get is not None
        self.assertLess(prototype.start(), list_get.start())

    def test_move_only_by_value_parameter_consumes_its_argument(self) -> None:
        self._assert_rejected(
            "move_only_parameter_rejected.nq",
            code_family="NQ-BORROW-",
            category="BORROW",
            message_fragment="moved",
        )

    def test_match_cannot_move_a_noncopy_field_out_of_its_owner(self) -> None:
        self._assert_rejected(
            "match_noncopy_field_rejected.nq",
            code_family="NQ-BORROW-",
            category="BORROW",
            message_fragment="moving out of fields",
        )

    def test_bytes_move_cleanup_is_binding_exact(self) -> None:
        c_text, result = self._emit_compile_run("bytes_cleanup.nq")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "")
        for binding in ("source_bytes", "temporary_bytes", "payload"):
            with self.subTest(binding=binding):
                calls = re.findall(
                    rf"nq_(?:value__bytes_drop|bytes_drop)\(&nqv_\d+_{binding}\)",
                    c_text,
                )
                self.assertEqual(len(calls), 1, c_text)

    def test_replacement_rhs_may_borrow_the_old_owned_target(self) -> None:
        c_text, result = self._emit_compile_run("replacement_rhs_borrow.nq")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "")
        self.assertIn("nq_replacement_value_", c_text)

    def test_field_value_is_snapshotted_before_owned_temporary_cleanup(self) -> None:
        c_text, result = self._emit_compile_run("temporary_field_snapshot.nq")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "")
        field_read = c_text.index(")).value;")
        owner_drop = c_text.index("_drop(&nq_value_", field_read)
        self.assertLess(field_read, owner_drop)

    def test_owned_paths_are_address_and_leak_clean(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_text:
            tmp = Path(tmp_text)
            compiler = self._sanitizer_compiler(tmp)
            for fixture_name in (
                "copy_transfer_replacement.nq",
                "control_boundaries.nq",
                "bytes_cleanup.nq",
                "list_get_copy_named.nq",
                "replacement_rhs_borrow.nq",
                "temporary_field_snapshot.nq",
            ):
                with self.subTest(fixture=fixture_name):
                    source = self._fixture(fixture_name)
                    emitted_c = tmp / f"{source.stem}.c"
                    self._emit(fixture_name, emitted_c)
                    executable = tmp / f"{source.stem}-sanitized"
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
                        timeout=180,
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
                        timeout=180,
                        env=env,
                    )
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                    self.assertEqual(result.stdout, "")
                    self.assertEqual(result.stderr, "")


if __name__ == "__main__":
    unittest.main()
