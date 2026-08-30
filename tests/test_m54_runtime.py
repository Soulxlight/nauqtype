from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

from tests.test_support import ROOT, STAGE1_DRIVER_BUILD_TIMEOUT, built_stage1_driver


STREAM_PROGRAM = r'''
fn write_text_mode() -> i32 {
    match stdin_read() {
        Ok(value) => {
            match stdout_write(value) {
                Ok(_) => {},
                Err(err) => {
                    if io_err_kind(ref err) != "broken_pipe" {
                        return 15;
                    }
                    return 11;
                },
            }
        },
        Err(_) => { return 10; },
    }
    match stderr_write("text-stderr") {
        Ok(_) => {},
        Err(_) => { return 12; },
    }
    match stdout_flush() {
        Ok(_) => {},
        Err(err) => {
            if io_err_kind(ref err) != "broken_pipe" {
                return 16;
            }
            return 13;
        },
    }
    match stderr_flush() {
        Ok(_) => {},
        Err(_) => { return 14; },
    }
    return 0;
}

fn write_bytes_mode() -> i32 {
    match stdin_read_bytes() {
        Ok(data) => {
            let length = bytes_len(ref data);
            match stdout_write_bytes(ref data) {
                Ok(_) => {},
                Err(_) => { return 21; },
            }
            if bytes_len(ref data) != length {
                return 22;
            }
        },
        Err(_) => { return 20; },
    }
    let marker = bytes_from_str("BYTES");
    match stderr_write_bytes(ref marker) {
        Ok(_) => {},
        Err(_) => { return 23; },
    }
    if bytes_len(ref marker) != 5 {
        return 24;
    }
    match stdout_flush() {
        Ok(_) => {},
        Err(_) => { return 25; },
    }
    match stderr_flush() {
        Ok(_) => {},
        Err(_) => { return 26; },
    }
    return 0;
}

fn write_line_mode() -> i32 {
    match stdin_read_line() {
        Ok(value) => {
            match value {
                Some(line) => {
                    match stdout_write(line) {
                        Ok(_) => {},
                        Err(_) => { return 31; },
                    }
                },
                None => {
                    match stdout_write("EOF") {
                        Ok(_) => {},
                        Err(_) => { return 32; },
                    }
                },
            }
        },
        Err(_) => { return 30; },
    }
    match stdout_flush() {
        Ok(_) => {},
        Err(_) => { return 33; },
    }
    return 0;
}

fn embedded_nul_mode() -> i32 {
    match stdin_read_bytes() {
        Ok(data) => {
            let path = str_from_bytes(ref data);
            if bytes_len(ref data) != 8 or str_len(path) != 8 {
                return 41;
            }
            match path_metadata(path, false) {
                Ok(_) => { return 42; },
                Err(err) => {
                    if io_err_kind(ref err) != "invalid_input" {
                        return 43;
                    }
                    if io_err_operation(ref err) != "path_metadata" {
                        return 44;
                    }
                    if io_err_os_code(ref err) != 0 {
                        return 45;
                    }
                    match io_err_path(ref err) {
                        Some(error_path) => {
                            if str_len(error_path) != 8 {
                                return 46;
                            }
                            match str_get(error_path, 3) {
                                Some(value) => {
                                    if value != 0 {
                                        return 47;
                                    }
                                },
                                None => { return 48; },
                            }
                        },
                        None => { return 49; },
                    }
                    match io_err_other_path(ref err) {
                        Some(_) => { return 50; },
                        None => {},
                    }
                    if str_len(io_err_text(err)) == 0 {
                        return 51;
                    }
                },
            }
        },
        Err(_) => { return 40; },
    }
    return 0;
}

fn main() -> i32 {
    let Some(mode) = arg_get(1) else {
        return 90;
    };
    if mode == "text" {
        return write_text_mode();
    } else {
        if mode == "bytes" {
            return write_bytes_mode();
        } else {
            if mode == "line" {
                return write_line_mode();
            } else {
                if mode == "nul" {
                    return embedded_nul_mode();
                }
            }
        }
    }
    return 91;
}
'''


