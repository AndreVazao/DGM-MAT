import pytest

from core.providers.base.provider_base import ProviderBase
from core.provider_sync.provider_registry import ProviderRegistry


class HealthyProvider(ProviderBase):
    def check_health(self):
        self.health_metrics["last_check"] = 1
        self.health_metrics["status"] = "ok"
        return {"status": "ok", "latency": 0.0}


def test_base_provider_does_not_claim_health_without_observation():
    provider = ProviderBase("unknown-provider")
    assert provider.health_metrics["status"] == "unknown"
    assert provider.check_health()["status"] == "unknown"
    assert provider.is_available() is False


def test_base_health_attempt_does_not_forge_observation_timestamp():
    provider = ProviderBase("unknown-provider")

    result = provider.check_health()

    assert result["status"] == "unknown"
    assert provider.health_metrics["last_check_attempt"] > 0
    assert provider.health_metrics["last_check"] == 0


def test_base_health_check_downgrades_unverified_manual_status():
    provider = ProviderBase("unknown-provider")
    provider.health_metrics["status"] = "ok"

    result = provider.check_health()

    assert result["status"] == "unknown"
    assert provider.is_available() is False


def test_cooldown_never_auto_promotes_to_healthy():
    provider = ProviderBase("unknown-provider")
    provider.set_cooldown(-1)
    assert provider.is_available() is False
    assert provider.check_health()["status"] == "unknown"
    assert provider.is_available() is False


def test_registry_does_not_auto_import_provider_source():
    registry = ProviderRegistry()
    assert registry.discover_providers() == []
    assert registry.list_providers() == []


def test_registry_accepts_explicit_provider_registration():
    registry = ProviderRegistry()
    provider = HealthyProvider("trusted-provider")
    registry.register(provider.name, provider)
    assert registry.list_providers() == ["trusted-provider"]
    assert registry.get_provider("trusted-provider") is provider


def test_registry_rejects_name_that_does_not_match_adapter():
    registry = ProviderRegistry()
    provider = HealthyProvider("actual-name")

    with pytest.raises(ValueError, match="does not match adapter.name"):
        registry.register("different-name", provider)

    assert registry.list_providers() == []


def test_registry_rejects_silent_adapter_replacement():
    registry = ProviderRegistry()
    original = HealthyProvider("trusted-provider")
    replacement = HealthyProvider("trusted-provider")
    registry.register(original.name, original)

    with pytest.raises(ValueError, match="already registered"):
        registry.register(replacement.name, replacement)

    assert registry.get_provider("trusted-provider") is original


def test_registry_allows_idempotent_registration_of_same_instance():
    registry = ProviderRegistry()
    provider = HealthyProvider("trusted-provider")

    registry.register(provider.name, provider)
    registry.register(provider.name, provider)

    assert registry.get_provider("trusted-provider") is provider
    assert registry.list_providers() == ["trusted-provider"]
