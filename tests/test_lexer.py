from __future__ import annotations

import unittest
from pathlib import Path

from compiler.diagnostics import DiagnosticBag, SourceFile
from compiler.lexer import Lexer


class LexerTests(unittest.TestCase):
    def test_lexes_keywords_and_symbols(self) -> None:
        source = SourceFile(Path("lexer.nq"), 'fn main() -> i32 { let mut value = 1; return value; }')
        diagnostics = DiagnosticBag()
        tokens = Lexer(source, diagnostics).tokenize()
        kinds = [token.kind for token in tokens[:10]]
        self.assertEqual(
            kinds,
            ["FN", "IDENT", "LPAREN", "RPAREN", "ARROW", "IDENT", "LBRACE", "LET", "MUT", "IDENT"],
        )
        self.assertFalse(diagnostics.has_errors())


if __name__ == "__main__":
    unittest.main()