FILESYSTEM_PROGRAM = r'''
fn join(root: str, name: str) -> str {
    return str_concat(str_concat(root, "/"), name);
}

fn check_existing_error(err: io_err, expected_path: str) -> i32 {
    if io_err_kind(ref err) != "already_exists" {
        return 1;
    }
    if io_err_operation(ref err) != "create_file_new" {
        return 2;
    }
    if io_err_os_code(ref err) <= 0 {
        return 3;
    }
    match io_err_path(ref err) {
        Some(path) => {
            if path != expected_path {
                return 4;
            }
        },
        None => { return 5; },
    }
    match io_err_other_path(ref err) {
        Some(_) => { return 6; },
        None => {},
    }
    if str_len(io_err_text(err)) == 0 {
        return 7;
    }
    return 0;
}

fn check_rename_error(err: io_err, source: str, target: str) -> i32 {
    if io_err_kind(ref err) != "not_found" {
        return 1;
    }
    if io_err_operation(ref err) != "rename_path" {
        return 2;
    }
    if io_err_os_code(ref err) <= 0 {
        return 3;
    }
    match io_err_path(ref err) {
        Some(path) => {
            if path != source {
                return 4;
            }
        },
        None => { return 5; },
    }
    match io_err_other_path(ref err) {
        Some(path) => {
            if path != target {
                return 6;
            }
        },
        None => { return 7; },
    }
    return 0;
}

fn main() -> i32 {
    let Some(root) = arg_get(1) else {
        return 100;
    };
    match current_dir() {
        Ok(path) => {
            if path != root {
                return 101;
            }
        },
        Err(_) => { return 102; },
    }

    match env_get("NQ_M54_RUNTIME") {
        Ok(value) => {
            match value {
                Some(text) => {
                    if text != "checked-env" {
                        return 103;
                    }
                },
                None => { return 104; },
            }
        },
        Err(_) => { return 105; },
    }
    match env_get("NQ_M54_RUNTIME_MISSING") {
        Ok(value) => {
            match value {
                Some(_) => { return 106; },
                None => {},
            }
        },
        Err(_) => { return 107; },
    }

    let owned_dir = join(root, "owned");
    let deep_dir = join(root, "deep");
    let leaf_dir = join(deep_dir, "leaf");
    match create_dir(owned_dir) {
        Ok(_) => {},
        Err(_) => { return 108; },
    }
    match create_dir_all(leaf_dir) {
        Ok(_) => {},
        Err(_) => { return 109; },
    }

    let created_file = join(owned_dir, "new.txt");
    match create_file_new(created_file) {
        Ok(_) => {},
        Err(_) => { return 110; },
    }
    match create_file_new(created_file) {
        Ok(_) => { return 111; },
        Err(err) => {
            let status = check_existing_error(err, created_file);
            if status != 0 {
                return 111 + status;
            }
        },
    }

    let input_file = join(root, "binary.bin");
    let copied_file = join(root, "copied.bin");
    let atomic_file = join(root, "atomic.bin");
    match read_file_bytes(input_file) {
        Ok(data) => {
            if bytes_len(ref data) != 3 {
                return 120;
            }
            match bytes_get(ref data, 0) {
                Some(value) => { if value != 0 { return 121; } },
                None => { return 122; },
            }
            match bytes_get(ref data, 1) {
                Some(value) => { if value != 255 { return 123; } },
                None => { return 124; },
            }
            match bytes_get(ref data, 2) {
                Some(value) => { if value != 65 { return 125; } },
                None => { return 126; },
            }
            match write_file_bytes(copied_file, ref data) {
                Ok(_) => {},
                Err(_) => { return 127; },
            }
            if bytes_len(ref data) != 3 {
                return 128;
            }
        },
        Err(_) => { return 129; },
    }
    match read_file(input_file) {
        Ok(text) => {
            if str_len(text) != 3 {
                return 166;
            }
            match str_get(text, 0) {
                Some(value) => { if value != 0 { return 167; } },
                None => { return 168; },
            }
            match str_get(text, 1) {
                Some(value) => { if value != 255 { return 169; } },
                None => { return 170; },
            }
            match str_get(text, 2) {
                Some(value) => { if value != 65 { return 171; } },
                None => { return 172; },
            }
        },
        Err(_) => { return 173; },
    }

    match path_metadata(copied_file, true) {
        Ok(metadata) => {
            if not metadata.is_file or metadata.is_directory or metadata.is_symlink {
                return 130;
            }
            if metadata.size != 3 or metadata.mode <= 0 or metadata.modified_ns <= 0 {
                return 131;
            }
        },
        Err(_) => { return 132; },
    }

    let link_file = join(root, "link.bin");
    match path_metadata(link_file, false) {
        Ok(metadata) => {
            if not metadata.is_symlink or metadata.is_file or metadata.is_directory {
                return 133;
            }
        },
        Err(_) => { return 134; },
    }
    match path_metadata(link_file, true) {
        Ok(metadata) => {
            if not metadata.is_file or metadata.is_symlink or metadata.size != 3 {
                return 135;
            }
        },
        Err(_) => { return 136; },
    }

    match read_dir(root) {
        Ok(entries) => {
            let mut saw_binary = false;
            let mut saw_link = false;
            let mut saw_owned = false;
            let mut saw_deep = false;
            let mut saw_copy = false;
            for name in entries {
                if name == "binary.bin" { saw_binary = true; }
                if name == "link.bin" { saw_link = true; }
                if name == "owned" { saw_owned = true; }
                if name == "deep" { saw_deep = true; }
                if name == "copied.bin" { saw_copy = true; }
            }
            if not saw_binary or not saw_link or not saw_owned or not saw_deep or not saw_copy {
                return 137;
            }
        },
        Err(_) => { return 138; },
    }

    let missing_file = join(root, "missing.bin");
    let never_file = join(root, "never.bin");
    match rename_path(missing_file, never_file) {
        Ok(_) => { return 139; },
        Err(err) => {
            let status = check_rename_error(err, missing_file, never_file);
            if status != 0 {
                return 139 + status;
            }
        },
    }

    match rename_path(copied_file, atomic_file) {
        Ok(_) => {},
        Err(_) => { return 147; },
    }
    let replacement = bytes_from_str("replacement");
    match atomic_write_file(atomic_file, ref replacement) {
        Ok(_) => {},
        Err(_) => { return 148; },
    }
    if bytes_len(ref replacement) != 11 {
        return 149;
    }
    match read_file_bytes(atomic_file) {
        Ok(data) => {
            if str_from_bytes(ref data) != "replacement" {
                return 150;
            }
        },
        Err(_) => { return 151; },
    }
    let atomic_link_file = join(root, "atomic-link.bin");
    match atomic_write_file(atomic_link_file, ref replacement) {
        Ok(_) => {},
        Err(_) => { return 191; },
    }
    match path_metadata(atomic_link_file, false) {
        Ok(metadata) => {
            if not metadata.is_file or metadata.is_symlink or metadata.size != 11 {
                return 192;
            }
        },
        Err(_) => { return 193; },
    }
    match read_file_bytes(input_file) {
        Ok(data) => {
            if bytes_len(ref data) != 3 {
                return 194;
            }
            match bytes_get(ref data, 1) {
                Some(value) => { if value != 255 { return 195; } },
                None => { return 196; },
            }
        },
        Err(_) => { return 197; },
    }

    match create_temp_file(root, "nq-file-") {
        Ok(path) => {
            match path_metadata(path, false) {
                Ok(metadata) => {
                    if not metadata.is_file or metadata.mode != 384 {
                        return 152;
                    }
                },
                Err(_) => { return 153; },
            }
            match remove_file(path) {
                Ok(_) => {},
                Err(_) => { return 154; },
            }
        },
        Err(_) => { return 155; },
    }
    match create_temp_dir(root, "nq-dir-") {
        Ok(path) => {
            match path_metadata(path, false) {
                Ok(metadata) => {
                    if not metadata.is_directory or metadata.mode != 448 {
                        return 156;
                    }
                },
                Err(_) => { return 157; },
            }
            match remove_dir(path) {
                Ok(_) => {},
                Err(_) => { return 158; },
            }
        },
        Err(_) => { return 159; },
    }

    match create_temp_file(root, "bad/prefix") {
        Ok(_) => { return 160; },
        Err(err) => {
            if io_err_kind(ref err) != "invalid_input" or io_err_os_code(ref err) != 0 {
                return 161;
            }
        },
    }

    let path_name_source = join(root, "path-name.bin");
    match read_file_bytes(path_name_source) {
        Ok(name_bytes) => {
            let opaque_name = str_from_bytes(ref name_bytes);
            if str_len(opaque_name) != 1 {
                return 174;
            }
            match str_get(opaque_name, 0) {
                Some(value) => { if value != 255 { return 175; } },
                None => { return 176; },
            }
            let opaque_path = join(root, opaque_name);
            match create_file_new(opaque_path) {
                Ok(_) => {},
                Err(_) => { return 177; },
            }
            match path_metadata(opaque_path, false) {
                Ok(metadata) => {
                    if not metadata.is_file {
                        return 178;
                    }
                },
                Err(_) => { return 179; },
            }
            match read_dir(root) {
                Ok(entries) => {
                    let mut index = 0;
                    let mut found = false;
                    while index < list_len(ref entries) {
                        match list_get(ref entries, index) {
                            Some(entry) => {
                                if str_len(entry) == 1 {
                                    match str_get(entry, 0) {
                                        Some(value) => {
                                            if value == 255 {
                                                found = true;
                                            }
                                        },
                                        None => {},
                                    }
                                }
                            },
                            None => { return 180; },
                        }
                        index = index + 1;
                    }
                    if not found {
                        return 181;
                    }
                },
                Err(_) => { return 182; },
            }
            match remove_file(opaque_path) {
                Ok(_) => {},
                Err(_) => { return 183; },
            }
        },
        Err(_) => { return 184; },
    }
    match remove_file(path_name_source) {
        Ok(_) => {},
        Err(_) => { return 185; },
    }
    match remove_file(link_file) {
        Ok(_) => {},
        Err(_) => { return 186; },
    }
    match remove_file(atomic_link_file) {
        Ok(_) => {},
        Err(_) => { return 198; },
    }
    match path_metadata(input_file, true) {
        Ok(metadata) => {
            if not metadata.is_file {
                return 187;
            }
        },
        Err(_) => { return 188; },
    }
    match path_metadata(link_file, false) {
        Ok(_) => { return 189; },
        Err(err) => {
            if io_err_kind(ref err) != "not_found" {
                return 190;
            }
        },
    }

    match remove_file(created_file) {
        Ok(_) => {},
        Err(_) => { return 162; },
    }
    match remove_dir(owned_dir) {
        Ok(_) => {},
        Err(_) => { return 163; },
    }
    match remove_dir(leaf_dir) {
        Ok(_) => {},
        Err(_) => { return 164; },
    }
    match remove_dir(deep_dir) {
        Ok(_) => {},
        Err(_) => { return 165; },
    }
    return 0;
}
'''


