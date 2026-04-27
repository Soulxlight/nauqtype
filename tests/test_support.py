from __future__ import annotations

from contextlib import contextmanager
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
import re

from compiler.diagnostics import render_diagnostics
from compiler.diagnostics import SourceFile
from compiler.main import compile_c, compile_source

ROOT = Path(__file__).resolve().parents[1]
_BOOTSTRAP_READY = False
_COPIED_SELFHOST_CACHE: dict[int, subprocess.CompletedProcess[str]] = {}
SELFHOST_REFERENCE_TIMEOUT = 360
STAGE1_DRIVER_BUILD_TIMEOUT = 1200


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
    zig = ROOT / ".deps" / "ziglang" / "zig.exe"
    zig_dist = ROOT / ".deps" / "ziglang-0.16.0.dist-info"
    tiktoken_package = ROOT / ".deps" / "tiktoken"
    tiktoken_dist = ROOT / ".deps" / "tiktoken-0.12.0.dist-info"
    deps_path = str(ROOT / ".deps")
    if zig.exists() and zig_dist.exists() and tiktoken_package.exists() and tiktoken_dist.exists():
        if deps_path not in sys.path:
            sys.path.insert(0, deps_path)
        try:
            import tiktoken  # pylint: disable=import-outside-toplevel

            if tiktoken.__version__ == "0.12.0":
                _BOOTSTRAP_READY = True
                return
        except ImportError:
            pass
    result = subprocess.run(
        [sys.executable, "scripts/setup_deps.py"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise AssertionError(result.stdout + result.stderr)
    _BOOTSTRAP_READY = True


def copy_selfhost_workspace(destination: Path) -> None:
    for module_path in (ROOT / "selfhost").glob("*.nq"):
        shutil.copy(module_path, destination / module_path.name)


@contextmanager
def copied_selfhost_workspace():
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp_dir:
        tmp = Path(tmp_dir)
        copy_selfhost_workspace(tmp)
        yield tmp


def normalize_structural_c(text: str) -> str:
    normalized_lines: list[str] = []
    binding_ids: dict[str, str] = {}
    tmp_ids: dict[str, str] = {}

    def replace_binding(match: re.Match[str]) -> str:
        original = match.group(1)
        if original not in binding_ids:
            binding_ids[original] = str(len(binding_ids) + 1)
        return f"nqv_{binding_ids[original]}_{match.group(2)}"

    def replace_tmp(match: re.Match[str]) -> str:
        original = match.group(1)
        if original not in tmp_ids:
            tmp_ids[original] = str(len(tmp_ids) + 1)
        return f"nq_tmp_{tmp_ids[original]}"

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        line = re.sub(r"nqv_(\d+)_([A-Za-z0-9_]+)", replace_binding, line)
        line = re.sub(r"nq_tmp_(\d+)", replace_tmp, line)
        normalized_lines.append(line)
    return "\n".join(normalized_lines)


def run_stage0_selfhost(workspace: Path, *, timeout: int = 240) -> subprocess.CompletedProcess[str]:
    ensure_bootstrap_deps()
    return subprocess.run(
        [sys.executable, "-m", "compiler.main", "run", str(workspace / "main.nq")],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def run_stage0_selfhost_and_capture_c(workspace: Path, *, timeout: int = 240) -> tuple[subprocess.CompletedProcess[str], str]:
    result = run_stage0_selfhost(workspace, timeout=timeout)
    emitted_c = workspace / "build" / "main.c"
    if not emitted_c.exists():
        raise AssertionError(f"missing emitted C at {emitted_c}")
    return result, emitted_c.read_text(encoding="utf-8")


def compile_c_only(c_path: Path, *, exe_path: Path | None = None) -> Path:
    ensure_bootstrap_deps()
    exe_path = exe_path if exe_path is not None else c_path.with_suffix(".exe")
    code, output = compile_c(ROOT, c_path, exe_path)
    if code != 0:
        raise AssertionError(output)
    return exe_path


def run_executable(exe_path: Path, *, cwd: Path, timeout: int = 240) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(exe_path)],
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def compile_and_run_c(c_path: Path, *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    exe_path = compile_c_only(c_path)
    return run_executable(
        exe_path,
        cwd=cwd if cwd is not None else c_path.parent,
    )


def run_copied_selfhost(timeout: int = SELFHOST_REFERENCE_TIMEOUT) -> subprocess.CompletedProcess[str]:
    # Several trust tests only inspect the process result; avoid rerunning the same copied selfhost build.
    cached = _COPIED_SELFHOST_CACHE.get(timeout)
    if cached is not None:
        return cached
    with copied_selfhost_workspace() as tmp:
        result = run_stage0_selfhost(tmp, timeout=timeout)
    _COPIED_SELFHOST_CACHE[timeout] = result
    return result


@contextmanager
def built_stage1_driver(timeout: int = STAGE1_DRIVER_BUILD_TIMEOUT):
    with copied_selfhost_workspace() as tmp:
        # Driver tests need an executable; self-build proof tests cover running it over selfhost.
        ensure_bootstrap_deps()
        build_dir = tmp / "build"
        build_dir.mkdir(exist_ok=True)
        emitted_exe = tmp / "build" / "main.exe"
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "compiler.main",
                "build",
                str(tmp / "main.nq"),
                "-o",
                str(emitted_exe),
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if result.returncode != 0:
            raise AssertionError(result.stdout + result.stderr)
        if not emitted_exe.exists():
            raise AssertionError(f"missing stage1 driver at {emitted_exe}")
        yield tmp, emitted_exe
