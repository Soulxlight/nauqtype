from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from compiler.ast import nodes as ast
from compiler.diagnostics import DiagnosticBag, SourceFile
from compiler.lexer import Lexer
from compiler.parser import Parser


@dataclass(slots=True)
class ModuleUnit:
    name: str
    path: Path
    source: SourceFile
    program: ast.Program
    uses: list[ast.UseDecl] = field(default_factory=list)


@dataclass(slots=True)
class Project:
    workspace_root: Path
    entry_module: str
    modules: dict[str, ModuleUnit]
    order: list[str]


class ProjectLoader:
    def __init__(self, diagnostics: DiagnosticBag) -> None:
        self.diagnostics = diagnostics
        self.workspace_root: Path | None = None
        self.modules: dict[str, ModuleUnit] = {}
        self.order: list[str] = []
        self._loading: list[str] = []

    def load(self, entry_source: SourceFile) -> Project | None:
        entry_path = entry_source.path.resolve()
        self.workspace_root = entry_path.parent
        entry_name = entry_path.stem
        self._load_module(entry_name, entry_path, use_decl=None, source_override=entry_source)
        if self.workspace_root is None:
            return None
        return Project(
            workspace_root=self.workspace_root,
            entry_module=entry_name,
            modules=self.modules,
            order=self.order,
        )

    def _load_module(
        self,
        module_name: str,
        module_path: Path,
        *,
        use_decl: ast.UseDecl | None,
        source_override: SourceFile | None = None,
    ) -> None:
        if module_name in self._loading:
            cycle = " -> ".join(self._loading + [module_name])
            self.diagnostics.add(
                "NQ-IMPORT-003",
                "IMPORT",
                f"import cycle detected: {cycle}",
                use_decl.span if use_decl is not None else None,
                source=self.modules[self._loading[-1]].source if self._loading else None,
            )
            return
        if module_name in self.modules:
            return
        if source_override is None and not module_path.exists():
            source = None
            if self._loading:
                source = self.modules[self._loading[-1]].source
            self.diagnostics.add(
                "NQ-IMPORT-001",
                "IMPORT",
                f"module `{module_name}` was not found at `{module_path.name}`",
                use_decl.span if use_decl is not None else None,
                source=source,
            )
            return

        source = source_override or SourceFile.from_path(module_path)
        tokens = Lexer(source, self.diagnostics).tokenize()
        program = Parser(tokens, self.diagnostics, source).parse()
        program.module_name = module_name
        self._annotate_module_name(program, module_name)
        unit = ModuleUnit(
            name=module_name,
            path=module_path,
            source=source,
            program=program,
            uses=[item for item in program.items if isinstance(item, ast.UseDecl)],
        )
        self.modules[module_name] = unit

        self._loading.append(module_name)
        for use in unit.uses:
            assert self.workspace_root is not None
            imported_path = self.workspace_root / f"{use.name}.nq"
            self._load_module(use.name, imported_path, use_decl=use)
        self._loading.pop()
        self.order.append(module_name)

    def _annotate_module_name(self, program: ast.Program, module_name: str) -> None:
        for item in program.items:
            if isinstance(item, ast.FunctionDecl | ast.TypeDecl | ast.EnumDecl):
                item.module_name = module_name
