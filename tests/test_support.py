from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from compiler.diagnostics import render_diagnostics
from compiler.diagnostics import SourceFile
from compiler.main import compile_source

ROOT = Path(__file__).resolve().parents[1]
_BOOTSTRAP_READY = False


def compile_text(text: str, name: str = "test.nq"):
    source = SourceFile(Path(name), text)
    return compile_source(source)


def render_text_diagnostics(text: str, name: str = "test.nq") -> str:
    source = SourceFile(Path(name), text)
    diagnostics, _ = compile_source(source)
    return render_diagnostics(source, diagnostics.items)


def ensure_bootstrap_deps() -> None:
    global _BOOTSTRAP_READY
    if _BOOTSTRAP_READY:
        return
    result = subprocess.run(
        [sys.executable, "scripts/setup_deps.py"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise AssertionError(result.stdout + result.stderr)
    _BOOTSTRAP_READY = True

