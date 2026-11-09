from __future__ import annotations

from core.api import mobile_bridge


def test_mobile_status_distinguishes_healthy_api_from_missing_ai_engine(monkeypatch):
    monkeypatch.setattr(
        mobile_bridge,
        "_tailscale_identity",
        lambda: {"online": False, "hostname": None, "dns_name": None, "ipv4": None, "https_endpoint": None},
    )
    monkeypatch.setattr(mobile_bridge, "_ollama_status", lambda: {"available": False, "models": []})
    monkeypatch.setattr(
        mobile_bridge.service,
        "governed_chat_status",
        lambda: {"enabled": False, "available": False, "reason": "disabled_by_configuration"},
    )

    result = mobile_bridge.get_mobile_status()

    assert result["api_status"] == "ready"
    assert result["status"] == "degraded"
    assert result["ai_ready"] is False
    assert result["ai_mode"] == "not-configured"


def test_mobile_status_reports_ready_when_a_governed_provider_is_available(monkeypatch):
    monkeypatch.setattr(
        mobile_bridge,
        "_tailscale_identity",
        lambda: {"online": False, "hostname": None, "dns_name": None, "ipv4": None, "https_endpoint": None},
    )
    monkeypatch.setattr(mobile_bridge, "_ollama_status", lambda: {"available": False, "models": []})
    monkeypatch.setattr(
        mobile_bridge.service,
        "governed_chat_status",
        lambda: {"enabled": True, "available": True, "provider_id": "nvidia_nim", "reason": "ready"},
    )

    result = mobile_bridge.get_mobile_status()

    assert result["api_status"] == "ready"
    assert result["status"] == "ready"
    assert result["ai_ready"] is True
    assert result["ai_mode"] == "governed-provider"
