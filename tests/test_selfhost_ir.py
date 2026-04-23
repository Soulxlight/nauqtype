from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

from tests.test_support import run_copied_selfhost


class SelfhostIRTests(unittest.TestCase):
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

    def _escape_nauq_string(self, text: str) -> str:
        return textwrap.dedent(text).strip().replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ")

    def _build_probe(self, modules: dict[str, str], assertions: list[str]) -> str:
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

        checks = "\n".join(assertions)

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

                let mut failures = 0;
{checks}
                if checked_summary.function_count < 1 or borrow_summary.function_count < checked_summary.function_count or ir_summary.function_count < checked_summary.function_count or ir_summary.expression_count < 1 {{
                    print_line("ir summary did not capture the lowered program");
                    failures = failures + 1;
                }}

                if failures > 0 {{
                    return 1;
                }}
                return 0;
            }}
            """
        ).strip() + "\n"

    def _run_probe(self, modules: dict[str, str], assertions: list[str]) -> tuple[int, str]:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            for module_name in self.runtime_modules:
                shutil.copy(self.selfhost_dir / module_name, tmp / module_name)
            (tmp / "main.nq").write_text(self._build_probe(modules, assertions), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, "-m", "compiler.main", "run", str(tmp / "main.nq")],
                cwd=self.root,
                capture_output=True,
                text=True,
            )
            return result.returncode, (result.stdout + result.stderr).strip()

    def test_ir_lowers_control_flow_and_metadata(self) -> None:
        modules = {
            "util": """
            pub type pair {
                left: i32,
                right: i32,
            }

            pub fn make_pair(value: i32) -> pair {
                return pair {
                    left: value,
                    right: value + 1,
                };
            }

            pub enum parse_err {
                bad(i32),
            }
            """,
            "main": """
            use util;

            fn main() -> i32 {
                let mut value: i32 = 0;
                let current: pair = make_pair(value);

                if current.left < 10 {
                    value = current.right;
                }

                while value < 5 {
                    value = value + 1;
                }

                let err_value: parse_err = bad(current.left);
                match err_value {
                    bad(code) => {
                        return code;
                    },
                }
            }
            """,
        }
        assertions = [
            '                let main_fn = ir_lookup_function_id(ref ir_functions, "main::main");',
            '                if main_fn < 0 {',
            '                    print_line("missing lowered main function");',
            "                    failures = failures + 1;",
            "                }",
            '                if not ir_has_function_internal_name(ref ir_functions, "util::make_pair") {',
            '                    print_line("missing lowered util::make_pair function");',
            "                    failures = failures + 1;",
            "                }",
            '                if not ir_has_function_sig(ref ir_function_sigs, "util::make_pair", 1) {',
            '                    print_line("missing lowered util::make_pair signature");',
            "                    failures = failures + 1;",
            "                }",
            '                if not ir_has_named_type_shape(ref ir_type_shapes, "pair", "util") {',
            '                    print_line("missing lowered named type origin for util::pair");',
            "                    failures = failures + 1;",
            "                }",
            '                if not ir_has_root_block(ref ir_functions, ref ir_blocks, "main::main") {',
            '                    print_line("missing lowered root block mapping for main::main");',
            "                    failures = failures + 1;",
            "                }",
            '                if not ir_has_stmt_kind(ref ir_statements, main_fn, ir_stmt_if) {',
            '                    print_line("missing lowered if statement");',
            "                    failures = failures + 1;",
            "                }",
            '                if not ir_has_stmt_kind(ref ir_statements, main_fn, ir_stmt_while) {',
            '                    print_line("missing lowered while statement");',
            "                    failures = failures + 1;",
            "                }",
            '                if not ir_has_stmt_kind(ref ir_statements, main_fn, ir_stmt_match) {',
            '                    print_line("missing lowered match statement");',
            "                    failures = failures + 1;",
            "                }",
            '                if not ir_has_call_target(ref ir_expressions, main_fn, "make_pair", "util") {',
            '                    print_line("missing lowered function call target");',
            "                    failures = failures + 1;",
            "                }",
            '                if not ir_has_variant_expr(ref ir_expressions, main_fn, "bad") {',
            '                    print_line("missing lowered constructor target");',
            "                    failures = failures + 1;",
            "                }",
            '                if not ir_has_field_expr(ref ir_expressions, main_fn, "left", "pair", "util") {',
            '                    print_line("missing lowered field access");',
            "                    failures = failures + 1;",
            "                }",
            '                if not ir_has_struct_decl(ref ir_struct_decls, "util", "pair") {',
            '                    print_line("missing lowered struct declaration");',
            "                    failures = failures + 1;",
            "                }",
            '                if not ir_has_variant_decl(ref ir_variant_decls, "util", "parse_err", "bad", 1) {',
            '                    print_line("missing lowered variant declaration");',
            "                    failures = failures + 1;",
            "                }",
        ]
        returncode, output = self._run_probe(modules, assertions)
        self.assertEqual(returncode, 0, output)

    def test_ir_lowers_borrow_nodes_and_pattern_locals(self) -> None:
        modules = {
            "main": """
            enum wrapped {
                box(i32),
            }

            fn read(value: ref i32) -> i32 {
                return value;
            }

            fn bump(value: mutref i32) -> unit {
                value = value + 1;
                return;
            }

            fn unwrap(item: wrapped) -> i32 {
                match item {
                    box(inner) => {
                        return inner;
                    },
                }
            }

            fn main() -> i32 {
                let mut number: i32 = 1;
                let seen: i32 = read(ref number);
                bump(mutref number);
                number = number + 1;
                return unwrap(box(seen + number));
            }
            """,
        }
        assertions = [
            '                let read_fn = ir_lookup_function_id(ref ir_functions, "main::read");',
            '                let unwrap_fn = ir_lookup_function_id(ref ir_functions, "main::unwrap");',
            '                let main_fn = ir_lookup_function_id(ref ir_functions, "main::main");',
            '                if read_fn < 0 or unwrap_fn < 0 or main_fn < 0 {',
            '                    print_line("missing lowered function ids");',
            "                    failures = failures + 1;",
            "                }",
            '                if not ir_has_ref_local(ref ir_locals, read_fn, "value", false) {',
            '                    print_line("missing lowered ref param truth");',
            "                    failures = failures + 1;",
            "                }",
            '                if not ir_has_param_local(ref ir_locals, read_fn, "value", 0) {',
            '                    print_line("missing lowered param order truth");',
            "                    failures = failures + 1;",
            "                }",
            '                if not ir_has_ref_local(ref ir_locals, ir_lookup_function_id(ref ir_functions, "main::bump"), "value", true) {',
            '                    print_line("missing lowered mutref param truth");',
            "                    failures = failures + 1;",
            "                }",
            '                if not ir_has_borrow_expr(ref ir_expressions, main_fn, false) {',
            '                    print_line("missing lowered ref expression");',
            "                    failures = failures + 1;",
            "                }",
            '                if not ir_has_borrow_expr(ref ir_expressions, main_fn, true) {',
            '                    print_line("missing lowered mutref expression");',
            "                    failures = failures + 1;",
            "                }",
            '                if not ir_has_name_expr_local(ref ir_expressions, read_fn, "value") {',
            '                    print_line("missing lowered local-backed name expression");',
            "                    failures = failures + 1;",
            "                }",
            '                if not ir_has_pattern_local(ref ir_patterns, unwrap_fn, "inner") {',
            '                    print_line("missing lowered pattern local");',
            "                    failures = failures + 1;",
            "                }",
            '                if not ir_has_variant_expr(ref ir_expressions, main_fn, "box") {',
            '                    print_line("missing lowered variant expression");',
            "                    failures = failures + 1;",
            "                }",
        ]
        returncode, output = self._run_probe(modules, assertions)
        self.assertEqual(returncode, 0, output)

    def test_selfhost_tree_lowers_without_ir_errors(self) -> None:
        result = run_copied_selfhost()
        output = (result.stdout + result.stderr).strip()
        self.assertEqual(result.returncode, 0, output)
        self.assertNotIn("stage1 limitation", output)
        self.assertNotIn("stage1 ir error:", output)
        self.assertIn("stage1 front-end ok", output)


if __name__ == "__main__":
    unittest.main()
