from pathlib import Path

import pytest

from core.runtime.runtime_interpreters import resolve_python_executable


def test_source_runtime_uses_current_python(monkeypatch):
    import sys
    monkeypatch.delenv("DGM_PYTHON_EXECUTABLE", raising=False)
    monkeypatch.setattr(sys, "frozen", False, raising=False)
    assert resolve_python_executable() == sys.executable


def test_explicit_python_override_must_exist(monkeypatch, tmp_path):
    python = tmp_path / "python.exe"
    python.write_bytes(b"python")
    monkeypatch.setenv("DGM_PYTHON_EXECUTABLE", str(python))
    assert resolve_python_executable() == str(python.resolve())
    monkeypatch.setenv("DGM_PYTHON_EXECUTABLE", str(tmp_path / "missing.exe"))
    with pytest.raises(RuntimeError, match="existing file"):
        resolve_python_executable()


def test_frozen_runtime_uses_python_from_path_not_frozen_executable(monkeypatch, tmp_path):
    import sys
    python = tmp_path / "Python312" / "python.exe"
    python.parent.mkdir()
    python.write_bytes(b"python")
    monkeypatch.delenv("DGM_PYTHON_EXECUTABLE", raising=False)
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", str(tmp_path / "installed" / "DGM-MAT.exe"))
    monkeypatch.setattr("core.runtime.runtime_interpreters.shutil.which", lambda name: str(python) if name == "python.exe" else None)
    assert resolve_python_executable() == str(python.resolve())


def test_frozen_runtime_fails_closed_without_python(monkeypatch):
    import sys
    monkeypatch.delenv("DGM_PYTHON_EXECUTABLE", raising=False)
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr("core.runtime.runtime_interpreters.shutil.which", lambda _name: None)
    with pytest.raises(RuntimeError, match="needs a Python interpreter"):
        resolve_python_executable()
