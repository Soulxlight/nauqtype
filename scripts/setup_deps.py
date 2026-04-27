from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts._deps import deps_dir, project_root


PINNED_PACKAGES = [
    "ziglang==0.16.0",
    "tiktoken==0.12.0",
]


def deps_already_ready(target: Path) -> bool:
    zig = target / "ziglang" / "zig.exe"
    if not zig.exists():
        return False
    if not (target / "ziglang-0.16.0.dist-info").exists():
        return False
    if not (target / "tiktoken").exists():
        return False
    if not (target / "tiktoken-0.12.0.dist-info").exists():
        return False
    if str(target) not in sys.path:
        sys.path.insert(0, str(target))
    try:
        import tiktoken  # pylint: disable=import-outside-toplevel
    except ImportError:
        return False
    return tiktoken.__version__ == "0.12.0"


def overlay_tree(src: Path, dst: Path) -> None:
    for entry in src.iterdir():
        target = dst / entry.name
        if entry.is_dir():
            target.mkdir(parents=True, exist_ok=True)
            overlay_tree(entry, target)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            try:
                shutil.copy2(entry, target)
            except PermissionError:
                if not target.exists():
                    raise


def main() -> int:
    root = project_root()
    target = deps_dir()
    target.mkdir(parents=True, exist_ok=True)
    if deps_already_ready(target):
        zig = target / "ziglang" / "zig.exe"
        print(f"Bootstrap dependencies already available in {target}")
        print(f"Resolved zig compiler at {zig}")
        return 0

    with tempfile.TemporaryDirectory(prefix="nauqtype_deps_") as tmp_dir:
        temp_target = Path(tmp_dir) / "deps"
        temp_target.mkdir(parents=True, exist_ok=True)

        command = [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--upgrade",
            "--target",
            str(temp_target),
            *PINNED_PACKAGES,
        ]
        result = subprocess.run(command, cwd=root, text=True)
        if result.returncode != 0:
            return result.returncode

        overlay_tree(temp_target, target)

    zig = target / "ziglang" / "zig.exe"
    if not zig.exists():
        print("expected zig compiler at .deps/ziglang/zig.exe but it was not installed", file=sys.stderr)
        return 1

    print(f"Installed bootstrap dependencies into {target}")
    print(f"Resolved zig compiler at {zig}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
