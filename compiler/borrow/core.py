from __future__ import annotations

from dataclasses import dataclass

from compiler.ast import nodes as ast
from compiler.diagnostics import DiagnosticBag
from compiler.types import SemanticFunction, SemanticProgram
from compiler.types.model import Type


@dataclass(slots=True)
class MoveState:
    moved: dict[int, bool]

    def clone(self) -> "MoveState":
        return MoveState(dict(self.moved))


class BorrowChecker:
    def __init__(self, diagnostics: DiagnosticBag) -> None:
        self.diagnostics = diagnostics

    def check(self, program: SemanticProgram) -> None:
        for name, semantic_function in program.function_bodies.items():
            state = MoveState({symbol_id: False for symbol_id in semantic_function.bindings})
            self._check_block(program, semantic_function, semantic_function.decl.body, state)

    def _check_block(
        self,
        program: SemanticProgram,
        semantic_function: SemanticFunction,
        block: ast.Block,
        state: MoveState,
    ) -> MoveState:
        current = state.clone()
        for statement in block.statements:
            current = self._check_stmt(program, semantic_function, statement, current)
        return current

    def _check_stmt(
        self,
        program: SemanticProgram,
        semantic_function: SemanticFunction,
        stmt: ast.Stmt,
        state: MoveState,
    ) -> MoveState:
        current = state.clone()
        if isinstance(stmt, ast.LetStmt):
            self._walk_expr(program, semantic_function, stmt.expr, current, consume=True, in_call_arg=False)
            if stmt.symbol_id is not None:
                current.moved[stmt.symbol_id] = False
            return current
        if isinstance(stmt, ast.AssignStmt):
            self._walk_expr(program, semantic_function, stmt.expr, current, consume=True, in_call_arg=False)
            if stmt.symbol_id is not None:
                current.moved[stmt.symbol_id] = False
            return current
        if isinstance(stmt, ast.IfStmt):
            self._walk_expr(program, semantic_function, stmt.condition, current, consume=False, in_call_arg=False)
            then_state = self._check_block(program, semantic_function, stmt.then_block, current)
            else_state = self._check_block(program, semantic_function, stmt.else_block, current) if stmt.else_block else current
            return self._merge_states(current, then_state, else_state)
        if isinstance(stmt, ast.MatchStmt):
            self._walk_expr(program, semantic_function, stmt.expr, current, consume=False, in_call_arg=False)
            scrutinee_symbol = self._expr_symbol_id(stmt.expr)
            arm_states: list[MoveState] = []
            for arm in stmt.arms:
                arm_state = current.clone()
                for symbol_id in self._pattern_symbol_ids(arm.pattern):
                    arm_state.moved.setdefault(symbol_id, False)
                arm_states.append(self._check_block(program, semantic_function, arm.block, arm_state))
            if scrutinee_symbol is not None:
                binding = semantic_function.bindings.get(scrutinee_symbol)
                if binding is not None and not binding.typ.is_copy():
                    current.moved[scrutinee_symbol] = True
            merged = current
            for arm_state in arm_states:
                merged = self._merge_two_states(merged, arm_state)
            return merged
        if isinstance(stmt, ast.ReturnStmt):
            if stmt.expr is not None:
                self._walk_expr(program, semantic_function, stmt.expr, current, consume=True, in_call_arg=False)
            return current
        if isinstance(stmt, ast.ExprStmt):
            self._walk_expr(program, semantic_function, stmt.expr, current, consume=False, in_call_arg=False)
            return current
        return current

    def _walk_expr(
        self,
        program: SemanticProgram,
        semantic_function: SemanticFunction,
        expr: ast.Expr,
        state: MoveState,
        *,
        consume: bool,
        in_call_arg: bool,
    ) -> None:
        if isinstance(expr, ast.NameExpr):
            if expr.resolution_kind == "local" and expr.symbol_id is not None:
                binding = semantic_function.bindings.get(expr.symbol_id)
                if binding is None:
                    return
                if state.moved.get(expr.symbol_id, False) and not binding.is_ref_param:
                    self.diagnostics.add(
                        "NQ-BORROW-001",
                        "BORROW",
                        f"use of moved value `{binding.name}`",
                        expr.span,
                    )
                    return
                if consume and not binding.typ.is_copy() and not binding.is_ref_param:
                    state.moved[expr.symbol_id] = True
            return
        if isinstance(expr, ast.BorrowExpr):
            if not in_call_arg:
                self.diagnostics.add(
                    "NQ-BORROW-002",
                    "BORROW",
                    "borrow expressions are only valid as direct call arguments in v0.1",
                    expr.span,
                )
            if expr.symbol_id is not None and state.moved.get(expr.symbol_id, False):
                binding = semantic_function.bindings.get(expr.symbol_id)
                name = binding.name if binding is not None else expr.name
                self.diagnostics.add(
                    "NQ-BORROW-003",
                    "BORROW",
                    f"cannot borrow moved value `{name}`",
                    expr.span,
                )
            return
        if isinstance(expr, ast.UnaryExpr):
            self._walk_expr(program, semantic_function, expr.expr, state, consume=False, in_call_arg=False)
            return
        if isinstance(expr, ast.BinaryExpr):
            self._walk_expr(program, semantic_function, expr.left, state, consume=False, in_call_arg=False)
            self._walk_expr(program, semantic_function, expr.right, state, consume=False, in_call_arg=False)
            return
        if isinstance(expr, ast.FieldExpr):
            self._walk_expr(program, semantic_function, expr.base, state, consume=False, in_call_arg=False)
            if consume and expr.inferred_type is not None and not expr.inferred_type.is_copy():
                self.diagnostics.add(
                    "NQ-BORROW-004",
                    "BORROW",
                    "moving out of fields is not supported in v0.1",
                    expr.span,
                )
            return
        if isinstance(expr, ast.StructLiteralExpr):
            for field in expr.fields:
                self._walk_expr(program, semantic_function, field.expr, state, consume=True, in_call_arg=False)
            return
        if isinstance(expr, ast.CallExpr):
            if not isinstance(expr.callee, ast.NameExpr):
                self.diagnostics.add("NQ-BORROW-005", "BORROW", "unsupported callee shape", expr.span)
                return
            if expr.call_kind == "function" and expr.target_name in program.functions:
                signature = program.functions[expr.target_name]
                borrowed: dict[int, str] = {}
                consumed_symbols: set[int] = set()
                for arg, param_type in zip(expr.args, signature.param_types):
                    if param_type.kind == "ref":
                        if not isinstance(arg, ast.BorrowExpr) or arg.symbol_id is None:
                            continue
                        previous = borrowed.get(arg.symbol_id)
                        kind = "mutref" if arg.mutable else "ref"
                        if previous == "mutref" or (previous == "ref" and kind == "mutref"):
                            binding = semantic_function.bindings.get(arg.symbol_id)
                            name = binding.name if binding else arg.name
                            self.diagnostics.add(
                                "NQ-BORROW-006",
                                "BORROW",
                                f"conflicting borrows of `{name}` in one call",
                                arg.span,
                            )
                        borrowed[arg.symbol_id] = kind
                        if arg.symbol_id in consumed_symbols:
                            binding = semantic_function.bindings.get(arg.symbol_id)
                            name = binding.name if binding else arg.name
                            self.diagnostics.add(
                                "NQ-BORROW-007",
                                "BORROW",
                                f"cannot both move and borrow `{name}` in one call",
                                arg.span,
                            )
                        self._walk_expr(program, semantic_function, arg, state, consume=False, in_call_arg=True)
                        continue
                    symbol_id = self._expr_symbol_id(arg)
                    if symbol_id is not None:
                        if symbol_id in borrowed:
                            binding = semantic_function.bindings.get(symbol_id)
                            name = binding.name if binding else "<value>"
                            self.diagnostics.add(
                                "NQ-BORROW-007",
                                "BORROW",
                                f"cannot both move and borrow `{name}` in one call",
                                arg.span,
                            )
                        consumed_symbols.add(symbol_id)
                    self._walk_expr(program, semantic_function, arg, state, consume=True, in_call_arg=True)
                return
            if expr.call_kind == "variant":
                for arg in expr.args:
                    self._walk_expr(program, semantic_function, arg, state, consume=True, in_call_arg=True)
                return
            self._walk_expr(program, semantic_function, expr.callee, state, consume=False, in_call_arg=False)
            for arg in expr.args:
                self._walk_expr(program, semantic_function, arg, state, consume=False, in_call_arg=True)

    def _merge_states(self, base: MoveState, left: MoveState, right: MoveState) -> MoveState:
        merged = base.clone()
        for symbol_id in merged.moved:
            merged.moved[symbol_id] = left.moved.get(symbol_id, False) or right.moved.get(symbol_id, False)
        return merged

    def _merge_two_states(self, left: MoveState, right: MoveState) -> MoveState:
        merged = left.clone()
        for symbol_id in set(left.moved) | set(right.moved):
            merged.moved[symbol_id] = left.moved.get(symbol_id, False) or right.moved.get(symbol_id, False)
        return merged

    def _expr_symbol_id(self, expr: ast.Expr) -> int | None:
        if isinstance(expr, ast.NameExpr) and expr.resolution_kind == "local":
            return expr.symbol_id
        return None

    def _pattern_symbol_ids(self, pattern: ast.Pattern) -> list[int]:
        if isinstance(pattern, ast.NamePattern) and pattern.resolution_kind == "binding" and pattern.symbol_id is not None:
            return [pattern.symbol_id]
        if isinstance(pattern, ast.VariantPattern):
            result: list[int] = []
            for nested in pattern.args:
                result.extend(self._pattern_symbol_ids(nested))
            return result
        return []

