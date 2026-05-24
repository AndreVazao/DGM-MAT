# DGM-MAT Build EXE Recovery Plan

## Current Blockers
The Windows `.exe` build is currently unstable due to:
1. **Dynamic Imports**: Many engines are loaded via `try-except` blocks in `Runtime`, which PyInstaller fails to trace automatically.
2. **Hidden Imports**: Pydantic, FastAPI, and PySide6 internal modules are often missing from the build.
3. **Storage Paths**: Absolute paths or relative paths in `StorageManager` can break when bundled into a single file or running in a temporary PyInstaller directory.
4. **Subprocess/Thread Issues**: The background Runtime thread and FastAPI server might conflict with the PyInstaller main loop.

## Recovery Sequence

### 1. Hidden Imports Stabilization
Update `.github/workflows/build-exe.yml` to include a comprehensive list of hidden imports:
- `pydantic.deprecated.decorator`
- `uvicorn.protocols.http.httptools_impl`
- `uvicorn.protocols.websockets.websockets_impl`
- `PySide6.QtWebEngineWidgets` (if used)
- `PySide6.QtNetwork`
- `websockets.legacy.client`

### 2. Runtime Boot Fix
Ensure `RuntimeStorageManager` handles the `_MEIPASS` path provided by PyInstaller when running in `--onefile` mode.
```python
if hasattr(sys, '_MEIPASS'):
    # Running in PyInstaller bundle
    # Handle resource paths accordingly
```

### 3. Modularizing the Build
Instead of a single giant `pyinstaller` command, we will create a `dgm-mat.spec` file to:
- Define `datas` for Cockpit styles (`cockpit/styles/**`).
- Define `datas` for configuration files (`config/**`).
- Manage the exclusion of `tests/` and `legacy/`.

### 4. Headless Validation
Add a build step that validates the `.exe` can boot in `--headless` mode without triggering UI errors.

## Implementation Plan
1. Create `scripts/build_validation.py` to test the bundle after creation.
2. Transition to `pyinstaller dgm-mat.spec`.
3. Add `PySide6` runtime hook for path normalization.
4. Verify storage initialization in the bundled environment.
