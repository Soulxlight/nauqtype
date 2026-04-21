from __future__ import annotations

from compiler.ast import nodes as ast
from compiler.diagnostics import DiagnosticBag, SourceFile, Span
from compiler.lexer import Token


AUDIT_CLAUSES = {"intent", "mutates", "effects"}


class Parser:
    def __init__(self, tokens: list[Token], diagnostics: DiagnosticBag, source: SourceFile | None = None) -> None:
        self.tokens = tokens
        self.diagnostics = diagnostics
        self.source = source
        self.index = 0

    def parse(self) -> ast.Program:
        items: list[ast.Item] = []
        start = self._current().span.start
        seen_non_use = False
        while not self._at("EOF"):
            item = self._parse_item()
            if item is not None:
                if isinstance(item, ast.UseDecl):
                    if seen_non_use:
                        self.diagnostics.add(
                            "NQ-PARSE-004",
                            "PARSE",
                            "`use` declarations must appear before non-`use` items",
                            item.span,
                            source=self.source,
                        )
                else:
                    seen_non_use = True
                items.append(item)
            else:
                self._synchronize_item()
        end = self._current().span.end
        return ast.Program(items=items, span=Span(start, end))

    def _parse_item(self) -> ast.Item | None:
        public = self._match("PUB")
        if public and self._at("USE"):
            token = self._current()
            self.diagnostics.add(
                "NQ-PARSE-001",
                "PARSE",
                "`use` declarations cannot be marked `pub`",
                token.span,
                source=self.source,
            )
            public = False
        if self._at("FN"):
            return self._parse_function(public)
        if self._at("TYPE"):
            return self._parse_type_decl(public)
        if self._at("ENUM"):
            return self._parse_enum_decl(public)
        if self._at("USE"):
            return self._parse_use()

        token = self._current()
        self.diagnostics.add(
            "NQ-PARSE-001",
            "PARSE",
            f"expected item declaration, found `{token.lexeme or token.kind}`",
            token.span,
            source=self.source,
        )
        return None

    def _parse_use(self) -> ast.UseDecl:
        start = self._expect("USE", "expected `use`").span.start
        name = self._expect("IDENT", "expected module name after `use`")
        semi = self._expect("SEMI", "expected `;` after use declaration")
        return ast.UseDecl(name=name.lexeme, span=Span(start, semi.span.end))

    def _parse_function(self, public: bool) -> ast.FunctionDecl:
        start = self._expect("FN", "expected `fn`").span.start
        name = self._expect("IDENT", "expected function name")
        self._expect("LPAREN", "expected `(` after function name")
        params: list[ast.Param] = []
        if not self._at("RPAREN"):
            while True:
                param_start = self._current().span.start
                param_name = self._expect("IDENT", "expected parameter name")
                self._expect("COLON", "expected `:` after parameter name")
                type_expr = self._parse_type_expr()
                params.append(
                    ast.Param(name=param_name.lexeme, type_expr=type_expr, span=Span(param_start, type_expr.span.end))
                )
                if not self._match("COMMA"):
                    break
                if self._at("RPAREN"):
                    break
        self._expect("RPAREN", "expected `)` after parameters")
        self._expect("ARROW", "expected `->` after parameter list")
        return_type = self._parse_type_expr()
        audit = self._parse_audit_decl() if self._at("AUDIT") else None
        body = self._parse_block()
        return ast.FunctionDecl(
            name=name.lexeme,
            params=params,
            return_type=return_type,
            audit=audit,
            body=body,
            public=public,
            span=Span(start, body.span.end),
        )

    def _parse_audit_decl(self) -> ast.AuditDecl:
        start = self._expect("AUDIT", "expected `audit`").span.start
        self._expect("LBRACE", "expected `{` after `audit`")
        intent, intent_span = self._parse_intent_clause()
        mutates, mutates_span = self._parse_audit_name_list_clause("mutates")
        effects, effects_span = self._parse_audit_name_list_clause("effects")
        end = self._expect("RBRACE", "expected `}` after audit block").span.end
        return ast.AuditDecl(
            intent=intent,
            intent_span=intent_span,
            mutates=mutates,
            mutates_span=mutates_span,
            effects=effects,
            effects_span=effects_span,
            span=Span(start, end),
        )

    def _parse_intent_clause(self) -> tuple[str, Span]:
        matched, clause_span = self._expect_audit_clause_name("intent")
        if not matched:
            return "", clause_span
        self._expect("LPAREN", "expected `(` after `intent`")
        token = self._expect("STRING", "expected string literal in `intent(...)`")
        self._expect("RPAREN", "expected `)` after `intent` text")
        semi = self._expect("SEMI", "expected `;` after `intent(...)`")
        return token.lexeme if token.kind == "STRING" else "", Span(clause_span.start, semi.span.end)

    def _parse_audit_name_list_clause(self, clause_name: str) -> tuple[list[ast.AuditName], Span]:
        matched, clause_span = self._expect_audit_clause_name(clause_name)
        if not matched:
            return [], clause_span
        self._expect("LPAREN", f"expected `(` after `{clause_name}`")
        names: list[ast.AuditName] = []
        if not self._at("RPAREN"):
            while True:
                token = self._expect("IDENT", f"expected name in `{clause_name}(...)`")
                if token.kind == "IDENT":
                    names.append(ast.AuditName(name=token.lexeme, span=token.span))
                if not self._match("COMMA"):
                    break
                if self._at("RPAREN"):
                    break
        self._expect("RPAREN", f"expected `)` after `{clause_name}` list")
        semi = self._expect("SEMI", f"expected `;` after `{clause_name}(...)`")
        return names, Span(clause_span.start, semi.span.end)

    def _expect_audit_clause_name(self, expected: str) -> tuple[bool, Span]:
        token = self._current()
        while token.kind == "IDENT" and token.lexeme in AUDIT_CLAUSES and token.lexeme != expected:
            self.diagnostics.add(
                "NQ-CONTRACT-002",
                "CONTRACT",
                f"expected `{expected}(...)` clause, found `{token.lexeme}(...)`",
                token.span,
                source=self.source,
                help="Audit clause order is fixed: `intent`, then `mutates`, then `effects`.",
            )
            self._skip_audit_clause()
            token = self._current()
        if token.kind == "IDENT" and token.lexeme == expected:
            self._advance()
            return True, token.span
        self.diagnostics.add(
            "NQ-CONTRACT-002",
            "CONTRACT",
            f"expected `{expected}(...)` clause in audit block",
            token.span,
            source=self.source,
            help="Audit blocks must contain `intent`, `mutates`, and `effects` in that order.",
        )
        return False, token.span

    def _skip_audit_clause(self) -> None:
        depth = 0
        if not self._at("EOF") and not self._at("RBRACE"):
            self._advance()
        while not self._at("EOF"):
            token = self._current()
            if token.kind == "LPAREN":
                depth += 1
                self._advance()
                continue
            if token.kind == "RPAREN":
                depth = max(0, depth - 1)
                self._advance()
                continue
            if token.kind == "SEMI" and depth == 0:
                self._advance()
                return
            if token.kind == "RBRACE" and depth == 0:
                return
            self._advance()

    def _parse_type_decl(self, public: bool) -> ast.TypeDecl:
        start = self._expect("TYPE", "expected `type`").span.start
        name = self._expect("IDENT", "expected type name")
        self._expect("LBRACE", "expected `{` after type name")
        fields: list[ast.FieldDecl] = []
        if not self._at("RBRACE"):
            while True:
                field_start = self._current().span.start
                field_name = self._expect("IDENT", "expected field name")
                self._expect("COLON", "expected `:` after field name")
                field_type = self._parse_type_expr()
                fields.append(ast.FieldDecl(field_name.lexeme, field_type, Span(field_start, field_type.span.end)))
                if not self._match("COMMA"):
                    break
                if self._at("RBRACE"):
                    break
        end = self._expect("RBRACE", "expected `}` after type declaration").span.end
        return ast.TypeDecl(name.lexeme, fields, public, Span(start, end))

    def _parse_enum_decl(self, public: bool) -> ast.EnumDecl:
        start = self._expect("ENUM", "expected `enum`").span.start
        name = self._expect("IDENT", "expected enum name")
        self._expect("LBRACE", "expected `{` after enum name")
        variants: list[ast.VariantDecl] = []
        if not self._at("RBRACE"):
            while True:
                variant_start = self._current().span.start
                variant_name = self._expect("IDENT", "expected variant name")
                payloads: list[ast.TypeExpr] = []
                if self._match("LPAREN"):
                    if not self._at("RPAREN"):
                        while True:
                            payloads.append(self._parse_type_expr())
                            if not self._match("COMMA"):
                                break
                            if self._at("RPAREN"):
                                break
                    self._expect("RPAREN", "expected `)` after variant payloads")
                variants.append(ast.VariantDecl(variant_name.lexeme, payloads, Span(variant_start, self._previous().span.end)))
                if not self._match("COMMA"):
                    break
                if self._at("RBRACE"):
                    break
        end = self._expect("RBRACE", "expected `}` after enum declaration").span.end
        return ast.EnumDecl(name.lexeme, variants, public, Span(start, end))

    def _parse_type_expr(self) -> ast.TypeExpr:
        if self._match("REF"):
            op = self._previous()
            inner = self._parse_named_type_expr()
            return ast.BorrowTypeExpr(mutable=False, inner=inner, span=Span(op.span.start, inner.span.end))
        if self._match("MUTREF"):
            op = self._previous()
            inner = self._parse_named_type_expr()
            return ast.BorrowTypeExpr(mutable=True, inner=inner, span=Span(op.span.start, inner.span.end))
        return self._parse_named_type_expr()

    def _parse_named_type_expr(self) -> ast.NamedTypeExpr:
        name = self._expect("IDENT", "expected type name")
        args: list[ast.TypeExpr] = []
        end = name.span.end
        if self._match("LT"):
            while True:
                args.append(self._parse_type_expr())
                if not self._match("COMMA"):
                    break
                if self._at("GT"):
                    break
            end = self._expect("GT", "expected `>` after type arguments").span.end
        return ast.NamedTypeExpr(name.lexeme, args, Span(name.span.start, end))

    def _parse_block(self) -> ast.Block:
        start = self._expect("LBRACE", "expected `{` to start block").span.start
        statements: list[ast.Stmt] = []
        while not self._at("RBRACE") and not self._at("EOF"):
            stmt = self._parse_stmt()
            if stmt is not None:
                statements.append(stmt)
            else:
                self._synchronize_stmt()
        end = self._expect("RBRACE", "expected `}` to close block").span.end
        return ast.Block(statements=statements, span=Span(start, end))

    def _parse_stmt(self) -> ast.Stmt | None:
        if self._at("LET"):
            return self._parse_let_stmt()
        if self._at("IF"):
            return self._parse_if_stmt()
        if self._at("WHILE"):
            return self._parse_while_stmt()
        if self._at("MATCH"):
            return self._parse_match_stmt()
        if self._at("RETURN"):
            return self._parse_return_stmt()
        if self._at("IDENT") and self._peek(1).kind == "EQ":
            return self._parse_assign_stmt()
        expr = self._parse_expr()
        semi = self._expect("SEMI", "expected `;` after expression")
        return ast.ExprStmt(expr=expr, span=Span(expr.span.start, semi.span.end))

    def _parse_let_stmt(self) -> ast.LetStmt:
        start = self._expect("LET", "expected `let`").span.start
        mutable = self._match("MUT")
        name = self._expect("IDENT", "expected binding name")
        annotation = None
        if self._match("COLON"):
            annotation = self._parse_type_expr()
        self._expect("EQ", "expected `=` in binding")
        expr = self._parse_expr()
        semi = self._expect("SEMI", "expected `;` after binding")
        return ast.LetStmt(name.lexeme, mutable, annotation, expr, Span(start, semi.span.end))

    def _parse_assign_stmt(self) -> ast.AssignStmt:
        target = self._expect("IDENT", "expected assignment target")
        self._expect("EQ", "expected `=` in assignment")
        expr = self._parse_expr()
        semi = self._expect("SEMI", "expected `;` after assignment")
        return ast.AssignStmt(target.lexeme, expr, Span(target.span.start, semi.span.end))

    def _parse_if_stmt(self) -> ast.IfStmt:
        start = self._expect("IF", "expected `if`").span.start
        condition = self._parse_expr()
        then_block = self._parse_block()
        else_block = None
        end = then_block.span.end
        if self._match("ELSE"):
            else_block = self._parse_block()
            end = else_block.span.end
        return ast.IfStmt(condition, then_block, else_block, Span(start, end))

    def _parse_while_stmt(self) -> ast.WhileStmt:
        start = self._expect("WHILE", "expected `while`").span.start
        condition = self._parse_expr()
        body = self._parse_block()
        return ast.WhileStmt(condition=condition, body=body, span=Span(start, body.span.end))

    def _parse_match_stmt(self) -> ast.MatchStmt:
        start = self._expect("MATCH", "expected `match`").span.start
        expr = self._parse_expr()
        self._expect("LBRACE", "expected `{` after match expression")
        arms: list[ast.MatchArm] = []
        while not self._at("RBRACE") and not self._at("EOF"):
            arm_start = self._current().span.start
            pattern = self._parse_pattern()
            self._expect("FAT_ARROW", "expected `=>` in match arm")
            block = self._parse_block()
            arms.append(ast.MatchArm(pattern, block, Span(arm_start, block.span.end)))
            if not self._match("COMMA"):
                break
        end = self._expect("RBRACE", "expected `}` after match arms").span.end
        return ast.MatchStmt(expr, arms, Span(start, end))

    def _parse_return_stmt(self) -> ast.ReturnStmt:
        start = self._expect("RETURN", "expected `return`").span.start
        expr = None
        if not self._at("SEMI"):
            expr = self._parse_expr()
        semi = self._expect("SEMI", "expected `;` after return")
        return ast.ReturnStmt(expr, Span(start, semi.span.end))

    def _parse_pattern(self) -> ast.Pattern:
        if self._at("IDENT") and self._current().lexeme == "_":
            token = self._advance()
            return ast.WildcardPattern(token.span)
        name = self._expect("IDENT", "expected pattern")
        if self._match("LPAREN"):
            args: list[ast.Pattern] = []
            if not self._at("RPAREN"):
                while True:
                    args.append(self._parse_pattern())
                    if not self._match("COMMA"):
                        break
            end = self._expect("RPAREN", "expected `)` after pattern arguments").span.end
            return ast.VariantPattern(name.lexeme, args, Span(name.span.start, end))
        return ast.NamePattern(name.lexeme, name.span)

    def _parse_expr(self) -> ast.Expr:
        return self._parse_or()

    def _parse_or(self) -> ast.Expr:
        expr = self._parse_and()
        while self._match("OR"):
            op = self._previous()
            right = self._parse_and()
            expr = ast.BinaryExpr(expr, op.lexeme, right, Span(expr.span.start, right.span.end))
        return expr

    def _parse_and(self) -> ast.Expr:
        expr = self._parse_equality()
        while self._match("AND"):
            op = self._previous()
            right = self._parse_equality()
            expr = ast.BinaryExpr(expr, op.lexeme, right, Span(expr.span.start, right.span.end))
        return expr

    def _parse_equality(self) -> ast.Expr:
        expr = self._parse_comparison()
        while self._match("EQEQ", "NOTEQ"):
            op = self._previous()
            right = self._parse_comparison()
            expr = ast.BinaryExpr(expr, op.lexeme, right, Span(expr.span.start, right.span.end))
        return expr

    def _parse_comparison(self) -> ast.Expr:
        expr = self._parse_term()
        while self._match("LT", "LTE", "GT", "GTE"):
            op = self._previous()
            right = self._parse_term()
            expr = ast.BinaryExpr(expr, op.lexeme, right, Span(expr.span.start, right.span.end))
        return expr

    def _parse_term(self) -> ast.Expr:
        expr = self._parse_factor()
        while self._match("PLUS", "MINUS"):
            op = self._previous()
            right = self._parse_factor()
            expr = ast.BinaryExpr(expr, op.lexeme, right, Span(expr.span.start, right.span.end))
        return expr

    def _parse_factor(self) -> ast.Expr:
        expr = self._parse_unary()
        while self._match("STAR", "SLASH"):
            op = self._previous()
            right = self._parse_unary()
            expr = ast.BinaryExpr(expr, op.lexeme, right, Span(expr.span.start, right.span.end))
        return expr

    def _parse_unary(self) -> ast.Expr:
        if self._match("MINUS", "NOT"):
            op = self._previous()
            expr = self._parse_unary()
            return ast.UnaryExpr(op.lexeme, expr, Span(op.span.start, expr.span.end))
        if self._match("REF", "MUTREF"):
            op = self._previous()
            name = self._expect("IDENT", "expected identifier after borrow operator")
            return ast.BorrowExpr(op.kind == "MUTREF", name.lexeme, Span(op.span.start, name.span.end))
        return self._parse_postfix()

    def _parse_postfix(self) -> ast.Expr:
        expr = self._parse_primary()
        while True:
            if self._match("LPAREN"):
                args: list[ast.Expr] = []
                if not self._at("RPAREN"):
                    while True:
                        args.append(self._parse_expr())
                        if not self._match("COMMA"):
                            break
                        if self._at("RPAREN"):
                            break
                end = self._expect("RPAREN", "expected `)` after arguments").span.end
                expr = ast.CallExpr(expr, args, Span(expr.span.start, end))
                continue
            if self._match("DOT"):
                name = self._expect("IDENT", "expected field name after `.`")
                expr = ast.FieldExpr(expr, name.lexeme, Span(expr.span.start, name.span.end))
                continue
            break
        return expr

    def _parse_primary(self) -> ast.Expr:
        if self._match("INT"):
            token = self._previous()
            return ast.IntLiteral(value=int(token.lexeme), span=token.span)
        if self._match("STRING"):
            token = self._previous()
            return ast.StringLiteral(value=token.lexeme, span=token.span)
        if self._match("TRUE"):
            token = self._previous()
            return ast.BoolLiteral(value=True, span=token.span)
        if self._match("FALSE"):
            token = self._previous()
            return ast.BoolLiteral(value=False, span=token.span)
        if self._match("IDENT"):
            token = self._previous()
            if self._at("LBRACE") and self._looks_like_struct_literal():
                self._advance()
                fields: list[ast.FieldInit] = []
                if not self._at("RBRACE"):
                    while True:
                        field_name = self._expect("IDENT", "expected field name in struct literal")
                        self._expect("COLON", "expected `:` after field name")
                        value = self._parse_expr()
                        fields.append(ast.FieldInit(field_name.lexeme, value, Span(field_name.span.start, value.span.end)))
                        if not self._match("COMMA"):
                            break
                        if self._at("RBRACE"):
                            break
                end = self._expect("RBRACE", "expected `}` after struct literal").span.end
                return ast.StructLiteralExpr(token.lexeme, fields, Span(token.span.start, end))
            return ast.NameExpr(token.lexeme, token.span)
        if self._match("LPAREN"):
            expr = self._parse_expr()
            self._expect("RPAREN", "expected `)` after expression")
            return expr

        token = self._current()
        self.diagnostics.add(
            "NQ-PARSE-002",
            "PARSE",
            f"expected expression, found `{token.lexeme or token.kind}`",
            token.span,
            source=self.source,
        )
        self._advance()
        return ast.IntLiteral(0, token.span)

    def _synchronize_item(self) -> None:
        while not self._at("EOF"):
            if self._current().kind in {"FN", "TYPE", "ENUM", "USE", "PUB"}:
                return
            self._advance()

    def _synchronize_stmt(self) -> None:
        while not self._at("EOF") and not self._at("RBRACE"):
            if self._match("SEMI"):
                return
            if self._current().kind in {"LET", "IF", "WHILE", "MATCH", "RETURN"}:
                return
            self._advance()

    def _at(self, kind: str) -> bool:
        return self._current().kind == kind

    def _match(self, *kinds: str) -> bool:
        if self._current().kind in kinds:
            self._advance()
            return True
        return False

    def _expect(self, kind: str, message: str) -> Token:
        if self._at(kind):
            return self._advance()
        token = self._current()
        self.diagnostics.add("NQ-PARSE-003", "PARSE", message, token.span, source=self.source)
        return token

    def _current(self) -> Token:
        return self.tokens[self.index]

    def _previous(self) -> Token:
        return self.tokens[self.index - 1]

    def _peek(self, offset: int) -> Token:
        index = min(self.index + offset, len(self.tokens) - 1)
        return self.tokens[index]

    def _advance(self) -> Token:
        token = self.tokens[self.index]
        if self.index < len(self.tokens) - 1:
            self.index += 1
        return token

    def _looks_like_struct_literal(self) -> bool:
        if not self._at("LBRACE"):
            return False
        next_token = self._peek(1)
        if next_token.kind == "RBRACE":
            return True
        return next_token.kind == "IDENT" and self._peek(2).kind == "COLON"
