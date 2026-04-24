from __future__ import annotations

from dataclasses import dataclass, field

from compiler.ast import nodes as ast
from compiler.diagnostics import DiagnosticBag, SourceFile
from compiler.resolve import ModuleInfo
from compiler.types.model import BOOL, I32, IO_ERR, PROCESS_RESULT, STR, UNIT, BindingInfo, EnumDef, FunctionSig, StructDef, Type, VariantDef


@dataclass(slots=True)
class SemanticFunction:
    internal_name: str
    decl: ast.FunctionDecl
    signature: FunctionSig
    source: SourceFile
    bindings: dict[int, BindingInfo] = field(default_factory=dict)
    direct_calls: set[str] = field(default_factory=set)
    direct_print: bool = False
    inferred_mutates: list[str] = field(default_factory=list)
    inferred_effects: list[str] = field(default_factory=list)


@dataclass(slots=True)
class SemanticProgram:
    module: ModuleInfo
    structs: dict[str, StructDef]
    enums: dict[str, EnumDef]
    functions: dict[str, FunctionSig]
    function_bodies: dict[str, SemanticFunction]
    entry_main: str | None
    copyable_named: dict[str, bool]

    def is_copy_type(self, typ: Type) -> bool:
        if typ.kind in {"bool", "i32", "str", "unit", "ref", "io_err", "process_result"}:
            return True
        if typ.kind == "list":
            return False
        if typ.kind == "option":
            return self.is_copy_type(typ.args[0])
        if typ.kind == "result":
            return self.is_copy_type(typ.args[0]) and self.is_copy_type(typ.args[1])
        if typ.kind == "named" and typ.name is not None:
            return self.copyable_named.get(typ.name, False)
        return False


