import sys

from core.connectors.boundary import create_runtime_connectors


def test_frozen_connectors_import_from_pyinstaller_bundle(monkeypatch, tmp_path):
    bundle = tmp_path / "_MEI"
    source = bundle / "DGM-MAT-Connectors" / "src"
    package = source / "dgm_mat_connectors"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text(
        "class ObsidianConnector: pass\nobsidian_connector = ObsidianConnector()\n",
        encoding="utf-8",
    )

    monkeypatch.delenv("DGM_CONNECTORS_PATH", raising=False)
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", str(bundle), raising=False)
    monkeypatch.setattr(sys, "path", [str(tmp_path / "empty")])
    monkeypatch.delitem(sys.modules, "dgm_mat_connectors", raising=False)

    connectors = create_runtime_connectors()

    assert str(source) in sys.path
    assert set(connectors) == {"obsidian", "obsidian_class"}
    assert connectors["obsidian_class"].__module__ == "dgm_mat_connectors"
