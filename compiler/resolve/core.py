from __future__ import annotations

from dataclasses import dataclass, field

from compiler.ast import nodes as ast
from compiler.diagnostics import DiagnosticBag, SourceFile
from compiler.project import Project


def qualify_name(module_name: str, name: str) -> str:
    return f"{module_name}::{name}"


@dataclass(slots=True)
class FunctionInfo:
    internal_name: str
    name: str
    module_name: str
    decl: ast.FunctionDecl | None
    public: bool
    builtin: bool = False


@dataclass(slots=True)
class StructInfo:
    internal_name: str
    name: str
    module_name: str
    decl: ast.TypeDecl
    public: bool


@dataclass(slots=True)
class EnumInfo:
    internal_name: str
    name: str
    module_name: str
    decl: ast.EnumDecl
    public: bool


@dataclass(slots=True)
class VariantInfo:
    internal_name: str
    name: str
    enum_name: str
    enum_internal_name: str
    module_name: str
    payload_count: int
    public: bool
    builtin_kind: str | None = None


@dataclass(slots=True)
class ModuleScope:
    name: str
    source: SourceFile
    functions: dict[str, str] = field(default_factory=dict)
    structs: dict[str, str] = field(default_factory=dict)
    enums: dict[str, str] = field(default_factory=dict)
    variants: dict[str, str] = field(default_factory=dict)
    exported_functions: dict[str, str] = field(default_factory=dict)
    exported_structs: dict[str, str] = field(default_factory=dict)
    exported_enums: dict[str, str] = field(default_factory=dict)
    exported_variants: dict[str, str] = field(default_factory=dict)
    hidden_functions: set[str] = field(default_factory=set)
    hidden_types: set[str] = field(default_factory=set)
    hidden_variants: set[str] = field(default_factory=set)


@dataclass(slots=True)
class ModuleInfo:
    project: Project
    modules: dict[str, ModuleScope] = field(default_factory=dict)
    functions: dict[str, FunctionInfo] = field(default_factory=dict)
    structs: dict[str, StructInfo] = field(default_factory=dict)
    enums: dict[str, EnumInfo] = field(default_factory=dict)
    variants: dict[str, VariantInfo] = field(default_factory=dict)


@dataclass(slots=True)
class LocalSymbol:
    id: int
    name: str
    mutable: bool
    is_param: bool