FORWARDED_BORROW_PROGRAM = r'''
fn forward_write(path: str, data: ref bytes) -> result<unit, io_err> {
    return write_file_bytes(path, data);
}

fn forward_atomic(path: str, data: ref bytes) -> result<unit, io_err> {
    return atomic_write_file(path, data);
}

fn forward_stdout(data: ref bytes) -> result<unit, io_err> {
    return stdout_write_bytes(data);
}

fn forward_stderr(data: ref bytes) -> result<unit, io_err> {
    return stderr_write_bytes(data);
}

fn forward_text(data: ref bytes) -> str {
    return str_from_bytes(data);
}

fn copy_text(value: ref str) -> str {
    return value;
}

fn validate_error(err: ref io_err, expected_path: str) -> bool {
    if io_err_kind(err) != "already_exists" or io_err_operation(err) != "create_file_new" {
        return false;
    }
    if io_err_os_code(err) <= 0 {
        return false;
    }
    match io_err_path(err) {
        Some(path) => {
            if path != expected_path {
                return false;
            }
        },
        None => { return false; },
    }
    match io_err_other_path(err) {
        Some(_) => { return false; },
        None => {},
    }
    return true;
}

fn main() -> i32 {
    let original = "copy";
    let copied = copy_text(ref original);
    if copied != original {
        return 9;
    }
    let path = "forwarded.bin";
    let data = bytes_from_str("initial");
    if forward_text(ref data) != "initial" {
        return 1;
    }
    match forward_write(path, ref data) {
        Ok(_) => {},
        Err(_) => { return 2; },
    }
    let replacement = bytes_from_str("replacement");
    match forward_atomic(path, ref replacement) {
        Ok(_) => {},
        Err(_) => { return 3; },
    }
    let empty = bytes_from_str("");
    match forward_stdout(ref empty) {
        Ok(_) => {},
        Err(_) => { return 4; },
    }
    match forward_stderr(ref empty) {
        Ok(_) => {},
        Err(_) => { return 5; },
    }
    match create_file_new(path) {
        Ok(_) => { return 6; },
        Err(err) => {
            if not validate_error(ref err, path) {
                return 7;
            }
        },
    }
    match remove_file(path) {
        Ok(_) => {},
        Err(_) => { return 8; },
    }
    return 0;
}
'''


