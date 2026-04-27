from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


class IntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[1]

    def run_program(self, path: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-m", "compiler.main", "run", str(path)],
            cwd=self.root,
            capture_output=True,
            text=True,
        )

    def run_example(self, name: str) -> subprocess.CompletedProcess[str]:
        return self.run_program(self.root / "examples" / name)

    def run_workspace_program(self, workspace: Path, entry_name: str = "main.nq") -> subprocess.CompletedProcess[str]:
        return self.run_program(workspace / entry_name)

    def copy_selfhost_support(self, workspace: Path) -> None:
        for module in ("ast.nq", "diag.nq", "files.nq", "lexer.nq", "parser.nq", "source.nq", "text.nq", "token.nq"):
            shutil.copy(self.root / "selfhost" / module, workspace / module)

    def write_workspace_files(self, workspace: Path, files: dict[str, str]) -> None:
        for name, text in files.items():
            (workspace / name).write_text(textwrap.dedent(text).strip() + "\n", encoding="utf-8")

    def write_loader_probe(self, workspace: Path, entry_module: str) -> None:
        (workspace / "main.nq").write_text(
            textwrap.dedent(
                f"""
                use ast;
                use diag;
                use files;
                use lexer;
                use parser;
                use source;

                fn list_contains(items: ref list<str>, target: str) -> bool {{
                    let mut index = 0;
                    while index < list_len(ref items) {{
                        let entry = list_get(ref items, index);
                        match entry {{
                            Some(value) => {{
                                if value == target {{
                                    return true;
                                }}
                            }},
                            None => {{
                            }},
                        }}
                        index = index + 1;
                    }}
                    return false;
                }}

                fn queue_if_missing(pending: mutref list<str>, seen: ref list<str>, name: str) -> unit {{
                    if list_contains(ref seen, name) {{
                        return;
                    }}
                    if list_contains(ref pending, name) {{
                        return;
                    }}
                    list_push(mutref pending, name);
                    return;
                }}

                fn module_reaches_start(start: str, uses: ref list<module_use>) -> bool {{
                    let mut pending: list<str> = list();
                    let mut seen: list<str> = list();
                    let mut cursor = 0;
                    list_push(mutref pending, start);
                    while cursor < list_len(ref pending) {{
                        let current = list_get(ref pending, cursor);
                        match current {{
                            Some(module_name) => {{
                                if not list_contains(ref seen, module_name) {{
                                    list_push(mutref seen, module_name);
                                    let mut use_index = 0;
                                    while use_index < list_len(ref uses) {{
                                        let edge = list_get(ref uses, use_index);
                                        match edge {{
                                            Some(value) => {{
                                                if value.module == module_name {{
                                                    if value.name == start {{
                                                        return true;
                                                    }}
                                                    queue_if_missing(mutref pending, ref seen, value.name);
                                                }}
                                            }},
                                            None => {{
                                            }},
                                        }}
                                        use_index = use_index + 1;
                                    }}
                                }}
                            }},
                            None => {{
                            }},
                        }}
                        cursor = cursor + 1;
                    }}
                    return false;
                }}

                fn detect_import_cycles(modules: ref list<str>, uses: ref list<module_use>, diags: mutref list<diag>) -> unit {{
                    let mut index = 0;
                    while index < list_len(ref modules) {{
                        let entry = list_get(ref modules, index);
                        match entry {{
                            Some(module_name) => {{
                                if module_reaches_start(module_name, ref uses) {{
                                    list_push(mutref diags, make_diag(module_name, 0, "import cycle detected"));
                                    return;
                                }}
                            }},
                            None => {{
                            }},
                        }}
                        index = index + 1;
                    }}
                    return;
                }}

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

                fn analyze_module(name: str, pending: mutref list<str>, seen: ref list<str>, loaded: mutref list<str>, sources: mutref list<source_file>, uses: mutref list<module_use>, items: mutref list<top_item>, scopes: mutref list<body_scope>, bindings: mutref list<body_binding>, refs: mutref list<name_ref>, type_refs: mutref list<type_ref>, diags: mutref list<diag>) -> unit {{
                    let loaded_file = read_named_module(name);
                    match loaded_file {{
                        Ok(file) => {{
                            list_push(mutref loaded, name);
                            list_push(mutref sources, file);
                            let tokens = lex(file.text);
                            let imports = extract_uses(ref tokens);
                            let mut import_index = 0;
                            while import_index < list_len(ref imports) {{
                                let entry = list_get(ref imports, import_index);
                                match entry {{
                                    Some(import_name) => {{
                                        queue_if_missing(mutref pending, ref seen, import_name);
                                    }},
                                    None => {{
                                    }},
                                }}
                                import_index = import_index + 1;
                            }}
                            parse_file(file.name, ref tokens, mutref items, mutref uses, mutref scopes, mutref bindings, mutref refs, mutref type_refs, mutref diags);
                        }},
                        Err(err) => {{
                            list_push(mutref diags, make_diag(name, 0, io_err_text(err)));
                        }},
                    }}
                    return;
                }}

                fn main() -> i32 {{
                    let mut pending: list<str> = list();
                    let mut seen: list<str> = list();
                    let mut loaded: list<str> = list();
                    let mut sources: list<source_file> = list();
                    let mut uses: list<module_use> = list();
                    let mut items: list<top_item> = list();
                    let mut scopes: list<body_scope> = list();
                    let mut bindings: list<body_binding> = list();
                    let mut refs: list<name_ref> = list();
                    let mut type_refs: list<type_ref> = list();
                    let mut diags: list<diag> = list();
                    let mut cursor = 0;

                    list_push(mutref pending, "{entry_module}");

                    while cursor < list_len(ref pending) {{
                        let current = list_get(ref pending, cursor);
                        match current {{
                            Some(name) => {{
                                if not list_contains(ref seen, name) {{
                                    list_push(mutref seen, name);
                                    analyze_module(name, mutref pending, ref seen, mutref loaded, mutref sources, mutref uses, mutref items, mutref scopes, mutref bindings, mutref refs, mutref type_refs, mutref diags);
                                }}
                            }},
                            None => {{
                            }},
                        }}
                        cursor = cursor + 1;
                    }}

                    detect_import_cycles(ref loaded, ref uses, mutref diags);
                    if list_len(ref diags) > 0 {{
                        emit_all(ref diags);
                        return 1;
                    }}
                    return 0;
                }}
                """
            ).strip()
            + "\n",
            encoding="utf-8",
        )

    def test_hello_runs(self) -> None:
        result = self.run_example("hello.nq")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "Hello, Nauqtype!\n")

    def test_result_program_runs(self) -> None:
        result = self.run_example("result_handling.nq")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_mutation_program_runs(self) -> None:
        result = self.run_example("mutate_counter.nq")
        self.assertEqual(result.returncode, 42, result.stderr)

    def test_while_program_runs(self) -> None:
        result = self.run_example("while_counter.nq")
        self.assertEqual(result.returncode, 5, result.stderr)

    def test_fibonacci_program_runs(self) -> None:
        result = self.run_example("fibonacci.nq")
        self.assertEqual(result.returncode, 55, result.stderr)

    def test_review_contracts_program_runs(self) -> None:
        result = self.run_example("review_contracts.nq")
        self.assertEqual(result.returncode, 42, result.stderr)
        self.assertEqual(result.stdout, "Hello, contracts!\n")

    def test_list_program_runs(self) -> None:
        result = self.run_example("list_sum.nq")
        self.assertEqual(result.returncode, 42, result.stderr)

    def test_read_file_program_runs(self) -> None:
        result = self.run_example("read_file_len.nq")
        self.assertEqual(result.returncode, 6, result.stderr)

    def test_multi_file_program_runs(self) -> None:
        result = self.run_example("multi_file_main.nq")
        self.assertEqual(result.returncode, 7, result.stderr)

    def test_selfhost_stage1_runs(self) -> None:
        result = self.run_program(self.root / "selfhost" / "main.nq")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "stage1 front-end ok\n")

    def test_selfhost_loader_supports_flat_root_module_names(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            workspace = Path(tmp_dir)
            self.copy_selfhost_support(workspace)
            self.write_loader_probe(workspace, "entry")
            self.write_workspace_files(
                workspace,
                {
                    "entry.nq": """
                    use custom_mod;

                    fn main() -> i32 {
                        return 0;
                    }
                    """,
                    "custom_mod.nq": """
                    pub fn helper() -> i32 {
                        return 7;
                    }
                    """,
                },
            )
            result = self.run_workspace_program(workspace)
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_selfhost_loader_reports_missing_module(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            workspace = Path(tmp_dir)
            self.copy_selfhost_support(workspace)
            self.write_loader_probe(workspace, "entry")
            self.write_workspace_files(
                workspace,
                {
                    "entry.nq": """
                    use ghost;

                    fn main() -> i32 {
                        return 0;
                    }
                    """,
                },
            )
            result = self.run_workspace_program(workspace)
            self.assertEqual(result.returncode, 1)
            self.assertIn("failed to open file", result.stdout + result.stderr)

    def test_selfhost_loader_detects_import_cycles(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            workspace = Path(tmp_dir)
            self.copy_selfhost_support(workspace)
            self.write_loader_probe(workspace, "entry")
            self.write_workspace_files(
                workspace,
                {
                    "entry.nq": """
                    use a;

                    fn main() -> i32 {
                        return 0;
                    }
                    """,
                    "a.nq": """
                    use b;

                    pub fn a_value() -> i32 {
                        return 1;
                    }
                    """,
                    "b.nq": """
                    use entry;

                    pub fn b_value() -> i32 {
                        return 2;
                    }
                    """,
                },
            )
            result = self.run_workspace_program(workspace)
            self.assertEqual(result.returncode, 1)
            self.assertIn("import cycle detected", result.stdout + result.stderr)

    def test_selfhost_resolve_probe_runs(self) -> None:
        result = self.run_program(self.root / "selfhost" / "resolve_probe.nq")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_selfhost_resolve_collision_probe_reports_error(self) -> None:
        result = self.run_program(self.root / "selfhost" / "resolve_collision_probe.nq")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_selfhost_body_resolve_probe_runs(self) -> None:
        result = self.run_program(self.root / "selfhost" / "body_resolve_probe.nq")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_selfhost_body_resolve_error_probe_reports_error(self) -> None:
        result = self.run_program(self.root / "selfhost" / "body_resolve_error_probe.nq")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_selfhost_pattern_resolve_probe_runs(self) -> None:
        result = self.run_program(self.root / "selfhost" / "pattern_resolve_probe.nq")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_selfhost_pattern_resolve_error_probe_reports_error(self) -> None:
        result = self.run_program(self.root / "selfhost" / "pattern_resolve_error_probe.nq")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_selfhost_hidden_import_body_error_probe_reports_error(self) -> None:
        result = self.run_program(self.root / "selfhost" / "hidden_import_body_error_probe.nq")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_selfhost_hidden_import_pattern_error_probe_reports_error(self) -> None:
        result = self.run_program(self.root / "selfhost" / "hidden_import_pattern_error_probe.nq")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_selfhost_expression_resolve_error_probe_reports_error(self) -> None:
        result = self.run_program(self.root / "selfhost" / "expression_resolve_error_probe.nq")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_selfhost_call_value_class_error_probe_reports_error(self) -> None:
        result = self.run_program(self.root / "selfhost" / "call_value_class_error_probe.nq")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_selfhost_hidden_import_struct_literal_error_probe_reports_error(self) -> None:
        result = self.run_program(self.root / "selfhost" / "hidden_import_struct_literal_error_probe.nq")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_selfhost_type_resolve_probe_runs(self) -> None:
        result = self.run_program(self.root / "selfhost" / "type_resolve_probe.nq")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_selfhost_unknown_type_error_probe_reports_error(self) -> None:
        result = self.run_program(self.root / "selfhost" / "unknown_type_error_probe.nq")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_selfhost_hidden_import_type_error_probe_reports_error(self) -> None:
        result = self.run_program(self.root / "selfhost" / "hidden_import_type_error_probe.nq")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_selfhost_typecheck_probe_runs(self) -> None:
        result = self.run_program(self.root / "selfhost" / "typecheck_probe.nq")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_selfhost_call_arity_typecheck_error_probe_reports_error(self) -> None:
        result = self.run_program(self.root / "selfhost" / "call_arity_typecheck_error_probe.nq")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_selfhost_pattern_arity_typecheck_error_probe_reports_error(self) -> None:
        result = self.run_program(self.root / "selfhost" / "pattern_arity_typecheck_error_probe.nq")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_selfhost_main_signature_typecheck_error_probe_reports_error(self) -> None:
        result = self.run_program(self.root / "selfhost" / "main_signature_typecheck_error_probe.nq")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_selfhost_value_flow_typecheck_probe_runs(self) -> None:
        result = self.run_program(self.root / "selfhost" / "value_flow_typecheck_probe.nq")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_selfhost_multi_module_value_flow_error_probe_reports_error(self) -> None:
        result = self.run_program(self.root / "selfhost" / "multi_module_value_flow_error_probe.nq")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_selfhost_assignment_value_typecheck_probe_runs(self) -> None:
        result = self.run_program(self.root / "selfhost" / "assignment_value_typecheck_probe.nq")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_selfhost_assignment_typecheck_error_probe_reports_error(self) -> None:
        result = self.run_program(self.root / "selfhost" / "assignment_typecheck_error_probe.nq")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_selfhost_inferred_local_typecheck_probe_runs(self) -> None:
        result = self.run_program(self.root / "selfhost" / "inferred_local_typecheck_probe.nq")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_selfhost_inferred_local_return_typecheck_error_probe_reports_error(self) -> None:
        result = self.run_program(self.root / "selfhost" / "inferred_local_return_typecheck_error_probe.nq")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_selfhost_field_access_inferred_local_typecheck_probe_runs(self) -> None:
        result = self.run_program(self.root / "selfhost" / "field_access_inferred_local_typecheck_probe.nq")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_selfhost_field_access_return_typecheck_error_probe_reports_error(self) -> None:
        result = self.run_program(self.root / "selfhost" / "field_access_return_typecheck_error_probe.nq")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_selfhost_annotated_local_typecheck_error_probe_reports_error(self) -> None:
        result = self.run_program(self.root / "selfhost" / "annotated_local_typecheck_error_probe.nq")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_selfhost_return_typecheck_error_probe_reports_error(self) -> None:
        result = self.run_program(self.root / "selfhost" / "return_typecheck_error_probe.nq")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_selfhost_if_condition_typecheck_error_probe_reports_error(self) -> None:
        result = self.run_program(self.root / "selfhost" / "if_condition_typecheck_error_probe.nq")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_selfhost_while_condition_typecheck_error_probe_reports_error(self) -> None:
        result = self.run_program(self.root / "selfhost" / "while_condition_typecheck_error_probe.nq")
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
