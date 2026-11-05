from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from core.organization.dgm_hub_multichat_bridge import (
    DGMHubMultiChatBridge,
    HubBridgeError,
    HubProviderUnavailable,
)


def test_default_bridge_targets_operational_hub_port_and_allows_slow_nim(monkeypatch):
    monkeypatch.delenv("DGM_HUB_MULTICHAT_URL", raising=False)
    bridge = DGMHubMultiChatBridge()

    assert bridge.base_url == "http://127.0.0.1:8771"
    assert bridge.task_timeout == 300.0


def test_bridge_accepts_configured_loopback_hub_test_port():
    bridge = DGMHubMultiChatBridge("http://127.0.0.1:8771")
    assert bridge.base_url == "http://127.0.0.1:8771"


def test_bridge_rejects_non_loopback_hub_urls():
    for url in (
        "http://192.168.1.20:8770",
        "https://127.0.0.1:8770",
        "http://user:pass@127.0.0.1:8770",
        "http://127.0.0.1:8770/proxy",
        "http://127.0.0.1:8080",
        "http://localhost:8770",
    ):
        with pytest.raises(HubBridgeError):
            DGMHubMultiChatBridge(url)


def test_status_exposes_only_allowlisted_providers_and_observer_mode(monkeypatch):
    bridge = DGMHubMultiChatBridge()
    monkeypatch.setattr(
        bridge,
        "_request_json",
        lambda path, **kwargs: {
            "hub": "online",
            "dgm_mat_mode": "observer",
            "providers": {
                "codex": {"enabled": True, "online": True, "ready": True},
                "claude": {"enabled": True, "online": True, "ready": True},
                "kilo": {"enabled": True, "online": True, "ready": True},
                "llm7": {"enabled": True, "online": True, "ready": True},
                "dgm_mat": {"enabled": True, "online": True, "ready": True},
                "ollama": {"enabled": True, "online": True, "ready": True},
            },
        },
    )

    result = bridge.get_status()

    assert set(result["providers"]) == {"codex", "claude", "kilo", "llm7"}
    assert result["providers"]["codex"]["transport_online"] is False
    assert result["providers"]["codex"]["response_verified"] is False
    assert result["room_mode"] == "operator_led_observer_dgm_mat"
    assert result["dgm_mat_mode"] == "observer"
    assert result["dgm_mat_response_enabled"] is False
    assert result["dgm_mat_leadership"] is False
    assert result["paid_fallback"] is False
    assert result["ollama_included"] is False


def test_consult_requires_ready_providers_and_never_auto_enables_them(monkeypatch):
    bridge = DGMHubMultiChatBridge()
    monkeypatch.setattr(
        bridge,
        "get_status",
        lambda: {
            "providers": {
                "codex": {"ready": True},
                "claude": {"ready": False},
                "kilo": {"ready": True},
                "llm7": {"ready": True},
            }
        },
    )
    called = []
    monkeypatch.setattr(bridge, "_request_json", lambda *args, **kwargs: called.append(args) or {})

    with pytest.raises(HubProviderUnavailable):
        bridge.consult(goal="Review this task", context="", providers=["claude"])

    assert called == []


def test_consult_sends_only_selected_external_providers_and_polls_results(monkeypatch):
    bridge = DGMHubMultiChatBridge(poll_interval=0.2)
    monkeypatch.setattr(
        bridge,
        "get_status",
        lambda: {"providers": {name: {"ready": True} for name in ("codex", "claude", "kilo", "llm7")}},
    )
    calls = []
    responses = iter([
        {"task_id": "task-123", "targets": ["codex", "kilo"]},
        {
            "task_id": "task-123",
            "done": True,
            "completed": ["codex", "kilo"],
            "results": {
                "codex": {"provider": "codex", "status": "ok", "text": "Codex answer"},
                "kilo": {"provider": "kilo", "model": "nvidia/free-model", "status": "ok", "text": "Kilo answer"},
            },
        },
    ])

    def fake_request(path, **kwargs):
        calls.append((path, kwargs))
        return next(responses)

    monkeypatch.setattr(bridge, "_request_json", fake_request)
    result = bridge.consult(
        goal="Review the provider integration",
        context="Only authorized excerpts.",
        providers=["codex", "kilo"],
    )

    assert result.task_id == "task-123"
    assert set(result.results) == {"codex", "kilo"}
    assert result.results["codex"]["model"] is None
    assert result.results["kilo"]["model"] == "nvidia/free-model"
    assert calls[0][0] == "/api/chat"
    assert calls[0][1]["payload"]["targets"] == ["codex", "kilo"]
    assert calls[0][1]["payload"]["conversation_id"].startswith("dgm-mat-")
    assert "MODO ESTRITAMENTE CONSULTIVO" in calls[0][1]["payload"]["message"]


