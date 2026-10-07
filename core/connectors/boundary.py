"""Core composition boundary for standalone DGM-MAT connectors."""

from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path
from typing import Any


def _ensure_connectors_importable() -> None:
    try:
        importlib.import_module("dgm_mat_connectors")
        return
    except ModuleNotFoundError:
        pass

    configured = os.environ.get("DGM_CONNECTORS_PATH")
    candidates: list[Path] = []
    if configured:
        candidates.append(Path(configured))
    candidates.append(Path(__file__).resolve().parents[3] / "DGM-MAT-Connectors" / "src")

    for candidate in candidates:
        if candidate.exists():
            value = str(candidate)
            if value not in sys.path:
                sys.path.insert(0, value)
            try:
                importlib.import_module("dgm_mat_connectors")
                return
            except ModuleNotFoundError:
                continue

    raise ModuleNotFoundError(
        "dgm_mat_connectors is unavailable; configure DGM_CONNECTORS_PATH "
        "or install DGM-MAT-Connectors."
    )


def create_runtime_connectors() -> dict[str, Any]:
    _ensure_connectors_importable()
    from dgm_mat_connectors import ObsidianConnector, obsidian_connector

    return {
        "obsidian": obsidian_connector,
        "obsidian_class": ObsidianConnector,
    }
