from __future__ import annotations

import unittest

from tests.test_support import compile_text


class BorrowTests(unittest.TestCase):
    def test_use_after_move_is_reported(self) -> None:
        source = """
type User {
    age: i32,
}

fn take(user: User) -> i32 {
    return user.age;
}

fn main() -> i32 {
    let user = User { age: 1 };
    take(user);
    take(user);
    return 0;
}
"""
        diagnostics, emitted = compile_text(source)
        self.assertIsNone(emitted)
        codes = [item.code for item in diagnostics.items]
        self.assertIn("NQ-BORROW-001", codes)

    def test_conflicting_borrows_in_one_call_are_reported(self) -> None:
        source = """
fn probe(left: ref i32, right: mutref i32) -> unit {
    return;
}

fn main() -> i32 {
    let mut value = 1;
    probe(ref value, mutref value);
    return 0;
}
"""
        diagnostics, emitted = compile_text(source)
        self.assertIsNone(emitted)
        codes = [item.code for item in diagnostics.items]
        self.assertIn("NQ-BORROW-006", codes)

    def test_use_after_move_across_while_iterations_is_reported(self) -> None:
        source = """
type User {
    age: i32,
}

fn take(user: User) -> i32 {
    return user.age;
}

fn main() -> i32 {
    let user = User { age: 1 };
    while true {
        take(user);
    }
    return 0;
}
"""
        diagnostics, emitted = compile_text(source)
        self.assertIsNone(emitted)
        codes = [item.code for item in diagnostics.items]
        self.assertIn("NQ-BORROW-001", codes)


if __name__ == "__main__":
    unittest.main()
