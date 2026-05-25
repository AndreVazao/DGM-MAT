import pytest
from core.provider_sync.provider_memory_sync import ProviderMemorySync

def test_provider_sync():
    sync = ProviderMemorySync()
    assert sync is not None
