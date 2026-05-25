import pytest
from core.self_healing.degraded_mode_router import DegradedModeRouter

def test_degraded_mode_routing():
    router = DegradedModeRouter()
    assert router.is_module_active("provider_sync") is True

    router.activate_degraded_mode("provider_sync")
    assert router.is_module_active("provider_sync") is False
