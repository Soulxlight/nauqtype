from __future__ import annotations

from dataclasses import dataclass

from compiler.ast import nodes as ast
from compiler.diagnostics import DiagnosticBag, Span
from compiler.types import SemanticFunction, SemanticProgram
from compiler.types.model import BindingInfo, EnumDef, FunctionSig, StructDef, Type


@dataclass(frozen=True, slots=True)
class IRLocal:
    symbol_id: int
    name: str
    typ: Type
    is_ref_param: bool = False
    ref_mutable: bool = False


@dataclass(slots=True)
class IRProgram:
    structs: dict[str, StructDef]
    enums: dict[str, EnumDef]
    functions: list["IRFunction"]
    signatures: dict[str, FunctionSig]
    entry_function: str | None


@dataclass(slots=True)
class IRFunction:
    name: str
    params: list[IRLocal]
    return_type: Type
    body: "IRBlock"
    span: Span


@dataclass(slots=True)
class IRBlock:
    statements: list["IRStmt"]
    span: Span


@dataclass(slots=True)
class IRLetStmt:
    local: IRLocal
    expr: "IRExpr"
    span: Span


@dataclass(slots=True)
class IRAssignStmt:
    target: IRLocal
    expr: "IRExpr"
    span: Span


@dataclass(slots=True)
class IRIfStmt:
    condition: "IRExpr"
    then_block: IRBlock
    else_block: IRBlock | None
    span: Span


@dataclass(slots=True)
class IRWhileStmt:
    condition: "IRExpr"
    body: IRBlock
    span: Span


@dataclass(slots=True)
class IRMatchArm:
    pattern: "IRPattern"
    block: IRBlock
    span: Span


@dataclass(slots=True)
class IRMatchStmt:
    expr: "IRExpr"
    scrutinee_type: Type
    arms: list[IRMatchArm]
    span: Span


@dataclass(slots=True)
class IRReturnStmt:
    expr: "IRExpr" | None
    span: Span


@dataclass(slots=True)
class IRExprStmt:
    expr: "IRExpr"
    span: Span


IRStmt = IRLetStmt | IRAssignStmt | IRIfStmt | IRWhileStmt | IRMatchStmt | IRReturnStmt | IRExprStmt


@dataclass(slots=True)
class IRIntLiteral:
    value: int
    typ: Type
    span: Span


@dataclass(slots=True)
class IRStringLiteral:
    value: str
    typ: Type
    span: Span


@dataclass(slots=True)
class IRBoolLiteral:
    value: bool
    typ: Type
    span: Span


@dataclass(slots=True)
class IRNameExpr:
    local: IRLocal
    typ: Type
    span: Span


@dataclass(slots=True)
class IRBorrowExpr:
    local: IRLocal
    mutable: bool
    typ: Type
    span: Span


@dataclass(slots=True)
class IRUnaryExpr:
    op: str
    expr: "IRExpr"
    typ: Type
    span: Span


@dataclass(slots=True)
class IRBinaryExpr:
    left: "IRExpr"
    op: str
    right: "IRExpr"
    typ: Type
    span: Span


@dataclass(slots=True)
class IRCallExpr:
    function_name: str
    args: list["IRExpr"]
    param_types: list[Type]
    typ: Type
    span: Span


@dataclass(slots=True)
class IRVariantExpr:
    typ: Type
    variant_name: str
    args: list["IRExpr"]
    span: Span


@dataclass(slots=True)
class IRFieldExpr:
    base: "IRExpr"
    name: str
    typ: Type
    span: Span


@dataclass(slots=True)
class IRFieldValue:
    name: str
    expr: "IRExpr"
    span: Span


@dataclass(slots=True)
class IRStructLiteralExpr:
    type_name: str
    fields: list[IRFieldValue]
    typ: Type
    span: Span


IRExpr = (
    IRIntLiteral
    | IRStringLiteral
    | IRBoolLiteral
    | IRNameExpr
    | IRBorrowExpr
    | IRUnaryExpr
    | IRBinaryExpr
    | IRCallExpr
    | IRVariantExpr
    | IRFieldExpr
    | IRStructLiteralExpr
)


@dataclass(slots=True)
class IRWildcardPattern:
    span: Span