class TypeChecker:
    def __init__(self, diagnostics: DiagnosticBag) -> None:
        self.diagnostics = diagnostics

    def check(self, module: ModuleInfo, *, require_main: bool = True) -> SemanticProgram:
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
            "read_file": FunctionSig("read_file", [STR], Type("result", args=(STR, IO_ERR)), None, builtin=True),
            "write_file": FunctionSig("write_file", [STR, STR], Type("result", args=(UNIT, IO_ERR)), None, builtin=True),
            "arg_count": FunctionSig("arg_count", [], I32, None, builtin=True),
            "arg_get": FunctionSig("arg_get", [I32], Type("option", args=(STR,)), None, builtin=True),
            "create_dir_all": FunctionSig("create_dir_all", [STR], Type("result", args=(UNIT, IO_ERR)), None, builtin=True),
            "io_err_text": FunctionSig("io_err_text", [IO_ERR], STR, None, builtin=True),
            "str_len": FunctionSig("str_len", [STR], I32, None, builtin=True),
            "str_get": FunctionSig("str_get", [STR, I32], Type("option", args=(I32,)), None, builtin=True),
            "str_slice": FunctionSig("str_slice", [STR, I32, I32], Type("option", args=(STR,)), None, builtin=True),
            "str_concat": FunctionSig("str_concat", [STR, STR], STR, None, builtin=True),
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

        copyable_named = self._compute_copyability(structs, enums)

        for internal_name, info in module.functions.items():
            if info.builtin or info.decl is None:
                continue
            item = info.decl
            param_types: list[Type] = []
            for param in item.params:
                param_type = self._resolve_type_expr(param.type_expr, module, structs, enums, allow_borrow=True)
                param.semantic_type = param_type
                param_types.append(param_type)
            return_type = self._resolve_type_expr(item.return_type, module, structs, enums, allow_borrow=False)
            functions[internal_name] = FunctionSig(internal_name, param_types, return_type, item)

        semantic_functions: dict[str, SemanticFunction] = {}
        for internal_name, info in module.functions.items():
            if info.builtin or info.decl is None:
                continue
            item = info.decl
            signature = functions[internal_name]
            source = module.modules[item.module_name].source
            semantic_function = SemanticFunction(internal_name, item, signature, source)
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
            self._check_block(
                item.body,
                signature,
                env,
                semantic_function,
                module,
                structs,
                enums,
                functions,
                copyable_named,
                source,
            )
            for binding in semantic_function.bindings.values():
                if binding.mutable and not binding.written and not binding.is_ref_param:
                    self.diagnostics.add(
                        "NQ-LINT-001",
                        "LINT",
                        f"`{binding.name}` is mutable but never mutated",
                        item.span,
                        source=source,
                        severity="warning",
                    )
            semantic_functions[internal_name] = semantic_function

        entry_main = None
        expected_entry = f"{module.project.entry_module}::main"
        if require_main:
            main = functions.get(expected_entry)
            if main is None:
                entry_source = module.modules[module.project.entry_module].source
                self.diagnostics.add("NQ-TYPE-001", "TYPE", "missing `main` entry point", source=entry_source)
            elif main.return_type != I32:
                self.diagnostics.add(
                    "NQ-TYPE-002",
                    "TYPE",
                    "`main` must return `i32` in v0.1",
                    main.decl.span if main.decl else None,
                    source=module.modules[module.project.entry_module].source,
                )
            else:
                entry_main = expected_entry

        semantic_program = SemanticProgram(
            module=module,
            structs=structs,
            enums=enums,
            functions=functions,
            function_bodies=semantic_functions,
            entry_main=entry_main,
            copyable_named=copyable_named,
        )
        self._finalize_contracts(semantic_program)
        return semantic_program

    def _compute_copyability(self, structs: dict[str, StructDef], enums: dict[str, EnumDef]) -> dict[str, bool]:
        cache: dict[str, bool] = {}
        visiting: set[str] = set()

        def inner(typ: Type) -> bool:
            if typ.kind in {"bool", "i32", "str", "unit", "ref", "io_err"}:
                return True
            if typ.kind == "list":
                return False
            if typ.kind == "option":
                return inner(typ.args[0])
            if typ.kind == "result":
                return inner(typ.args[0]) and inner(typ.args[1])
            if typ.kind != "named" or typ.name is None:
                return False
            if typ.name in cache:
                return cache[typ.name]
            if typ.name in visiting:
                return False
            visiting.add(typ.name)
            if typ.name in structs:
                result = all(inner(field_type) for field_type in structs[typ.name].fields.values())
            elif typ.name in enums:
                result = all(all(inner(payload) for payload in variant.payloads) for variant in enums[typ.name].variants.values())
            else:
                result = False
            visiting.remove(typ.name)
            cache[typ.name] = result
            return result

        for name in structs:
            inner(Type("named", name=name))
        for name in enums:
            if name not in {"option", "result"}:
                inner(Type("named", name=name))
        return cache

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
                source = module.modules[type_expr.inner.resolved_name.split("::")[0]].source if type_expr.inner.resolved_name and "::" in type_expr.inner.resolved_name else None
                self.diagnostics.add(
                    "NQ-TYPE-003",
                    "TYPE",
                    "borrow types are only allowed in function parameters in v0.1",
                    type_expr.span,
                    source=source,
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
        if name == "io_err":
            return IO_ERR
        if name == "process_result":
            return PROCESS_RESULT
        if name == "list":
            if len(type_expr.args) != 1:
                self.diagnostics.add("NQ-TYPE-031", "TYPE", "`list` expects one type argument", type_expr.span)
                return Type("list", args=(UNIT,))
            inner = self._resolve_type_expr(type_expr.args[0], module, structs, enums, allow_borrow=False)
            return Type("list", args=(inner,))
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
        if type_expr.resolved_name in structs or type_expr.resolved_name in enums:
            return Type("named", name=type_expr.resolved_name)
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
        copyable_named: dict[str, bool],
        source: SourceFile,
    ) -> None:
        local_env = dict(env)
        for statement in block.statements:
            self._check_stmt(
                statement,
                signature,
                local_env,
                semantic_function,
                module,
                structs,
                enums,
                functions,
                copyable_named,
                source,
            )

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
        copyable_named: dict[str, bool],
        source: SourceFile,
    ) -> None:
        if isinstance(stmt, ast.LetStmt):
            expected = None
            if stmt.annotation is not None:
                expected = self._resolve_type_expr(stmt.annotation, module, structs, enums, allow_borrow=False)
            value_type = self._check_expr(stmt.expr, env, semantic_function, module, structs, enums, functions, copyable_named, source, expected)
            if expected is not None and value_type != expected:
                self._type_mismatch(source, stmt.expr.span, expected, value_type)
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
                    source=source,
                )
            value_type = self._check_expr(stmt.expr, env, semantic_function, module, structs, enums, functions, copyable_named, source, binding.typ)
            if value_type != binding.typ:
                self._type_mismatch(source, stmt.expr.span, binding.typ, value_type)
            binding.written = True
            return
        if isinstance(stmt, ast.IfStmt):
            condition_type = self._check_expr(stmt.condition, env, semantic_function, module, structs, enums, functions, copyable_named, source)
            if condition_type != BOOL:
                self._type_mismatch(source, stmt.condition.span, BOOL, condition_type)
            self._check_block(stmt.then_block, signature, env, semantic_function, module, structs, enums, functions, copyable_named, source)
            if stmt.else_block is not None:
                self._check_block(stmt.else_block, signature, env, semantic_function, module, structs, enums, functions, copyable_named, source)
            return
        if isinstance(stmt, ast.WhileStmt):
            condition_type = self._check_expr(stmt.condition, env, semantic_function, module, structs, enums, functions, copyable_named, source)
            if condition_type != BOOL:
                self._type_mismatch(source, stmt.condition.span, BOOL, condition_type)
            self._check_block(stmt.body, signature, env, semantic_function, module, structs, enums, functions, copyable_named, source)
            return
        if isinstance(stmt, ast.MatchStmt):
            scrutinee_type = self._check_expr(stmt.expr, env, semantic_function, module, structs, enums, functions, copyable_named, source)
            covered: set[str] = set()
            exhaustive = False
            for arm in stmt.arms:
                arm_env = dict(env)
                arm_variant = self._check_pattern(arm.pattern, scrutinee_type, arm_env, semantic_function, enums, source)
                if arm_variant is None:
                    exhaustive = True
                else:
                    covered.add(arm_variant)
                self._check_block(arm.block, signature, arm_env, semantic_function, module, structs, enums, functions, copyable_named, source)
            if not exhaustive:
                missing = self._missing_variants(scrutinee_type, enums) - covered
                if missing:
                    self.diagnostics.add(
                        "NQ-TYPE-008",
                        "TYPE",
                        f"non-exhaustive match; missing {', '.join(sorted(name.split('::')[-1] for name in missing))}",
                        stmt.span,
                        source=source,
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
                        source=source,
                    )
                return
            value_type = self._check_expr(stmt.expr, env, semantic_function, module, structs, enums, functions, copyable_named, source, signature.return_type)
            if value_type != signature.return_type:
                self._type_mismatch(source, stmt.expr.span, signature.return_type, value_type)
            return
        if isinstance(stmt, ast.ExprStmt):
            value_type = self._check_expr(stmt.expr, env, semantic_function, module, structs, enums, functions, copyable_named, source)
            if value_type.kind == "result":
                self.diagnostics.add(
                    "NQ-LINT-002",
                    "LINT",
                    "discarded `result` value",
                    stmt.span,
                    source=source,
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
        copyable_named: dict[str, bool],
        source: SourceFile,
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
            if expr.resolution_kind == "variant" and expr.target_name is not None:
                variant_info = module.variants[expr.target_name]
                if variant_info.builtin_kind == "option":
                    if expected is not None and expected.kind == "option" and variant_info.name == "None":
                        expr.inferred_type = expected
                        return expected
                    self.diagnostics.add("NQ-TYPE-010", "TYPE", "`None` requires an expected `option<T>` context", expr.span, source=source)
                    expr.inferred_type = Type("option", args=(UNIT,))
                    return expr.inferred_type
                if variant_info.payload_count == 0:
                    expr.inferred_type = Type("named", name=variant_info.enum_internal_name)
                    return expr.inferred_type
            if expr.resolution_kind == "function":
                self.diagnostics.add("NQ-TYPE-011", "TYPE", "functions are not first-class in v0.1", expr.span, source=source)
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
                    source=source,
                )
            binding.written = binding.written or expr.mutable
            expr.inferred_type = Type("ref", args=(binding.typ,), mutable=expr.mutable)
            return expr.inferred_type
        if isinstance(expr, ast.UnaryExpr):
            operand = self._check_expr(expr.expr, env, semantic_function, module, structs, enums, functions, copyable_named, source)
            if expr.op == "-" and operand != I32:
                self._type_mismatch(source, expr.span, I32, operand)
            if expr.op == "not" and operand != BOOL:
                self._type_mismatch(source, expr.span, BOOL, operand)
            expr.inferred_type = I32 if expr.op == "-" else BOOL
            return expr.inferred_type
        if isinstance(expr, ast.BinaryExpr):
            left = self._check_expr(expr.left, env, semantic_function, module, structs, enums, functions, copyable_named, source)
            right = self._check_expr(expr.right, env, semantic_function, module, structs, enums, functions, copyable_named, source)
            if expr.op in {"+", "-", "*", "/"}:
                if left != I32 or right != I32:
                    self.diagnostics.add("NQ-TYPE-013", "TYPE", "arithmetic operators require `i32` operands", expr.span, source=source)
                expr.inferred_type = I32
                return I32
            if expr.op in {"<", "<=", ">", ">="}:
                if left != I32 or right != I32:
                    self.diagnostics.add("NQ-TYPE-014", "TYPE", "comparison operators require `i32` operands", expr.span, source=source)
                expr.inferred_type = BOOL
                return BOOL
            if expr.op in {"and", "or"}:
                if left != BOOL or right != BOOL:
                    self.diagnostics.add("NQ-TYPE-015", "TYPE", "logical operators require `bool` operands", expr.span, source=source)
                expr.inferred_type = BOOL
                return BOOL
            if expr.op in {"==", "!="}:
                if left != right or left.kind not in {"bool", "i32", "str", "io_err"}:
                    self.diagnostics.add("NQ-TYPE-016", "TYPE", "equality requires matching comparable operands", expr.span, source=source)
                expr.inferred_type = BOOL
                return BOOL
        if isinstance(expr, ast.CallExpr):
            if isinstance(expr.callee, ast.NameExpr) and expr.callee.resolution_kind == "function" and expr.callee.target_name is not None:
                target_name = expr.callee.target_name
                if target_name == "list":
                    if expr.args:
                        self.diagnostics.add("NQ-TYPE-032", "TYPE", "`list()` expects no arguments", expr.span, source=source)
                    if expected is None or expected.kind != "list":
                        self.diagnostics.add("NQ-TYPE-033", "TYPE", "`list()` requires an expected `list<T>` context", expr.span, source=source)
                        expr.inferred_type = Type("list", args=(UNIT,))
                    else:
                        expr.inferred_type = expected
                    expr.call_kind = "function"
                    expr.target_name = target_name
                    expr.param_types = []
                    return expr.inferred_type
                if target_name == "list_push":
                    expr.call_kind = "function"
                    expr.target_name = target_name
                    if len(expr.args) != 2:
                        self.diagnostics.add("NQ-TYPE-017", "TYPE", "`list_push` expects 2 argument(s)", expr.span, source=source)
                        expr.inferred_type = UNIT
                        expr.param_types = []
                        return UNIT
                    list_arg_type = self._check_expr(expr.args[0], env, semantic_function, module, structs, enums, functions, copyable_named, source)
                    if list_arg_type.kind != "ref" or not list_arg_type.mutable or list_arg_type.inner().kind != "list":
                        self.diagnostics.add("NQ-TYPE-034", "TYPE", "`list_push` expects `mutref list<T>` as its first argument", expr.args[0].span, source=source)
                        element_type = UNIT
                    else:
                        element_type = list_arg_type.inner().args[0]
                    value_type = self._check_expr(expr.args[1], env, semantic_function, module, structs, enums, functions, copyable_named, source, element_type)
                    if element_type != UNIT and value_type != element_type:
                        self._type_mismatch(source, expr.args[1].span, element_type, value_type)
                    expr.param_types = [Type("ref", args=(Type("list", args=(element_type,)),), mutable=True), element_type]
                    expr.inferred_type = UNIT
                    return UNIT
                if target_name == "list_len":
                    expr.call_kind = "function"
                    expr.target_name = target_name
                    if len(expr.args) != 1:
                        self.diagnostics.add("NQ-TYPE-017", "TYPE", "`list_len` expects 1 argument(s)", expr.span, source=source)
                        expr.inferred_type = I32
                        expr.param_types = []
                        return I32
                    list_arg_type = self._check_expr(expr.args[0], env, semantic_function, module, structs, enums, functions, copyable_named, source)
                    if list_arg_type.kind != "ref" or list_arg_type.inner().kind != "list":
                        self.diagnostics.add("NQ-TYPE-035", "TYPE", "`list_len` expects `ref list<T>` as its argument", expr.args[0].span, source=source)
                    expr.param_types = [list_arg_type]
                    expr.inferred_type = I32
                    return I32
                if target_name == "list_get":
                    expr.call_kind = "function"
                    expr.target_name = target_name
                    if len(expr.args) != 2:
                        self.diagnostics.add("NQ-TYPE-017", "TYPE", "`list_get` expects 2 argument(s)", expr.span, source=source)
                        expr.inferred_type = Type("option", args=(UNIT,))
                        expr.param_types = []
                        return expr.inferred_type
                    list_arg_type = self._check_expr(expr.args[0], env, semantic_function, module, structs, enums, functions, copyable_named, source)
                    if list_arg_type.kind != "ref" or list_arg_type.inner().kind != "list":
                        self.diagnostics.add("NQ-TYPE-036", "TYPE", "`list_get` expects `ref list<T>` as its first argument", expr.args[0].span, source=source)
                        element_type = UNIT
                    else:
                        element_type = list_arg_type.inner().args[0]
                    if element_type != UNIT and not self._is_copy(element_type, copyable_named):
                        self.diagnostics.add("NQ-TYPE-037", "TYPE", "`list_get` is only supported for copy element types in stage1", expr.span, source=source)
                    index_type = self._check_expr(expr.args[1], env, semantic_function, module, structs, enums, functions, copyable_named, source, I32)
                    if index_type != I32:
                        self._type_mismatch(source, expr.args[1].span, I32, index_type)
                    expr.param_types = [list_arg_type, I32]
                    expr.inferred_type = Type("option", args=(element_type,))
                    return expr.inferred_type

                if target_name in functions:
                    signature = functions[target_name]
                    expr.call_kind = "function"
                    expr.target_name = target_name
                    expr.param_types = list(signature.param_types)
                    if target_name == "print_line":
                        semantic_function.direct_print = True
                    elif not signature.builtin:
                        semantic_function.direct_calls.add(target_name)
                    if len(expr.args) != len(signature.param_types):
                        display_name = target_name.split("::")[-1]
                        self.diagnostics.add(
                            "NQ-TYPE-017",
                            "TYPE",
                            f"`{display_name}` expects {len(signature.param_types)} argument(s), found {len(expr.args)}",
                            expr.span,
                            source=source,
                        )
                    for arg, param_type in zip(expr.args, signature.param_types):
                        arg_type = self._check_expr(arg, env, semantic_function, module, structs, enums, functions, copyable_named, source, param_type)
                        if arg_type != param_type:
                            self._type_mismatch(source, arg.span, param_type, arg_type)
                    expr.inferred_type = signature.return_type
                    return signature.return_type
            if isinstance(expr.callee, ast.NameExpr) and expr.callee.resolution_kind == "variant" and expr.callee.target_name is not None:
                variant = module.variants[expr.callee.target_name]
                expr.call_kind = "variant"
                expr.target_name = expr.callee.target_name
                if variant.builtin_kind == "option":
                    if expected is None or expected.kind != "option":
                        self.diagnostics.add("NQ-TYPE-018", "TYPE", "`Some(...)` requires an expected `option<T>` context", expr.span, source=source)
                        inferred = Type("option", args=(UNIT,))
                    else:
                        inferred = expected
                        if len(expr.args) != 1:
                            self.diagnostics.add("NQ-TYPE-020", "TYPE", "`Some` expects 1 argument(s), found 0", expr.span, source=source)
                        elif expr.args:
                            payload_type = self._check_expr(expr.args[0], env, semantic_function, module, structs, enums, functions, copyable_named, source, expected.args[0])
                            if payload_type != expected.args[0]:
                                self._type_mismatch(source, expr.args[0].span, expected.args[0], payload_type)
                    expr.inferred_type = inferred
                    return inferred
                if variant.builtin_kind == "result":
                    if expected is None or expected.kind != "result":
                        self.diagnostics.add("NQ-TYPE-019", "TYPE", f"`{variant.name}(...)` requires an expected `result<T, E>` context", expr.span, source=source)
                        inferred = Type("result", args=(UNIT, UNIT))
                    else:
                        inferred = expected
                        payload_index = 0 if variant.name == "Ok" else 1
                        payload_expected = expected.args[payload_index]
                        if len(expr.args) != 1:
                            self.diagnostics.add("NQ-TYPE-020", "TYPE", f"`{variant.name}` expects 1 argument(s), found {len(expr.args)}", expr.span, source=source)
                        elif expr.args:
                            payload_type = self._check_expr(expr.args[0], env, semantic_function, module, structs, enums, functions, copyable_named, source, payload_expected)
                            if payload_type != payload_expected:
                                self._type_mismatch(source, expr.args[0].span, payload_expected, payload_type)
                    expr.inferred_type = inferred
                    return inferred
                enum_def = enums[variant.enum_internal_name]
                variant_def = enum_def.variants[variant.name]
                if len(expr.args) != len(variant_def.payloads):
                    self.diagnostics.add(
                        "NQ-TYPE-020",
                        "TYPE",
                        f"`{variant.name}` expects {len(variant_def.payloads)} argument(s), found {len(expr.args)}",
                        expr.span,
                        source=source,
                    )
                for arg, payload_type in zip(expr.args, variant_def.payloads):
                    arg_type = self._check_expr(arg, env, semantic_function, module, structs, enums, functions, copyable_named, source, payload_type)
                    if arg_type != payload_type:
                        self._type_mismatch(source, arg.span, payload_type, arg_type)
                inferred = Type("named", name=variant.enum_internal_name)
                expr.inferred_type = inferred
                return inferred
            self.diagnostics.add("NQ-TYPE-021", "TYPE", "calls must target a function or constructor name", expr.span, source=source)
            expr.inferred_type = UNIT
            return UNIT
        if isinstance(expr, ast.FieldExpr):
            base_type = self._check_expr(expr.base, env, semantic_function, module, structs, enums, functions, copyable_named, source)
            if base_type.kind == "process_result":
                if expr.name == "exit_code":
                    expr.inferred_type = I32
                    return I32
                if expr.name == "stdout":
                    expr.inferred_type = STR
                    return STR
                if expr.name == "stderr":
                    expr.inferred_type = STR
                    return STR
                self.diagnostics.add("NQ-TYPE-023", "TYPE", "`process_result` has no field `{}`".format(expr.name), expr.span, source=source)
                expr.inferred_type = UNIT
                return UNIT
            if base_type.kind != "named" or base_type.name not in structs:
                self.diagnostics.add("NQ-TYPE-022", "TYPE", "field access requires a struct value", expr.span, source=source)
                expr.inferred_type = UNIT
                return UNIT
            struct_def = structs[base_type.name]
            if expr.name not in struct_def.fields:
                self.diagnostics.add("NQ-TYPE-023", "TYPE", f"`{base_type.display()}` has no field `{expr.name}`", expr.span, source=source)
                expr.inferred_type = UNIT
                return UNIT
            expr.inferred_type = struct_def.fields[expr.name]
            return expr.inferred_type
        if isinstance(expr, ast.StructLiteralExpr):
            if expr.resolved_name not in structs:
                expr.inferred_type = UNIT
                return UNIT
            struct_def = structs[expr.resolved_name]
            seen: set[str] = set()
            for field in expr.fields:
                if field.name not in struct_def.fields:
                    self.diagnostics.add(
                        "NQ-TYPE-024",
                        "TYPE",
                        f"`{expr.type_name}` has no field `{field.name}`",
                        field.span,
                        source=source,
                    )
                    continue
                seen.add(field.name)
                field_type = self._check_expr(field.expr, env, semantic_function, module, structs, enums, functions, copyable_named, source, struct_def.fields[field.name])
                if field_type != struct_def.fields[field.name]:
                    self._type_mismatch(source, field.expr.span, struct_def.fields[field.name], field_type)
            missing = set(struct_def.fields) - seen
            if missing:
                self.diagnostics.add(
                    "NQ-TYPE-025",
                    "TYPE",
                    f"missing field(s) in `{expr.type_name}` literal: {', '.join(sorted(missing))}",
                    expr.span,
                    source=source,
                )
            expr.inferred_type = Type("named", name=expr.resolved_name)
            return expr.inferred_type

        return UNIT

    def _is_copy(self, typ: Type, copyable_named: dict[str, bool]) -> bool:
        if typ.kind in {"bool", "i32", "str", "unit", "ref", "io_err", "process_result"}:
            return True
        if typ.kind == "list":
            return False
        if typ.kind == "option":
            return self._is_copy(typ.args[0], copyable_named)
        if typ.kind == "result":
            return self._is_copy(typ.args[0], copyable_named) and self._is_copy(typ.args[1], copyable_named)
        if typ.kind == "named" and typ.name is not None:
            return copyable_named.get(typ.name, False)
        return False

    def _check_pattern(
        self,
        pattern: ast.Pattern,
        expected_type: Type,
        env: dict[int, BindingInfo],
        semantic_function: SemanticFunction,
        enums: dict[str, EnumDef],
        source: SourceFile,
    ) -> str | None:
        if isinstance(pattern, ast.WildcardPattern):
            return None
        if isinstance(pattern, ast.NamePattern):
            if pattern.resolution_kind == "variant":
                variant_name = pattern.target_name or pattern.name
                self._check_variant_pattern_name(source, pattern.span, variant_name, expected_type, enums, 0)
                return variant_name
            if pattern.symbol_id is not None:
                binding = BindingInfo(pattern.symbol_id, pattern.name, expected_type, mutable=False, is_param=False)
                env[pattern.symbol_id] = binding
                semantic_function.bindings[pattern.symbol_id] = binding
                pattern.semantic_type = expected_type
            return None
        if isinstance(pattern, ast.VariantPattern):
            variant_name = pattern.target_name or pattern.name
            payload_types = self._check_variant_pattern_name(source, pattern.span, variant_name, expected_type, enums, len(pattern.args))
            for nested, payload_type in zip(pattern.args, payload_types):
                if isinstance(nested, ast.VariantPattern):
                    self.diagnostics.add("NQ-TYPE-030", "TYPE", "nested constructor patterns are deferred in v0.1", nested.span, source=source)
                self._check_pattern(nested, payload_type, env, semantic_function, enums, source)
            return variant_name
        return None

    def _check_variant_pattern_name(self, source: SourceFile, span, variant_name: str, expected_type: Type, enums: dict[str, EnumDef], arg_count: int) -> list[Type]:
        if expected_type.kind == "option":
            valid = {"Some": [expected_type.args[0]], "None": []}
        elif expected_type.kind == "result":
            valid = {"Ok": [expected_type.args[0]], "Err": [expected_type.args[1]]}
        elif expected_type.kind == "named" and expected_type.name in enums:
            enum_def = enums[expected_type.name]
            valid = {f"{expected_type.name}::{name}": variant.payloads for name, variant in enum_def.variants.items()}
        else:
            self.diagnostics.add("NQ-TYPE-026", "TYPE", "this value cannot be pattern matched in v0.1", span, source=source)
            return []

        if variant_name in valid:
            payloads = valid[variant_name]
        else:
            display_variant = variant_name.split("::")[-1]
            self.diagnostics.add("NQ-TYPE-027", "TYPE", f"`{display_variant}` is not a variant of `{expected_type.display()}`", span, source=source)
            return []
        if len(payloads) != arg_count:
            self.diagnostics.add(
                "NQ-TYPE-028",
                "TYPE",
                f"`{variant_name.split('::')[-1]}` pattern expects {len(payloads)} argument(s), found {arg_count}",
                span,
                source=source,
            )
        return payloads

    def _missing_variants(self, typ: Type, enums: dict[str, EnumDef]) -> set[str]:
        if typ.kind == "option":
            return {"Some", "None"}
        if typ.kind == "result":
            return {"Ok", "Err"}
        if typ.kind == "named" and typ.name in enums:
            return {f"{typ.name}::{name}" for name in enums[typ.name].variants}
        return set()

    def _type_mismatch(self, source: SourceFile, span, expected: Type, actual: Type) -> None:
        self.diagnostics.add(
            "NQ-TYPE-029",
            "TYPE",
            f"type mismatch: expected `{expected.display()}`, found `{actual.display()}`",
            span,
            source=source,
        )

    def _finalize_contracts(self, semantic_program: SemanticProgram) -> None:
        print_effects = {
            name: semantic_function.direct_print for name, semantic_function in semantic_program.function_bodies.items()
        }
        changed = True
        while changed:
            changed = False
            for name, semantic_function in semantic_program.function_bodies.items():
                if print_effects[name]:
                    continue
                if any(print_effects.get(callee, False) for callee in semantic_function.direct_calls):
                    print_effects[name] = True
                    changed = True

        for internal_name, semantic_function in semantic_program.function_bodies.items():
            function = semantic_function.decl
            semantic_function.inferred_mutates = [
                param.name
                for param in function.params
                if param.symbol_id is not None
                and param.symbol_id in semantic_function.bindings
                and semantic_function.bindings[param.symbol_id].is_ref_param
                and semantic_function.bindings[param.symbol_id].ref_mutable
                and semantic_function.bindings[param.symbol_id].written
            ]
            semantic_function.inferred_effects = ["print"] if print_effects.get(internal_name, False) else []
            self._check_contract_for_function(function, semantic_function)

    def _check_contract_for_function(self, function: ast.FunctionDecl, semantic_function: SemanticFunction) -> None:
        source = semantic_function.source
        if function.public and function.audit is None:
            self.diagnostics.add(
                "NQ-CONTRACT-001",
                "CONTRACT",
                f"public function `{function.name}` is missing an `audit` block",
                function.span,
                source=source,
                severity="warning",
                help="Add `audit { intent(...); mutates(...); effects(...); }` before the function body.",
            )
            return
        if function.audit is None:
            return

        declared_mutates = [entry.name for entry in function.audit.mutates]
        declared_effects = [entry.name for entry in function.audit.effects]

        if not function.audit.intent.strip():
            self.diagnostics.add("NQ-CONTRACT-003", "CONTRACT", "`intent(...)` text must be non-empty", function.audit.intent_span, source=source)

        param_types = {param.name: param.semantic_type for param in function.params}
        seen_mutates: set[str] = set()
        valid_declared_mutates: set[str] = set()
        for entry in function.audit.mutates:
            if entry.name in seen_mutates:
                self.diagnostics.add("NQ-CONTRACT-010", "CONTRACT", f"duplicate `mutates(...)` entry `{entry.name}`", entry.span, source=source)
                continue
            seen_mutates.add(entry.name)
            param_type = param_types.get(entry.name)
            if param_type is None or param_type.kind != "ref" or not param_type.mutable:
                self.diagnostics.add("NQ-CONTRACT-004", "CONTRACT", f"`mutates(...)` entry `{entry.name}` must name a `mutref` parameter", entry.span, source=source)
                continue
            valid_declared_mutates.add(entry.name)

        seen_effects: set[str] = set()
        valid_declared_effects: set[str] = set()
        for entry in function.audit.effects:
            if entry.name in seen_effects:
                self.diagnostics.add("NQ-CONTRACT-010", "CONTRACT", f"duplicate `effects(...)` entry `{entry.name}`", entry.span, source=source)
                continue
            seen_effects.add(entry.name)
            if entry.name != "print":
                self.diagnostics.add(
                    "NQ-CONTRACT-007",
                    "CONTRACT",
                    f"unknown audit effect `{entry.name}`",
                    entry.span,
                    source=source,
                    help="The current AI Contracts alpha supports only `print` in `effects(...)`.",
                )
                continue
            valid_declared_effects.add(entry.name)

        inferred_mutates = set(semantic_function.inferred_mutates)
        inferred_effects = set(semantic_function.inferred_effects)

        for name in semantic_function.inferred_mutates:
            if name not in valid_declared_mutates:
                self.diagnostics.add("NQ-CONTRACT-005", "CONTRACT", f"`audit` omits mutated `mutref` parameter `{name}`", function.audit.mutates_span, source=source)
        for name in declared_mutates:
            if name in valid_declared_mutates and name not in inferred_mutates:
                self.diagnostics.add(
                    "NQ-CONTRACT-006",
                    "CONTRACT",
                    f"`audit` declares mutation of `{name}` but no write-through was inferred",
                    function.audit.mutates_span,
                    source=source,
                    severity="warning",
                )

        if "print" in inferred_effects and "print" not in valid_declared_effects:
            self.diagnostics.add("NQ-CONTRACT-008", "CONTRACT", "`audit` omits `print` from `effects(...)`", function.audit.effects_span, source=source)
        if "print" in valid_declared_effects and "print" not in inferred_effects:
            self.diagnostics.add(
                "NQ-CONTRACT-009",
                "CONTRACT",
                "`audit` declares `print` in `effects(...)` but no print effect was inferred",
                function.audit.effects_span,
                source=source,
                severity="warning",
            )
