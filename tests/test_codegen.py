from __future__ import annotations

import unittest

from tests.test_support import compile_text


class CodegenTests(unittest.TestCase):
    def test_emits_c_wrapper_and_runtime_call(self) -> None:
        source = """
fn main() -> i32 {
    print_line("Hello");
    return 0;
}
"""
        diagnostics, emitted = compile_text(source)
        self.assertFalse(diagnostics.has_errors(), [d.message for d in diagnostics.items])
        assert emitted is not None
        self.assertIn("int main(void)", emitted)
        self.assertIn("nq_print_line", emitted)


if __name__ == "__main__":
    unittest.main()

