import sys
import types

from core.connectors.boundary import create_runtime_connectors


def test_frozen_connectors_import_from_bundled_package(monkeypatch):
    module = types.ModuleType("dgm_mat_connectors")

    class ObsidianConnector:
        pass

    instance = ObsidianConnector()
    module.ObsidianConnector = ObsidianConnector
    module.obsidian_connector = instance

    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setitem(sys.modules, "dgm_mat_connectors", module)

    connectors = create_runtime_connectors()

    assert connectors["obsidian"] is instance
    assert connectors["obsidian_class"] is ObsidianConnector
