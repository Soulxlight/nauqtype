from __future__ import annotations

import unittest
from pathlib import Path

from compiler.diagnostics import SourceFile, render_diagnostics
from compiler.main import compile_source
from tests.test_support import ROOT


class GoldenTests(unittest.TestCase):
    def assertGolden(self, actual: str, golden_path: Path) -> None:  # noqa: N802
        expected = golden_path.read_text(encoding="utf-8")
        self.assertEqual(actual.rstrip("\n"), expected.rstrip("\n"))

    def test_c_output_hello(self) -> None:
        source = SourceFile.from_path(ROOT / "examples" / "hello.nq")
        diagnostics, emitted = compile_source(source)
        self.assertFalse(diagnostics.has_errors(), render_diagnostics(source, diagnostics.items))
        self.assertGolden(emitted, ROOT / "tests" / "golden" / "c" / "hello.c")

    def test_c_output_result_handling(self) -> None:
        source = SourceFile.from_path(ROOT / "examples" / "result_handling.nq")
        diagnostics, emitted = compile_source(source)
        self.assertFalse(diagnostics.has_errors(), render_diagnostics(source, diagnostics.items))
        self.assertGolden(emitted, ROOT / "tests" / "golden" / "c" / "result_handling.c")

    def test_c_output_mutate_counter(self) -> None:
        source = SourceFile.from_path(ROOT / "examples" / "mutate_counter.nq")
        diagnostics, emitted = compile_source(source)
        self.assertFalse(diagnostics.has_errors(), render_diagnostics(source, diagnostics.items))
        self.assertGolden(emitted, ROOT / "tests" / "golden" / "c" / "mutate_counter.c")

    def test_c_output_while_counter(self) -> None:
        source = SourceFile.from_path(ROOT / "examples" / "while_counter.nq")
        diagnostics, emitted = compile_source(source)
        self.assertFalse(diagnostics.has_errors(), render_diagnostics(source, diagnostics.items))
        self.assertGolden(emitted, ROOT / "tests" / "golden" / "c" / "while_counter.c")

    def test_diagnostic_snapshot_parse(self) -> None:
        source = SourceFile(
            Path("diag_parse.nq"),
            "fn main() -> i32 {\n    return 0\n}\n",
        )
        diagnostics, _ = compile_source(source)
        self.assertGolden(render_diagnostics(source, diagnostics.items), ROOT / "tests" / "golden" / "diagnostics" / "parse.txt")

    def test_diagnostic_snapshot_type(self) -> None:
        source = SourceFile(
            Path("diag_type.nq"),
            "fn main() -> i32 {\n    let mut count = 1;\n    count = true;\n    return 0;\n}\n",
        )
        diagnostics, _ = compile_source(source)
        self.assertGolden(render_diagnostics(source, diagnostics.items), ROOT / "tests" / "golden" / "diagnostics" / "type.txt")

    def test_diagnostic_snapshot_borrow(self) -> None:
        source = SourceFile(
            Path("diag_borrow.nq"),
            "type Bucket {\n    items: list<i32>,\n}\n\nfn take(bucket: Bucket) -> i32 {\n    return 0;\n}\n\nfn main() -> i32 {\n    let mut items: list<i32> = list();\n    list_push(mutref items, 1);\n    let bucket = Bucket { items: items };\n    take(bucket);\n    take(bucket);\n    return 0;\n}\n",
        )
        diagnostics, _ = compile_source(source)
        self.assertGolden(render_diagnostics(source, diagnostics.items), ROOT / "tests" / "golden" / "diagnostics" / "borrow.txt")

    def test_diagnostic_snapshot_deferred_pattern(self) -> None:
        source = SourceFile(
            Path("diag_deferred.nq"),
            "fn main() -> i32 {\n    let value: option<option<i32>> = Some(Some(1));\n    match value {\n        Some(Some(inner)) => {\n            return inner;\n        },\n        Some(None) => {\n            return 1;\n        },\n        None => {\n            return 2;\n        },\n    }\n}\n",
        )
        diagnostics, _ = compile_source(source)
        self.assertGolden(
            render_diagnostics(source, diagnostics.items),
            ROOT / "tests" / "golden" / "diagnostics" / "deferred_pattern.txt",
        )


if __name__ == "__main__":
    unittest.main()
