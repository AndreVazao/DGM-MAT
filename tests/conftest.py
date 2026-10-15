"""Global test isolation: never let pytest mutate the live DGM-MAT runtime store.

This file intentionally imports only standard-library modules before redirecting
DGM_STORAGE_PATH, so all project singletons and subprocess tests use a disposable
local test database rather than storage/runtime.
"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

_TEST_ROOT = Path(tempfile.mkdtemp(prefix="dgm-mat-pytest-"))
_TEST_STORAGE = _TEST_ROOT / "runtime"
_TEST_STORAGE.mkdir(parents=True, exist_ok=True)
os.environ["DGM_BASE_PATH"] = str(_TEST_ROOT)
os.environ["DGM_STORAGE_PATH"] = str(_TEST_STORAGE)
os.environ["DGM_TEST_MODE"] = "1"
