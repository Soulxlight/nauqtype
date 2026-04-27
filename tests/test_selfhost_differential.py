from __future__ import annotations

import re
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

from tests.test_support import (
    STAGE1_DRIVER_BUILD_TIMEOUT,
    built_stage1_driver,
)

class SelfhostDifferentialTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root = Path(__file__).resolve().parents[1]
        cls._driver_ctx = built_stage1_driver(timeout=STAGE1_DRIVER_BUILD_TIMEOUT)
        cls.driver_workspace, cls.driver_exe = cls._driver_ctx.__enter__()

    @classmethod
    def tearDownClass(cls) -> None:
        cls._driver_ctx.__exit__(None, None, None)

    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[1]

    def _write_modules(self, tmp: Path, modules: dict[str, str]) -> None:
        for name, text in modules.items():
            (tmp / f"{name}.nq").write_text(textwrap.dedent(text).strip() + "\n", encoding="utf-8")

    def _stage0_family(self, returncode: int, output: str) -> str:
        if returncode == 0:
            return "ACCEPT"
        families = set(re.findall(r"error\[(NQ-[A-Z]+)-\d+\]", output))
        if "NQ-BORROW" in families:
            return "BORROW"
        if "NQ-TYPE" in families:
            return "TYPE"
        if "NQ-RESOLVE" in families:
            return "RESOLVE"
        if "NQ-PARSE" in families:
            return "PARSE"
        return "OTHER"

    def _stage1_family(self, returncode: int, output: str) -> str:
        if returncode == 0:
            return "ACCEPT"
        if "stage1 limitation:" in output:
            return "STAGE1_LIMITATION"
        borrow_markers = [
            "use of moved value `",
            "borrow expressions are only valid as direct call arguments in v0.1",
            "cannot borrow moved value `",
            "moving out of fields is not supported in v0.1",
            "unsupported callee shape",
            "conflicting borrows of `",
            "cannot both move and borrow `",
        ]
        if any(marker in output for marker in borrow_markers):
            return "BORROW"
        if "unknown name" in output or "unknown type" in output:
            return "RESOLVE"
        type_markers = [
            "annotated local initializer does not match declared type",
            "return expression does not match function return type",
            "assignment value does not match target type",
            "call argument type does not match parameter type",
            "constructor payload type does not match variant payload type",
            "field access base",
            "field does not exist on base type",
            "struct literal",
            "condition must have type `bool`",
            "comparison operands must have matching types",
            "arithmetic operand must have integer type",
        ]
        if any(marker in output for marker in type_markers):
            return "TYPE"
        return "OTHER"

    def _run_stage0(self, modules: dict[str, str]) -> tuple[int, str]:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            self._write_modules(tmp, modules)
            result = subprocess.run(
                [sys.executable, "-m", "compiler.main", "check", str(tmp / "main.nq")],
                cwd=self.root,
                capture_output=True,
                text=True,
            )
            return result.returncode, (result.stdout + result.stderr).strip()

    def _run_stage1(self, modules: dict[str, str]) -> tuple[int, str]:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            self._write_modules(tmp, modules)
            result = subprocess.run(
                [str(self.driver_exe), "check", str(tmp / "main.nq")],
                cwd=self.root,
                capture_output=True,
                text=True,
                timeout=240,
            )
            return result.returncode, (result.stdout + result.stderr).strip()

    def _evaluate_case(
        self,
        name: str,
        modules: dict[str, str],
        *,
        expected_stage0: str,
        allowed_stage1: set[str],
    ) -> tuple[str, str, str, str, str, set[str]]:
        stage0_returncode, stage0_output = self._run_stage0(modules)
        stage1_returncode, stage1_output = self._run_stage1(modules)

        stage0_family = self._stage0_family(stage0_returncode, stage0_output)
        stage1_family = self._stage1_family(stage1_returncode, stage1_output)

        return (
            name,
            stage0_family,
            stage0_output,
            stage1_family,
            stage1_output,
            allowed_stage1,
        )

    def _assert_evaluated_case(
        self,
        result: tuple[str, str, str, str, str, set[str]],
        *,
        expected_stage0: str,
    ) -> None:
        name, stage0_family, stage0_output, stage1_family, stage1_output, allowed_stage1 = result
        self.assertEqual(stage0_family, expected_stage0, f"{name} stage0: {stage0_output}")
        self.assertIn(stage1_family, allowed_stage1, f"{name} stage1: {stage1_output}")

    def _assert_cases(
        self,
        cases: list[tuple[str, dict[str, str], str, set[str]]],
    ) -> None:
        for name, modules, expected_stage0, allowed_stage1 in cases:
            with self.subTest(name=name):
                result = self._evaluate_case(
                    name,
                    modules,
                    expected_stage0=expected_stage0,
                    allowed_stage1=allowed_stage1,
                )
                self._assert_evaluated_case(result, expected_stage0=expected_stage0)

    def test_differential_subset_corpus(self) -> None:
        cases = [
            (
                "arithmetic type mismatch",
                {
                    "main": """
                    fn main() -> i32 {
                        let value: i32 = true + 1;
                        return value;
                    }
                    """,
                },
                "TYPE",
                {"TYPE"},
            ),
            (
                "function call argument mismatch",
                {
                    "main": """
                    fn take(value: i32) -> i32 {
                        return value;
                    }

                    fn main() -> i32 {
                        return take(true);
                    }
                    """,
                },
                "TYPE",
                {"TYPE"},
            ),
            (
                "constructor payload mismatch",
                {
                    "main": """
                    enum parse_err {
                        bad_digit(i32),
                    }

                    fn main() -> i32 {
                        let value: parse_err = bad_digit(true);
                        match value {
                            bad_digit(_) => {
                                return 0;
                            },
                        }
                    }
                    """,
                },
                "TYPE",
                {"TYPE"},
            ),
            (
                "invalid field base",
                {
                    "main": """
                    fn main() -> i32 {
                        let value: i32 = true.text;
                        return value;
                    }
                    """,
                },
                "TYPE",
                {"TYPE"},
            ),
            (
                "missing struct field",
                {
                    "main": """
                    type pair {
                        left: i32,
                        right: i32,
                    }

                    fn main() -> i32 {
                        let value: pair = pair {
                            left: 1,
                        };
                        return value.left;
                    }
                    """,
                },
                "TYPE",
                {"TYPE"},
            ),
            (
                "mistyped struct field",
                {
                    "main": """
                    type pair {
                        left: i32,
                    }

                    fn main() -> i32 {
                        let value: pair = pair {
                            left: true,
                        };
                        return value.left;
                    }
                    """,
                },
                "TYPE",
                {"TYPE"},
            ),
            (
                "imported field acceptance",
                {
                    "helper": """
                    pub type pair {
                        left: i32,
                    }

                    pub fn make_pair() -> pair {
                        return pair {
                            left: 7,
                        };
                    }
                    """,
                    "main": """
                    use helper;

                    fn main() -> i32 {
                        let pair_value = make_pair();
                        return pair_value.left;
                    }
                    """,
                },
                "ACCEPT",
                {"ACCEPT"},
            ),
            (
                "nested field chain accept",
                {
                    "main": """
                    type inner {
                        right: i32,
                    }

                    type outer {
                        left: inner,
                    }

                    fn main() -> i32 {
                        let value: i32 = outer {
                            left: inner {
                                right: 3,
                            },
                        }.left.right;
                        return value;
                    }
                    """,
                },
                "ACCEPT",
                {"ACCEPT"},
            ),
            (
                "nested field chain second-hop missing field",
                {
                    "main": """
                    type inner {
                        right: i32,
                    }

                    type outer {
                        left: inner,
                    }

                    fn main() -> i32 {
                        let value: i32 = outer {
                            left: inner {
                                right: 3,
                            },
                        }.left.missing;
                        return value;
                    }
                    """,
                },
                "TYPE",
                {"TYPE"},
            ),
            (
                "nested field chain argument mismatch",
                {
                    "main": """
                    type inner {
                        right: bool,
                    }

                    type outer {
                        left: inner,
                    }

                    fn take(value: i32) -> i32 {
                        return value;
                    }

                    fn main() -> i32 {
                        return take(outer {
                            left: inner {
                                right: true,
                            },
                        }.left.right);
                    }
                    """,
                },
                "TYPE",
                {"TYPE"},
            ),
            (
                "contextual option constructor mismatch",
                {
                    "main": """
                    fn main() -> i32 {
                        let value: option<i32> = Some(true);
                        match value {
                            Some(inner) => {
                                return inner;
                            },
                            None => {
                                return 0;
                            },
                        }
                    }
                    """,
                },
                "TYPE",
                {"TYPE"},
            ),
            (
                "contextual list construction success",
                {
                    "main": """
                    fn main() -> i32 {
                        let items: list<i32> = list();
                        return list_len(ref items);
                    }
                    """,
                },
                "ACCEPT",
                {"ACCEPT"},
            ),
            (
                "assignment rhs builtin context mismatch",
                {
                    "main": """
                    fn main() -> i32 {
                        let mut value: option<i32> = Some(1);
                        value = Some(true);
                        match value {
                            Some(inner) => {
                                return inner;
                            },
                            None => {
                                return 0;
                            },
                        }
                    }
                    """,
                },
                "TYPE",
                {"TYPE"},
            ),
            (
                "constructor payload mismatch through composite expression",
                {
                    "main": """
                    type wrapper {
                        value: bool,
                    }

                    enum parse_err {
                        bad_digit(i32),
                    }

                    fn main() -> i32 {
                        let value: parse_err = bad_digit(wrapper {
                            value: true,
                        }.value);
                        match value {
                            bad_digit(_) => {
                                return 0;
                            },
                        }
                    }
                    """,
                },
                "TYPE",
                {"TYPE"},
            ),
            (
                "builtin inside variant payload mismatch",
                {
                    "main": """
                    enum wrapper {
                        hold(option<i32>),
                    }

                    fn main() -> i32 {
                        let value: wrapper = hold(Some(true));
                        match value {
                            hold(Some(number)) => {
                                return number;
                            },
                            hold(None) => {
                                return 0;
                            },
                        }
                    }
                    """,
                },
                "TYPE",
                {"TYPE"},
            ),
            (
                "contextual ok return mismatch",
                {
                    "main": """
                    fn bad() -> result<i32, io_err> {
                        return Ok("bad");
                    }

                    fn main() -> i32 {
                        let value = bad();
                        match value {
                            Ok(number) => {
                                return number;
                            },
                            Err(err) => {
                                return 0;
                            },
                        }
                    }
                    """,
                },
                "TYPE",
                {"TYPE"},
            ),
            (
                "pattern-bound payload mismatch",
                {
                    "main": """
                    fn main() -> i32 {
                        let value: option<i32> = Some(7);
                        match value {
                            Some(number) => {
                                let wrong: bool = number;
                                return 0;
                            },
                            None => {
                                return 0;
                            },
                        }
                    }
                    """,
                },
                "TYPE",
                {"TYPE"},
            ),
            (
                "match arm ok err return success",
                {
                    "main": """
                    fn promote(value: option<i32>) -> result<i32, i32> {
                        match value {
                            Some(number) => {
                                return Ok(number);
                            },
                            None => {
                                return Err(0);
                            },
                        }
                    }

                    fn main() -> i32 {
                        let value = promote(Some(7));
                        match value {
                            Ok(number) => {
                                return number;
                            },
                            Err(_) => {
                                return 0;
                            },
                        }
                    }
                    """,
                },
                "ACCEPT",
                {"ACCEPT"},
            ),
            (
                "non-name callee limitation",
                {
                    "main": """
                    fn take(value: i32) -> i32 {
                        return value;
                    }

                    fn main() -> i32 {
                        return (take)(1);
                    }
                    """,
                },
                "ACCEPT",
                {"STAGE1_LIMITATION"},
            ),
            (
                "borrow use after move on non-copy local",
                {
                    "main": """
                    type bucket {
                        items: list<i32>,
                    }

                    fn take(value: bucket) -> i32 {
                        return 0;
                    }

                    fn main() -> i32 {
                        let mut items: list<i32> = list();
                        list_push(mutref items, 1);
                        let bucket_value = bucket {
                            items: items,
                        };
                        take(bucket_value);
                        return take(bucket_value);
                    }
                    """,
                },
                "BORROW",
                {"BORROW"},
            ),
            (
                "borrow structural copy reuse",
                {
                    "main": """
                    type user {
                        age: i32,
                    }

                    fn take(value: user) -> i32 {
                        return value.age;
                    }

                    fn main() -> i32 {
                        let person = user {
                            age: 7,
                        };
                        take(person);
                        return take(person);
                    }
                    """,
                },
                "ACCEPT",
                {"ACCEPT"},
            ),
            (
                "borrow use after move across while",
                {
                    "main": """
                    type bucket {
                        items: list<i32>,
                    }

                    fn take(value: bucket) -> i32 {
                        return 0;
                    }

                    fn main() -> i32 {
                        let mut items: list<i32> = list();
                        list_push(mutref items, 1);
                        let bucket_value = bucket {
                            items: items,
                        };
                        while true {
                            take(bucket_value);
                        }
                        return 0;
                    }
                    """,
                },
                "BORROW",
                {"BORROW"},
            ),
            (
                "borrow moved value",
                {
                    "main": """
                    type bucket {
                        items: list<i32>,
                    }

                    fn take(value: bucket) -> i32 {
                        return 0;
                    }

                    fn inspect(value: ref bucket) -> i32 {
                        return 0;
                    }

                    fn main() -> i32 {
                        let mut items: list<i32> = list();
                        list_push(mutref items, 1);
                        let bucket_value = bucket {
                            items: items,
                        };
                        take(bucket_value);
                        return inspect(ref bucket_value);
                    }
                    """,
                },
                "BORROW",
                {"BORROW"},
            ),
            (
                "borrow conflicting ref mutref in one call",
                {
                    "main": """
                    fn probe(left: ref i32, right: mutref i32) -> unit {
                        return;
                    }

                    fn main() -> i32 {
                        let mut value = 1;
                        probe(ref value, mutref value);
                        return 0;
                    }
                    """,
                },
                "BORROW",
                {"BORROW"},
            ),
            (
                "borrow move and borrow in one call",
                {
                    "main": """
                    type bucket {
                        items: list<i32>,
                    }

                    fn inspect(left: ref bucket, moved: bucket) -> i32 {
                        return 0;
                    }

                    fn main() -> i32 {
                        let mut items: list<i32> = list();
                        list_push(mutref items, 1);
                        let bucket_value = bucket {
                            items: items,
                        };
                        return inspect(ref bucket_value, bucket_value);
                    }
                    """,
                },
                "BORROW",
                {"BORROW"},
            ),
            (
                "borrow moving out of non-copy field",
                {
                    "main": """
                    type bucket {
                        items: list<i32>,
                    }

                    fn take(values: list<i32>) -> i32 {
                        return 0;
                    }

                    fn main() -> i32 {
                        let mut values: list<i32> = list();
                        list_push(mutref values, 1);
                        let bucket_value = bucket {
                            items: values,
                        };
                        return take(bucket_value.items);
                    }
                    """,
                },
                "BORROW",
                {"BORROW"},
            ),
            (
                "borrow expression outside direct call arg",
                {
                    "main": """
                    fn main() -> i32 {
                        let value = 1;
                        let alias: ref i32 = ref value;
                        return 0;
                    }
                    """,
                },
                "BORROW",
                {"BORROW"},
            ),
            (
                "match scrutinee move behavior on non-copy values",
                {
                    "main": """
                    enum wrapper {
                        hold(list<i32>),
                    }

                    fn take(value: wrapper) -> i32 {
                        return 0;
                    }

                    fn main() -> i32 {
                        let mut values: list<i32> = list();
                        list_push(mutref values, 1);
                        let wrapped: wrapper = hold(values);
                        match wrapped {
                            hold(inner) => {
                                let ignored = list_len(ref inner);
                                return 0;
                            },
                        }
                        return take(wrapped);
                    }
                    """,
                },
                "BORROW",
                {"BORROW"},
            ),
            (
                "pattern-bound payload bindings remain usable inside arm",
                {
                    "main": """
                    enum wrapper {
                        hold(i32),
                    }

                    fn main() -> i32 {
                        let wrapped: wrapper = hold(7);
                        match wrapped {
                            hold(inner) => {
                                return inner;
                            },
                        }
                    }
                    """,
                },
                "ACCEPT",
                {"ACCEPT"},
            ),
        ]

        self._assert_cases(cases)

    def test_selfhost_stage1_performance_smoke(self) -> None:
        result = subprocess.run(
            [str(self.driver_exe), "check", str(self.driver_workspace / "main.nq")],
            cwd=self.root,
            capture_output=True,
            text=True,
            timeout=240,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertNotIn("stage1 limitation:", result.stdout + result.stderr)

    def test_selfhost_tree_has_no_stage1_limitations(self) -> None:
        result = subprocess.run(
            [str(self.driver_exe), "check", str(self.driver_workspace / "main.nq")],
            cwd=self.root,
            capture_output=True,
            text=True,
            timeout=240,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn("stage1 limitation:", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
