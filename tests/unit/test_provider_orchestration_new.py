import pytest
import asyncio
from core.provider_sync.provider_registry import provider_registry, initialize_default_providers
from core.provider_mesh.provider_orchestrator import ProviderOrchestrator
from core.provider_mesh.capability_router import capability_router

@pytest.fixture(autouse=True)
def setup_providers():
    initialize_default_providers()

def test_discovery():
    providers = provider_registry.list_providers()
    assert "openai" in providers
    assert "chatgpt" in providers

def test_routing():
    best = capability_router.select_best_provider("coding")
    assert best is not None

@pytest.mark.asyncio
async def test_fallback():
    orchestrator = ProviderOrchestrator()
    # Mocking openai to fail (cooldown)
    p_openai = provider_registry.get_provider("openai")
    p_openai.set_cooldown(60)

    # Should use another available provider
    response = await orchestrator.chat_with_fallback([{"role": "user", "content": "hi"}])
    assert "placeholder" in response
