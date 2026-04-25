from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

from tests.test_support import SELFHOST_REFERENCE_TIMEOUT, run_copied_selfhost


class SelfhostDifferentialTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[1]
        self.selfhost_dir = self.root / "selfhost"
        self.selfhost_runtime_modules = [
            "ast.nq",
            "borrow.nq",
            "diag.nq",
            "handoff.nq",
            "ir.nq",
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
    collect_stmt_facts("{name}", ref {name}_tokens, mutref stmt_facts, mutref diags);
"""
            )

        return textwrap.dedent(
            f"""
            use ast;
            use borrow;
            use diag;
            use handoff;
            use ir;
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
                let mut stmt_facts: list<stmt_fact> = list();
                let mut resolved_bindings: list<typed_binding_fact> = list();
                let mut pattern_bindings: list<pattern_binding_fact> = list();
                let mut checked_modules: list<checked_module> = list();
                let mut checked_functions: list<checked_function> = list();
                let mut checked_bindings: list<checked_binding> = list();
                let mut checked_params: list<checked_param> = list();
                let mut checked_type_shapes: list<checked_type_shape> = list();
                let mut checked_type_decls: list<checked_type_decl> = list();
                let mut checked_field_decls: list<checked_field_decl> = list();
                let mut checked_enum_decls: list<checked_enum_decl> = list();
                let mut checked_variant_decls: list<checked_variant_decl> = list();
                let mut checked_variant_payload_decls: list<checked_variant_payload_decl> = list();
                let mut checked_blocks: list<checked_block> = list();
                let mut checked_statements: list<checked_stmt> = list();
                let mut checked_match_arms: list<checked_match_arm> = list();
                let mut checked_patterns: list<checked_pattern> = list();
                let mut checked_pattern_children: list<checked_pattern_child> = list();
                let mut checked_pattern_bindings: list<checked_pattern_binding> = list();
                let mut checked_expressions: list<checked_expr> = list();
                let mut checked_expr_children: list<checked_expr_child> = list();
                let mut checked_struct_fields: list<checked_struct_field_init> = list();
                let mut ir_programs: list<ir_program> = list();
                let mut ir_function_sigs: list<ir_function_sig> = list();
                let mut ir_functions: list<ir_function> = list();
                let mut ir_locals: list<ir_local> = list();
                let mut ir_blocks: list<ir_block> = list();
                let mut ir_statements: list<ir_stmt> = list();
                let mut ir_match_arms: list<ir_match_arm> = list();
                let mut ir_patterns: list<ir_pattern> = list();
                let mut ir_pattern_children: list<ir_pattern_child> = list();
                let mut ir_expressions: list<ir_expr> = list();
                let mut ir_expr_children: list<ir_expr_child> = list();
                let mut ir_field_values: list<ir_field_value> = list();
                let mut ir_type_shapes: list<ir_type_shape> = list();
                let mut ir_struct_decls: list<ir_struct_decl> = list();
                let mut ir_field_decls: list<ir_field_decl> = list();
                let mut ir_enum_decls: list<ir_enum_decl> = list();
                let mut ir_variant_decls: list<ir_variant_decl> = list();
                let mut ir_variant_payload_decls: list<ir_variant_payload_decl> = list();
                let mut diags: list<diag> = list();
{''.join(module_blocks)}
                resolve_modules(ref modules, ref uses, ref items, mutref diags);
                resolve_types(ref type_refs, ref uses, ref items, mutref diags);
                resolve_bodies(ref scopes, ref bindings, ref refs, ref uses, ref items, mutref diags);
                typecheck_modules(ref function_facts, ref variant_facts, ref call_facts, ref pattern_facts, ref uses, ref items, mutref diags);
                typecheck_value_facts(ref function_facts, ref function_param_facts, ref variant_facts, ref variant_payload_facts, ref scopes, ref typed_bindings, ref field_facts, ref match_arms, ref local_inits, ref return_facts, ref condition_facts, ref assignment_facts, ref uses, ref items, ref sources, mutref diags);
                collect_resolved_binding_facts(ref function_facts, ref function_param_facts, ref variant_facts, ref variant_payload_facts, ref scopes, ref typed_bindings, ref field_facts, ref match_arms, ref local_inits, ref uses, ref items, ref sources, mutref resolved_bindings, mutref pattern_bindings, mutref diags);
                let checked_summary = build_checked_handoff(ref function_facts, ref function_param_facts, ref variant_facts, ref variant_payload_facts, ref scopes, ref resolved_bindings, ref field_facts, ref match_arms, ref pattern_bindings, ref stmt_facts, ref uses, ref items, ref sources, mutref checked_modules, mutref checked_functions, mutref checked_bindings, mutref checked_params, mutref checked_type_shapes, mutref checked_type_decls, mutref checked_field_decls, mutref checked_enum_decls, mutref checked_variant_decls, mutref checked_variant_payload_decls, mutref checked_blocks, mutref checked_statements, mutref checked_match_arms, mutref checked_patterns, mutref checked_pattern_children, mutref checked_pattern_bindings, mutref checked_expressions, mutref checked_expr_children, mutref checked_struct_fields, mutref diags);
                let borrow_summary = check_checked_handoff_borrows(ref checked_functions, ref checked_bindings, ref checked_params, ref checked_type_decls, ref checked_field_decls, ref checked_enum_decls, ref checked_variant_decls, ref checked_variant_payload_decls, ref checked_blocks, ref checked_statements, ref checked_match_arms, ref checked_pattern_bindings, ref checked_expressions, ref checked_expr_children, ref checked_struct_fields, mutref diags);
                let ir_summary = build_ir_program(ref checked_functions, ref checked_bindings, ref checked_params, ref checked_type_shapes, ref checked_type_decls, ref checked_field_decls, ref checked_enum_decls, ref checked_variant_decls, ref checked_variant_payload_decls, ref checked_blocks, ref checked_statements, ref checked_match_arms, ref checked_patterns, ref checked_pattern_children, ref checked_pattern_bindings, ref checked_expressions, ref checked_expr_children, ref checked_struct_fields, mutref ir_programs, mutref ir_function_sigs, mutref ir_functions, mutref ir_locals, mutref ir_blocks, mutref ir_statements, mutref ir_match_arms, mutref ir_patterns, mutref ir_pattern_children, mutref ir_expressions, mutref ir_expr_children, mutref ir_field_values, mutref ir_type_shapes, mutref ir_struct_decls, mutref ir_field_decls, mutref ir_enum_decls, mutref ir_variant_decls, mutref ir_variant_payload_decls, mutref diags);

                if list_len(ref diags) > 0 {{
                    emit_all(ref diags);
                    return 1;
                }}
                if checked_summary.function_count < 1 or borrow_summary.function_count < checked_summary.function_count or ir_summary.function_count < checked_summary.function_count {{
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

        for name, modules, expected_stage0, allowed_stage1 in cases:
            with self.subTest(name=name):
                self._assert_case(name, modules, expected_stage0=expected_stage0, allowed_stage1=allowed_stage1)

    def test_selfhost_stage1_performance_smoke(self) -> None:
        result = run_copied_selfhost(timeout=SELFHOST_REFERENCE_TIMEOUT)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "stage1 front-end ok\n")
        self.assertNotIn("stage1 limitation:", result.stdout + result.stderr)

    def test_selfhost_tree_has_no_stage1_limitations(self) -> None:
        result = run_copied_selfhost(timeout=SELFHOST_REFERENCE_TIMEOUT)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("stage1 limitation:", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
