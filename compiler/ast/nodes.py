from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from compiler.diagnostics import Span


@dataclass(slots=True)
class Program:
    items: list[Any]
    span: Span


@dataclass(slots=True)
class UseDecl:
    name: str
    span: Span


@dataclass(slots=True)
class NamedTypeExpr:
    name: str
    args: list[Any]
    span: Span


@dataclass(slots=True)
class BorrowTypeExpr:
    mutable: bool
    inner: NamedTypeExpr
    span: Span


TypeExpr = NamedTypeExpr | BorrowTypeExpr


@dataclass(slots=True)
class Param:
    name: str
    type_expr: TypeExpr
    span: Span
    symbol_id: int | None = None
    semantic_type: Any = None


@dataclass(slots=True)
class Block:
    statements: list[Any]
    span: Span


@dataclass(slots=True)
class FieldDecl:
    name: str
    type_expr: TypeExpr
    span: Span


@dataclass(slots=True)
class VariantDecl:
    name: str
    payloads: list[TypeExpr]
    span: Span


@dataclass(slots=True)
class FunctionDecl:
    name: str
    params: list[Param]
    return_type: TypeExpr
    body: Block
    public: bool
    span: Span


@dataclass(slots=True)
class TypeDecl:
    name: str
    fields: list[FieldDecl]
    public: bool
    span: Span


@dataclass(slots=True)
class EnumDecl:
    name: str
    variants: list[VariantDecl]
    public: bool
    span: Span


Item = FunctionDecl | TypeDecl | EnumDecl | UseDecl


@dataclass(slots=True)
class LetStmt:
    name: str
    mutable: bool
    annotation: TypeExpr | None
    expr: Any
    span: Span
    symbol_id: int | None = None
    semantic_type: Any = None


@dataclass(slots=True)
class AssignStmt:
    target: str
    expr: Any
    span: Span
    symbol_id: int | None = None


@dataclass(slots=True)
class IfStmt:
    condition: Any
    then_block: Block
    else_block: Block | None
    span: Span


@dataclass(slots=True)
class MatchArm:
    pattern: Any
    block: Block
    span: Span


@dataclass(slots=True)
class MatchStmt:
    expr: Any
    arms: list[MatchArm]
    span: Span


@dataclass(slots=True)
class ReturnStmt:
    expr: Any | None
    span: Span


@dataclass(slots=True)
class ExprStmt:
    expr: Any
    span: Span


Stmt = LetStmt | AssignStmt | IfStmt | MatchStmt | ReturnStmt | ExprStmt


@dataclass(slots=True)
class IntLiteral:
    value: int
    span: Span
    inferred_type: Any = None


@dataclass(slots=True)
class StringLiteral:
    value: str
    span: Span
    inferred_type: Any = None


@dataclass(slots=True)
class BoolLiteral:
    value: bool
    span: Span
    inferred_type: Any = None


@dataclass(slots=True)
class NameExpr:
    name: str
    span: Span
    inferred_type: Any = None
    resolution_kind: str | None = None
    symbol_id: int | None = None
    target_name: str | None = None


@dataclass(slots=True)
class BorrowExpr:
    mutable: bool
    name: str
    span: Span
    inferred_type: Any = None
    symbol_id: int | None = None


@dataclass(slots=True)
class UnaryExpr:
    op: str
    expr: Any
    span: Span
    inferred_type: Any = None


@dataclass(slots=True)
class BinaryExpr:
    left: Any
    op: str
    right: Any
    span: Span
    inferred_type: Any = None


@dataclass(slots=True)
class CallExpr:
    callee: Any
    args: list[Any]
    span: Span
    inferred_type: Any = None
    call_kind: str | None = None
    target_name: str | None = None


@dataclass(slots=True)
class FieldExpr:
    base: Any
    name: str
    span: Span
    inferred_type: Any = None


@dataclass(slots=True)
class FieldInit:
    name: str
    expr: Any
    span: Span


@dataclass(slots=True)
class StructLiteralExpr:
    type_name: str
    fields: list[FieldInit]
    span: Span
    inferred_type: Any = None


Expr = (
    IntLiteral
    | StringLiteral
    | BoolLiteral
    | NameExpr
    | BorrowExpr
    | UnaryExpr
    | BinaryExpr
    | CallExpr
    | FieldExpr
    | StructLiteralExpr
)


@dataclass(slots=True)
class WildcardPattern:
    span: Span


@dataclass(slots=True)
class NamePattern:
    name: str
    span: Span
    symbol_id: int | None = None
    resolution_kind: str | None = None
    target_name: str | None = None
    semantic_type: Any = None


@dataclass(slots=True)
class VariantPattern:
    name: str
    args: list[Any]
    span: Span
    resolution_kind: str | None = None
    target_name: str | None = None


Pattern = WildcardPattern | NamePattern | VariantPattern