def test_consult_preserves_grounding_status_and_evidence_references(monkeypatch):
    bridge = DGMHubMultiChatBridge()
    monkeypatch.setattr(
        bridge,
        "get_status",
        lambda: {"providers": {"llm7": {"ready": True}}},
    )
    responses = iter([
        {"task_id": "task-grounding", "targets": ["llm7"]},
        {
            "task_id": "task-grounding",
            "done": True,
            "completed": ["llm7"],
            "results": {
                "llm7": {
                    "provider": "llm7",
                    "status": "unverified",
                    "text": "Resposta retida pelo contrato de evidência.",
                    "grounding_status": "blocked_missing_or_invalid_evidence_citations",
                    "evidence_refs": [],
                }
            },
        },
    ])
    monkeypatch.setattr(bridge, "_request_json", lambda *args, **kwargs: next(responses))

    result = bridge.consult(goal="Audit DGM-MAT", context="Evidence packet", providers=["llm7"])

    assert result.results["llm7"]["status"] == "unverified"
    assert result.results["llm7"]["grounding_status"] == "blocked_missing_or_invalid_evidence_citations"
    assert result.results["llm7"]["evidence_refs"] == []


def test_consult_rejects_dgm_mat_ollama_duplicates_and_empty_targets():
    bridge = DGMHubMultiChatBridge()
    for providers in ([], ["dgm_mat"], ["ollama"], ["codex", "codex"]):
        with pytest.raises(ValueError):
            bridge.consult(goal="Review", context="", providers=providers)


def test_rate_limit_does_not_retry_or_fallback(monkeypatch):
    bridge = DGMHubMultiChatBridge()
    monkeypatch.setattr(
        bridge,
        "get_status",
        lambda: {"providers": {"kilo": {"ready": True}}},
    )
    calls = []

    def fail(*args, **kwargs):
        calls.append(args)
        raise HubBridgeError("rate limit reached; no retry or paid fallback was attempted.")

    monkeypatch.setattr(bridge, "_request_json", fail)
    with pytest.raises(HubBridgeError, match="no retry"):
        bridge.consult(goal="Review", context="", providers=["kilo"])
    assert len(calls) == 1


def test_model_identity_is_not_inferred_from_provider_response_text(monkeypatch):
    bridge = DGMHubMultiChatBridge()
    monkeypatch.setattr(
        bridge,
        "get_status",
        lambda: {"providers": {"llm7": {"ready": True}}},
    )
    responses = iter([
        {"task_id": "task-llm7", "targets": ["llm7"]},
        {
            "task_id": "task-llm7",
            "done": True,
            "completed": ["llm7"],
            "results": {
                "llm7": {
                    "status": "ok",
                    "text": "I am GPT-4, says the model.",
                    "model": "gpt-oss:20b",
                }
            },
        },
    ])
    monkeypatch.setattr(bridge, "_request_json", lambda *args, **kwargs: next(responses))

    result = bridge.consult(goal="Test model provenance", context="", providers=["llm7"])

    assert result.results["llm7"]["model"] == "gpt-oss:20b"
    assert "GPT-4" in result.results["llm7"]["text"]


def test_status_reports_operator_enabled_respond_mode_without_claiming_dgm_mat_leadership(monkeypatch):
    bridge = DGMHubMultiChatBridge("http://127.0.0.1:8771")
    monkeypatch.setattr(
        bridge,
        "_request_json",
        lambda path, **kwargs: {
            "hub": "online",
            "dgm_mat_mode": "respond",
            "providers": {
                "dgm_mat": {"enabled": True, "online": True, "ready": True, "mode": "respond"},
                "kilo": {"enabled": True, "online": True, "ready": True},
                "llm7": {"enabled": True, "online": True, "ready": True},
            },
        },
    )

    result = bridge.get_status()

    assert result["room_mode"] == "operator_led_respond_dgm_mat"
    assert result["dgm_mat_mode"] == "respond"
    assert result["dgm_mat_response_enabled"] is True
    assert result["dgm_mat_leadership"] is False


def test_project_audit_prompt_rejects_unsupported_repository_assumptions():
    prompt = DGMHubMultiChatBridge.build_prompt(
        "Audit the current DGM-MAT repository.",
        "No repository files or CI evidence were supplied.",
    )

    assert "DevOps God Mode" in prompt
    assert "não um módulo de matemática" in prompt
    assert "NÃO VERIFICADO" in prompt
    assert "nunca simules comandos" in prompt
    assert "Não assumas que existem Matrix" in prompt
    assert "FACTOS COM EVIDÊNCIA" in prompt
    assert "cita o ID exato em cada facto" in prompt
    assert "nunca inventes IDs" in prompt
    assert "NÃO VERIFICADA" in prompt
    assert "Não transformes recomendações genéricas em erros detetados" in prompt
