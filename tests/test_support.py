from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
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


def run_copied_selfhost(timeout: int = 40) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp = Path(tmp_dir)
        for module_path in (ROOT / "selfhost").glob("*.nq"):
            shutil.copy(module_path, tmp / module_path.name)
        return subprocess.run(
            [sys.executable, "-m", "compiler.main", "run", str(tmp / "main.nq")],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
