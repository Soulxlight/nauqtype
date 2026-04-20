from __future__ import annotations

import sys
from pathlib import Path


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def deps_dir() -> Path:
    return project_root() / ".deps"


def bootstrap_sys_path() -> None:
    deps = deps_dir()
    deps_text = str(deps)
    if deps.exists() and deps_text not in sys.path:
        sys.path.insert(0, deps_text)

