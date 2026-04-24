from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.test_support import compile_text


class Stage1RuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[1]

    def run_program(self, source: str, extra_files: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            (tmp / "main.nq").write_text(source, encoding="utf-8")
            if extra_files:
                for name, content in extra_files.items():
                    (tmp / name).write_text(content, encoding="utf-8")
            return subprocess.run(
                [sys.executable, "-m", "compiler.main", "run", str(tmp / "main.nq")],
                cwd=self.root,
                capture_output=True,
                text=True,
            )

    def test_read_file_success_path(self) -> None:
        result = self.run_program(
            """
fn main() -> i32 {
    let data = read_file("input.txt");
    match data {
        Ok(text) => {
            return str_len(text);
        },
        Err(err) => {
            print_line(io_err_text(err));
            return 1;
        },
    }
}
""",
            {"input.txt": "hello"},
        )
        self.assertEqual(result.returncode, 5, result.stderr)

    def test_read_file_error_path(self) -> None:
        result = self.run_program(
            """
fn main() -> i32 {
    let data = read_file("missing.txt");
    match data {
        Ok(text) => {
            return str_len(text);
        },
        Err(err) => {
            print_line(io_err_text(err));
            return 1;
        },
    }
}
"""
        )
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("failed to open file", result.stdout)

    def test_write_file_success_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            source = """
fn main() -> i32 {
    let outcome = write_file("output.txt", "hello");
    match outcome {
        Ok(_) => {
            let reread = read_file("output.txt");
            match reread {
                Ok(text) => {
                    return str_len(text);
                },
                Err(err) => {
                    print_line(io_err_text(err));
                    return 1;
                },
            }
        },
        Err(err) => {
            print_line(io_err_text(err));
            return 1;
        },
    }
}
"""
            (tmp / "main.nq").write_text(source, encoding="utf-8")
            result = subprocess.run(
                [sys.executable, "-m", "compiler.main", "run", str(tmp / "main.nq")],
                cwd=self.root,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 5, result.stderr)
            self.assertEqual((tmp / "output.txt").read_text(encoding="utf-8"), "hello")

    def test_write_file_error_path(self) -> None:
        result = self.run_program(
            """
fn main() -> i32 {
    let outcome = write_file("missing/output.txt", "hello");
    match outcome {
        Ok(_) => {
            return 0;
        },
        Err(err) => {
            print_line(io_err_text(err));
            return 1;
        },
    }
}
"""
        )
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("failed to open file for write", result.stdout)

    def test_list_push_len_and_get_run(self) -> None:
        result = self.run_program(
            """
fn main() -> i32 {
    let mut items: list<i32> = list();
    list_push(mutref items, 41);
    list_push(mutref items, 1);
    let first: option<i32> = list_get(ref items, 0);
    match first {
        Some(value) => {
            return value + 1;
        },
        None => {
            return list_len(ref items);
        },
    }
}
"""
        )
        self.assertEqual(result.returncode, 42, result.stderr)

    def test_list_get_rejects_non_copy_element_type(self) -> None:
        diagnostics, emitted = compile_text(
            """
fn main() -> i32 {
    let mut outer: list<list<i32>> = list();
    let inner: list<i32> = list();
    list_push(mutref outer, inner);
    let first = list_get(ref outer, 0);
    match first {
        Some(_) => {
            return 1;
        },
        None => {
            return 0;
        },
    }
}
"""
        )
        self.assertIsNone(emitted)
        codes = [item.code for item in diagnostics.items]
        self.assertIn("NQ-TYPE-037", codes)

    def test_run_process_success_path(self) -> None:
        if os.name == "nt":
            program = "cmd"
            arg_lines = """
    list_push(mutref args, "/c");
    list_push(mutref args, "echo hello");
"""
        else:
            program = "sh"
            arg_lines = """
    list_push(mutref args, "-c");
    list_push(mutref args, "printf hello");
"""
        result = self.run_program(
            f"""
fn main() -> i32 {{
    let mut args: list<str> = list();
{arg_lines}
    let outcome = run_process("{program}", ref args, ".");
    match outcome {{
        Ok(process) => {{
            if process.exit_code != 0 {{
                return process.exit_code;
            }}
            if str_len(process.stdout) > 0 and process.stderr == "" {{
                return 10;
            }}
            return 1;
        }},
        Err(err) => {{
            print_line(io_err_text(err));
            return 1;
        }},
    }}
}}
"""
        )
        self.assertEqual(result.returncode, 10, result.stderr)

    def test_run_process_uses_supplied_cwd(self) -> None:
        if os.name == "nt":
            program = "cmd"
            arg_lines = """
    list_push(mutref args, "/c");
    list_push(mutref args, "type marker.txt");
"""
        else:
            program = "sh"
            arg_lines = """
    list_push(mutref args, "-c");
    list_push(mutref args, "cat marker.txt");
"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            (tmp / "main.nq").write_text(
                f"""
fn main() -> i32 {{
    let mut args: list<str> = list();
{arg_lines}
    let outcome = run_process("{program}", ref args, ".");
    match outcome {{
        Ok(process) => {{
            return str_len(process.stdout);
        }},
        Err(err) => {{
            print_line(io_err_text(err));
            return 1;
        }},
    }}
}}
""".strip()
                + "\n",
                encoding="utf-8",
            )
            (tmp / "marker.txt").write_text("hello", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, "-m", "compiler.main", "run", str(tmp / "main.nq")],
                cwd=self.root,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 5, result.stderr)


if __name__ == "__main__":
    unittest.main()
