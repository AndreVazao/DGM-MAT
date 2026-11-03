from __future__ import annotations

import subprocess
from types import SimpleNamespace

import pytest

from core.development import external_agent_probe as probe


def test_claude_probe_reports_installed_but_logged_out_without_model_request(monkeypatch):
    monkeypatch.setattr(probe, "_claude_command", lambda: (["claude", "auth", "status"], "C:/npm/claude.ps1"))
    monkeypatch.setattr(
        probe.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(
            stdout='{"loggedIn": false, "authMethod": "none", "apiProvider": "firstParty"}',
            stderr="",
            returncode=1,
        ),
    )

    result = probe.probe_claude_code()

    assert result["installed"] is True
    assert result["authenticated"] is False
    assert result["status"] == "installed_logged_out"
    assert result["cost_status"] == "unverified"
    assert result["execution_ready"] is False
    assert result["model_requests_sent"] == 0


def test_authenticated_claude_is_still_blocked_until_zero_cost_is_verified(monkeypatch):
    monkeypatch.setattr(probe, "_claude_command", lambda: (["claude", "auth", "status"], "claude"))
    monkeypatch.setattr(
        probe.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(
            stdout='{"loggedIn": true, "authMethod": "oauth", "apiProvider": "firstParty"}',
            stderr="",
            returncode=0,
        ),
    )

    result = probe.probe_claude_code()

    assert result["authenticated"] is True
    assert result["status"] == "authenticated_cost_unverified"
    assert result["execution_ready"] is False
    assert result["cost_status"] == "unverified"
    assert result["model_requests_sent"] == 0


def test_claude_auth_probe_timeout_fails_closed(monkeypatch):
    monkeypatch.setattr(probe, "_claude_command", lambda: (["claude", "auth", "status"], "claude"))

    def timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd=args[0], timeout=3)

    monkeypatch.setattr(probe.subprocess, "run", timeout)
    result = probe.probe_claude_code()

    assert result["status"] == "auth_probe_timeout"
    assert result["authenticated"] is None
    assert result["execution_ready"] is False


def test_claude_probe_does_not_accept_malformed_auth_output(monkeypatch):
    monkeypatch.setattr(probe, "_claude_command", lambda: (["claude", "auth", "status"], "claude"))
    monkeypatch.setattr(
        probe.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(stdout="not-json", stderr="", returncode=0),
    )

    result = probe.probe_claude_code()

    assert result["status"] == "auth_probe_unrecognized"
    assert result["authenticated"] is None
    assert result["execution_ready"] is False


def test_fcc_wildcard_listener_is_reported_as_network_exposed(monkeypatch):
    monkeypatch.setattr(probe.shutil, "which", lambda name: f"C:/tools/{name}.exe")
    monkeypatch.setattr(
        probe.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(
            stdout="TCP    0.0.0.0:8082    0.0.0.0:0    LISTENING    5192\n",
            stderr="",
            returncode=0,
        ),
    )

    result = probe.probe_fcc_gateway()

    assert result["cli_installed"] is True
    assert result["gateway_status"] == "network_exposed"
    assert result["bind_scope"] == "non_loopback"
    assert result["execution_ready"] is False
    assert result["model_requests_sent"] == 0


def test_fcc_loopback_listener_is_not_execution_ready_without_cost_evidence(monkeypatch):
    monkeypatch.setattr(probe.shutil, "which", lambda name: f"C:/tools/{name}.exe")
    monkeypatch.setattr(
        probe.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(
            stdout="TCP    127.0.0.1:8082    0.0.0.0:0    LISTENING    5192\n",
            stderr="",
            returncode=0,
        ),
    )

    result = probe.probe_fcc_gateway()

    assert result["gateway_status"] == "loopback_only"
    assert result["bind_scope"] == "loopback"
    assert result["cost_status"] == "unverified"
    assert result["execution_ready"] is False


def test_fcc_stopped_listener_is_reported_without_starting_service(monkeypatch):
    monkeypatch.setattr(probe.shutil, "which", lambda name: f"C:/tools/{name}.exe")
    monkeypatch.setattr(
        probe.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(stdout="Active Connections\n", stderr="", returncode=0),
    )

    result = probe.probe_fcc_gateway()

    assert result["gateway_status"] == "stopped"
    assert result["bind_scope"] == "not_listening"
    assert result["model_requests_sent"] == 0


