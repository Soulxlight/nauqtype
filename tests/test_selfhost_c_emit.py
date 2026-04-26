from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

from tests.test_support import (
    ROOT,
    SELFHOST_REFERENCE_TIMEOUT,
    compile_and_run_c,
    copy_selfhost_workspace,
    ensure_bootstrap_deps,
    normalize_structural_c,
    run_stage0_selfhost,
)


class SelfhostCEmitTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = ROOT
        self.selfhost_dir = self.root / "selfhost"
        self.runtime_modules = [
            "ast.nq",
            "borrow.nq",
            "c_emit.nq",
            "diag.nq",
            "files.nq",
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

    def _build_emit_probe(self, modules: dict[str, str]) -> str:
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
    collect_typecheck_facts("{name}", ref {name}_tokens, mutref function_facts, mutref function_param_facts, mutref variant_facts, mutref variant_payload_facts, mutref const_facts, mutref call_facts, mutref pattern_facts, mutref diags);
    collect_value_type_facts("{name}", ref {name}_tokens, mutref typed_bindings, mutref field_facts, mutref match_arms, mutref local_inits, mutref return_facts, mutref condition_facts, mutref assignment_facts, mutref diags);
    collect_stmt_facts("{name}", ref {name}_tokens, mutref stmt_facts, mutref diags);
"""
            )

        return textwrap.dedent(
            f"""
            use ast;
            use borrow;
            use c_emit;
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
    let mut const_facts: list<const_fact> = list();
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
    let mut checked_consts: list<checked_const_decl> = list();
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
    let mut ir_consts: list<ir_const_decl> = list();
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
                let mut c_lines: list<str> = list();
                let mut diags: list<diag> = list();
{''.join(module_blocks)}
                resolve_modules(ref modules, ref uses, ref items, mutref diags);
                resolve_types(ref type_refs, ref uses, ref items, mutref diags);
                resolve_bodies(ref scopes, ref bindings, ref refs, ref uses, ref items, mutref diags);
                typecheck_modules(ref function_facts, ref variant_facts, ref call_facts, ref pattern_facts, ref uses, ref items, mutref diags);
                typecheck_value_facts(ref function_facts, ref function_param_facts, ref variant_facts, ref variant_payload_facts, ref const_facts, ref scopes, ref typed_bindings, ref field_facts, ref match_arms, ref local_inits, ref return_facts, ref condition_facts, ref assignment_facts, ref uses, ref items, ref sources, mutref diags);
                collect_resolved_binding_facts(ref function_facts, ref function_param_facts, ref variant_facts, ref variant_payload_facts, ref const_facts, ref scopes, ref typed_bindings, ref field_facts, ref match_arms, ref local_inits, ref uses, ref items, ref sources, mutref resolved_bindings, mutref pattern_bindings, mutref diags);
                let checked_summary = build_checked_handoff(ref function_facts, ref function_param_facts, ref variant_facts, ref variant_payload_facts, ref const_facts, ref scopes, ref resolved_bindings, ref field_facts, ref match_arms, ref pattern_bindings, ref stmt_facts, ref uses, ref items, ref sources, mutref checked_modules, mutref checked_functions, mutref checked_bindings, mutref checked_params, mutref checked_consts, mutref checked_type_shapes, mutref checked_type_decls, mutref checked_field_decls, mutref checked_enum_decls, mutref checked_variant_decls, mutref checked_variant_payload_decls, mutref checked_blocks, mutref checked_statements, mutref checked_match_arms, mutref checked_patterns, mutref checked_pattern_children, mutref checked_pattern_bindings, mutref checked_expressions, mutref checked_expr_children, mutref checked_struct_fields, mutref diags);
                let borrow_summary = check_checked_handoff_borrows(ref checked_functions, ref checked_bindings, ref checked_params, ref checked_type_decls, ref checked_field_decls, ref checked_enum_decls, ref checked_variant_decls, ref checked_variant_payload_decls, ref checked_blocks, ref checked_statements, ref checked_match_arms, ref checked_pattern_bindings, ref checked_expressions, ref checked_expr_children, ref checked_struct_fields, mutref diags);
                let ir_summary = build_ir_program(ref checked_functions, ref checked_bindings, ref checked_params, ref checked_consts, ref checked_type_shapes, ref checked_type_decls, ref checked_field_decls, ref checked_enum_decls, ref checked_variant_decls, ref checked_variant_payload_decls, ref checked_blocks, ref checked_statements, ref checked_match_arms, ref checked_patterns, ref checked_pattern_children, ref checked_pattern_bindings, ref checked_expressions, ref checked_expr_children, ref checked_struct_fields, mutref ir_programs, mutref ir_function_sigs, mutref ir_functions, mutref ir_locals, mutref ir_consts, mutref ir_blocks, mutref ir_statements, mutref ir_match_arms, mutref ir_patterns, mutref ir_pattern_children, mutref ir_expressions, mutref ir_expr_children, mutref ir_field_values, mutref ir_type_shapes, mutref ir_struct_decls, mutref ir_field_decls, mutref ir_enum_decls, mutref ir_variant_decls, mutref ir_variant_payload_decls, mutref diags);
                let c_summary = emit_c_program(ref ir_programs, ref ir_function_sigs, ref ir_functions, ref ir_locals, ref ir_consts, ref ir_blocks, ref ir_statements, ref ir_match_arms, ref ir_patterns, ref ir_pattern_children, ref ir_expressions, ref ir_expr_children, ref ir_field_values, ref ir_type_shapes, ref ir_struct_decls, ref ir_field_decls, ref ir_enum_decls, ref ir_variant_decls, ref ir_variant_payload_decls, mutref c_lines, mutref diags);
                if list_len(ref diags) > 0 {{
                    emit_all(ref diags);
                    return 1;
                }}
                if checked_summary.function_count < 1 or borrow_summary.function_count < checked_summary.function_count or ir_summary.function_count < checked_summary.function_count or c_summary.function_count < ir_summary.function_count or c_summary.line_count < 1 {{
                    print_line("stage1 c emit summary is incomplete");
                    return 1;
                }}
                let rendered = render_c_lines(ref c_lines);
                let write_result = write_rendered_c("generated.c", rendered);
                match write_result {{
                    Ok(_) => {{
                        return 0;
                    }},
                    Err(err) => {{
                        print_line(io_err_text(err));
                        return 1;
                    }},
                }}
            }}
            """
        ).strip() + "\n"

    def _run_stage1_emit(self, modules: dict[str, str]) -> tuple[int, str, str]:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            for module_name in self.runtime_modules:
                shutil.copy(self.selfhost_dir / module_name, tmp / module_name)
            (tmp / "main.nq").write_text(self._build_emit_probe(modules), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, "-m", "compiler.main", "run", str(tmp / "main.nq")],
                cwd=self.root,
                capture_output=True,
                text=True,
            )
            generated = ""
            generated_path = tmp / "generated.c"
            if generated_path.exists():
                generated = generated_path.read_text(encoding="utf-8")
            return result.returncode, (result.stdout + result.stderr).strip(), generated

    def _run_stage0(self, workspace: Path) -> subprocess.CompletedProcess[str]:
        return run_stage0_selfhost(workspace, timeout=180)

    def _emit_stage0_c(self, workspace: Path) -> str:
        output = workspace / "stage0.c"
        result = subprocess.run(
            [sys.executable, "-m", "compiler.main", "emit-c", str(workspace / "main.nq"), "-o", str(output)],
            cwd=self.root,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return output.read_text(encoding="utf-8")

    def test_stage1_c_emit_writes_expected_shapes(self) -> None:
        modules = {
            "main": """
            type pair {
                left: i32,
                right: i32,
            }

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

            fn main() -> i32 {
                let mut items: list<i32> = list();
                let mut number: i32 = 1;
                list_push(mutref items, 1);
                let current = pair { left: 1, right: list_len(ref items) };
                let wrapped_value = box(current.left);
                let seen = read(ref number);
                bump(mutref number);
                let write_result = write_file("stage1.txt", "ok");
                match wrapped_value {
                    box(inner) => {
                        match write_result {
                            Ok(_) => {
                                print_line("ok");
                                return inner + seen;
                            },
                            Err(err) => {
                                print_line(io_err_text(err));
                                return 1;
                            },
                        }
                    },
                }
            }
            """,
        }
        returncode, output, emitted = self._run_stage1_emit(modules)
        self.assertEqual(returncode, 0, output)
        self.assertIn('#include "runtime.h"', emitted)
        self.assertIn("typedef enum NQ_main__wrapped_Tag", emitted)
        self.assertIn("typedef struct NQ_main__pair", emitted)
        self.assertIn("static inline NQ_List__i32", emitted)
        self.assertIn("nq_write_file(", emitted)
        self.assertIn("switch (nq_tmp_1.tag)", emitted)
        self.assertIn("const int32_t* nqv_", emitted)
        self.assertIn("int main(int argc, char** argv)", emitted)
        self.assertIn("nq_init_process_args(argc, argv);", emitted)

    def test_stage1_c_emit_matches_stage0_structurally_on_locked_corpus(self) -> None:
        cases = {
            "hello_print": {
                "main.nq": """
                fn main() -> i32 {
                    print_line("hello");
                    return 0;
                }
                """,
            },
            "borrow_params": {
                "main.nq": """
                fn read(value: ref i32) -> i32 {
                    return value;
                }

                fn bump(value: mutref i32) -> unit {
                    value = value + 1;
                    return;
                }

                fn main() -> i32 {
                    let mut number: i32 = 1;
                    let seen = read(ref number);
                    bump(mutref number);
                    return seen + number;
                }
                """,
            },
            "struct_fields": {
                "main.nq": """
                type pair {
                    left: i32,
                    right: i32,
                }

                fn main() -> i32 {
                    let value = pair { left: 20, right: 22 };
                    return value.left + value.right;
                }
                """,
            },
            "enum_match": {
                "main.nq": """
                enum wrapped {
                    box(i32),
                    none,
                }

                fn main() -> i32 {
                    let item = box(42);
                    match item {
                        box(value) => {
                            return value;
                        },
                        none => {
                            return 0;
                        },
                    }
                }
                """,
            },
            "option_result": {
                "main.nq": """
                fn main() -> i32 {
                    let item: option<i32> = Some(40);
                    match item {
                        Some(value) => {
                            let outcome: result<i32, io_err> = Ok(value + 2);
                            match outcome {
                                Ok(inner) => {
                                    return inner;
                                },
                                Err(_) => {
                                    return 1;
                                },
                            }
                        },
                        None => {
                            return 0;
                        },
                    }
                }
                """,
            },
            "list_i32": {
                "main.nq": """
                fn main() -> i32 {
                    let mut items: list<i32> = list();
                    list_push(mutref items, 41);
                    list_push(mutref items, 1);
                    let first = list_get(ref items, 0);
                    match first {
                        Some(value) => {
                            return value + 1;
                        },
                        None => {
                            return list_len(ref items);
                        },
                    }
                }
                """,
            },
        }

        for name, files in cases.items():
            with self.subTest(case=name):
                with tempfile.TemporaryDirectory() as tmp_dir:
                    tmp = Path(tmp_dir)
                    for filename, content in files.items():
                        (tmp / filename).write_text(textwrap.dedent(content).strip() + "\n", encoding="utf-8")
                    stage0_c = self._emit_stage0_c(tmp)
                    modules = {path.stem: content for path, content in ((tmp / filename, content) for filename, content in files.items())}
                    returncode, output, stage1_c = self._run_stage1_emit(modules)
                    self.assertEqual(returncode, 0, output)
                    self.assertEqual(normalize_structural_c(stage1_c), normalize_structural_c(stage0_c))

    def test_stage1_emitted_c_compiles_and_runs_on_locked_corpus(self) -> None:
        ensure_bootstrap_deps()
        cases = {
            "hello_print": {
                "main.nq": """
                fn main() -> i32 {
                    print_line("hello");
                    return 0;
                }
                """,
            },
            "borrow_params": {
                "main.nq": """
                fn read(value: ref i32) -> i32 {
                    return value;
                }

                fn bump(value: mutref i32) -> unit {
                    value = value + 1;
                    return;
                }

                fn main() -> i32 {
                    let mut number: i32 = 1;
                    let seen = read(ref number);
                    bump(mutref number);
                    return seen + number;
                }
                """,
            },
            "struct_fields": {
                "main.nq": """
                type pair {
                    left: i32,
                    right: i32,
                }

                fn main() -> i32 {
                    let value = pair { left: 20, right: 22 };
                    return value.left + value.right;
                }
                """,
            },
            "enum_match": {
                "main.nq": """
                enum wrapped {
                    box(i32),
                    none,
                }

                fn main() -> i32 {
                    let item = box(42);
                    match item {
                        box(value) => {
                            return value;
                        },
                        none => {
                            return 0;
                        },
                    }
                }
                """,
            },
            "option_result": {
                "main.nq": """
                fn main() -> i32 {
                    let item: option<i32> = Some(40);
                    match item {
                        Some(value) => {
                            let outcome: result<i32, io_err> = Ok(value + 2);
                            match outcome {
                                Ok(inner) => {
                                    return inner;
                                },
                                Err(_) => {
                                    return 1;
                                },
                            }
                        },
                        None => {
                            return 0;
                        },
                    }
                }
                """,
            },
            "list_i32": {
                "main.nq": """
                fn main() -> i32 {
                    let mut items: list<i32> = list();
                    list_push(mutref items, 41);
                    list_push(mutref items, 1);
                    let first = list_get(ref items, 0);
                    match first {
                        Some(value) => {
                            return value + 1;
                        },
                        None => {
                            return list_len(ref items);
                        },
                    }
                }
                """,
            },
        }

        for name, files in cases.items():
            with self.subTest(case=name):
                with tempfile.TemporaryDirectory() as tmp_dir:
                    tmp = Path(tmp_dir)
                    for filename, content in files.items():
                        (tmp / filename).write_text(textwrap.dedent(content).strip() + "\n", encoding="utf-8")
                    stage0_result = self._run_stage0(tmp)
                    self.assertEqual(stage0_result.stderr, "")

                    modules = {Path(filename).stem: content for filename, content in files.items()}
                    returncode, output, stage1_c = self._run_stage1_emit(modules)
                    self.assertEqual(returncode, 0, output)

                    stage1_path = tmp / "stage1.c"
                    stage1_path.write_text(stage1_c, encoding="utf-8")
                    stage1_result = compile_and_run_c(stage1_path, cwd=tmp)
                    self.assertEqual(stage1_result.returncode, stage0_result.returncode, stage1_result.stdout + stage1_result.stderr)
                    self.assertEqual(stage1_result.stdout, stage0_result.stdout)

    def test_copied_selfhost_emits_and_runs_generated_c(self) -> None:
        ensure_bootstrap_deps()
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp_dir:
            tmp = Path(tmp_dir)
            copy_selfhost_workspace(tmp)
            result = subprocess.run(
                [sys.executable, "-m", "compiler.main", "run", str(tmp / "main.nq")],
                cwd=self.root,
                capture_output=True,
                text=True,
                timeout=SELFHOST_REFERENCE_TIMEOUT,
            )
            combined = result.stdout + result.stderr
            self.assertEqual(result.returncode, 0, combined)
            self.assertIn("stage1 front-end ok", result.stdout)
            self.assertNotIn("stage1 limitation", combined)
            self.assertNotIn("stage1 c error:", combined)
            emitted_c = tmp / "build" / "main.c"
            self.assertTrue(emitted_c.exists(), f"missing emitted C at {emitted_c}")
            rerun = compile_and_run_c(emitted_c, cwd=tmp)
            self.assertEqual(rerun.returncode, 0, rerun.stdout + rerun.stderr)
            self.assertIn("stage1 front-end ok", rerun.stdout)


if __name__ == "__main__":
    unittest.main()
