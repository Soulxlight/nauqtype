from __future__ import annotations

from bisect import bisect_right
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True, slots=True)
class Span:
    start: int
    end: int


@dataclass(slots=True)
class Diagnostic:
    code: str
    category: str
    message: str
    span: Span | None = None
    source: "SourceFile | None" = None
    severity: str = "error"
    notes: list[str] = field(default_factory=list)
    help: str | None = None


@dataclass(slots=True)
class SourceFile:
    path: Path
    text: str
    line_starts: list[int] = field(init=False)

    def __post_init__(self) -> None:
        self.line_starts = [0]
        for index, char in enumerate(self.text):
            if char == "\n":
                self.line_starts.append(index + 1)

    @classmethod
    def from_path(cls, path: str | Path) -> "SourceFile":
        file_path = Path(path)
        return cls(path=file_path, text=file_path.read_text(encoding="utf-8"))

    def line_col(self, offset: int) -> tuple[int, int]:
        line_index = bisect_right(self.line_starts, offset) - 1
        line_start = self.line_starts[line_index]
        return line_index + 1, offset - line_start + 1

    def line_text(self, line_number: int) -> str:
        start = self.line_starts[line_number - 1]
        if line_number < len(self.line_starts):
            end = self.line_starts[line_number] - 1
        else:
            end = len(self.text)
        return self.text[start:end]


class DiagnosticBag:
    def __init__(self) -> None:
        self.items: list[Diagnostic] = []

    def add(
        self,
        code: str,
        category: str,
        message: str,
        span: Span | None = None,
        *,
        source: SourceFile | None = None,
        severity: str = "error",
        notes: list[str] | None = None,
        help: str | None = None,
    ) -> None:
        self.items.append(
            Diagnostic(
                code=code,
                category=category,
                message=message,
                span=span,
                source=source,
                severity=severity,
                notes=notes or [],
                help=help,
            )
        )

    def extend(self, diagnostics: list[Diagnostic]) -> None:
        self.items.extend(diagnostics)

    def has_errors(self) -> bool:
        return any(item.severity == "error" for item in self.items)


def render_diagnostics(source: SourceFile, diagnostics: list[Diagnostic]) -> str:
    rendered: list[str] = []
    for diagnostic in diagnostics:
        header = f"{diagnostic.severity}[{diagnostic.code}]: {diagnostic.message}"
        rendered.append(header)
        active_source = diagnostic.source or source
        if diagnostic.span is not None and active_source is not None:
            line, column = active_source.line_col(diagnostic.span.start)
            rendered.append(f"  --> {active_source.path}:{line}:{column}")
            line_text = active_source.line_text(line)
            rendered.append(f"   | {line_text}")
            marker_len = max(1, diagnostic.span.end - diagnostic.span.start)
            rendered.append(f"   | {' ' * (column - 1)}{'^' * marker_len}")
        elif active_source is not None:
            rendered.append(f"  --> {active_source.path}")
        for note in diagnostic.notes:
            rendered.append(f"  note: {note}")
        if diagnostic.help:
            rendered.append(f"  help: {diagnostic.help}")
    return "\n".join(rendered)
