from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from compiler.borrow import BorrowChecker
from compiler.codegen_c import CEmitter
from compiler.diagnostics import DiagnosticBag, SourceFile, render_diagnostics
from compiler.ir import lower_program
from compiler.lexer import Lexer
from compiler.parser import Parser
from compiler.resolve import Resolver
from compiler.types import TypeChecker


def compile_source(source: SourceFile) -> tuple[DiagnosticBag, str | None]:
    diagnostics = DiagnosticBag()
    try:
        tokens = Lexer(source, diagnostics).tokenize()
        program = Parser(tokens, diagnostics).parse()
        module = Resolver(diagnostics).resolve(program)
        semantic = TypeChecker(diagnostics).check(program, module)
        BorrowChecker(diagnostics).check(semantic)
        if diagnostics.has_errors():
            return diagnostics, None
        lowered = lower_program(semantic, diagnostics)
        if diagnostics.has_errors() or lowered is None:
            return diagnostics, None
        emitted = CEmitter(lowered).emit()
        return diagnostics, emitted
    except Exception as exc:  # pragma: no cover - defensive final safety net
        diagnostics.add(
            "NQ-INTERNAL-001",
            "INTERNAL",
            "internal compiler error",
            notes=[f"{type(exc).__name__}: {exc}"],
            help="This is a compiler bug; please report it with the source file that triggered it.",
        )
        return diagnostics, None


def detect_zig(project_root: Path) -> Path | None:
    candidate = project_root / ".deps" / "ziglang" / "zig.exe"
    if candidate.exists():
        return candidate
    return None


def compile_c(project_root: Path, c_path: Path, exe_path: Path) -> tuple[int, str]:
    zig = detect_zig(project_root)
    if zig is None:
        return 1, "zig compiler not found at .deps/ziglang/zig.exe; run `python scripts/setup_deps.py` first"
    runtime_c = project_root / "stdlib" / "runtime.c"
    include_dir = project_root / "stdlib"
    command = [
        str(zig),
        "cc",
        "-std=c11",
        f"-I{include_dir}",
        str(c_path),
        str(runtime_c),
        "-o",
        str(exe_path),
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    output = (result.stdout + result.stderr).strip()
    return result.returncode, output


def run_cli(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="nauqc", description="Nauqtype bootstrap compiler")
    subparsers = parser.add_subparsers(dest="command", required=True)

    for command in ("check", "emit-c", "build", "run"):
        sub = subparsers.add_parser(command)
        sub.add_argument("source")
        sub.add_argument("-o", "--output")

    args = parser.parse_args(argv)
    source_path = Path(args.source).resolve()
    project_root = Path(__file__).resolve().parents[1]
    source = SourceFile.from_path(source_path)
    diagnostics, emitted = compile_source(source)
    if diagnostics.items:
        print(render_diagnostics(source, diagnostics.items), file=sys.stderr)
    if diagnostics.has_errors():
        return 1

    assert emitted is not None
    output_path = Path(args.output).resolve() if args.output else None

    if args.command == "check":
        return 0

    if args.command == "emit-c":
        if output_path is None:
            output_path = source_path.with_suffix(".c")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(emitted, encoding="utf-8")
        return 0

    build_dir = source_path.parent / "build"
    build_dir.mkdir(exist_ok=True)
    c_path = output_path if output_path and output_path.suffix == ".c" else build_dir / f"{source_path.stem}.c"
    exe_path = output_path if output_path and output_path.suffix != ".c" else build_dir / f"{source_path.stem}.exe"
    c_path.parent.mkdir(parents=True, exist_ok=True)
    exe_path.parent.mkdir(parents=True, exist_ok=True)
    c_path.write_text(emitted, encoding="utf-8")
    code, output = compile_c(project_root, c_path, exe_path)
    if code != 0:
        if output:
            print(output, file=sys.stderr)
        return code
    if args.command == "build":
        return 0

    result = subprocess.run([str(exe_path)], capture_output=True, text=True)
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)
    return result.returncode


def main() -> int:
    return run_cli(sys.argv[1:])


if __name__ == "__main__":
    raise SystemExit(main())
