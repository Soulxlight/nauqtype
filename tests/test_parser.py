from __future__ import annotations

import unittest

from compiler.ast import nodes as ast
from tests.test_support import compile_text


class ParserShapeTests(unittest.TestCase):
    def test_parses_struct_literal_and_match(self) -> None:
        source = """
type User {
    age: i32,
}

enum Flag {
    Ready,
}

fn main() -> i32 {
    let user = User { age: 3 };
    match Ready {
        Ready => {
            return user.age;
        },
    }
}
"""
        diagnostics, emitted = compile_text(source)
        self.assertFalse(diagnostics.has_errors(), [d.message for d in diagnostics.items])
        self.assertIn("nq_fn_main", emitted)


if __name__ == "__main__":
    unittest.main()

