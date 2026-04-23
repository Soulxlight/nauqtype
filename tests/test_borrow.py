from __future__ import annotations

import unittest

from tests.test_support import compile_text


class BorrowTests(unittest.TestCase):
    def test_use_after_move_is_reported(self) -> None:
        source = """
type Bucket {
    items: list<i32>,
}

fn take(bucket: Bucket) -> i32 {
    return 0;
}

fn main() -> i32 {
    let mut items: list<i32> = list();
    list_push(mutref items, 1);
    let bucket = Bucket { items: items };
    take(bucket);
    take(bucket);
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
type Bucket {
    items: list<i32>,
}

fn take(bucket: Bucket) -> i32 {
    return 0;
}

fn main() -> i32 {
    let mut items: list<i32> = list();
    list_push(mutref items, 1);
    let bucket = Bucket { items: items };
    while true {
        take(bucket);
    }
    return 0;
}
"""
        diagnostics, emitted = compile_text(source)
        self.assertIsNone(emitted)
        codes = [item.code for item in diagnostics.items]
        self.assertIn("NQ-BORROW-001", codes)

    def test_structural_copy_allows_reuse_of_copy_struct(self) -> None:
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
    return take(user);
}
"""
        diagnostics, emitted = compile_text(source)
        self.assertFalse(diagnostics.has_errors(), [item.message for item in diagnostics.items])
        self.assertIsNotNone(emitted)

    def test_borrow_expression_outside_direct_call_arg_is_reported(self) -> None:
        source = """
fn main() -> i32 {
    let value = 1;
    let alias: ref i32 = ref value;
    return 0;
}
"""
        diagnostics, emitted = compile_text(source)
        self.assertIsNone(emitted)
        codes = [item.code for item in diagnostics.items]
        self.assertIn("NQ-BORROW-002", codes)

    def test_borrow_of_moved_value_is_reported(self) -> None:
        source = """
type Bucket {
    items: list<i32>,
}

fn take(bucket: Bucket) -> i32 {
    return 0;
}

fn inspect(bucket: ref Bucket) -> i32 {
    return 0;
}

fn main() -> i32 {
    let mut items: list<i32> = list();
    list_push(mutref items, 1);
    let bucket = Bucket { items: items };
    take(bucket);
    return inspect(ref bucket);
}
"""
        diagnostics, emitted = compile_text(source)
        self.assertIsNone(emitted)
        codes = [item.code for item in diagnostics.items]
        self.assertIn("NQ-BORROW-003", codes)

    def test_moving_out_of_non_copy_field_is_reported(self) -> None:
        source = """
type Bucket {
    items: list<i32>,
}

fn take(items: list<i32>) -> i32 {
    return 0;
}

fn main() -> i32 {
    let mut values: list<i32> = list();
    list_push(mutref values, 1);
    let bucket = Bucket { items: values };
    return take(bucket.items);
}
"""
        diagnostics, emitted = compile_text(source)
        self.assertIsNone(emitted)
        codes = [item.code for item in diagnostics.items]
        self.assertIn("NQ-BORROW-004", codes)

    def test_move_and_borrow_in_one_call_are_reported(self) -> None:
        source = """
type Bucket {
    items: list<i32>,
}

fn inspect(bucket: ref Bucket, moved: Bucket) -> i32 {
    return 0;
}

fn main() -> i32 {
    let mut values: list<i32> = list();
    list_push(mutref values, 1);
    let bucket = Bucket { items: values };
    return inspect(ref bucket, bucket);
}
"""
        diagnostics, emitted = compile_text(source)
        self.assertIsNone(emitted)
        codes = [item.code for item in diagnostics.items]
        self.assertIn("NQ-BORROW-007", codes)


if __name__ == "__main__":
    unittest.main()
