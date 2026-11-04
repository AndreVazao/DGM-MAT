"""Resolve a real Python interpreter for bounded local validation subprocesses."""
from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path


def resolve_python_executable() -> str:
    """Return a Python interpreter, never the frozen DGM-MAT executable itself."""
    configured = os.getenv("DGM_PYTHON_EXECUTABLE", "").strip()
    if configured:
        path = Path(configured).expanduser().resolve()
        if not path.is_file():
            raise RuntimeError("DGM_PYTHON_EXECUTABLE does not point to an existing file")
        return str(path)

    if not getattr(sys, "frozen", False):
        return sys.executable

    for candidate in ("python.exe", "python", "python3.exe", "python3"):
        found = shutil.which(candidate)
        if found:
            return str(Path(found).resolve())
    raise RuntimeError(
        "A frozen DGM-MAT runtime needs a Python interpreter on PATH or DGM_PYTHON_EXECUTABLE for local QA/worktree validation."
    )
