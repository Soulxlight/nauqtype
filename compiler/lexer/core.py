from __future__ import annotations

from dataclasses import dataclass

from compiler.diagnostics import DiagnosticBag, SourceFile, Span


KEYWORDS = {
    "and": "AND",
    "audit": "AUDIT",
    "else": "ELSE",
    "enum": "ENUM",
    "false": "FALSE",
    "fn": "FN",
    "if": "IF",
    "let": "LET",
    "match": "MATCH",
    "mut": "MUT",
    "mutref": "MUTREF",
    "not": "NOT",
    "or": "OR",
    "pub": "PUB",
    "ref": "REF",
    "return": "RETURN",
    "true": "TRUE",
    "type": "TYPE",
    "use": "USE",
    "while": "WHILE",
}

SINGLE_TOKENS = {
    "(": "LPAREN",
    ")": "RPAREN",
    "{": "LBRACE",
    "}": "RBRACE",
    ",": "COMMA",
    ";": "SEMI",
    ":": "COLON",
    ".": "DOT",
    "=": "EQ",
    "<": "LT",
    ">": "GT",
    "+": "PLUS",
    "-": "MINUS",
    "*": "STAR",
    "/": "SLASH",
}

DOUBLE_TOKENS = {
    "->": "ARROW",
    "=>": "FAT_ARROW",
    "==": "EQEQ",
    "!=": "NOTEQ",
    "<=": "LTE",
    ">=": "GTE",
}


@dataclass(frozen=True, slots=True)
class Token:
    kind: str
    lexeme: str
    span: Span


class Lexer:
    def __init__(self, source: SourceFile, diagnostics: DiagnosticBag) -> None:
        self.source = source
        self.diagnostics = diagnostics
        self.text = source.text
        self.length = len(self.text)
        self.index = 0
        self.tokens: list[Token] = []

    def tokenize(self) -> list[Token]:
        while not self._at_end():
            start = self.index
            char = self._advance()

            if char in " \r\t\n":
                continue

            if char == "/" and self._match("/"):
                while not self._at_end() and self._peek() != "\n":
                    self._advance()
                continue

            pair = char + self._peek()
            if pair in DOUBLE_TOKENS:
                self._advance()
                self.tokens.append(Token(DOUBLE_TOKENS[pair], pair, Span(start, self.index)))
                continue

            if char in SINGLE_TOKENS:
                self.tokens.append(Token(SINGLE_TOKENS[char], char, Span(start, self.index)))
                continue

            if char == "!":
                self.diagnostics.add(
                    "NQ-LEX-001",
                    "LEX",
                    "unexpected `!`; use `not` or `!=`",
                    Span(start, self.index),
                )
                continue

            if char == '"':
                self._lex_string(start)
                continue

            if char.isdigit():
                self._lex_number(start)
                continue

            if char == "_" or char.isalpha():
                self._lex_identifier(start)
                continue

            self.diagnostics.add(
                "NQ-LEX-002",
                "LEX",
                f"unexpected character `{char}`",
                Span(start, self.index),
            )

        eof_span = Span(self.length, self.length)
        self.tokens.append(Token("EOF", "", eof_span))
        return self.tokens

    def _lex_string(self, start: int) -> None:
        value: list[str] = []
        while not self._at_end():
            char = self._advance()
            if char == '"':
                lexeme = self.text[start:self.index]
                self.tokens.append(Token("STRING", "".join(value), Span(start, self.index)))
                return
            if char == "\\":
                if self._at_end():
                    break
                escape = self._advance()
                mapping = {"n": "\n", "t": "\t", '"': '"', "\\": "\\"}
                if escape not in mapping:
                    self.diagnostics.add(
                        "NQ-LEX-003",
                        "LEX",
                        f"unsupported escape `\\{escape}`",
                        Span(self.index - 2, self.index),
                    )
                    value.append(escape)
                else:
                    value.append(mapping[escape])
                continue
            if char == "\n":
                self.diagnostics.add(
                    "NQ-LEX-004",
                    "LEX",
                    "unterminated string literal",
                    Span(start, self.index),
                )
                return
            value.append(char)

        self.diagnostics.add(
            "NQ-LEX-004",
            "LEX",
            "unterminated string literal",
            Span(start, self.index),
        )

    def _lex_number(self, start: int) -> None:
        while not self._at_end() and self._peek().isdigit():
            self._advance()
        lexeme = self.text[start:self.index]
        self.tokens.append(Token("INT", lexeme, Span(start, self.index)))

    def _lex_identifier(self, start: int) -> None:
        while not self._at_end() and (self._peek() == "_" or self._peek().isalnum()):
            self._advance()
        lexeme = self.text[start:self.index]
        kind = KEYWORDS.get(lexeme, "IDENT")
        self.tokens.append(Token(kind, lexeme, Span(start, self.index)))

    def _at_end(self) -> bool:
        return self.index >= self.length

    def _peek(self) -> str:
        if self._at_end():
            return "\0"
        return self.text[self.index]

    def _advance(self) -> str:
        char = self.text[self.index]
        self.index += 1
        return char

    def _match(self, expected: str) -> bool:
        if self._at_end() or self.text[self.index] != expected:
            return False
        self.index += 1
        return True
