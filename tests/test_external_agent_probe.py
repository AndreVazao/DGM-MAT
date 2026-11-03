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
        lambda: {"gateway_status": "loopback_only", "bind_scope": "loopback"},
    )

    result = probe.get_external_agent_readiness()

    assert result["execution_ready"] is False
    assert result["policy"] == "FREE_ONLY_PAID_DENY"
    assert result["provider_calls_performed"] == 0
    assert "provider_zero_cost_not_verified" in result["blockers"]
