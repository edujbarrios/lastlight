"""General utility helpers."""

from __future__ import annotations

import os
from pathlib import Path


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def normalize_relative_path(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return os.fspath(path)

