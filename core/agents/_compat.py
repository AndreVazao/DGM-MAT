"""Compatibility loader for the standalone DGM-MAT Agents package."""
from __future__ import annotations
import importlib
import os
import sys
from pathlib import Path

def _ensure_agents_importable() -> None:
    try:
        importlib.import_module("dgm_mat_agents")
        return
    except ModuleNotFoundError:
        pass
    configured = os.environ.get("DGM_AGENTS_PATH")
    candidates = []
    if configured:
        candidates.append(Path(configured))
    candidates.append(Path(__file__).resolve().parents[3] / "DGM-MAT-Agents" / "src")
    for candidate in candidates:
        if candidate.exists():
            value = str(candidate)
            if value not in sys.path:
                sys.path.insert(0, value)
            try:
                importlib.import_module("dgm_mat_agents")
                return
            except ModuleNotFoundError:
                continue
    raise ModuleNotFoundError(
        "dgm_mat_agents is unavailable; configure DGM_AGENTS_PATH or install DGM-MAT-Agents."
    )

def load(module: str):
    _ensure_agents_importable()
    return importlib.import_module(module)