@dataclass(slots=True)
class IRBindPattern:
    local: IRLocal
    span: Span


@dataclass(slots=True)
class IRVariantPattern:
    name: str
    args: list["IRPattern"]
    span: Span


IRPattern = IRWildcardPattern | IRBindPattern | IRVariantPattern


class IRLowerer:
    def __init__(self, semantic: SemanticProgram, diagnostics: DiagnosticBag) -> None:
        self.semantic = semantic
        self.diagnostics = diagnostics

    def lower(self) -> IRProgram | None:
        functions: list[IRFunction] = []
        for module_name in self.semantic.module.project.order:
            program = self.semantic.module.project.modules[module_name].program
            for item in program.items:
                if not isinstance(item, ast.FunctionDecl):
                    continue
                internal_name = f"{item.module_name}::{item.name}"
                semantic_function = self.semantic.function_bodies[internal_name]
                lowered = self._lower_function(item, semantic_function)
                if lowered is not None:
                    functions.append(lowered)

        if self.diagnostics.has_errors():
            return None

        return IRProgram(
            structs=self.semantic.structs,
            enums=self.semantic.enums,
            functions=functions,
            signatures=self.semantic.functions,
            entry_function=self.semantic.entry_main,
        )

    def _lower_function(self, decl: ast.FunctionDecl, semantic_function: SemanticFunction) -> IRFunction | None:
        locals_by_id = self._locals_for_function(semantic_function)
        params: list[IRLocal] = []
        for param in decl.params:
            if param.symbol_id is None or param.symbol_id not in locals_by_id:
                self.diagnostics.add(
                    "NQ-IR-001",
                    "IR",
                    f"internal lowering failure for parameter `{param.name}`",
                    param.span,
                    help="This is a compiler bug; please report it with the source file.",
                )
                return None
            params.append(locals_by_id[param.symbol_id])

        body = self._lower_block(decl.body, locals_by_id)
        if body is None:
            return None

        return IRFunction(
            name=semantic_function.internal_name,
            params=params,
            return_type=semantic_function.signature.return_type,
            body=body,
            span=decl.span,
        )

    def _locals_for_function(self, semantic_function: SemanticFunction) -> dict[int, IRLocal]:
        locals_by_id: dict[int, IRLocal] = {}
        for symbol_id, binding in semantic_function.bindings.items():
            locals_by_id[symbol_id] = IRLocal(
                symbol_id=binding.symbol_id,
                name=binding.name,
                typ=binding.typ,
                is_ref_param=binding.is_ref_param,
                ref_mutable=binding.ref_mutable,
            )
        return locals_by_id

    def _lower_block(self, block: ast.Block, locals_by_id: dict[int, IRLocal]) -> IRBlock | None:
        statements: list[IRStmt] = []
        for statement in block.statements:
            lowered = self._lower_stmt(statement, locals_by_id)
            if lowered is None:
                return None
            statements.append(lowered)
        return IRBlock(statements=statements, span=block.span)

    def _lower_stmt(self, stmt: ast.Stmt, locals_by_id: dict[int, IRLocal]) -> IRStmt | None:
        if isinstance(stmt, ast.LetStmt):
            if stmt.symbol_id is None or stmt.symbol_id not in locals_by_id:
                self.diagnostics.add(
                    "NQ-IR-002",
                    "IR",
                    f"internal lowering failure for local `{stmt.name}`",
                    stmt.span,
                    help="This is a compiler bug; please report it with the source file.",
                )
                return None
            expr = self._lower_expr(stmt.expr, locals_by_id)
            if expr is None:
                return None
            return IRLetStmt(local=locals_by_id[stmt.symbol_id], expr=expr, span=stmt.span)
        if isinstance(stmt, ast.AssignStmt):
            if stmt.symbol_id is None or stmt.symbol_id not in locals_by_id:
                self.diagnostics.add(
                    "NQ-IR-003",
                    "IR",
                    f"internal lowering failure for assignment target `{stmt.target}`",
                    stmt.span,
                    help="This is a compiler bug; please report it with the source file.",
                )
                return None
            expr = self._lower_expr(stmt.expr, locals_by_id)
            if expr is None:
                return None
            return IRAssignStmt(target=locals_by_id[stmt.symbol_id], expr=expr, span=stmt.span)
        if isinstance(stmt, ast.IfStmt):
            condition = self._lower_expr(stmt.condition, locals_by_id)
            then_block = self._lower_block(stmt.then_block, locals_by_id)
            else_block = self._lower_block(stmt.else_block, locals_by_id) if stmt.else_block is not None else None
            if condition is None or then_block is None or (stmt.else_block is not None and else_block is None):
                return None
            return IRIfStmt(condition=condition, then_block=then_block, else_block=else_block, span=stmt.span)
        if isinstance(stmt, ast.WhileStmt):
            condition = self._lower_expr(stmt.condition, locals_by_id)
            body = self._lower_block(stmt.body, locals_by_id)
            if condition is None or body is None:
                return None
            return IRWhileStmt(condition=condition, body=body, span=stmt.span)
        if isinstance(stmt, ast.MatchStmt):
            expr = self._lower_expr(stmt.expr, locals_by_id)
            if expr is None or stmt.expr.inferred_type is None:
                self.diagnostics.add(
                    "NQ-IR-004",
                    "IR",
                    "internal lowering failure for match expression",
                    stmt.span,
                    help="This is a compiler bug; please report it with the source file.",
                )
                return None
            arms: list[IRMatchArm] = []
            for arm in stmt.arms:
                pattern = self._lower_pattern(arm.pattern, locals_by_id)
                block = self._lower_block(arm.block, locals_by_id)
                if pattern is None or block is None:
                    return None
                arms.append(IRMatchArm(pattern=pattern, block=block, span=arm.span))
            return IRMatchStmt(expr=expr, scrutinee_type=stmt.expr.inferred_type, arms=arms, span=stmt.span)
        if isinstance(stmt, ast.ReturnStmt):
            expr = self._lower_expr(stmt.expr, locals_by_id) if stmt.expr is not None else None
            if stmt.expr is not None and expr is None:
                return None
            return IRReturnStmt(expr=expr, span=stmt.span)
        if isinstance(stmt, ast.ExprStmt):
            expr = self._lower_expr(stmt.expr, locals_by_id)
            if expr is None:
                return None
            return IRExprStmt(expr=expr, span=stmt.span)

        self.diagnostics.add(
            "NQ-IR-005",
            "IR",
            f"unsupported statement shape `{type(stmt).__name__}`",
            stmt.span,
            help="This source form is outside the current v0.1 lowering surface.",
        )
        return None

    def _lower_expr(self, expr: ast.Expr | None, locals_by_id: dict[int, IRLocal]) -> IRExpr | None:
        if expr is None:
            return None
        if isinstance(expr, ast.IntLiteral):
            return IRIntLiteral(value=expr.value, typ=expr.inferred_type, span=expr.span)
        if isinstance(expr, ast.StringLiteral):
            return IRStringLiteral(value=expr.value, typ=expr.inferred_type, span=expr.span)
        if isinstance(expr, ast.BoolLiteral):
            return IRBoolLiteral(value=expr.value, typ=expr.inferred_type, span=expr.span)
        if isinstance(expr, ast.NameExpr):
            if expr.resolution_kind == "local" and expr.symbol_id is not None and expr.symbol_id in locals_by_id:
                return IRNameExpr(local=locals_by_id[expr.symbol_id], typ=expr.inferred_type, span=expr.span)
            if expr.resolution_kind == "variant" and expr.inferred_type is not None:
                variant_name = expr.target_name or expr.name
                return IRVariantExpr(typ=expr.inferred_type, variant_name=variant_name, args=[], span=expr.span)
            self.diagnostics.add(
                "NQ-IR-006",
                "IR",
                f"cannot lower name expression `{expr.name}`",
                expr.span,
                help="Use a local binding, function call, or constructor value supported by v0.1.",
            )
            return None
        if isinstance(expr, ast.BorrowExpr):
            if expr.symbol_id is None or expr.symbol_id not in locals_by_id:
                self.diagnostics.add(
                    "NQ-IR-007",
                    "IR",
                    f"cannot lower borrow of `{expr.name}`",
                    expr.span,
                    help="Use `ref` or `mutref` on a named local supported by v0.1.",
                )
                return None
            return IRBorrowExpr(
                local=locals_by_id[expr.symbol_id],
                mutable=expr.mutable,
                typ=expr.inferred_type,
                span=expr.span,
            )
        if isinstance(expr, ast.UnaryExpr):
            inner = self._lower_expr(expr.expr, locals_by_id)
            if inner is None:
                return None
            return IRUnaryExpr(op=expr.op, expr=inner, typ=expr.inferred_type, span=expr.span)
        if isinstance(expr, ast.BinaryExpr):
            left = self._lower_expr(expr.left, locals_by_id)
            right = self._lower_expr(expr.right, locals_by_id)
            if left is None or right is None:
                return None
            return IRBinaryExpr(left=left, op=expr.op, right=right, typ=expr.inferred_type, span=expr.span)
        if isinstance(expr, ast.CallExpr):
            args: list[IRExpr] = []
            for arg in expr.args:
                lowered_arg = self._lower_expr(arg, locals_by_id)
                if lowered_arg is None:
                    return None
                args.append(lowered_arg)
            if expr.call_kind == "function" and expr.target_name is not None:
                return IRCallExpr(
                    function_name=expr.target_name,
                    args=args,
                    param_types=list(expr.param_types or []),
                    typ=expr.inferred_type,
                    span=expr.span,
                )
            if expr.call_kind == "variant" and expr.target_name is not None:
                return IRVariantExpr(typ=expr.inferred_type, variant_name=expr.target_name, args=args, span=expr.span)
            self.diagnostics.add(
                "NQ-IR-008",
                "IR",
                "calls must target a lowered function or constructor",
                expr.span,
                help="Only direct function and constructor calls are supported by the current v0.1 lowerer.",
            )
            return None
        if isinstance(expr, ast.FieldExpr):
            base = self._lower_expr(expr.base, locals_by_id)
            if base is None:
                return None
            return IRFieldExpr(base=base, name=expr.name, typ=expr.inferred_type, span=expr.span)
        if isinstance(expr, ast.StructLiteralExpr):
            fields: list[IRFieldValue] = []
            for field in expr.fields:
                lowered_value = self._lower_expr(field.expr, locals_by_id)
                if lowered_value is None:
                    return None
                fields.append(IRFieldValue(name=field.name, expr=lowered_value, span=field.span))
            return IRStructLiteralExpr(
                type_name=expr.resolved_name or expr.type_name,
                fields=fields,
                typ=expr.inferred_type,
                span=expr.span,
            )

        self.diagnostics.add(
            "NQ-IR-009",
            "IR",
            f"unsupported expression shape `{type(expr).__name__}`",
            expr.span,
            help="This source form is outside the current v0.1 lowering surface.",
        )
        return None

    def _lower_pattern(self, pattern: ast.Pattern, locals_by_id: dict[int, IRLocal]) -> IRPattern | None:
        if isinstance(pattern, ast.WildcardPattern):
            return IRWildcardPattern(span=pattern.span)
        if isinstance(pattern, ast.NamePattern):
            if pattern.resolution_kind == "variant":
                return IRVariantPattern(name=pattern.target_name or pattern.name, args=[], span=pattern.span)
            if pattern.symbol_id is not None and pattern.symbol_id in locals_by_id:
                return IRBindPattern(local=locals_by_id[pattern.symbol_id], span=pattern.span)
            self.diagnostics.add(
                "NQ-IR-010",
                "IR",
                f"cannot lower pattern `{pattern.name}`",
                pattern.span,
                help="Use wildcard, binding, or constructor patterns supported by v0.1.",
            )
            return None
        if isinstance(pattern, ast.VariantPattern):
            args: list[IRPattern] = []
            for nested in pattern.args:
                lowered = self._lower_pattern(nested, locals_by_id)
                if lowered is None:
                    return None
                args.append(lowered)
            return IRVariantPattern(name=pattern.target_name or pattern.name, args=args, span=pattern.span)

        self.diagnostics.add(
            "NQ-IR-011",
            "IR",
            f"unsupported pattern shape `{type(pattern).__name__}`",
            pattern.span,
            help="This pattern form is outside the current v0.1 lowering surface.",
        )
        return None


def lower_program(semantic: SemanticProgram, diagnostics: DiagnosticBag) -> IRProgram | None:
    return IRLowerer(semantic, diagnostics).lower()
