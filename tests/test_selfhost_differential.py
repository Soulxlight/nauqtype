from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


class SelfhostDifferentialTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[1]
        self.selfhost_dir = self.root / "selfhost"
        self.selfhost_runtime_modules = [
            "ast.nq",
            "diag.nq",
            "lexer.nq",
            "parser.nq",
            "resolve.nq",
            "source.nq",
            "token.nq",
            "typecheck.nq",
        ]

    def _write_modules(self, tmp: Path, modules: dict[str, str]) -> None:
        for name, text in modules.items():
            (tmp / f"{name}.nq").write_text(textwrap.dedent(text).strip() + "\n", encoding="utf-8")

    def _escape_nauq_string(self, text: str) -> str:
        return textwrap.dedent(text).strip().replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ")

    def _stage0_family(self, returncode: int, output: str) -> str:
        if returncode == 0:
            return "ACCEPT"
        families = set(re.findall(r"error\[(NQ-[A-Z]+)-\d+\]", output))
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

    def _build_stage1_probe(self, modules: dict[str, str]) -> str:
        module_blocks: list[str] = []
        for name, text in modules.items():
            escaped = self._escape_nauq_string(text)
            module_blocks.append(
                f"""
    let {name}_text = "{escaped}";
    let {name}_tokens = lex({name}_text);
    list_push(mutref modules, "{name}");
    list_push(mutref sources, make_source_file("{name}", {name}_text));
    parse_file("{name}", ref {name}_tokens, mutref items, mutref uses, mutref scopes, mutref bindings, mutref refs, mutref type_refs, mutref diags);
    collect_typecheck_facts("{name}", ref {name}_tokens, mutref function_facts, mutref function_param_facts, mutref variant_facts, mutref variant_payload_facts, mutref call_facts, mutref pattern_facts, mutref diags);
    collect_value_type_facts("{name}", ref {name}_tokens, mutref typed_bindings, mutref field_facts, mutref match_arms, mutref local_inits, mutref return_facts, mutref condition_facts, mutref assignment_facts, mutref diags);
"""
            )

        return textwrap.dedent(
            f"""
            use ast;
            use diag;
            use lexer;
            use parser;
            use resolve;
            use source;
            use typecheck;

            fn emit_all(diags: ref list<diag>) -> unit {{
                let mut index = 0;
                while index < list_len(ref diags) {{
                    let entry = list_get(ref diags, index);
                    match entry {{
                        Some(value) => {{
                            emit_diag(value);
                        }},
                        None => {{
                        }},
                    }}
                    index = index + 1;
                }}
                return;
            }}

            fn main() -> i32 {{
                let mut modules: list<str> = list();
                let mut sources: list<source_file> = list();
                let mut items: list<top_item> = list();
                let mut uses: list<module_use> = list();
                let mut scopes: list<body_scope> = list();
                let mut bindings: list<body_binding> = list();
                let mut refs: list<name_ref> = list();
                let mut type_refs: list<type_ref> = list();
                let mut function_facts: list<function_fact> = list();
                let mut function_param_facts: list<function_param_fact> = list();
                let mut variant_facts: list<variant_fact> = list();
                let mut variant_payload_facts: list<variant_payload_fact> = list();
                let mut call_facts: list<call_fact> = list();
                let mut pattern_facts: list<pattern_ctor_fact> = list();
                let mut typed_bindings: list<typed_binding_fact> = list();
                let mut field_facts: list<field_fact> = list();
                let mut match_arms: list<match_arm_fact> = list();
                let mut local_inits: list<local_init_fact> = list();
                let mut return_facts: list<return_expr_fact> = list();
                let mut condition_facts: list<condition_fact> = list();
                let mut assignment_facts: list<assignment_fact> = list();
                let mut diags: list<diag> = list();
{''.join(module_blocks)}
                resolve_modules(ref modules, ref uses, ref items, mutref diags);
                resolve_types(ref type_refs, ref uses, ref items, mutref diags);
                resolve_bodies(ref scopes, ref bindings, ref refs, ref uses, ref items, mutref diags);
                typecheck_modules(ref function_facts, ref variant_facts, ref call_facts, ref pattern_facts, ref uses, ref items, mutref diags);
                typecheck_value_facts(ref function_facts, ref function_param_facts, ref variant_facts, ref variant_payload_facts, ref scopes, ref typed_bindings, ref field_facts, ref match_arms, ref local_inits, ref return_facts, ref condition_facts, ref assignment_facts, ref uses, ref items, ref sources, mutref diags);

                if list_len(ref diags) > 0 {{
                    emit_all(ref diags);
                    return 1;
                }}
                return 0;
            }}
            """
        ).strip() + "\n"

    def _run_stage1(self, modules: dict[str, str]) -> tuple[int, str]:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            for module_name in self.selfhost_runtime_modules:
                shutil.copy(self.selfhost_dir / module_name, tmp / module_name)
            (tmp / "main.nq").write_text(self._build_stage1_probe(modules), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, "-m", "compiler.main", "run", str(tmp / "main.nq")],
                cwd=self.root,
                capture_output=True,
                text=True,
            )
            return result.returncode, (result.stdout + result.stderr).strip()

    def _assert_case(
        self,
        name: str,
        modules: dict[str, str],
        *,
        expected_stage0: str,
        allowed_stage1: set[str],
    ) -> None:
        stage0_returncode, stage0_output = self._run_stage0(modules)
        stage1_returncode, stage1_output = self._run_stage1(modules)

        stage0_family = self._stage0_family(stage0_returncode, stage0_output)
        stage1_family = self._stage1_family(stage1_returncode, stage1_output)

        self.assertEqual(stage0_family, expected_stage0, f"{name} stage0: {stage0_output}")
        self.assertIn(stage1_family, allowed_stage1, f"{name} stage1: {stage1_output}")

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
        ]

        for name, modules, expected_stage0, allowed_stage1 in cases:
            with self.subTest(name=name):
                self._assert_case(name, modules, expected_stage0=expected_stage0, allowed_stage1=allowed_stage1)

    def test_selfhost_stage1_performance_smoke(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "compiler.main", "run", str(self.root / "selfhost" / "main.nq")],
            cwd=self.root,
            capture_output=True,
            text=True,
            timeout=20,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "stage1 front-end ok\n")
        self.assertNotIn("stage1 limitation:", result.stdout + result.stderr)

    def test_selfhost_tree_has_no_stage1_limitations(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "compiler.main", "run", str(self.root / "selfhost" / "main.nq")],
            cwd=self.root,
            capture_output=True,
            text=True,
            timeout=20,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("stage1 limitation:", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
