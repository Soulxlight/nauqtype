from __future__ import annotations

import unittest
from pathlib import Path

from compiler.ast import nodes as ast
from compiler.diagnostics import DiagnosticBag, SourceFile
from compiler.lexer import Lexer
from compiler.parser import Parser
from tests.test_support import compile_text


class ParserShapeTests(unittest.TestCase):
    def test_parses_audit_block_shape(self) -> None:
        source = SourceFile(
            Path("audit_shape.nq"),
            """
fn main() -> i32
audit {
    intent("Add two values");
    mutates();
    effects();
}
{
    return 0;
}
""",
        )
        diagnostics = DiagnosticBag()
        tokens = Lexer(source, diagnostics).tokenize()
        program = Parser(tokens, diagnostics).parse()
        self.assertFalse(diagnostics.has_errors(), [d.message for d in diagnostics.items])
        function = program.items[0]
        self.assertIsInstance(function, ast.FunctionDecl)
        self.assertIsNotNone(function.audit)
        assert function.audit is not None
        self.assertEqual(function.audit.intent, "Add two values")
        self.assertEqual(function.audit.mutates, [])
        self.assertEqual(function.audit.effects, [])

    def test_parses_while_statement_shape(self) -> None:
        source = SourceFile(
            Path("while_shape.nq"),
            "fn main() -> i32 { let mut count = 0; while count < 3 { count = count + 1; } return count; }",
        )
        diagnostics = DiagnosticBag()
        tokens = Lexer(source, diagnostics).tokenize()
        program = Parser(tokens, diagnostics).parse()
        self.assertFalse(diagnostics.has_errors(), [d.message for d in diagnostics.items])
        function = program.items[0]
        self.assertIsInstance(function, ast.FunctionDecl)
        self.assertIsInstance(function.body.statements[1], ast.WhileStmt)
        loop = function.body.statements[1]
        self.assertIsInstance(loop.condition, ast.BinaryExpr)
        self.assertIsInstance(loop.body.statements[0], ast.AssignStmt)

    def test_reports_out_of_order_audit_clause(self) -> None:
        diagnostics, emitted = compile_text(
            """
fn main() -> i32
audit {
    mutates();
    intent("bad");
    effects();
}
{
    return 0;
}
"""
        )
        self.assertIsNone(emitted)
        codes = [item.code for item in diagnostics.items]
        self.assertIn("NQ-CONTRACT-002", codes)

    def test_reports_missing_audit_clause(self) -> None:
        diagnostics, emitted = compile_text(
            """
fn main() -> i32
audit {
    intent("missing effects");
    mutates();
}
{
    return 0;
}
"""
        )
        self.assertIsNone(emitted)
        codes = [item.code for item in diagnostics.items]
        self.assertIn("NQ-CONTRACT-002", codes)

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
