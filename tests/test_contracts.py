from __future__ import annotations

import unittest

from tests.test_support import compile_text


class ContractTests(unittest.TestCase):
    def test_public_function_without_audit_warns(self) -> None:
        diagnostics, emitted = compile_text(
            """
pub fn greet() -> unit {
    return;
}

fn main() -> i32 {
    greet();
    return 0;
}
"""
        )
        self.assertIsNotNone(emitted)
        severities = {item.code: item.severity for item in diagnostics.items}
        self.assertEqual(severities.get("NQ-CONTRACT-001"), "warning")

    def test_mutates_entry_must_name_mutref_param(self) -> None:
        diagnostics, emitted = compile_text(
            """
fn bump(value: i32) -> unit
audit {
    intent("Bad mutates entry");
    mutates(value);
    effects();
}
{
    return;
}

fn main() -> i32 {
    bump(1);
    return 0;
}
"""
        )
        self.assertIsNone(emitted)
        codes = [item.code for item in diagnostics.items]
        self.assertIn("NQ-CONTRACT-004", codes)

    def test_missing_declared_mutation_is_error(self) -> None:
        diagnostics, emitted = compile_text(
            """
fn bump(value: mutref i32) -> unit
audit {
    intent("Forgets mutation");
    mutates();
    effects();
}
{
    value = value + 1;
    return;
}

fn main() -> i32 {
    let mut count = 0;
    bump(mutref count);
    return count;
}
"""
        )
        self.assertIsNone(emitted)
        codes = [item.code for item in diagnostics.items]
        self.assertIn("NQ-CONTRACT-005", codes)

    def test_overdeclared_mutation_is_warning(self) -> None:
        diagnostics, emitted = compile_text(
            """
fn inspect(value: mutref i32) -> unit
audit {
    intent("Reads without writing");
    mutates(value);
    effects();
}
{
    return;
}

fn main() -> i32 {
    let mut count = 0;
    inspect(mutref count);
    return 0;
}
"""
        )
        self.assertIsNotNone(emitted)
        severities = {item.code: item.severity for item in diagnostics.items}
        self.assertEqual(severities.get("NQ-CONTRACT-006"), "warning")

    def test_invalid_effect_atom_is_error(self) -> None:
        diagnostics, emitted = compile_text(
            """
fn greet() -> unit
audit {
    intent("Unknown effect");
    mutates();
    effects(network);
}
{
    return;
}

fn main() -> i32 {
    greet();
    return 0;
}
"""
        )
        self.assertIsNone(emitted)
        codes = [item.code for item in diagnostics.items]
        self.assertIn("NQ-CONTRACT-007", codes)

    def test_missing_direct_print_effect_is_error(self) -> None:
        diagnostics, emitted = compile_text(
            """
fn greet() -> unit
audit {
    intent("Prints");
    mutates();
    effects();
}
{
    print_line("hi");
    return;
}

fn main() -> i32 {
    greet();
    return 0;
}
"""
        )
        self.assertIsNone(emitted)
        codes = [item.code for item in diagnostics.items]
        self.assertIn("NQ-CONTRACT-008", codes)

    def test_missing_transitive_print_effect_is_error(self) -> None:
        diagnostics, emitted = compile_text(
            """
fn helper() -> unit
audit {
    intent("Prints");
    mutates();
    effects(print);
}
{
    print_line("hi");
    return;
}

fn greet() -> unit
audit {
    intent("Calls helper");
    mutates();
    effects();
}
{
    helper();
    return;
}

fn main() -> i32 {
    greet();
    return 0;
}
"""
        )
        self.assertIsNone(emitted)
        codes = [item.code for item in diagnostics.items]
        self.assertIn("NQ-CONTRACT-008", codes)

    def test_overdeclared_print_effect_is_warning(self) -> None:
        diagnostics, emitted = compile_text(
            """
fn greet() -> unit
audit {
    intent("No printing");
    mutates();
    effects(print);
}
{
    return;
}

fn main() -> i32 {
    greet();
    return 0;
}
"""
        )
        self.assertIsNotNone(emitted)
        severities = {item.code: item.severity for item in diagnostics.items}
        self.assertEqual(severities.get("NQ-CONTRACT-009"), "warning")


if __name__ == "__main__":
    unittest.main()
