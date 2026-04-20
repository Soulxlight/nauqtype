from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts._deps import deps_dir, project_root


PINNED_PACKAGES = [
    "ziglang==0.16.0",
    "tiktoken==0.12.0",
]


def main() -> int:
    root = project_root()
    target = deps_dir()
    target.mkdir(parents=True, exist_ok=True)

    command = [
        sys.executable,
        "-m",
        "pip",
        "install",
        "--upgrade",
        "--target",
        str(target),
        *PINNED_PACKAGES,
    ]
    result = subprocess.run(command, cwd=root, text=True)
    if result.returncode != 0:
        return result.returncode

    zig = target / "ziglang" / "zig.exe"
    if not zig.exists():
        print("expected zig compiler at .deps/ziglang/zig.exe but it was not installed", file=sys.stderr)
        return 1

    print(f"Installed bootstrap dependencies into {target}")
    print(f"Resolved zig compiler at {zig}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
