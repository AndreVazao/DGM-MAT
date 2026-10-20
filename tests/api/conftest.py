"""Use a no-I/O connector stub for API unit tests when the optional satellite is absent."""
from __future__ import annotations

import importlib.util
import os
from pathlib import Path

try:
    connector_spec = importlib.util.find_spec("dgm_mat_connectors")
except (ImportError, ValueError):
    connector_spec = None

if connector_spec is None:
    os.environ.setdefault(
        "DGM_CONNECTORS_PATH",
        str(Path(__file__).resolve().parents[1] / "fixtures"),
    )
