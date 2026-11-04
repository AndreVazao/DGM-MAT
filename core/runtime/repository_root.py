"""Resolve the real project checkout for source and PyInstaller runtimes."""
from __future__ import annotations

import os
import sys
from pathlib import Path


def resolve_repository_root(
    source_file: str | Path,
    *,
    cwd: str | Path | None = None,
    executable: str | Path | None = None,
    frozen: bool | None = None,
) -> Path:
    """Resolve a Git checkout without mistaking PyInstaller's _MEIPASS for it.

    Priority: explicit operator override, current working tree, installed
    executable's project parent, then the source package's checkout.
    """
    configured = os.getenv("DGM_REPOSITORY_ROOT", "").strip()
    if configured:
        return Path(configured).expanduser().resolve()

    current = Path(cwd if cwd is not None else Path.cwd()).expanduser().resolve()
    is_frozen = bool(getattr(sys, "frozen", False)) if frozen is None else bool(frozen)
    if is_frozen:
        executable_path = Path(executable if executable is not None else sys.executable).expanduser().resolve()
        executable_dir = executable_path.parent
        candidates = (executable_dir.parent, executable_dir)
        for candidate in candidates:
            if (candidate / ".git").exists():
                return candidate
        if (current / ".git").exists():
            return current
        # Return the expected install root; callers that require Git must fail closed.
        return candidates[0]

    source = Path(source_file).expanduser().resolve()
    for candidate in source.parents:
        if (candidate / ".git").exists():
            return candidate
    if (current / ".git").exists():
        return current
    return source.parents[2] if len(source.parents) > 2 else source.parent