def test_combined_readiness_never_claims_execution_without_free_cost_proof(monkeypatch):
    monkeypatch.setattr(
        probe,
        "probe_claude_code",
        lambda: {"authenticated": True, "status": "authenticated_cost_unverified"},
    )
    monkeypatch.setattr(
        probe,
        "probe_fcc_gateway",
        lambda: {"gateway_status": "loopback_only", "bind_scope": "loopback", "cli_installed": True},
    )
    monkeypatch.setattr(
        probe,
        "probe_fcc_admin_status",
        lambda: {
            "status": "ready_free_endpoint",
            "selected_provider": "nvidia_nim",
            "selected_model": "nvidia_nim/nvidia/nemotron-3.5-super-vl-120b-a12b",
            "configured_remote_providers": ["nvidia_nim"],
            "free_endpoint_verified": True,
            "cost_status": "official_free_endpoint",
            "quota_status": "free_endpoint_rate_limits_and_account_quota_apply",
            "execution_ready": True,
        },
    )

    result = probe.get_external_agent_readiness()

    assert result["execution_ready"] is True
    assert result["policy"] == "FREE_ONLY_PAID_DENY"
    assert result["provider_calls_performed"] == 0
    assert result["fcc"]["admin"]["free_endpoint_verified"] is True
    assert result["fcc"]["admin"]["quota_status"] == "free_endpoint_rate_limits_and_account_quota_apply"
    assert result["blockers"] == []



def test_fcc_admin_status_accepts_only_the_allowlisted_free_nim_model(monkeypatch):
    payload = {
        "status": "running",
        "provider": "nvidia_nim",
        "model": "nvidia_nim/nvidia/nemotron-3.5-super-vl-120b-a12b",
        "provider_status": [
            {"provider_id": "nvidia_nim", "kind": "remote", "status": "configured"},
            {"provider_id": "anthropic", "kind": "remote", "status": "missing_key"},
        ],
    }
    class Response:
        status = 200
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def read(self, size): return __import__("json").dumps(payload).encode("utf-8")

    monkeypatch.setattr(probe.urllib.request, "urlopen", lambda *args, **kwargs: Response())

    result = probe.probe_fcc_admin_status()

    assert result["free_endpoint_verified"] is True
    assert result["selected_provider"] == "nvidia_nim"
    assert result["selected_model"] == payload["model"]
    assert result["configured_remote_providers"] == ["nvidia_nim"]
    assert result["execution_ready"] is True
    assert "api_key" not in str(result).casefold()


def test_fcc_admin_status_rejects_unlisted_model_or_paid_fallback(monkeypatch):
    payload = {
        "status": "running",
        "provider": "nvidia_nim",
        "model": "nvidia_nim/nvidia/unknown-model",
        "provider_status": [
            {"provider_id": "nvidia_nim", "kind": "remote", "status": "configured"},
            {"provider_id": "anthropic", "kind": "remote", "status": "configured"},
        ],
    }
    class Response:
        status = 200
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def read(self, size): return __import__("json").dumps(payload).encode("utf-8")

    monkeypatch.setattr(probe.urllib.request, "urlopen", lambda *args, **kwargs: Response())

    result = probe.probe_fcc_admin_status()

    assert result["free_endpoint_verified"] is False
    assert result["execution_ready"] is False
    assert result["cost_status"] == "unverified"


def test_readiness_does_not_query_fcc_admin_when_listener_is_not_loopback(monkeypatch):
    monkeypatch.setattr(probe, "probe_claude_code", lambda: {"authenticated": False})
    monkeypatch.setattr(
        probe,
        "probe_fcc_gateway",
        lambda: {"gateway_status": "network_exposed", "bind_scope": "non_loopback", "cli_installed": True},
    )
    def must_not_call():
        raise AssertionError("Admin API must not be called on a non-loopback listener")
    monkeypatch.setattr(probe, "probe_fcc_admin_status", must_not_call)

    result = probe.get_external_agent_readiness()

    assert result["execution_ready"] is False
    assert "fcc_gateway_not_loopback_only" in result["blockers"]
