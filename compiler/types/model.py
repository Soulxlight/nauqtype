from __future__ import annotations

from dataclasses import dataclass, field

from compiler.ast import nodes as ast


@dataclass(frozen=True, slots=True)
class Type:
    kind: str
    name: str | None = None
    args: tuple["Type", ...] = ()
    mutable: bool = False

    def display(self) -> str:
        if self.kind in {"bool", "i32", "str", "unit", "io_err", "process_result"}:
            return self.kind
        if self.kind == "named":
            if self.name is None:
                return "<named>"
            return self.name.split("::")[-1]
        if self.kind == "list":
            return f"list<{self.args[0].display()}>"
        if self.kind == "option":
            return f"option<{self.args[0].display()}>"
        if self.kind == "result":
            return f"result<{self.args[0].display()}, {self.args[1].display()}>"
        if self.kind == "ref":
            prefix = "mutref" if self.mutable else "ref"
            return f"{prefix} {self.args[0].display()}"
        return self.kind

    def is_copy(self) -> bool:
        if self.kind in {"bool", "i32", "str", "unit", "ref", "io_err", "process_result"}:
            return True
        if self.kind == "list":
            return False
        if self.kind == "option":
            return self.args[0].is_copy()
        if self.kind == "result":
            return self.args[0].is_copy() and self.args[1].is_copy()
        return False

    def inner(self) -> "Type":
        return self.args[0]


BOOL = Type("bool")
I32 = Type("i32")
STR = Type("str")
UNIT = Type("unit")
IO_ERR = Type("io_err")
PROCESS_RESULT = Type("process_result")


@dataclass(slots=True)
class StructDef:
    name: str
    decl: ast.TypeDecl
    fields: dict[str, Type] = field(default_factory=dict)


@dataclass(slots=True)
class VariantDef:
    name: str
    enum_name: str
    payloads: list[Type]
    builtin_kind: str | None = None


@dataclass(slots=True)
class EnumDef:
    name: str
    decl: ast.EnumDecl | None
    variants: dict[str, VariantDef] = field(default_factory=dict)


@dataclass(slots=True)
class FunctionSig:
    name: str
    param_types: list[Type]
    return_type: Type
    decl: ast.FunctionDecl | None
    builtin: bool = False


@dataclass(slots=True)
class BindingInfo:
    symbol_id: int
    name: str
    typ: Type
    mutable: bool
    is_param: bool
    is_ref_param: bool = False
    ref_mutable: bool = False
    written: bool = False
