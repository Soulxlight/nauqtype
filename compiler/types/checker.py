from __future__ import annotations

from dataclasses import dataclass, field

from compiler.ast import nodes as ast
from compiler.diagnostics import DiagnosticBag
from compiler.resolve import ModuleInfo
from compiler.types.model import BOOL, I32, STR, UNIT, BindingInfo, EnumDef, FunctionSig, StructDef, Type, VariantDef


@dataclass(slots=True)
class SemanticFunction:
    decl: ast.FunctionDecl
    signature: FunctionSig
    bindings: dict[int, BindingInfo] = field(default_factory=dict)
    direct_calls: set[str] = field(default_factory=set)
    direct_print: bool = False
    inferred_mutates: list[str] = field(default_factory=list)
    inferred_effects: list[str] = field(default_factory=list)


@dataclass(slots=True)
class SemanticProgram:
    program: ast.Program
    module: ModuleInfo
    structs: dict[str, StructDef]
    enums: dict[str, EnumDef]
    functions: dict[str, FunctionSig]
    function_bodies: dict[str, SemanticFunction]


class TypeChecker:
    def __init__(self, diagnostics: DiagnosticBag) -> None:
        self.diagnostics = diagnostics

    def check(self, program: ast.Program, module: ModuleInfo, *, require_main: bool = True) -> SemanticProgram:
        structs = {name: StructDef(name, info.decl) for name, info in module.structs.items()}
        enums = {
            "option": EnumDef("option", None),
            "result": EnumDef("result", None),
        }
        enums["option"].variants["Some"] = VariantDef("Some", "option", [Type("placeholder")], builtin_kind="option")
        enums["option"].variants["None"] = VariantDef("None", "option", [], builtin_kind="option")
        enums["result"].variants["Ok"] = VariantDef("Ok", "result", [Type("placeholder")], builtin_kind="result")
        enums["result"].variants["Err"] = VariantDef("Err", "result", [Type("placeholder")], builtin_kind="result")
        for name, info in module.enums.items():
            enums[name] = EnumDef(name, info.decl)

        functions: dict[str, FunctionSig] = {
            "print_line": FunctionSig("print_line", [STR], UNIT, None, builtin=True),
        }

        for struct in structs.values():
            for field in struct.decl.fields:
                struct.fields[field.name] = self._resolve_type_expr(field.type_expr, module, structs, enums, allow_borrow=False)

        for enum_name, enum_def in enums.items():
            if enum_name in {"option", "result"}:
                continue
            assert enum_def.decl is not None
            for variant in enum_def.decl.variants:
                payloads = [
                    self._resolve_type_expr(payload, module, structs, enums, allow_borrow=False)
                    for payload in variant.payloads
                ]
                enum_def.variants[variant.name] = VariantDef(variant.name, enum_name, payloads)

        for item in program.items:
            if not isinstance(item, ast.FunctionDecl):
                continue
            param_types: list[Type] = []
            for param in item.params:
                param_type = self._resolve_type_expr(param.type_expr, module, structs, enums, allow_borrow=True)
                param.semantic_type = param_type
                param_types.append(param_type)
            return_type = self._resolve_type_expr(item.return_type, module, structs, enums, allow_borrow=False)
            functions[item.name] = FunctionSig(item.name, param_types, return_type, item)

        function_bodies: dict[str, SemanticFunction] = {}
        for item in program.items:
            if not isinstance(item, ast.FunctionDecl):
                continue
            signature = functions[item.name]
            semantic_function = SemanticFunction(item, signature)
            env: dict[int, BindingInfo] = {}
            for param, param_type in zip(item.params, signature.param_types):
                if param.symbol_id is None:
                    continue
                binding_type = param_type.inner() if param_type.kind == "ref" else param_type
                binding = BindingInfo(
                    symbol_id=param.symbol_id,
                    name=param.name,
                    typ=binding_type,
                    mutable=param_type.kind == "ref" and param_type.mutable,
                    is_param=True,
                    is_ref_param=param_type.kind == "ref",
                    ref_mutable=param_type.kind == "ref" and param_type.mutable,
                )
                env[param.symbol_id] = binding
                semantic_function.bindings[param.symbol_id] = binding
            self._check_block(item.body, signature, env, semantic_function, module, structs, enums, functions)
            for binding in semantic_function.bindings.values():
                if binding.mutable and not binding.written and not binding.is_ref_param:
                    self.diagnostics.add(
                        "NQ-LINT-001",
                        "LINT",
                        f"`{binding.name}` is mutable but never mutated",
                        item.span,
                        severity="warning",
                    )
            function_bodies[item.name] = semantic_function

        semantic_program = SemanticProgram(program, module, structs, enums, functions, function_bodies)
        self._finalize_contracts(semantic_program)

        if require_main:
            main = functions.get("main")
            if main is None:
                self.diagnostics.add("NQ-TYPE-001", "TYPE", "missing `main` entry point")
            elif main.return_type != I32:
                self.diagnostics.add(
                    "NQ-TYPE-002",
                    "TYPE",
                    "`main` must return `i32` in v0.1",
                    main.decl.span if main.decl else None,
                )

        return semantic_program

    def _resolve_type_expr(
        self,
        type_expr: ast.TypeExpr,
        module: ModuleInfo,
        structs: dict[str, StructDef],
        enums: dict[str, EnumDef],
        *,
        allow_borrow: bool,
    ) -> Type:
        if isinstance(type_expr, ast.BorrowTypeExpr):
            if not allow_borrow:
                self.diagnostics.add(
                    "NQ-TYPE-003",
                    "TYPE",
                    "borrow types are only allowed in function parameters in v0.1",
                    type_expr.span,
                )
            inner = self._resolve_type_expr(type_expr.inner, module, structs, enums, allow_borrow=False)
            return Type("ref", args=(inner,), mutable=type_expr.mutable)

        name = type_expr.name
        if name == "bool":
            return BOOL
        if name == "i32":
            return I32
        if name == "str":
            return STR
        if name == "unit":
            return UNIT
        if name == "option":
            if len(type_expr.args) != 1:
                self.diagnostics.add("NQ-TYPE-004", "TYPE", "`option` expects one type argument", type_expr.span)
                return Type("option", args=(UNIT,))
            inner = self._resolve_type_expr(type_expr.args[0], module, structs, enums, allow_borrow=False)
            return Type("option", args=(inner,))
        if name == "result":
            if len(type_expr.args) != 2:
                self.diagnostics.add("NQ-TYPE-005", "TYPE", "`result` expects two type arguments", type_expr.span)
                return Type("result", args=(UNIT, UNIT))
            ok_type = self._resolve_type_expr(type_expr.args[0], module, structs, enums, allow_borrow=False)
            err_type = self._resolve_type_expr(type_expr.args[1], module, structs, enums, allow_borrow=False)
            return Type("result", args=(ok_type, err_type))
        if name in structs or name in enums:
            return Type("named", name=name)
        self.diagnostics.add("NQ-TYPE-006", "TYPE", f"unknown type `{name}`", type_expr.span)
        return UNIT

    def _check_block(
        self,
        block: ast.Block,
        signature: FunctionSig,
        env: dict[int, BindingInfo],
        semantic_function: SemanticFunction,
        module: ModuleInfo,
        structs: dict[str, StructDef],
        enums: dict[str, EnumDef],
        functions: dict[str, FunctionSig],
    ) -> None:
        local_env = dict(env)
        for statement in block.statements:
            self._check_stmt(statement, signature, local_env, semantic_function, module, structs, enums, functions)

    def _check_stmt(
        self,
        stmt: ast.Stmt,
        signature: FunctionSig,
        env: dict[int, BindingInfo],
        semantic_function: SemanticFunction,
        module: ModuleInfo,
        structs: dict[str, StructDef],
        enums: dict[str, EnumDef],
        functions: dict[str, FunctionSig],
    ) -> None:
        if isinstance(stmt, ast.LetStmt):
            expected = None
            if stmt.annotation is not None:
                expected = self._resolve_type_expr(stmt.annotation, module, structs, enums, allow_borrow=False)
            value_type = self._check_expr(stmt.expr, env, semantic_function, module, structs, enums, functions, expected)
            if expected is not None and value_type != expected:
                self._type_mismatch(stmt.expr.span, expected, value_type)
                value_type = expected
            stmt.semantic_type = value_type
            if stmt.symbol_id is not None:
                binding = BindingInfo(stmt.symbol_id, stmt.name, value_type, stmt.mutable, is_param=False)
                env[stmt.symbol_id] = binding
                semantic_function.bindings[stmt.symbol_id] = binding
            return
        if isinstance(stmt, ast.AssignStmt):
            if stmt.symbol_id is None or stmt.symbol_id not in env:
                return
            binding = env[stmt.symbol_id]
            if not binding.mutable and not binding.ref_mutable:
                self.diagnostics.add(
                    "NQ-TYPE-007",
                    "TYPE",
                    f"cannot assign to immutable binding `{binding.name}`",
                    stmt.span,
                )
            value_type = self._check_expr(stmt.expr, env, semantic_function, module, structs, enums, functions, binding.typ)
            if value_type != binding.typ:
                self._type_mismatch(stmt.expr.span, binding.typ, value_type)
            binding.written = True
            return
        if isinstance(stmt, ast.IfStmt):
            condition_type = self._check_expr(stmt.condition, env, semantic_function, module, structs, enums, functions)
            if condition_type != BOOL:
                self._type_mismatch(stmt.condition.span, BOOL, condition_type)
            self._check_block(stmt.then_block, signature, env, semantic_function, module, structs, enums, functions)
            if stmt.else_block is not None:
                self._check_block(stmt.else_block, signature, env, semantic_function, module, structs, enums, functions)
            return
        if isinstance(stmt, ast.WhileStmt):
            condition_type = self._check_expr(stmt.condition, env, semantic_function, module, structs, enums, functions)
            if condition_type != BOOL:
                self._type_mismatch(stmt.condition.span, BOOL, condition_type)
            self._check_block(stmt.body, signature, env, semantic_function, module, structs, enums, functions)
            return
        if isinstance(stmt, ast.MatchStmt):
            scrutinee_type = self._check_expr(stmt.expr, env, semantic_function, module, structs, enums, functions)
            covered: set[str] = set()
            exhaustive = False
            for arm in stmt.arms:
                arm_env = dict(env)
                arm_variant = self._check_pattern(arm.pattern, scrutinee_type, arm_env, semantic_function, enums)
                if arm_variant is None:
                    exhaustive = True
                else:
                    covered.add(arm_variant)
                self._check_block(arm.block, signature, arm_env, semantic_function, module, structs, enums, functions)
            if not exhaustive:
                missing = self._missing_variants(scrutinee_type, enums) - covered
                if missing:
                    self.diagnostics.add(
                        "NQ-TYPE-008",
                        "TYPE",
                        f"non-exhaustive match; missing {', '.join(sorted(missing))}",
                        stmt.span,
                    )
            return
        if isinstance(stmt, ast.ReturnStmt):
            if stmt.expr is None:
                if signature.return_type != UNIT:
                    self.diagnostics.add(
                        "NQ-TYPE-009",
                        "TYPE",
                        f"`return;` is only valid in functions returning `unit`, not `{signature.return_type.display()}`",
                        stmt.span,
                    )
                return
            value_type = self._check_expr(
                stmt.expr,
                env,
                semantic_function,
                module,
                structs,
                enums,
                functions,
                signature.return_type,
            )
            if value_type != signature.return_type:
                self._type_mismatch(stmt.expr.span, signature.return_type, value_type)
            return
        if isinstance(stmt, ast.ExprStmt):
            value_type = self._check_expr(stmt.expr, env, semantic_function, module, structs, enums, functions)
            if value_type.kind == "result":
                self.diagnostics.add(
                    "NQ-LINT-002",
                    "LINT",
                    "discarded `result` value",
                    stmt.span,
                    severity="warning",
                )

    def _check_expr(
        self,
        expr: ast.Expr,
        env: dict[int, BindingInfo],
        semantic_function: SemanticFunction,
        module: ModuleInfo,
        structs: dict[str, StructDef],
        enums: dict[str, EnumDef],
        functions: dict[str, FunctionSig],
        expected: Type | None = None,
    ) -> Type:
        if isinstance(expr, ast.IntLiteral):
            expr.inferred_type = I32
            return I32
        if isinstance(expr, ast.StringLiteral):
            expr.inferred_type = STR
            return STR
        if isinstance(expr, ast.BoolLiteral):
            expr.inferred_type = BOOL
            return BOOL
        if isinstance(expr, ast.NameExpr):
            if expr.resolution_kind == "local" and expr.symbol_id in env:
                expr.inferred_type = env[expr.symbol_id].typ
                return expr.inferred_type
            if expr.resolution_kind == "variant":
                variant_name = expr.target_name or expr.name
                variant_info = module.variants[variant_name]
                if variant_info.builtin_kind == "option":
                    if expected is not None and expected.kind == "option" and variant_name == "None":
                        expr.inferred_type = expected
                        return expected
                    self.diagnostics.add(
                        "NQ-TYPE-010",
                        "TYPE",
                        "`None` requires an expected `option<T>` context",
                        expr.span,
                    )
                    expr.inferred_type = Type("option", args=(UNIT,))
                    return expr.inferred_type
                if variant_info.payload_count == 0:
                    expr.inferred_type = Type("named", name=variant_info.enum_name)
                    return expr.inferred_type
            if expr.resolution_kind == "function":
                self.diagnostics.add("NQ-TYPE-011", "TYPE", "functions are not first-class in v0.1", expr.span)
                expr.inferred_type = UNIT
                return UNIT
            expr.inferred_type = UNIT
            return UNIT
        if isinstance(expr, ast.BorrowExpr):
            if expr.symbol_id is None or expr.symbol_id not in env:
                expr.inferred_type = Type("ref", args=(UNIT,), mutable=expr.mutable)
                return expr.inferred_type
            binding = env[expr.symbol_id]
            if expr.mutable and not binding.mutable:
                self.diagnostics.add(
                    "NQ-TYPE-012",
                    "TYPE",
                    f"cannot take `mutref` of immutable binding `{binding.name}`",
                    expr.span,
                )
            binding.written = binding.written or expr.mutable
            expr.inferred_type = Type("ref", args=(binding.typ,), mutable=expr.mutable)
            return expr.inferred_type
        if isinstance(expr, ast.UnaryExpr):
            operand = self._check_expr(expr.expr, env, semantic_function, module, structs, enums, functions)
            if expr.op == "-" and operand != I32:
                self._type_mismatch(expr.span, I32, operand)
            if expr.op == "not" and operand != BOOL:
                self._type_mismatch(expr.span, BOOL, operand)
            expr.inferred_type = I32 if expr.op == "-" else BOOL
            return expr.inferred_type
        if isinstance(expr, ast.BinaryExpr):
            left = self._check_expr(expr.left, env, semantic_function, module, structs, enums, functions)
            right = self._check_expr(expr.right, env, semantic_function, module, structs, enums, functions)
            if expr.op in {"+", "-", "*", "/"}:
                if left != I32 or right != I32:
                    self.diagnostics.add("NQ-TYPE-013", "TYPE", "arithmetic operators require `i32` operands", expr.span)
                expr.inferred_type = I32
                return I32
            if expr.op in {"<", "<=", ">", ">="}:
                if left != I32 or right != I32:
                    self.diagnostics.add("NQ-TYPE-014", "TYPE", "comparison operators require `i32` operands", expr.span)
                expr.inferred_type = BOOL
                return BOOL
            if expr.op in {"and", "or"}:
                if left != BOOL or right != BOOL:
                    self.diagnostics.add("NQ-TYPE-015", "TYPE", "logical operators require `bool` operands", expr.span)
                expr.inferred_type = BOOL
                return BOOL
            if expr.op in {"==", "!="}:
                if left != right or left.kind not in {"bool", "i32", "str"}:
                    self.diagnostics.add("NQ-TYPE-016", "TYPE", "equality requires matching `bool`, `i32`, or `str` operands", expr.span)
                expr.inferred_type = BOOL
                return BOOL
        if isinstance(expr, ast.CallExpr):
            callee_type = None
            if isinstance(expr.callee, ast.NameExpr):
                callee_name = expr.callee.name
                if expr.callee.resolution_kind == "function" and callee_name in functions:
                    signature = functions[callee_name]
                    expr.call_kind = "function"
                    expr.target_name = callee_name
                    if callee_name == "print_line":
                        semantic_function.direct_print = True
                    elif not signature.builtin:
                        semantic_function.direct_calls.add(callee_name)
                    if len(expr.args) != len(signature.param_types):
                        self.diagnostics.add(
                            "NQ-TYPE-017",
                            "TYPE",
                            f"`{callee_name}` expects {len(signature.param_types)} argument(s), found {len(expr.args)}",
                            expr.span,
                        )
                    for arg, param_type in zip(expr.args, signature.param_types):
                        arg_type = self._check_expr(arg, env, semantic_function, module, structs, enums, functions, param_type)
                        if arg_type != param_type:
                            self._type_mismatch(arg.span, param_type, arg_type)
                    expr.inferred_type = signature.return_type
                    return signature.return_type
                if expr.callee.resolution_kind == "variant" and callee_name in module.variants:
                    variant = module.variants[callee_name]
                    expr.call_kind = "variant"
                    expr.target_name = callee_name
                    if variant.builtin_kind == "option":
                        if expected is None or expected.kind != "option":
                            self.diagnostics.add(
                                "NQ-TYPE-018",
                                "TYPE",
                                "`Some(...)` requires an expected `option<T>` context",
                                expr.span,
                            )
                            inferred = Type("option", args=(UNIT,))
                        else:
                            inferred = expected
                            if expr.args:
                                payload_type = self._check_expr(
                                    expr.args[0], env, semantic_function, module, structs, enums, functions, expected.args[0]
                                )
                                if payload_type != expected.args[0]:
                                    self._type_mismatch(expr.args[0].span, expected.args[0], payload_type)
                        expr.inferred_type = inferred
                        return inferred
                    if variant.builtin_kind == "result":
                        if expected is None or expected.kind != "result":
                            self.diagnostics.add(
                                "NQ-TYPE-019",
                                "TYPE",
                                f"`{callee_name}(...)` requires an expected `result<T, E>` context",
                                expr.span,
                            )
                            inferred = Type("result", args=(UNIT, UNIT))
                        else:
                            inferred = expected
                            payload_index = 0 if callee_name == "Ok" else 1
                            payload_expected = expected.args[payload_index]
                            payload_type = self._check_expr(
                                expr.args[0], env, semantic_function, module, structs, enums, functions, payload_expected
                            )
                            if payload_type != payload_expected:
                                self._type_mismatch(expr.args[0].span, payload_expected, payload_type)
                        expr.inferred_type = inferred
                        return inferred
                    enum_def = enums[variant.enum_name]
                    variant_def = enum_def.variants[callee_name]
                    if len(expr.args) != len(variant_def.payloads):
                        self.diagnostics.add(
                            "NQ-TYPE-020",
                            "TYPE",
                            f"`{callee_name}` expects {len(variant_def.payloads)} argument(s), found {len(expr.args)}",
                            expr.span,
                        )
                    for arg, payload_type in zip(expr.args, variant_def.payloads):
                        arg_type = self._check_expr(arg, env, semantic_function, module, structs, enums, functions, payload_type)
                        if arg_type != payload_type:
                            self._type_mismatch(arg.span, payload_type, arg_type)
                    inferred = Type("named", name=variant.enum_name)
                    expr.inferred_type = inferred
                    return inferred
            self.diagnostics.add("NQ-TYPE-021", "TYPE", "calls must target a function or constructor name", expr.span)
            expr.inferred_type = UNIT
            return UNIT
        if isinstance(expr, ast.FieldExpr):
            base_type = self._check_expr(expr.base, env, semantic_function, module, structs, enums, functions)
            if base_type.kind != "named" or base_type.name not in structs:
                self.diagnostics.add("NQ-TYPE-022", "TYPE", "field access requires a struct value", expr.span)
                expr.inferred_type = UNIT
                return UNIT
            struct_def = structs[base_type.name]
            if expr.name not in struct_def.fields:
                self.diagnostics.add(
                    "NQ-TYPE-023",
                    "TYPE",
                    f"`{base_type.name}` has no field `{expr.name}`",
                    expr.span,
                )
                expr.inferred_type = UNIT
                return UNIT
            expr.inferred_type = struct_def.fields[expr.name]
            return expr.inferred_type
        if isinstance(expr, ast.StructLiteralExpr):
            if expr.type_name not in structs:
                expr.inferred_type = UNIT
                return UNIT
            struct_def = structs[expr.type_name]
            seen: set[str] = set()
            for field in expr.fields:
                if field.name not in struct_def.fields:
                    self.diagnostics.add(
                        "NQ-TYPE-024",
                        "TYPE",
                        f"`{expr.type_name}` has no field `{field.name}`",
                        field.span,
                    )
                    continue
                seen.add(field.name)
                field_type = self._check_expr(
                    field.expr, env, semantic_function, module, structs, enums, functions, struct_def.fields[field.name]
                )
                if field_type != struct_def.fields[field.name]:
                    self._type_mismatch(field.expr.span, struct_def.fields[field.name], field_type)
            missing = set(struct_def.fields) - seen
            if missing:
                self.diagnostics.add(
                    "NQ-TYPE-025",
                    "TYPE",
                    f"missing field(s) in `{expr.type_name}` literal: {', '.join(sorted(missing))}",
                    expr.span,
                )
            expr.inferred_type = Type("named", name=expr.type_name)
            return expr.inferred_type

        return UNIT

    def _check_pattern(
        self,
        pattern: ast.Pattern,
        expected_type: Type,
        env: dict[int, BindingInfo],
        semantic_function: SemanticFunction,
        enums: dict[str, EnumDef],
    ) -> str | None:
        if isinstance(pattern, ast.WildcardPattern):
            return None
        if isinstance(pattern, ast.NamePattern):
            if pattern.resolution_kind == "variant":
                variant_name = pattern.target_name or pattern.name
                self._check_variant_pattern_name(pattern.span, variant_name, expected_type, enums, 0)
                return variant_name
            if pattern.symbol_id is not None:
                binding = BindingInfo(pattern.symbol_id, pattern.name, expected_type, mutable=False, is_param=False)
                env[pattern.symbol_id] = binding
                semantic_function.bindings[pattern.symbol_id] = binding
                pattern.semantic_type = expected_type
            return None
        if isinstance(pattern, ast.VariantPattern):
            variant_name = pattern.target_name or pattern.name
            payload_types = self._check_variant_pattern_name(pattern.span, variant_name, expected_type, enums, len(pattern.args))
            for nested, payload_type in zip(pattern.args, payload_types):
                if isinstance(nested, ast.VariantPattern):
                    self.diagnostics.add(
                        "NQ-TYPE-030",
                        "TYPE",
                        "nested constructor patterns are deferred in v0.1",
                        nested.span,
                    )
                self._check_pattern(nested, payload_type, env, semantic_function, enums)
            return variant_name
        return None

    def _check_variant_pattern_name(self, span, variant_name: str, expected_type: Type, enums: dict[str, EnumDef], arg_count: int) -> list[Type]:
        if expected_type.kind == "option":
            valid = {
                "Some": [expected_type.args[0]],
                "None": [],
            }
        elif expected_type.kind == "result":
            valid = {
                "Ok": [expected_type.args[0]],
                "Err": [expected_type.args[1]],
            }
        elif expected_type.kind == "named" and expected_type.name in enums:
            enum_def = enums[expected_type.name]
            valid = {name: variant.payloads for name, variant in enum_def.variants.items()}
        else:
            self.diagnostics.add("NQ-TYPE-026", "TYPE", "this value cannot be pattern matched in v0.1", span)
            return []

        if variant_name not in valid:
            self.diagnostics.add(
                "NQ-TYPE-027",
                "TYPE",
                f"`{variant_name}` is not a variant of `{expected_type.display()}`",
                span,
            )
            return []
        payloads = valid[variant_name]
        if len(payloads) != arg_count:
            self.diagnostics.add(
                "NQ-TYPE-028",
                "TYPE",
                f"`{variant_name}` pattern expects {len(payloads)} argument(s), found {arg_count}",
                span,
            )
        return payloads

    def _missing_variants(self, typ: Type, enums: dict[str, EnumDef]) -> set[str]:
        if typ.kind == "option":
            return {"Some", "None"}
        if typ.kind == "result":
            return {"Ok", "Err"}
        if typ.kind == "named" and typ.name in enums:
            return set(enums[typ.name].variants)
        return set()

    def _type_mismatch(self, span, expected: Type, actual: Type) -> None:
        self.diagnostics.add(
            "NQ-TYPE-029",
            "TYPE",
            f"type mismatch: expected `{expected.display()}`, found `{actual.display()}`",
            span,
        )

    def _finalize_contracts(self, semantic_program: SemanticProgram) -> None:
        print_effects = {name: semantic_function.direct_print for name, semantic_function in semantic_program.function_bodies.items()}
        changed = True
        while changed:
            changed = False
            for name, semantic_function in semantic_program.function_bodies.items():
                if print_effects[name]:
                    continue
                if any(print_effects.get(callee, False) for callee in semantic_function.direct_calls):
                    print_effects[name] = True
                    changed = True

        for item in semantic_program.program.items:
            if not isinstance(item, ast.FunctionDecl):
                continue
            semantic_function = semantic_program.function_bodies[item.name]
            semantic_function.inferred_mutates = [
                param.name
                for param in item.params
                if param.symbol_id is not None
                and param.symbol_id in semantic_function.bindings
                and semantic_function.bindings[param.symbol_id].is_ref_param
                and semantic_function.bindings[param.symbol_id].ref_mutable
                and semantic_function.bindings[param.symbol_id].written
            ]
            semantic_function.inferred_effects = ["print"] if print_effects.get(item.name, False) else []
            self._check_contract_for_function(item, semantic_function)

    def _check_contract_for_function(self, function: ast.FunctionDecl, semantic_function: SemanticFunction) -> None:
        if function.public and function.audit is None:
            self.diagnostics.add(
                "NQ-CONTRACT-001",
                "CONTRACT",
                f"public function `{function.name}` is missing an `audit` block",
                function.span,
                severity="warning",
                help="Add `audit { intent(...); mutates(...); effects(...); }` before the function body.",
            )
            return
        if function.audit is None:
            return

        declared_mutates = [entry.name for entry in function.audit.mutates]
        declared_effects = [entry.name for entry in function.audit.effects]

        if not function.audit.intent.strip():
            self.diagnostics.add(
                "NQ-CONTRACT-003",
                "CONTRACT",
                "`intent(...)` text must be non-empty",
                function.audit.intent_span,
            )

        param_types = {param.name: param.semantic_type for param in function.params}
        seen_mutates: set[str] = set()
        valid_declared_mutates: set[str] = set()
        for entry in function.audit.mutates:
            if entry.name in seen_mutates:
                self.diagnostics.add(
                    "NQ-CONTRACT-010",
                    "CONTRACT",
                    f"duplicate `mutates(...)` entry `{entry.name}`",
                    entry.span,
                )
                continue
            seen_mutates.add(entry.name)
            param_type = param_types.get(entry.name)
            if param_type is None or param_type.kind != "ref" or not param_type.mutable:
                self.diagnostics.add(
                    "NQ-CONTRACT-004",
                    "CONTRACT",
                    f"`mutates(...)` entry `{entry.name}` must name a `mutref` parameter",
                    entry.span,
                )
                continue
            valid_declared_mutates.add(entry.name)

        seen_effects: set[str] = set()
        valid_declared_effects: set[str] = set()
        for entry in function.audit.effects:
            if entry.name in seen_effects:
                self.diagnostics.add(
                    "NQ-CONTRACT-010",
                    "CONTRACT",
                    f"duplicate `effects(...)` entry `{entry.name}`",
                    entry.span,
                )
                continue
            seen_effects.add(entry.name)
            if entry.name != "print":
                self.diagnostics.add(
                    "NQ-CONTRACT-007",
                    "CONTRACT",
                    f"unknown audit effect `{entry.name}`",
                    entry.span,
                    help="The current AI Contracts alpha supports only `print` in `effects(...)`.",
                )
                continue
            valid_declared_effects.add(entry.name)

        inferred_mutates = set(semantic_function.inferred_mutates)
        inferred_effects = set(semantic_function.inferred_effects)

        for name in semantic_function.inferred_mutates:
            if name not in valid_declared_mutates:
                self.diagnostics.add(
                    "NQ-CONTRACT-005",
                    "CONTRACT",
                    f"`audit` omits mutated `mutref` parameter `{name}`",
                    function.audit.mutates_span,
                )
        for name in declared_mutates:
            if name in valid_declared_mutates and name not in inferred_mutates:
                self.diagnostics.add(
                    "NQ-CONTRACT-006",
                    "CONTRACT",
                    f"`audit` declares mutation of `{name}` but no write-through was inferred",
                    function.audit.mutates_span,
                    severity="warning",
                )

        if "print" in inferred_effects and "print" not in valid_declared_effects:
            self.diagnostics.add(
                "NQ-CONTRACT-008",
                "CONTRACT",
                "`audit` omits `print` from `effects(...)`",
                function.audit.effects_span,
            )
        if "print" in valid_declared_effects and "print" not in inferred_effects:
            self.diagnostics.add(
                "NQ-CONTRACT-009",
                "CONTRACT",
                "`audit` declares `print` in `effects(...)` but no print effect was inferred",
                function.audit.effects_span,
                severity="warning",
            )