class M54RuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._driver_context = built_stage1_driver(timeout=STAGE1_DRIVER_BUILD_TIMEOUT)
        cls.driver_workspace, cls.driver = cls._driver_context.__enter__()

    @classmethod
    def tearDownClass(cls) -> None:
        cls._driver_context.__exit__(None, None, None)

    def _write_source(self, directory: Path, name: str, content: str) -> Path:
        source = directory / name
        source.write_text(textwrap.dedent(content).strip() + "\n", encoding="utf-8")
        return source

    def _build(self, source: Path, executable: Path) -> None:
        result = subprocess.run(
            [str(self.driver), "build", str(source), "-o", str(executable)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=180,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "")
        self.assertTrue(executable.is_file())

    def _review_io_kinds(self, source: Path, function_name: str) -> list[str]:
        result = subprocess.run(
            [str(self.driver), "review", str(source), "--format", "v2"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=120,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        function = next(entry for entry in payload["functions"] if entry["name"] == function_name)
        kinds = function["inferred"]["io_kinds"]
        schema = json.loads((ROOT / "schemas" / "review-v2.schema.json").read_text(encoding="utf-8"))
        self.assertTrue(set(kinds).issubset(set(schema["$defs"]["io_kind"]["enum"])))
        return kinds

    def _facts_builtin_io_kinds(self, source: Path) -> dict[str, str]:
        result = subprocess.run(
            [str(self.driver), "facts", str(source), "--format", "v2"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=120,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        kinds = {
            entry["callee"]: entry["io_kind"]
            for entry in payload["call_graph"]
            if entry["callee"].startswith("builtin:") and "io_kind" in entry
        }
        schema = json.loads((ROOT / "schemas" / "facts-v2.schema.json").read_text(encoding="utf-8"))
        self.assertTrue(set(kinds.values()).issubset(set(schema["$defs"]["io_kind"]["enum"])))
        return kinds

    def _run_binary(
        self,
        executable: Path,
        args: list[str],
        *,
        cwd: Path,
        input_data: bytes = b"",
        env: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[bytes]:
        return subprocess.run(
            [str(executable), *args],
            cwd=cwd,
            input=input_data,
            capture_output=True,
            timeout=60,
            env=env,
        )

    def test_streams_bytes_lines_flush_and_embedded_nul_rejection(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_text:
            tmp = Path(tmp_text)
            compile_dir = tmp / "compile"
            run_dir = tmp / "run"
            compile_dir.mkdir()
            run_dir.mkdir()
            source = self._write_source(compile_dir, "streams.nq", STREAM_PROGRAM)
            self.assertEqual(
                self._review_io_kinds(source, "main"),
                ["arguments", "stdin", "stdout", "stderr", "metadata"],
            )
            stream_kinds = self._facts_builtin_io_kinds(source)
            self.assertEqual(stream_kinds["builtin:arg_get"], "arguments")
            self.assertEqual(stream_kinds["builtin:stdin_read"], "stdin")
            self.assertEqual(stream_kinds["builtin:stdout_write_bytes"], "stdout")
            self.assertEqual(stream_kinds["builtin:stderr_write_bytes"], "stderr")
            self.assertEqual(stream_kinds["builtin:path_metadata"], "metadata")
            executable = compile_dir / "streams"
            self._build(source, executable)

            cases = [
                ("text", b"text-body", b"text-body", b"text-stderr"),
                ("text", b"\x00A\xff", b"\x00A\xff", b"text-stderr"),
                ("bytes", b"\x00A\xff", b"\x00A\xff", b"BYTES"),
                ("line", b"first line\nsecond line", b"first line", b""),
                ("line", b"", b"EOF", b""),
                ("nul", b"bad\x00path", b"", b""),
            ]
            for mode, input_data, stdout, stderr in cases:
                with self.subTest(mode=mode, input_data=input_data):
                    result = self._run_binary(
                        executable,
                        [mode],
                        cwd=run_dir,
                        input_data=input_data,
                    )
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                    self.assertEqual(result.stdout, stdout)
                    self.assertEqual(result.stderr, stderr)

            read_fd, write_fd = os.pipe()
            os.close(read_fd)
            process = subprocess.Popen(
                [str(executable), "text"],
                cwd=run_dir,
                stdin=subprocess.PIPE,
                stdout=write_fd,
                stderr=subprocess.PIPE,
            )
            os.close(write_fd)
            _, broken_pipe_stderr = process.communicate(input=b"closed-reader", timeout=60)
            self.assertEqual(process.returncode, 13, broken_pipe_stderr)
            self.assertEqual(broken_pipe_stderr, b"text-stderr")

            self.assertEqual(list(run_dir.iterdir()), [])

    def test_forwarded_borrow_parameters_reach_m54_builtins_as_pointers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_text:
            tmp = Path(tmp_text)
            compile_dir = tmp / "compile"
            run_dir = tmp / "run"
            compile_dir.mkdir()
            run_dir.mkdir()
            source = self._write_source(compile_dir, "forwarded_borrows.nq", FORWARDED_BORROW_PROGRAM)
            executable = compile_dir / "forwarded_borrows"
            self._build(source, executable)

            result = self._run_binary(executable, [], cwd=run_dir)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(result.stdout, b"")
            self.assertEqual(result.stderr, b"")
            self.assertEqual(list(run_dir.iterdir()), [])

    def test_owned_values_require_explicit_ref_at_borrowed_parameters(self) -> None:
        cases = {
            "builtin_positional": (r'''
                fn main() -> i32 {
                    let data = bytes_from_str("owned");
                    match stdout_write_bytes(data) {
                        Ok(_) => {},
                        Err(_) => {},
                    }
                    return 0;
                }
            ''', "borrow parameter requires explicit `ref` or an existing borrowed binding"),
            "builtin_named": (r'''
                fn main() -> i32 {
                    let data = bytes_from_str("owned");
                    match stdout_write_bytes(data: data) {
                        Ok(_) => {},
                        Err(_) => {},
                    }
                    return 0;
                }
            ''', "borrow parameter requires explicit `ref` or an existing borrowed binding"),
            "io_error": (r'''
                fn main() -> i32 {
                    match read_file("missing") {
                        Ok(_) => {},
                        Err(err) => {
                            if io_err_kind(err) == "" {
                                return 1;
                            }
                        },
                    }
                    return 0;
                }
            ''', "borrow parameter requires explicit `ref` or an existing borrowed binding"),
            "user_function": (r'''
                fn data_len(data: ref bytes) -> i64 {
                    return bytes_len(data);
                }

                fn main() -> i32 {
                    let data = bytes_from_str("owned");
                    if data_len(data) == 0 {
                        return 1;
                    }
                    return 0;
                }
            ''', "borrow parameter requires explicit `ref` or an existing borrowed binding"),
            "stored_borrow": (r'''
                fn main() -> i32 {
                    let data = bytes_from_str("owned");
                    let alias: ref bytes = data;
                    stdout_write_bytes(alias);
                    return 0;
                }
            ''', "borrow types are only allowed in function parameters in v0.1"),
            "nested_stored_borrow": (r'''
                fn main() -> i32 {
                    let aliases: list<ref bytes> = [];
                    return list_len(ref aliases);
                }
            ''', "borrow types are only allowed in function parameters in v0.1"),
            "borrow_return": (r'''
                fn leak(data: ref bytes) -> ref bytes {
                    return data;
                }
            ''', "borrow types are only allowed in function parameters in v0.1"),
            "borrow_field": (r'''
                type Holder {
                    data: ref bytes,
                }
            ''', "borrow types are only allowed in function parameters in v0.1"),
            "borrow_payload": (r'''
                enum ByteView {
                    Data(ref bytes),
                }
            ''', "borrow types are only allowed in function parameters in v0.1"),
            "borrow_const": (r'''
                const DATA: ref i32 = 1;
            ''', "borrow types are only allowed in function parameters in v0.1"),
            "immutable_to_mutable_borrow": (r'''
                fn append_one(items: mutref list<i32>) -> unit {
                    list_push(items, 1);
                    return;
                }

                fn forward(items: ref list<i32>) -> unit {
                    append_one(items);
                    return;
                }
            ''', "mutable borrow parameter requires explicit `mutref` or an existing mutable borrowed binding"),
            "explicit_borrow_to_owned_function": (r'''
                fn consume(value: i32) -> unit {
                    return;
                }

                fn main() -> i32 {
                    let value = 1;
                    consume(ref value);
                    return 0;
                }
            ''', "borrow expression does not match owned call argument type"),
            "explicit_borrow_to_constructor": (r'''
                fn main() -> i32 {
                    let value = 1;
                    let wrapped: option<i32> = Some(ref value);
                    return 0;
                }
            ''', "borrow expression does not match owned call argument type"),
            "explicit_borrow_to_path_metadata": (r'''
                fn main() -> i32 {
                    let path = "owned";
                    path_metadata(ref path, false);
                    return 0;
                }
            ''', "borrow expression does not match owned call argument type"),
            "explicit_borrow_to_io_err_text": (r'''
                fn main() -> i32 {
                    match read_file("missing") {
                        Ok(_) => {},
                        Err(err) => {
                            let text = io_err_text(ref err);
                            if text == "" { return 1; }
                        },
                    }
                    return 0;
                }
            ''', "borrow expression does not match owned call argument type"),
            "mutref_immutable_local": (r'''
                fn append_one(items: mutref list<i32>) -> unit {
                    list_push(items, 1);
                    return;
                }

                fn main() -> i32 {
                    let items: list<i32> = [];
                    append_one(mutref items);
                    return 0;
                }
            ''', "cannot take `mutref` of immutable binding `items`"),
            "mutref_immutable_borrow": (r'''
                fn write_value(value: mutref i32) -> unit {
                    return;
                }

                fn forward(value: ref i32) -> unit {
                    write_value(mutref value);
                    return;
                }
            ''', "cannot take `mutref` of immutable binding `value`"),
            "borrowed_move_to_owned_call": (r'''
                fn consume(data: bytes) -> unit {
                    return;
                }

                fn forward(data: ref bytes) -> unit {
                    consume(data);
                    return;
                }
            ''', "cannot move owned value out of borrowed binding `data`"),
            "borrowed_move_to_local": (r'''
                fn store(data: ref bytes) -> unit {
                    let owned = data;
                    return;
                }
            ''', "cannot move owned value out of borrowed binding `data`"),
            "borrowed_move_to_return": (r'''
                fn release(data: ref bytes) -> bytes {
                    return data;
                }
            ''', "cannot move owned value out of borrowed binding `data`"),
            "borrowed_move_to_struct_field": (r'''
                type Holder {
                    data: bytes,
                }

                fn store(data: ref bytes) -> Holder {
                    return Holder { data: data };
                }
            ''', "cannot move owned value out of borrowed binding `data`"),
            "borrowed_move_to_list_element": (r'''
                fn collect(data: ref bytes) -> list<bytes> {
                    return [data];
                }
            ''', "cannot move owned value out of borrowed binding `data`"),
            "borrowed_move_to_constructor": (r'''
                fn wrap(data: ref bytes) -> option<bytes> {
                    return Some(data);
                }
            ''', "cannot move owned value out of borrowed binding `data`"),
            "borrowed_move_to_assignment": (r'''
                fn replace(data: ref bytes) -> unit {
                    let mut owned = bytes_from_str("owned");
                    owned = data;
                    return;
                }
            ''', "cannot move owned value out of borrowed binding `data`"),
            "borrowed_move_to_match": (r'''
                fn inspect(value: ref option<bytes>) -> unit {
                    match value {
                        Some(_) => {},
                        None => {},
                    }
                    return;
                }
            ''', "cannot move owned value out of borrowed binding `value`"),
        }
        with tempfile.TemporaryDirectory() as tmp_text:
            tmp = Path(tmp_text)
            for name, (program, expected_message) in cases.items():
                with self.subTest(name=name):
                    source = self._write_source(tmp, f"{name}.nq", program)
                    result = subprocess.run(
                        [str(self.driver), "check", str(source)],
                        cwd=ROOT,
                        capture_output=True,
                        text=True,
                        timeout=120,
                    )
                    combined = result.stdout + result.stderr
                    self.assertEqual(result.returncode, 1, combined)
                    self.assertIn(expected_message, combined)
                    self.assertNotIn("stage1 limitation", combined)

    def test_checked_tooling_rejects_borrowed_to_owned_movement(self) -> None:
        program = r'''
            fn consume(data: bytes) -> unit {
                return;
            }

            fn forward(data: ref bytes) -> unit {
                consume(data);
                return;
            }

            fn main() -> i32 {
                return 0;
            }
        '''
        with tempfile.TemporaryDirectory() as tmp_text:
            tmp = Path(tmp_text)
            source = self._write_source(tmp, "borrowed_evidence.nq", program)
            before = source.read_bytes()
            commands = {
                "facts": ["facts", str(source), "--format", "v3"],
                "review": ["review", str(source), "--format", "v2"],
                "refactor": ["refactor-rename", str(source), "fn:borrowed_evidence::forward", "renamed"],
                "policy": ["policy-check", str(source), str(ROOT / "nauqtype.policy.json")],
                "review_diff": ["review-diff", str(source), str(source), "--format", "v2"],
                "change_report": ["change-report", str(source), str(source), "--format", "v1"],
            }
            for name, args in commands.items():
                with self.subTest(name=name):
                    result = subprocess.run(
                        [str(self.driver), *args],
                        cwd=ROOT,
                        capture_output=True,
                        text=True,
                        timeout=120,
                    )
                    combined = result.stdout + result.stderr
                    self.assertEqual(result.returncode, 1, combined)
                    self.assertNotIn('"evidence":"checked"', combined)
                    self.assertNotIn("stage1 limitation", combined)
            self.assertEqual(source.read_bytes(), before)

    @unittest.skipUnless(sys.platform.startswith("linux"), "M54 timestamp bounds are Linux-first")
    def test_path_metadata_timestamp_conversion_is_checked_at_i64_bounds(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_text:
            tmp = Path(tmp_text)
            source = tmp / "timestamp_bounds.c"
            executable = tmp / "timestamp_bounds"
            runtime_path = (ROOT / "stdlib" / "runtime.c").as_posix()
            source.write_text(
                textwrap.dedent(
                    f'''\
                    #include "{runtime_path}"

                    int main(void) {{
                        int64_t value = 0;
                        if (!nq_timestamp_to_i64_ns((time_t)9223372036LL, 854775807L, &value) || value != INT64_MAX) return 1;
                        if (nq_timestamp_to_i64_ns((time_t)9223372036LL, 854775808L, &value)) return 2;
                        if (!nq_timestamp_to_i64_ns((time_t)-9223372037LL, 145224192L, &value) || value != INT64_MIN) return 3;
                        if (nq_timestamp_to_i64_ns((time_t)-9223372037LL, 145224191L, &value)) return 4;
                        if (nq_timestamp_to_i64_ns((time_t)9223372037LL, 0L, &value)) return 5;
                        if (nq_timestamp_to_i64_ns((time_t)-9223372038LL, 999999999L, &value)) return 6;
                        if (nq_timestamp_to_i64_ns((time_t)0, -1L, &value)) return 7;
                        if (nq_timestamp_to_i64_ns((time_t)0, 1000000000L, &value)) return 8;
                        return 0;
                    }}
                    '''
                ),
                encoding="utf-8",
            )
            compile_result = subprocess.run(
                [
                    os.environ.get("CC", "cc"),
                    "-std=c11",
                    "-D_POSIX_C_SOURCE=200809L",
                    "-Wall",
                    "-Wextra",
                    "-Werror",
                    "-pedantic",
                    str(source),
                    "-o",
                    str(executable),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                timeout=60,
            )
            self.assertEqual(compile_result.returncode, 0, compile_result.stdout + compile_result.stderr)
            result = subprocess.run([str(executable)], capture_output=True, text=True, timeout=60)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    @unittest.skipUnless(sys.platform.startswith("linux"), "M54 filesystem contracts are Linux-first")
    def test_linux_filesystem_contracts_errors_modes_and_cleanup(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_text:
            tmp = Path(tmp_text)
            compile_dir = tmp / "compile"
            run_dir = tmp / "runtime"
            compile_dir.mkdir()
            run_dir.mkdir()
            (run_dir / "binary.bin").write_bytes(b"\x00\xffA")
            (run_dir / "path-name.bin").write_bytes(b"\xff")
            (run_dir / "link.bin").symlink_to("binary.bin")
            (run_dir / "atomic-link.bin").symlink_to("binary.bin")

            source = self._write_source(compile_dir, "filesystem.nq", FILESYSTEM_PROGRAM)
            self.assertEqual(
                self._review_io_kinds(source, "main"),
                [
                    "read",
                    "write",
                    "create_dir",
                    "arguments",
                    "environment",
                    "cwd",
                    "metadata",
                    "traversal",
                    "create_file",
                    "temporary",
                    "remove",
                    "rename",
                    "atomic_replace",
                ],
            )
            filesystem_kinds = self._facts_builtin_io_kinds(source)
            self.assertEqual(filesystem_kinds["builtin:read_file_bytes"], "read")
            self.assertEqual(filesystem_kinds["builtin:write_file_bytes"], "write")
            self.assertEqual(filesystem_kinds["builtin:create_file_new"], "create_file")
            self.assertEqual(filesystem_kinds["builtin:create_temp_dir"], "temporary")
            self.assertEqual(filesystem_kinds["builtin:remove_dir"], "remove")
            self.assertEqual(filesystem_kinds["builtin:rename_path"], "rename")
            self.assertEqual(filesystem_kinds["builtin:atomic_write_file"], "atomic_replace")
            executable = compile_dir / "filesystem"
            self._build(source, executable)

            env = os.environ.copy()
            env["NQ_M54_RUNTIME"] = "checked-env"
            env.pop("NQ_M54_RUNTIME_MISSING", None)
            result = self._run_binary(
                executable,
                [str(run_dir)],
                cwd=run_dir,
                env=env,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(result.stdout, b"")
            self.assertEqual(result.stderr, b"")
            self.assertEqual((run_dir / "atomic.bin").read_bytes(), b"replacement")
            self.assertEqual(
                {entry.name for entry in run_dir.iterdir()},
                {"atomic.bin", "binary.bin"},
            )
            self.assertEqual(
                [entry.name for entry in run_dir.iterdir() if entry.name.startswith(".nq-atomic-")],
                [],
            )


if __name__ == "__main__":
    unittest.main()
