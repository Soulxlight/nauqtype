from __future__ import annotations

import unittest

from tests.test_support import compile_text


class ResolutionTests(unittest.TestCase):
    def test_unknown_name_reports_diagnostic(self) -> None:
        source = """
fn main() -> i32 {
    return missing_value;
}
"""
        diagnostics, emitted = compile_text(source)
        self.assertIsNone(emitted)
        codes = [item.code for item in diagnostics.items]
        self.assertIn("NQ-RESOLVE-005", codes)


if __name__ == "__main__":
    unittest.main()

