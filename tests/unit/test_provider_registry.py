import json
from core.provider_sync.provider_registry import ProviderRegistry, ProviderBase
from core.storage.storage_manager import storage_manager

def test_provider_registry_persistence(tmp_path):
    registry = ProviderRegistry()
    registry.config_file = "test_providers.json"

    class MockProvider(ProviderBase):
        def __init__(self):
            super().__init__("test_p")
            self.config = {"key": "val"}

    registry.register("test_p", MockProvider())
    registry.save_configs()

    # Verify file exists in storage
    path = storage_manager.get_path("governance", "test_providers.json")
    assert path.exists()
    data = json.loads(path.read_text())
    assert data["test_p"]["key"] == "val"
