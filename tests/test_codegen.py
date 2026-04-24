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
        self.assertIn("int main(int argc, char** argv)", emitted)
        self.assertIn("nq_init_process_args(argc, argv);", emitted)
        self.assertIn("nq_print_line", emitted)

    def test_emits_c_while_loop(self) -> None:
        source = """
fn main() -> i32 {
    let mut count = 0;
    while count < 3 {
        count = count + 1;
    }
    return count;
}
"""
        diagnostics, emitted = compile_text(source)
        self.assertFalse(diagnostics.has_errors(), [d.message for d in diagnostics.items])
        assert emitted is not None
        self.assertIn("while (", emitted)


if __name__ == "__main__":
    unittest.main()
