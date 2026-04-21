from __future__ import annotations

from compiler.ir.core import (
    IRBinaryExpr,
    IRBindPattern,
    IRBlock,
    IRBoolLiteral,
    IRBorrowExpr,
    IRCallExpr,
    IRExpr,
    IRExprStmt,
    IRFieldExpr,
    IRFieldValue,
    IRFunction,
    IRIfStmt,
    IRIntLiteral,
    IRLocal,
    IRMatchStmt,
    IRNameExpr,
    IRPattern,
    IRProgram,
    IRReturnStmt,
    IRStringLiteral,
    IRStructLiteralExpr,
    IRUnaryExpr,
    IRVariantExpr,
    IRVariantPattern,
    IRWildcardPattern,
    IRWhileStmt,
    IRAssignStmt,
    IRLetStmt,
)
from compiler.types.model import EnumDef, StructDef, Type


class CEmitter:
    def __init__(self, program: IRProgram) -> None:
        self.program = program
        self.lines: list[str] = []
        self.temp_index = 0
        self.generated_generic_types: set[Type] = set()

    def emit(self) -> str:
        self.lines = ['#include "runtime.h"', ""]
        self._emit_user_types()
        self._emit_builtin_generics()
        self._emit_functions()
        return "\n".join(self.lines).rstrip() + "\n"

    def _emit_user_types(self) -> None:
        for struct in self.program.structs.values():
            self.lines.append(f"typedef struct {self._named_type_name(struct.name)} {{")
            for field_name, field_type in struct.fields.items():
                self.lines.append(f"    {self._c_type(field_type)} {field_name};")
            self.lines.append(f"}} {self._named_type_name(struct.name)};")
            self.lines.append("")

        for enum_name, enum_def in self.program.enums.items():
            if enum_name in {"option", "result"}:
                continue
            self._emit_enum_definition(enum_name, enum_def)

    def _emit_builtin_generics(self) -> None:
        seen: set[Type] = set()

        def collect_type(typ: Type) -> None:
            if typ in seen:
                return
            seen.add(typ)
            if typ.kind in {"option", "result"}:
                self.generated_generic_types.add(typ)
            for child in typ.args:
                collect_type(child)

        for struct in self.program.structs.values():
            for field_type in struct.fields.values():
                collect_type(field_type)
        for enum_name, enum_def in self.program.enums.items():
            if enum_name in {"option", "result"}:
                continue
            for variant in enum_def.variants.values():
                for payload in variant.payloads:
                    collect_type(payload)
        for signature in self.program.signatures.values():
            for param in signature.param_types:
                collect_type(param)
            collect_type(signature.return_type)
        for function in self.program.functions:
            for param in function.params:
                collect_type(param.typ)
            self._collect_block_types(function.body, collect_type)

        for typ in sorted(self.generated_generic_types, key=self._type_key):
            if typ.kind == "option":
                self._emit_option_definition(typ)
            elif typ.kind == "result":
                self._emit_result_definition(typ)

    def _collect_block_types(self, block: IRBlock, collect_type) -> None:
        for stmt in block.statements:
            if isinstance(stmt, IRLetStmt):
                collect_type(stmt.local.typ)
                self._collect_expr_types(stmt.expr, collect_type)
            elif isinstance(stmt, IRAssignStmt):
                collect_type(stmt.target.typ)
                self._collect_expr_types(stmt.expr, collect_type)
            elif isinstance(stmt, IRIfStmt):
                self._collect_expr_types(stmt.condition, collect_type)
                self._collect_block_types(stmt.then_block, collect_type)
                if stmt.else_block is not None:
                    self._collect_block_types(stmt.else_block, collect_type)
            elif isinstance(stmt, IRWhileStmt):
                self._collect_expr_types(stmt.condition, collect_type)
                self._collect_block_types(stmt.body, collect_type)
            elif isinstance(stmt, IRMatchStmt):
                collect_type(stmt.scrutinee_type)
                self._collect_expr_types(stmt.expr, collect_type)
                for arm in stmt.arms:
                    self._collect_pattern_types(arm.pattern, collect_type)
                    self._collect_block_types(arm.block, collect_type)
            elif isinstance(stmt, IRReturnStmt) and stmt.expr is not None:
                self._collect_expr_types(stmt.expr, collect_type)
            elif isinstance(stmt, IRExprStmt):
                self._collect_expr_types(stmt.expr, collect_type)

    def _collect_expr_types(self, expr: IRExpr, collect_type) -> None:
        collect_type(expr.typ)
        if isinstance(expr, IRUnaryExpr):
            self._collect_expr_types(expr.expr, collect_type)
        elif isinstance(expr, IRBinaryExpr):
            self._collect_expr_types(expr.left, collect_type)
            self._collect_expr_types(expr.right, collect_type)
        elif isinstance(expr, IRCallExpr):
            for arg in expr.args:
                self._collect_expr_types(arg, collect_type)
        elif isinstance(expr, IRVariantExpr):
            for arg in expr.args:
                self._collect_expr_types(arg, collect_type)
        elif isinstance(expr, IRFieldExpr):
            self._collect_expr_types(expr.base, collect_type)
        elif isinstance(expr, IRStructLiteralExpr):
            for field in expr.fields:
                self._collect_expr_types(field.expr, collect_type)

    def _collect_pattern_types(self, pattern: IRPattern, collect_type) -> None:
        if isinstance(pattern, IRBindPattern):
            collect_type(pattern.local.typ)
        elif isinstance(pattern, IRVariantPattern):
            for arg in pattern.args:
                self._collect_pattern_types(arg, collect_type)

    def _emit_option_definition(self, typ: Type) -> None:
        type_name = self._c_type(typ)
        tag_name = f"{type_name}_Tag"
        payload_type = typ.args[0]
        self.lines.append(f"typedef enum {tag_name} {{")
        self.lines.append(f"    {tag_name}_Some,")
        self.lines.append(f"    {tag_name}_None,")
        self.lines.append(f"}} {tag_name};")
        self.lines.append(f"typedef struct {type_name} {{")
        self.lines.append(f"    {tag_name} tag;")
        self.lines.append("    union {")
        self.lines.append(f"        struct {{ {self._c_type(payload_type)} _0; }} Some;")
        self.lines.append("        NQUnit None;")
        self.lines.append("    } data;")
        self.lines.append(f"}} {type_name};")
        self.lines.append("")

    def _emit_result_definition(self, typ: Type) -> None:
        type_name = self._c_type(typ)
        tag_name = f"{type_name}_Tag"
        ok_type, err_type = typ.args
        self.lines.append(f"typedef enum {tag_name} {{")
        self.lines.append(f"    {tag_name}_Ok,")
        self.lines.append(f"    {tag_name}_Err,")
        self.lines.append(f"}} {tag_name};")
        self.lines.append(f"typedef struct {type_name} {{")
        self.lines.append(f"    {tag_name} tag;")
        self.lines.append("    union {")
        self.lines.append(f"        struct {{ {self._c_type(ok_type)} _0; }} Ok;")
        self.lines.append(f"        struct {{ {self._c_type(err_type)} _0; }} Err;")
        self.lines.append("    } data;")
        self.lines.append(f"}} {type_name};")
        self.lines.append("")

    def _emit_enum_definition(self, enum_name: str, enum_def: EnumDef) -> None:
        type_name = self._named_type_name(enum_name)
        tag_name = f"{type_name}_Tag"
        self.lines.append(f"typedef enum {tag_name} {{")
        for variant_name in enum_def.variants:
            self.lines.append(f"    {tag_name}_{variant_name},")
        self.lines.append(f"}} {tag_name};")
        self.lines.append(f"typedef struct {type_name} {{")
        self.lines.append(f"    {tag_name} tag;")
        self.lines.append("    union {")
        for variant_name, variant in enum_def.variants.items():
            if not variant.payloads:
                self.lines.append(f"        NQUnit {variant_name};")
                continue
            payload_parts = " ".join(f"{self._c_type(payload)} _{index};" for index, payload in enumerate(variant.payloads))
            self.lines.append(f"        struct {{ {payload_parts} }} {variant_name};")
        self.lines.append("    } data;")
        self.lines.append(f"}} {type_name};")
        self.lines.append("")

    def _emit_functions(self) -> None:
        for function in self.program.functions:
            params = []
            for param in function.params:
                if param.is_ref_param:
                    pointee = self._c_type(param.typ)
                    rendered = f"{pointee}* {self._binding_name(param)}"
                    if not param.ref_mutable:
                        rendered = f"const {pointee}* {self._binding_name(param)}"
                else:
                    rendered = f"{self._c_type(param.typ)} {self._binding_name(param)}"
                params.append(rendered)
            params_rendered = ", ".join(params)
            self.lines.append(f"{self._c_type(function.return_type)} {self._function_name(function.name)}({params_rendered}) {{")
            self._emit_block(function.body, indent=1)
            if function.return_type == Type("unit") and not self._block_ends_with_return(function.body):
                self.lines.append("    return NQ_UNIT;")
            self.lines.append("}")
            self.lines.append("")
        if any(function.name == "main" for function in self.program.functions):
            self.lines.append("int main(void) {")
            self.lines.append(f"    return {self._function_name('main')}();")
            self.lines.append("}")
            self.lines.append("")

    def _emit_block(self, block: IRBlock, *, indent: int) -> None:
        for statement in block.statements:
            self._emit_stmt(statement, indent)

    def _block_ends_with_return(self, block: IRBlock) -> bool:
        if not block.statements:
            return False
        return isinstance(block.statements[-1], IRReturnStmt)

    def _emit_stmt(self, stmt, indent: int) -> None:
        prefix = "    " * indent
        if isinstance(stmt, IRLetStmt):
            expr = self._emit_expr(stmt.expr)
            self.lines.append(f"{prefix}{self._c_type(stmt.local.typ)} {self._binding_name(stmt.local)} = {expr};")
            return
        if isinstance(stmt, IRAssignStmt):
            expr = self._emit_expr(stmt.expr)
            target = f"*{self._binding_name(stmt.target)}" if stmt.target.is_ref_param else self._binding_name(stmt.target)
            self.lines.append(f"{prefix}{target} = {expr};")
            return
        if isinstance(stmt, IRIfStmt):
            condition = self._emit_expr(stmt.condition)
            self.lines.append(f"{prefix}if ({condition}) {{")
            self._emit_block(stmt.then_block, indent=indent + 1)
            if stmt.else_block is not None:
                self.lines.append(f"{prefix}}} else {{")
                self._emit_block(stmt.else_block, indent=indent + 1)
            self.lines.append(f"{prefix}}}")
            return
        if isinstance(stmt, IRWhileStmt):
            condition = self._emit_expr(stmt.condition)
            self.lines.append(f"{prefix}while ({condition}) {{")
            self._emit_block(stmt.body, indent=indent + 1)
            self.lines.append(f"{prefix}}}")
            return
        if isinstance(stmt, IRMatchStmt):
            self._emit_match(stmt, indent)
            return
        if isinstance(stmt, IRReturnStmt):
            if stmt.expr is None:
                self.lines.append(f"{prefix}return NQ_UNIT;")
            else:
                self.lines.append(f"{prefix}return {self._emit_expr(stmt.expr)};")
            return
        if isinstance(stmt, IRExprStmt):
            self.lines.append(f"{prefix}{self._emit_expr(stmt.expr)};")
            return
        raise RuntimeError(f"unreachable statement in C emission: {type(stmt).__name__}")

    def _emit_match(self, stmt: IRMatchStmt, indent: int) -> None:
        temp_name = self._fresh_temp()
        prefix = "    " * indent
        self.lines.append(f"{prefix}{self._c_type(stmt.scrutinee_type)} {temp_name} = {self._emit_expr(stmt.expr)};")
        default_arm = None
        self.lines.append(f"{prefix}switch ({temp_name}.tag) {{")
        for arm in stmt.arms:
            if isinstance(arm.pattern, IRWildcardPattern):
                default_arm = arm
                continue
            if isinstance(arm.pattern, IRBindPattern):
                default_arm = arm
                continue
            variant_name = self._pattern_variant_name(arm.pattern)
            if variant_name is None:
                continue
            self.lines.append(f"{prefix}    case {self._tag_name(stmt.scrutinee_type, variant_name)}: {{")
            self._emit_pattern_bindings(arm.pattern, stmt.scrutinee_type, temp_name, indent + 2)
            self._emit_block(arm.block, indent=indent + 2)
            self.lines.append(f"{prefix}        break;")
            self.lines.append(f"{prefix}    }}")
        if default_arm is not None:
            self.lines.append(f"{prefix}    default: {{")
            self._emit_pattern_bindings(default_arm.pattern, stmt.scrutinee_type, temp_name, indent + 2)
            self._emit_block(default_arm.block, indent=indent + 2)
            self.lines.append(f"{prefix}        break;")
            self.lines.append(f"{prefix}    }}")
        self.lines.append(f"{prefix}}}")

    def _emit_pattern_bindings(self, pattern: IRPattern, scrutinee_type: Type, value_expr: str, indent: int) -> None:
        prefix = "    " * indent
        if isinstance(pattern, IRBindPattern):
            self.lines.append(f"{prefix}{self._c_type(pattern.local.typ)} {self._binding_name(pattern.local)} = {value_expr};")
            return
        if isinstance(pattern, IRVariantPattern):
            payload_types = self._pattern_payload_types(scrutinee_type, pattern.name)
            for index, nested in enumerate(pattern.args):
                payload_expr = f"{value_expr}.data.{pattern.name}._{index}"
                if isinstance(nested, IRWildcardPattern):
                    continue
                if isinstance(nested, IRBindPattern):
                    self.lines.append(f"{prefix}{self._c_type(nested.local.typ)} {self._binding_name(nested.local)} = {payload_expr};")
                    continue
                if isinstance(nested, IRVariantPattern) and not nested.args:
                    variant_type = payload_types[index]
                    tag_check = self._tag_name(variant_type, nested.name)
                    self.lines.append(f"{prefix}if ({payload_expr}.tag != {tag_check}) {{")
                    self.lines.append(f"{prefix}    break;")
                    self.lines.append(f"{prefix}}}")
                    continue
                raise RuntimeError("nested constructor patterns must be rejected before C emission")

    def _emit_expr(self, expr: IRExpr) -> str:
        if isinstance(expr, IRIntLiteral):
            return str(expr.value)
        if isinstance(expr, IRStringLiteral):
            escaped = expr.value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
            return f'nq_str("{escaped}")'
        if isinstance(expr, IRBoolLiteral):
            return "true" if expr.value else "false"
        if isinstance(expr, IRNameExpr):
            name = self._binding_name(expr.local)
            return f"(*{name})" if expr.local.is_ref_param else name
        if isinstance(expr, IRBorrowExpr):
            name = self._binding_name(expr.local)
            return name if expr.local.is_ref_param else f"&{name}"
        if isinstance(expr, IRUnaryExpr):
            value = self._emit_expr(expr.expr)
            op = "!" if expr.op == "not" else expr.op
            return f"({op}{value})"
        if isinstance(expr, IRBinaryExpr):
            left = self._emit_expr(expr.left)
            right = self._emit_expr(expr.right)
            if expr.op == "and":
                return f"(({left}) && ({right}))"
            if expr.op == "or":
                return f"(({left}) || ({right}))"
            if expr.op == "==" and expr.left.typ.kind == "str":
                return f"nq_str_eq({left}, {right})"
            if expr.op == "!=" and expr.left.typ.kind == "str":
                return f"(!nq_str_eq({left}, {right}))"
            return f"(({left}) {expr.op} ({right}))"
        if isinstance(expr, IRCallExpr):
            args = ", ".join(self._emit_expr(arg) for arg in expr.args)
            if expr.function_name == "print_line":
                return f"nq_print_line({args})"
            return f"{self._function_name(expr.function_name)}({args})"
        if isinstance(expr, IRVariantExpr):
            payloads = [self._emit_expr(arg) for arg in expr.args]
            return self._emit_variant_constructor(expr.typ, expr.variant_name, payloads)
        if isinstance(expr, IRFieldExpr):
            return f"(({self._emit_expr(expr.base)})).{expr.name}"
        if isinstance(expr, IRStructLiteralExpr):
            field_parts = ", ".join(f".{field.name} = {self._emit_expr(field.expr)}" for field in expr.fields)
            return f"({self._named_type_name(expr.type_name)}){{ {field_parts} }}"
        raise RuntimeError(f"unreachable expression in C emission: {type(expr).__name__}")

    def _emit_variant_constructor(self, typ: Type, variant_name: str, payloads: list[str]) -> str:
        if typ.kind == "option":
            type_name = self._c_type(typ)
            tag = self._tag_name(typ, variant_name)
            if variant_name == "None":
                return f"({type_name}){{ .tag = {tag}, .data.None = NQ_UNIT }}"
            return f"({type_name}){{ .tag = {tag}, .data.Some = {{ ._0 = {payloads[0]} }} }}"
        if typ.kind == "result":
            type_name = self._c_type(typ)
            tag = self._tag_name(typ, variant_name)
            if variant_name == "Ok":
                return f"({type_name}){{ .tag = {tag}, .data.Ok = {{ ._0 = {payloads[0]} }} }}"
            return f"({type_name}){{ .tag = {tag}, .data.Err = {{ ._0 = {payloads[0]} }} }}"
        if typ.kind == "named":
            type_name = self._named_type_name(typ.name)
            tag = self._tag_name(typ, variant_name)
            if not payloads:
                return f"({type_name}){{ .tag = {tag} }}"
            fields = ", ".join(f"._{index} = {payload}" for index, payload in enumerate(payloads))
            return f"({type_name}){{ .tag = {tag}, .data.{variant_name} = {{ {fields} }} }}"
        raise RuntimeError(f"unreachable variant constructor type `{typ.display()}`")

    def _pattern_variant_name(self, pattern: IRPattern) -> str | None:
        if isinstance(pattern, IRVariantPattern):
            return pattern.name
        return None

    def _pattern_payload_types(self, scrutinee_type: Type, variant_name: str) -> list[Type]:
        if scrutinee_type.kind == "option":
            return [scrutinee_type.args[0]] if variant_name == "Some" else []
        if scrutinee_type.kind == "result":
            return [scrutinee_type.args[0]] if variant_name == "Ok" else [scrutinee_type.args[1]]
        if scrutinee_type.kind == "named":
            enum_def = self.program.enums[scrutinee_type.name]
            return enum_def.variants[variant_name].payloads
        raise RuntimeError(f"type `{scrutinee_type.display()}` does not have variants")

    def _binding_name(self, binding: IRLocal) -> str:
        return f"nqv_{binding.symbol_id}_{binding.name}"

    def _function_name(self, name: str) -> str:
        return f"nq_fn_{name}"

    def _c_type(self, typ: Type) -> str:
        if typ.kind == "bool":
            return "bool"
        if typ.kind == "i32":
            return "int32_t"
        if typ.kind == "str":
            return "NQStr"
        if typ.kind == "unit":
            return "NQUnit"
        if typ.kind == "named":
            return self._named_type_name(typ.name)
        if typ.kind == "option":
            return f"NQ_Option__{self._type_mangle(typ.args[0])}"
        if typ.kind == "result":
            return f"NQ_Result__{self._type_mangle(typ.args[0])}__{self._type_mangle(typ.args[1])}"
        if typ.kind == "ref":
            return self._c_type(typ.args[0])
        raise RuntimeError(f"unreachable C type for `{typ.display()}`")

    def _named_type_name(self, name: str) -> str:
        return f"NQ_{name}"

    def _type_mangle(self, typ: Type) -> str:
        if typ.kind in {"bool", "i32", "str", "unit"}:
            return typ.kind
        if typ.kind == "named":
            return typ.name or "named"
        if typ.kind == "option":
            return f"option__{self._type_mangle(typ.args[0])}"
        if typ.kind == "result":
            return f"result__{self._type_mangle(typ.args[0])}__{self._type_mangle(typ.args[1])}"
        if typ.kind == "ref":
            prefix = "mutref" if typ.mutable else "ref"
            return f"{prefix}__{self._type_mangle(typ.args[0])}"
        return typ.kind

    def _tag_name(self, typ: Type, variant_name: str) -> str:
        if typ.kind == "option":
            return f"{self._c_type(typ)}_Tag_{variant_name}"
        if typ.kind == "result":
            return f"{self._c_type(typ)}_Tag_{variant_name}"
        if typ.kind == "named":
            return f"{self._named_type_name(typ.name)}_Tag_{variant_name}"
        raise RuntimeError(f"type `{typ.display()}` does not have variants")

    def _type_key(self, typ: Type) -> str:
        return self._type_mangle(typ)

    def _fresh_temp(self) -> str:
        self.temp_index += 1
        return f"nq_tmp_{self.temp_index}"
