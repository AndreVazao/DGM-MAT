import json
from unittest.mock import MagicMock, patch

import pytest

from core.providers.local.ollama_adapter import OllamaProvider
from core.provider_sync.provider_registry import initialize_default_providers, provider_registry


def _response(payload):
    response = MagicMock()
    response.__enter__.return_value = response
    response.read.return_value = json.dumps(payload).encode("utf-8")
    return response


def test_ollama_health_discovers_only_local_installed_models():
    provider = OllamaProvider()
    with patch("core.providers.local.ollama_adapter.urlopen", return_value=_response({
        "models": [{"name": "qwen2.5:1.5b"}, {"name": "qwen2.5-coder:1.5b"}]
    })):
        health = provider.check_health()
    assert health["available"] is True
    assert health["status"] == "ok"
    assert health["models"] == ["qwen2.5-coder:1.5b", "qwen2.5:1.5b"]


def test_ollama_generate_uses_installed_model_and_bounded_local_options():
    provider = OllamaProvider()
    with patch("core.providers.local.ollama_adapter.urlopen", return_value=_response({
        "models": [{"name": "qwen2.5:1.5b"}]
    })):
        provider.check_health()
    with patch.object(provider, "available_memory_gb", return_value=2.0), patch("core.providers.local.ollama_adapter.urlopen", return_value=_response({
        "message": {"content": "{\\\"subtasks\\\":[{\\\"title\\\":\\\"A\\\",\\\"description\\\":\\\"Do A\\\"}]}"}
    })) as call:
        result = provider.generate([{"role": "user", "content": "plan"}], model="qwen2.5:1.5b", json_mode=True)
    assert "subtasks" in result
    request = call.call_args.args[0]
    payload = json.loads(request.data.decode("utf-8"))
    assert payload["model"] == "qwen2.5:1.5b"
    assert payload["stream"] is False
    assert payload["options"]["num_ctx"] <= 2048
    assert payload["format"] == "json"


def test_ollama_rejects_non_loopback_base_url():
    provider = OllamaProvider()
    provider.config["base_url"] = "https://example.com"
    health = provider.check_health()
    assert health["available"] is False
    assert health["status"] == "unavailable"
    assert health["error"] == "ValueError"


def test_default_provider_initialization_registers_trusted_local_adapter():
    initialize_default_providers()
    provider = provider_registry.get_provider("ollama")
    assert isinstance(provider, OllamaProvider)
    assert provider.config["base_url"] == "http://127.0.0.1:11434"

def test_ollama_skips_inference_when_free_ram_is_below_safe_threshold(monkeypatch):
    from types import SimpleNamespace
    provider = OllamaProvider()
    monkeypatch.delenv("DGM_OLLAMA_ALLOW_LOW_MEMORY", raising=False)
    monkeypatch.setenv("DGM_OLLAMA_MIN_FREE_GB", "1.25")
    with patch("psutil.virtual_memory", return_value=SimpleNamespace(available=int(0.5 * 1024 ** 3))):
        with patch("core.providers.local.ollama_adapter.urlopen") as urlopen:
            with pytest.raises(RuntimeError, match="No remote provider fallback"):
                provider.generate([{"role": "user", "content": "plan"}], model="llama3.2:1b")
    urlopen.assert_not_called()

def test_broadcast_health_persists_provider_observation_in_runtime_truth():
    import time
    from core.runtime.runtime_state_store import state_store
    provider = OllamaProvider()
    def healthy_observation():
        now = time.time()
        provider.health_metrics["status"] = "ok"
        provider.health_metrics["last_check"] = now
        provider.health_metrics["last_check_attempt"] = now
        provider._installed_models = ["llama3.2:1b"]
        return {"status": "ok", "available": True, "models": list(provider._installed_models)}
    with patch.object(provider, "check_health", side_effect=healthy_observation):
        provider.broadcast_health()
    record = state_store.get_snapshot().providers["ollama"]
    assert record["status"] == "ok"
    assert record["available"] is True
    assert record["healthy"] is True
    assert record["installed"] is True
    assert record["loaded"] is True
    assert record["health_observed_at"] is not None
