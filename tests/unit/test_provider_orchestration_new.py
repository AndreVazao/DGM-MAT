import pytest

from core.provider_sync.provider_registry import (
    provider_registry,
    initialize_default_providers,
)
from core.provider_mesh.provider_orchestrator import ProviderOrchestrator
from core.provider_mesh.capability_router import capability_router
from core.providers.base.provider_base import ProviderBase


@pytest.fixture(autouse=True)
def setup_providers(monkeypatch):
    # Isolate the singleton registry so test registrations/state cannot leak.
    monkeypatch.setattr(provider_registry, "_providers", {})
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
    assert providers == ["ollama"]
    assert "openai" not in providers
    assert "chatgpt" not in providers


def test_routing():
    ollama = provider_registry.get_provider("ollama")
    ollama.update_capabilities(coding=0.9)
    ollama.health_metrics["last_check"] = 1
    ollama.health_metrics["status"] = "ok"

    assert capability_router.select_best_provider("coding") == "ollama"


@pytest.mark.asyncio
async def test_fallback():
    provider_registry.register("placeholder", PlaceholderProvider())
    ollama = provider_registry.get_provider("ollama")
    ollama.set_cooldown(60)

    orchestrator = ProviderOrchestrator()
    response = await orchestrator.chat_with_fallback(
        [{"role": "user", "content": "hi"}]
    )

    assert response == "placeholder response"
