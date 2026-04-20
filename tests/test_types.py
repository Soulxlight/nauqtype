from __future__ import annotations

import unittest

from tests.test_support import compile_text


class TypeTests(unittest.TestCase):
    def test_assignment_type_mismatch_reports(self) -> None:
        source = """
fn main() -> i32 {
    let mut count = 1;
    count = true;
    return 0;
}
"""
        diagnostics, emitted = compile_text(source)
        self.assertIsNone(emitted)
        codes = [item.code for item in diagnostics.items]
        self.assertIn("NQ-TYPE-029", codes)


if __name__ == "__main__":
    unittest.main()

