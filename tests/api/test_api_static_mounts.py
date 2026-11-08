from __future__ import annotations

from pathlib import Path

from core.api import api_server


def test_frozen_windows_executable_discovers_sibling_pc_and_mobile_frontends(tmp_path, monkeypatch):
    repository_root = tmp_path / "ProgramasGodMode"
    executable = repository_root / "DGM-MAT" / "installed" / "DGM-MAT.exe"
    executable.parent.mkdir(parents=True)
    executable.write_bytes(b"test executable")

    cockpit = repository_root / "DGM-Cockpit-Frontend"
    cockpit.mkdir(parents=True)
    for filename in ("index.html", "app.js", "styles.css"):
        (cockpit / filename).write_text("test", encoding="utf-8")

    mobile_web = repository_root / "DGM-MAT-Mobile" / "web"
    mobile_web.mkdir(parents=True)
    (mobile_web / "index.html").write_text("test", encoding="utf-8")

    frozen_bundle = tmp_path / "_MEI12345" / "core" / "api"
    frozen_bundle.mkdir(parents=True)
    monkeypatch.setattr(api_server, "__file__", str(frozen_bundle / "api_server.py"))
    monkeypatch.setattr(api_server.sys, "frozen", True, raising=False)
    monkeypatch.setattr(api_server.sys, "executable", str(executable))
    monkeypatch.delenv("DGM_PC_COCKPIT_PATH", raising=False)
    monkeypatch.delenv("DGM_MOBILE_UI_PATH", raising=False)

    assert api_server._pc_cockpit_directory() == cockpit
    assert api_server._mobile_ui_directory() == mobile_web


def test_explicit_frontend_paths_override_frozen_sibling_discovery(tmp_path, monkeypatch):
    repository_root = tmp_path / "ProgramasGodMode"
    executable = repository_root / "DGM-MAT" / "installed" / "DGM-MAT.exe"
    executable.parent.mkdir(parents=True)
    executable.write_bytes(b"test executable")

    explicit_cockpit = tmp_path / "custom-cockpit"
    explicit_cockpit.mkdir()
    for filename in ("index.html", "app.js", "styles.css"):
        (explicit_cockpit / filename).write_text("test", encoding="utf-8")
    explicit_mobile = tmp_path / "custom-mobile-web"
    explicit_mobile.mkdir()
    (explicit_mobile / "index.html").write_text("test", encoding="utf-8")

    monkeypatch.setattr(api_server.sys, "frozen", True, raising=False)
    monkeypatch.setattr(api_server.sys, "executable", str(executable))
    monkeypatch.setenv("DGM_PC_COCKPIT_PATH", str(explicit_cockpit))
    monkeypatch.setenv("DGM_MOBILE_UI_PATH", str(explicit_mobile))

    assert api_server._pc_cockpit_directory() == explicit_cockpit
    assert api_server._mobile_ui_directory() == explicit_mobile
