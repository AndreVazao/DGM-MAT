import pytest
import asyncio
from core.provider_sync.provider_registry import provider_registry, initialize_default_providers
from core.provider_mesh.provider_orchestrator import ProviderOrchestrator
from core.provider_mesh.capability_router import capability_router
from core.providers.base.provider_base import ProviderBase


@pytest.fixture(autouse=True)
def setup_providers():
    initialize_default_providers()


class PlaceholderProvider(ProviderBase):
    def __init__(self):
        super().__init__("placeholder")
        self.health_metrics["last_check"] = 1
        self.health_metrics["status"] = "ok"

    async def chat(self, messages, **kwargs):
        return "placeholder response"


def test_discovery():
    providers = provider_registry.list_providers()
    assert "ollama" in providers
    assert "openai" not in providers


def test_routing():
    ollama = provider_registry.get_provider("ollama")
    ollama.health_metrics["last_check"] = 1
    ollama.health_metrics["status"] = "ok"
    best = capability_router.select_best_provider("coding")
    assert best == "ollama"


@pytest.mark.asyncio
async def test_fallback():
    provider_registry.register("placeholder", PlaceholderProvider())
    p_ollama = provider_registry.get_provider("ollama")
    p_ollama.set_cooldown(60)

    orchestrator = ProviderOrchestrator()
    response = await orchestrator.chat_with_fallback([{"role": "user", "content": "hi"}])
    assert "placeholder" in response
