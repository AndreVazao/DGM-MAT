# Dependency Convergence Report

## Overview
DGM-MAT has moved from ad-hoc dependency expansion to controlled dependency governance. This report outlines the converged dependency topology.

## Dependency Topology

### 1. Base Layer (`requirements/base.txt`)
- **Pydantic**: Data modeling and validation.
- **Rich**: Terminal formatting and logging.
- **Loguru**: System logging.
- **Requests**: HTTP client for API interactions (e.g., GitHub).

### 2. Runtime Layer (`requirements/runtime.txt`)
- **NetworkX**: Graph algorithms for topology and memory.
- **FastAPI/Uvicorn**: Core API and WebSocket communication.
- **SQLAlchemy**: Database ORM.
- **HTTPX**: Async HTTP client.
- **Websockets**: Real-time communication.
- **Psutil**: Resource monitoring.

### 3. Cockpit Layer (`requirements/cockpit.txt`)
- **PySide6**: GUI framework.

### 4. Build & Research Layers
- **PyInstaller**: EXE bundling.
- **Playwright**: Browser-based provider interactions.
- **Pytest**: Testing framework.

## Governance Rules
1. **Convergence**: All external dependencies must be declared in `requirements.txt` and the relevant sub-files in `requirements/`.
2. **Validation**: CI includes `scripts/validate_dependencies.py` and `tests/test_dependency_integrity.py`.
3. **No Hidden Imports**: Any new subsystem requiring an external package MUST update the requirements graph before merging.
4. **Separation**: Clear distinction between runtime-critical and dev-only packages.

## Convergence Status
- [x] `requests` integrated into base layer.
- [x] `requirements.txt` unified.
- [x] Dependency validator implemented.
- [x] Import integrity tests added.
- [x] CI workflow updated to use unified requirements.
