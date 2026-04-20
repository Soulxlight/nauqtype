from __future__ import annotations

from dataclasses import dataclass, field

from compiler.ast import nodes as ast
from compiler.diagnostics import DiagnosticBag


@dataclass(slots=True)
class FunctionInfo:
    name: str
    decl: ast.FunctionDecl | None
    builtin: bool = False


@dataclass(slots=True)
class StructInfo:
    name: str
    decl: ast.TypeDecl


@dataclass(slots=True)
class EnumInfo:
    name: str
    decl: ast.EnumDecl


@dataclass(slots=True)
class VariantInfo:
    name: str
    enum_name: str
    payload_count: int
    builtin_kind: str | None = None


@dataclass(slots=True)
class ModuleInfo:
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

    def resolve(self, program: ast.Program) -> ModuleInfo:
        module = ModuleInfo()
        module.functions["print_line"] = FunctionInfo("print_line", None, builtin=True)
        module.variants["Some"] = VariantInfo("Some", "option", 1, builtin_kind="option")
        module.variants["None"] = VariantInfo("None", "option", 0, builtin_kind="option")
        module.variants["Ok"] = VariantInfo("Ok", "result", 1, builtin_kind="result")
        module.variants["Err"] = VariantInfo("Err", "result", 1, builtin_kind="result")

        for item in program.items:
            if isinstance(item, ast.FunctionDecl):
                self._define_top_level(module.functions, item.name, FunctionInfo(item.name, item), item.span, "function")
            elif isinstance(item, ast.TypeDecl):
                self._define_top_level(module.structs, item.name, StructInfo(item.name, item), item.span, "type")
            elif isinstance(item, ast.EnumDecl):
                self._define_top_level(module.enums, item.name, EnumInfo(item.name, item), item.span, "enum")

        for enum_info in module.enums.values():
            for variant in enum_info.decl.variants:
                if variant.name in module.variants:
                    self.diagnostics.add(
                        "NQ-RESOLVE-001",
                        "RESOLVE",
                        f"duplicate variant or constructor `{variant.name}`",
                        variant.span,
                    )
                    continue
                module.variants[variant.name] = VariantInfo(
                    name=variant.name,
                    enum_name=enum_info.name,
                    payload_count=len(variant.payloads),
                )

        for item in program.items:
            if isinstance(item, ast.FunctionDecl):
                self._resolve_function(item, module)
            elif isinstance(item, ast.UseDecl):
                self.diagnostics.add(
                    "NQ-RESOLVE-002",
                    "RESOLVE",
                    "`use` declarations are reserved but not implemented in v0.1",
                    item.span,
                )

        return module

    def _define_top_level(self, table: dict[str, object], name: str, value: object, span, kind: str) -> None:
        if name in table:
            self.diagnostics.add(
                "NQ-RESOLVE-003",
                "RESOLVE",
                f"duplicate {kind} `{name}`",
                span,
            )
            return
        table[name] = value

    def _resolve_function(self, function: ast.FunctionDecl, module: ModuleInfo) -> None:
        scopes: list[dict[str, LocalSymbol]] = [{}]
        for param in function.params:
            symbol = self._declare(scopes[-1], param.name, mutable=False, is_param=True, span=param.span)
            if symbol is not None:
                param.symbol_id = symbol.id
        self._resolve_block(function.body, module, scopes)

    def _resolve_block(self, block: ast.Block, module: ModuleInfo, scopes: list[dict[str, LocalSymbol]]) -> None:
        scopes.append({})
        for statement in block.statements:
            self._resolve_stmt(statement, module, scopes)
        scopes.pop()

    def _resolve_stmt(self, stmt: ast.Stmt, module: ModuleInfo, scopes: list[dict[str, LocalSymbol]]) -> None:
        if isinstance(stmt, ast.LetStmt):
            self._resolve_expr(stmt.expr, module, scopes)
            symbol = self._declare(scopes[-1], stmt.name, mutable=stmt.mutable, is_param=False, span=stmt.span)
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
                )
            else:
                stmt.symbol_id = symbol.id
            self._resolve_expr(stmt.expr, module, scopes)
            return
        if isinstance(stmt, ast.IfStmt):
            self._resolve_expr(stmt.condition, module, scopes)
            self._resolve_block(stmt.then_block, module, scopes)
            if stmt.else_block is not None:
                self._resolve_block(stmt.else_block, module, scopes)
            return
        if isinstance(stmt, ast.MatchStmt):
            self._resolve_expr(stmt.expr, module, scopes)
            for arm in stmt.arms:
                scopes.append({})
                self._resolve_pattern(arm.pattern, module, scopes)
                self._resolve_block(arm.block, module, scopes)
                scopes.pop()
            return
        if isinstance(stmt, ast.ReturnStmt) and stmt.expr is not None:
            self._resolve_expr(stmt.expr, module, scopes)
            return
        if isinstance(stmt, ast.ExprStmt):
            self._resolve_expr(stmt.expr, module, scopes)

    def _resolve_expr(self, expr: ast.Expr, module: ModuleInfo, scopes: list[dict[str, LocalSymbol]]) -> None:
        if isinstance(expr, ast.NameExpr):
            symbol = self._lookup(scopes, expr.name)
            if symbol is not None:
                expr.resolution_kind = "local"
                expr.symbol_id = symbol.id
                return
            if expr.name in module.functions:
                expr.resolution_kind = "function"
                expr.target_name = expr.name
                return
            if expr.name in module.variants:
                expr.resolution_kind = "variant"
                expr.target_name = expr.name
                return
            self.diagnostics.add(
                "NQ-RESOLVE-005",
                "RESOLVE",
                f"unknown name `{expr.name}`",
                expr.span,
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
                )
            else:
                expr.symbol_id = symbol.id
            return
        if isinstance(expr, ast.UnaryExpr):
            self._resolve_expr(expr.expr, module, scopes)
            return
        if isinstance(expr, ast.BinaryExpr):
            self._resolve_expr(expr.left, module, scopes)
            self._resolve_expr(expr.right, module, scopes)
            return
        if isinstance(expr, ast.CallExpr):
            self._resolve_expr(expr.callee, module, scopes)
            for arg in expr.args:
                self._resolve_expr(arg, module, scopes)
            return
        if isinstance(expr, ast.FieldExpr):
            self._resolve_expr(expr.base, module, scopes)
            return
        if isinstance(expr, ast.StructLiteralExpr):
            if expr.type_name not in module.structs:
                self.diagnostics.add(
                    "NQ-RESOLVE-007",
                    "RESOLVE",
                    f"unknown type `{expr.type_name}`",
                    expr.span,
                )
            for field in expr.fields:
                self._resolve_expr(field.expr, module, scopes)
            return

    def _resolve_pattern(self, pattern: ast.Pattern, module: ModuleInfo, scopes: list[dict[str, LocalSymbol]]) -> None:
        if isinstance(pattern, ast.WildcardPattern):
            return
        if isinstance(pattern, ast.NamePattern):
            if pattern.name in module.variants:
                pattern.resolution_kind = "variant"
                pattern.target_name = pattern.name
                return
            symbol = self._declare(scopes[-1], pattern.name, mutable=False, is_param=False, span=pattern.span)
            if symbol is not None:
                pattern.symbol_id = symbol.id
                pattern.resolution_kind = "binding"
            return
        if isinstance(pattern, ast.VariantPattern):
            if pattern.name not in module.variants:
                self.diagnostics.add(
                    "NQ-RESOLVE-008",
                    "RESOLVE",
                    f"unknown pattern constructor `{pattern.name}`",
                    pattern.span,
                )
            else:
                pattern.resolution_kind = "variant"
                pattern.target_name = pattern.name
            for arg in pattern.args:
                self._resolve_pattern(arg, module, scopes)

    def _declare(self, scope: dict[str, LocalSymbol], name: str, *, mutable: bool, is_param: bool, span) -> LocalSymbol | None:
        if name in scope:
            self.diagnostics.add(
                "NQ-RESOLVE-009",
                "RESOLVE",
                f"duplicate local binding `{name}`",
                span,
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

