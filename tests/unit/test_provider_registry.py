import json

import pytest

from core.provider_sync.provider_registry import ProviderRegistry
from core.providers.base.provider_base import ProviderBase
from core.storage.storage_manager import storage_manager


def test_provider_registry_persistence(tmp_path, monkeypatch):
    monkeypatch.setattr(storage_manager, "base_path", tmp_path)
    registry = ProviderRegistry()
    registry.config_file = "test_providers.json"

    class MockProvider(ProviderBase):
        def __init__(self):
            super().__init__("test_p")
            self.config = {"key": "val"}

    registry.register("test_p", MockProvider())
    registry.save_configs()

    path = storage_manager.get_path("governance", "test_providers.json")
    assert path.exists()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data == {"test_p": {"key": "val"}}


def test_provider_registry_rejects_untyped_adapter():
    registry = ProviderRegistry()

    class InvalidProvider:
        name = "invalid"
        config = {}

    with pytest.raises(TypeError, match="ProviderBase"):
        registry.register("invalid", InvalidProvider())
