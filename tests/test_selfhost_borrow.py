from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

from tests.test_support import run_copied_selfhost


class SelfhostBorrowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[1]
        self.selfhost_dir = self.root / "selfhost"
        self.runtime_modules = [
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
        self.borrow_markers = [
            "use of moved value `",
            "borrow expressions are only valid as direct call arguments in v0.1",
            "cannot borrow moved value `",
            "moving out of fields is not supported in v0.1",
            "unsupported callee shape",
            "conflicting borrows of `",
            "cannot both move and borrow `",
        ]

    def _write_modules(self, tmp: Path, modules: dict[str, str]) -> None:
        for name, text in modules.items():
            (tmp / f"{name}.nq").write_text(textwrap.dedent(text).strip() + "\n", encoding="utf-8")

    def _escape_nauq_string(self, text: str) -> str:
        return textwrap.dedent(text).strip().replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ")

    def _build_probe(self, modules: dict[str, str]) -> str:
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

    def _run_probe(self, modules: dict[str, str]) -> tuple[int, str]:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            for module_name in self.runtime_modules:
                shutil.copy(self.selfhost_dir / module_name, tmp / module_name)
            (tmp / "main.nq").write_text(self._build_probe(modules), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, "-m", "compiler.main", "run", str(tmp / "main.nq")],
                cwd=self.root,
                capture_output=True,
                text=True,
            )
            return result.returncode, (result.stdout + result.stderr).strip()

    def test_stage1_borrow_reports_use_after_move(self) -> None:
        modules = {
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
        }
        returncode, output = self._run_probe(modules)
        self.assertNotEqual(returncode, 0, output)
        self.assertIn("use of moved value `bucket_value`", output)

    def test_stage1_borrow_allows_structural_copy_reuse(self) -> None:
        modules = {
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
        }
        returncode, output = self._run_probe(modules)
        self.assertEqual(returncode, 0, output)

    def test_stage1_borrow_reports_borrow_of_moved_value(self) -> None:
        modules = {
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
        }
        returncode, output = self._run_probe(modules)
        self.assertNotEqual(returncode, 0, output)
        self.assertIn("cannot borrow moved value `bucket_value`", output)

    def test_stage1_borrow_reports_conflicting_borrows(self) -> None:
        modules = {
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
        }
        returncode, output = self._run_probe(modules)
        self.assertNotEqual(returncode, 0, output)
        self.assertIn("conflicting borrows of `value` in one call", output)

    def test_stage1_borrow_reports_move_and_borrow_in_one_call(self) -> None:
        modules = {
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
        }
        returncode, output = self._run_probe(modules)
        self.assertNotEqual(returncode, 0, output)
        self.assertIn("cannot both move and borrow `bucket_value` in one call", output)

    def test_stage1_borrow_reports_field_move(self) -> None:
        modules = {
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
        }
        returncode, output = self._run_probe(modules)
        self.assertNotEqual(returncode, 0, output)
        self.assertIn("moving out of fields is not supported in v0.1", output)

    def test_stage1_borrow_reports_non_call_borrow_expr(self) -> None:
        modules = {
            "main": """
            fn main() -> i32 {
                let value = 1;
                let alias: ref i32 = ref value;
                return 0;
            }
            """,
        }
        returncode, output = self._run_probe(modules)
        self.assertNotEqual(returncode, 0, output)
        self.assertIn("borrow expressions are only valid as direct call arguments in v0.1", output)

    def test_selfhost_tree_passes_stage1_borrow_trust(self) -> None:
        result = run_copied_selfhost()
        output = (result.stdout + result.stderr).strip()
        self.assertEqual(result.returncode, 0, output)
        self.assertNotIn("stage1 limitation", output)
        for marker in self.borrow_markers:
            self.assertNotIn(marker, output)
        self.assertIn("stage1 front-end ok", output)


if __name__ == "__main__":
    unittest.main()