class Resolver:
    def __init__(self, diagnostics: DiagnosticBag) -> None:
        self.diagnostics = diagnostics
        self.next_symbol_id = 1

    def resolve(self, project: Project) -> ModuleInfo:
        module = ModuleInfo(project=project)
        for module_name in project.order:
            unit = project.modules[module_name]
            module.modules[module_name] = ModuleScope(name=module_name, source=unit.source)
        self._install_builtins(module)

        for module_name in project.order:
            self._define_module_items(module, module.modules[module_name], project.modules[module_name].program)

        for module_name in project.order:
            self._define_module_variants(module, module.modules[module_name], project.modules[module_name].program)

        for module_name in project.order:
            self._wire_imports(module, module.modules[module_name], project.modules[module_name].program)

        for module_name in project.order:
            self._resolve_module(module, module.modules[module_name], project.modules[module_name].program)

        return module

    def _install_builtins(self, module: ModuleInfo) -> None:
        for name in ("print_line", "eprint_line", "read_file", "write_file", "arg_count", "arg_get", "create_dir_all", "io_err_text", "str_len", "str_get", "str_slice", "str_concat", "list", "list_push", "list_len", "list_get"):
            module.functions[name] = FunctionInfo(name, name, "<builtin>", None, True, builtin=True)
        module.variants["Some"] = VariantInfo("Some", "Some", "option", "option", "<builtin>", 1, True, builtin_kind="option")
        module.variants["None"] = VariantInfo("None", "None", "option", "option", "<builtin>", 0, True, builtin_kind="option")
        module.variants["Ok"] = VariantInfo("Ok", "Ok", "result", "result", "<builtin>", 1, True, builtin_kind="result")
        module.variants["Err"] = VariantInfo("Err", "Err", "result", "result", "<builtin>", 1, True, builtin_kind="result")
        for scope in module.modules.values():
            scope.functions.update(
                {
                    "print_line": "print_line",
                    "eprint_line": "eprint_line",
                    "read_file": "read_file",
                    "write_file": "write_file",
                    "arg_count": "arg_count",
                    "arg_get": "arg_get",
                    "create_dir_all": "create_dir_all",
                    "io_err_text": "io_err_text",
                    "str_len": "str_len",
                    "str_get": "str_get",
                    "str_slice": "str_slice",
                    "str_concat": "str_concat",
                    "list": "list",
                    "list_push": "list_push",
                    "list_len": "list_len",
                    "list_get": "list_get",
                }
            )
            scope.variants.update({"Some": "Some", "None": "None", "Ok": "Ok", "Err": "Err"})

    def _define_module_items(self, module: ModuleInfo, scope: ModuleScope, program: ast.Program) -> None:
        for item in program.items:
            if isinstance(item, ast.FunctionDecl):
                internal_name = qualify_name(scope.name, item.name)
                info = FunctionInfo(internal_name, item.name, scope.name, item, item.public)
                self._define_top_level(scope.functions, module.functions, item.name, internal_name, info, item.span, scope.source, "function")
                if item.public:
                    scope.exported_functions[item.name] = internal_name
            elif isinstance(item, ast.TypeDecl):
                internal_name = qualify_name(scope.name, item.name)
                info = StructInfo(internal_name, item.name, scope.name, item, item.public)
                self._define_top_level(scope.structs, module.structs, item.name, internal_name, info, item.span, scope.source, "type")
                if item.public:
                    scope.exported_structs[item.name] = internal_name
            elif isinstance(item, ast.EnumDecl):
                internal_name = qualify_name(scope.name, item.name)
                info = EnumInfo(internal_name, item.name, scope.name, item, item.public)
                self._define_top_level(scope.enums, module.enums, item.name, internal_name, info, item.span, scope.source, "enum")
                if item.public:
                    scope.exported_enums[item.name] = internal_name

    def _define_module_variants(self, module: ModuleInfo, scope: ModuleScope, program: ast.Program) -> None:
        for item in program.items:
            if not isinstance(item, ast.EnumDecl):
                continue
            enum_internal_name = scope.enums.get(item.name)
            if enum_internal_name is None:
                continue
            for variant in item.variants:
                internal_name = f"{enum_internal_name}::{variant.name}"
                if internal_name in module.variants:
                    self.diagnostics.add(
                        "NQ-RESOLVE-001",
                        "RESOLVE",
                        f"duplicate variant or constructor `{variant.name}`",
                        variant.span,
                        source=scope.source,
                    )
                    continue
                info = VariantInfo(
                    internal_name=internal_name,
                    name=variant.name,
                    enum_name=item.name,
                    enum_internal_name=enum_internal_name,
                    module_name=scope.name,
                    payload_count=len(variant.payloads),
                    public=item.public,
                )
                module.variants[internal_name] = info
                if variant.name in scope.variants and scope.variants[variant.name] != internal_name:
                    self.diagnostics.add(
                        "NQ-RESOLVE-001",
                        "RESOLVE",
                        f"duplicate variant or constructor `{variant.name}`",
                        variant.span,
                        source=scope.source,
                    )
                    continue
                scope.variants[variant.name] = internal_name
                if item.public:
                    scope.exported_variants[variant.name] = internal_name

    def _wire_imports(self, module: ModuleInfo, scope: ModuleScope, program: ast.Program) -> None:
        for item in program.items:
            if not isinstance(item, ast.UseDecl):
                continue
            imported_scope = module.modules.get(item.name)
            if imported_scope is None:
                continue
            self._import_public_names(scope.functions, imported_scope.exported_functions, scope.hidden_functions, scope.source, item.span, "function")
            self._import_public_names(scope.structs, imported_scope.exported_structs, scope.hidden_types, scope.source, item.span, "type")
            self._import_public_names(scope.enums, imported_scope.exported_enums, scope.hidden_types, scope.source, item.span, "enum")
            self._import_public_names(scope.variants, imported_scope.exported_variants, scope.hidden_variants, scope.source, item.span, "variant")

            scope.hidden_functions.update(set(imported_scope.functions) - set(imported_scope.exported_functions) - {"print_line", "eprint_line", "read_file", "write_file", "arg_count", "arg_get", "create_dir_all", "io_err_text", "str_len", "str_get", "str_slice", "str_concat", "list", "list_push", "list_len", "list_get"})
            scope.hidden_types.update((set(imported_scope.structs) - set(imported_scope.exported_structs)) | (set(imported_scope.enums) - set(imported_scope.exported_enums)))
            scope.hidden_variants.update(set(imported_scope.variants) - set(imported_scope.exported_variants) - {"Some", "None", "Ok", "Err"})

    def _import_public_names(
        self,
        target: dict[str, str],
        exported: dict[str, str],
        hidden: set[str],
        source: SourceFile,
        span,
        kind: str,
    ) -> None:
        for name, internal_name in exported.items():
            if name in target and target[name] != internal_name:
                self.diagnostics.add(
                    "NQ-IMPORT-004",
                    "IMPORT",
                    f"duplicate imported {kind} `{name}`",
                    span,
                    source=source,
                )
                continue
            target[name] = internal_name
        hidden.difference_update(exported)

    def _define_top_level(
        self,
        local_table: dict[str, str],
        global_table: dict[str, object],
        display_name: str,
        internal_name: str,
        value: object,
        span,
        source: SourceFile,
        kind: str,
    ) -> None:
        if display_name in local_table:
            self.diagnostics.add(
                "NQ-RESOLVE-003",
                "RESOLVE",
                f"duplicate {kind} `{display_name}`",
                span,
                source=source,
            )
            return
        local_table[display_name] = internal_name
        global_table[internal_name] = value

    def _resolve_module(self, module: ModuleInfo, scope: ModuleScope, program: ast.Program) -> None:
        for item in program.items:
            if isinstance(item, ast.FunctionDecl):
                self._resolve_type_expr(item.return_type, scope)
                for param in item.params:
                    self._resolve_type_expr(param.type_expr, scope)
                scopes: list[dict[str, LocalSymbol]] = [{}]
                for param in item.params:
                    symbol = self._declare(scopes[-1], param.name, mutable=False, is_param=True, span=param.span, source=scope.source)
                    if symbol is not None:
                        param.symbol_id = symbol.id
                self._resolve_block(item.body, module, scope, scopes)
            elif isinstance(item, ast.TypeDecl):
                for field in item.fields:
                    self._resolve_type_expr(field.type_expr, scope)
            elif isinstance(item, ast.EnumDecl):
                for variant in item.variants:
                    for payload in variant.payloads:
                        self._resolve_type_expr(payload, scope)

    def _resolve_block(self, block: ast.Block, module: ModuleInfo, scope: ModuleScope, scopes: list[dict[str, LocalSymbol]]) -> None:
        scopes.append({})
        for statement in block.statements:
            self._resolve_stmt(statement, module, scope, scopes)
        scopes.pop()

    def _resolve_stmt(self, stmt: ast.Stmt, module: ModuleInfo, scope: ModuleScope, scopes: list[dict[str, LocalSymbol]]) -> None:
        if isinstance(stmt, ast.LetStmt):
            if stmt.annotation is not None:
                self._resolve_type_expr(stmt.annotation, scope)
            self._resolve_expr(stmt.expr, module, scope, scopes)
            symbol = self._declare(scopes[-1], stmt.name, mutable=stmt.mutable, is_param=False, span=stmt.span, source=scope.source)
            if symbol is not None:
                stmt.symbol_id = symbol.id
            return
        if isinstance(stmt, ast.AssignStmt):
            symbol = self._lookup(scopes, stmt.target)
            if symbol is None:
                self.diagnostics.add(
                    "NQ-RESOLVE-004",
                    "RESOLVE",
                    f"unknown assignment target `{stmt.target}`",
                    stmt.span,
                    source=scope.source,
                )
            else:
                stmt.symbol_id = symbol.id
            self._resolve_expr(stmt.expr, module, scope, scopes)
            return
        if isinstance(stmt, ast.IfStmt):
            self._resolve_expr(stmt.condition, module, scope, scopes)
            self._resolve_block(stmt.then_block, module, scope, scopes)
            if stmt.else_block is not None:
                self._resolve_block(stmt.else_block, module, scope, scopes)
            return
        if isinstance(stmt, ast.WhileStmt):
            self._resolve_expr(stmt.condition, module, scope, scopes)
            self._resolve_block(stmt.body, module, scope, scopes)
            return
        if isinstance(stmt, ast.MatchStmt):
            self._resolve_expr(stmt.expr, module, scope, scopes)
            for arm in stmt.arms:
                scopes.append({})
                self._resolve_pattern(arm.pattern, module, scope, scopes)
                self._resolve_block(arm.block, module, scope, scopes)
                scopes.pop()
            return
        if isinstance(stmt, ast.ReturnStmt) and stmt.expr is not None:
            self._resolve_expr(stmt.expr, module, scope, scopes)
            return
        if isinstance(stmt, ast.ExprStmt):
            self._resolve_expr(stmt.expr, module, scope, scopes)

    def _resolve_expr(self, expr: ast.Expr, module: ModuleInfo, scope: ModuleScope, scopes: list[dict[str, LocalSymbol]]) -> None:
        if isinstance(expr, ast.NameExpr):
            symbol = self._lookup(scopes, expr.name)
            if symbol is not None:
                expr.resolution_kind = "local"
                expr.symbol_id = symbol.id
                return
            if expr.name in scope.functions:
                expr.resolution_kind = "function"
                expr.target_name = scope.functions[expr.name]
                return
            if expr.name in scope.variants:
                expr.resolution_kind = "variant"
                expr.target_name = scope.variants[expr.name]
                return
            if expr.name in scope.hidden_functions or expr.name in scope.hidden_variants:
                self.diagnostics.add(
                    "NQ-IMPORT-005",
                    "IMPORT",
                    f"`{expr.name}` exists in an imported module but is not `pub`",
                    expr.span,
                    source=scope.source,
                )
                return
            self.diagnostics.add(
                "NQ-RESOLVE-005",
                "RESOLVE",
                f"unknown name `{expr.name}`",
                expr.span,
                source=scope.source,
            )
            return
        if isinstance(expr, ast.BorrowExpr):
            symbol = self._lookup(scopes, expr.name)
            if symbol is None:
                self.diagnostics.add(
                    "NQ-RESOLVE-006",
                    "RESOLVE",
                    f"cannot borrow unknown name `{expr.name}`",
                    expr.span,
                    source=scope.source,
                )
            else:
                expr.symbol_id = symbol.id
            return
        if isinstance(expr, ast.UnaryExpr):
            self._resolve_expr(expr.expr, module, scope, scopes)
            return
        if isinstance(expr, ast.BinaryExpr):
            self._resolve_expr(expr.left, module, scope, scopes)
            self._resolve_expr(expr.right, module, scope, scopes)
            return
        if isinstance(expr, ast.CallExpr):
            self._resolve_expr(expr.callee, module, scope, scopes)
            for arg in expr.args:
                self._resolve_expr(arg, module, scope, scopes)
            return
        if isinstance(expr, ast.FieldExpr):
            self._resolve_expr(expr.base, module, scope, scopes)
            return
        if isinstance(expr, ast.StructLiteralExpr):
            resolved_name = scope.structs.get(expr.type_name) or scope.enums.get(expr.type_name)
            if resolved_name is None:
                if expr.type_name in scope.hidden_types:
                    self.diagnostics.add(
                        "NQ-IMPORT-005",
                        "IMPORT",
                        f"`{expr.type_name}` exists in an imported module but is not `pub`",
                        expr.span,
                        source=scope.source,
                    )
                else:
                    self.diagnostics.add(
                        "NQ-RESOLVE-007",
                        "RESOLVE",
                        f"unknown type `{expr.type_name}`",
                        expr.span,
                        source=scope.source,
                    )
            else:
                expr.resolved_name = resolved_name
            for field in expr.fields:
                self._resolve_expr(field.expr, module, scope, scopes)
            return

    def _resolve_pattern(
        self,
        pattern: ast.Pattern,
        module: ModuleInfo,
        scope: ModuleScope,
        scopes: list[dict[str, LocalSymbol]],
    ) -> None:
        if isinstance(pattern, ast.WildcardPattern):
            return
        if isinstance(pattern, ast.NamePattern):
            if pattern.name in scope.variants:
                pattern.resolution_kind = "variant"
                pattern.target_name = scope.variants[pattern.name]
                return
            symbol = self._declare(scopes[-1], pattern.name, mutable=False, is_param=False, span=pattern.span, source=scope.source)
            if symbol is not None:
                pattern.symbol_id = symbol.id
                pattern.resolution_kind = "binding"
            return
        if isinstance(pattern, ast.VariantPattern):
            if pattern.name not in scope.variants:
                self.diagnostics.add(
                    "NQ-RESOLVE-008",
                    "RESOLVE",
                    f"unknown pattern constructor `{pattern.name}`",
                    pattern.span,
                    source=scope.source,
                )
            else:
                pattern.resolution_kind = "variant"
                pattern.target_name = scope.variants[pattern.name]
            for arg in pattern.args:
                self._resolve_pattern(arg, module, scope, scopes)

    def _resolve_type_expr(self, type_expr: ast.TypeExpr, scope: ModuleScope) -> None:
        if isinstance(type_expr, ast.BorrowTypeExpr):
            self._resolve_type_expr(type_expr.inner, scope)
            return
        if type_expr.name in {"bool", "i32", "str", "unit", "option", "result", "list", "io_err", "process_result"}:
            for arg in type_expr.args:
                self._resolve_type_expr(arg, scope)
            return
        resolved_name = scope.structs.get(type_expr.name) or scope.enums.get(type_expr.name)
        if resolved_name is None:
            if type_expr.name in scope.hidden_types:
                self.diagnostics.add(
                    "NQ-IMPORT-005",
                    "IMPORT",
                    f"`{type_expr.name}` exists in an imported module but is not `pub`",
                    type_expr.span,
                    source=scope.source,
                )
            else:
                self.diagnostics.add(
                    "NQ-TYPE-006",
                    "TYPE",
                    f"unknown type `{type_expr.name}`",
                    type_expr.span,
                    source=scope.source,
                )
        else:
            type_expr.resolved_name = resolved_name
        for arg in type_expr.args:
            self._resolve_type_expr(arg, scope)

    def _declare(self, scope: dict[str, LocalSymbol], name: str, *, mutable: bool, is_param: bool, span, source: SourceFile) -> LocalSymbol | None:
        if name in scope:
            self.diagnostics.add(
                "NQ-RESOLVE-009",
                "RESOLVE",
                f"duplicate local binding `{name}`",
                span,
                source=source,
            )
            return None
        symbol = LocalSymbol(self.next_symbol_id, name, mutable, is_param)
        self.next_symbol_id += 1
        scope[name] = symbol
        return symbol

    def _lookup(self, scopes: list[dict[str, LocalSymbol]], name: str) -> LocalSymbol | None:
        for scope in reversed(scopes):
            if name in scope:
                return scope[name]
        return None
