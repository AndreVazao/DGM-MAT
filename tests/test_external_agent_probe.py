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
        "probe_codex_cli",
        lambda: {"provider_id": "codex_cli", "installed": True, "status": "available", "execution_ready": False},
    )
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
            "fallbacks_free_only": True,
        },
    )

    result = probe.get_external_agent_readiness()

    assert result["execution_ready"] is True
    assert result["policy"] == "FREE_ONLY_PAID_DENY"
    assert result["provider_calls_performed"] == 0
    assert result["fcc"]["admin"]["free_endpoint_verified"] is True
    assert result["fcc"]["admin"]["quota_status"] == "free_endpoint_rate_limits_and_account_quota_apply"
    assert result["blockers"] == []



def test_fcc_admin_status_accepts_allowlisted_free_nim_model_and_same_model_fallback(monkeypatch):
    status_payload = {
        "status": "running",
        "provider": "nvidia_nim",
        "model": "nvidia_nim/nvidia/nemotron-3.5-super-vl-120b-a12b",
        "provider_status": [
            {"provider_id": "nvidia_nim", "kind": "remote", "status": "configured"},
            {"provider_id": "anthropic", "kind": "remote", "status": "missing_key"},
        ],
    }
    config_payload = {
        "fields": [
            {"key": "MODEL_FALLBACKS", "value": "nvidia_nim/nvidia/nemotron-3.5-super-vl-120b-a12b", "secret": False},
            {"key": "NVIDIA_NIM_API_KEY", "value": "********", "secret": True},
        ]
    }
    responses = iter([status_payload, config_payload])

    class Response:
        status = 200
        def __init__(self, payload): self.payload = payload
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def read(self, size): return __import__("json").dumps(self.payload).encode("utf-8")

    monkeypatch.setattr(
        probe.urllib.request,
        "urlopen",
        lambda *args, **kwargs: Response(next(responses)),
    )

    result = probe.probe_fcc_admin_status()

    assert result["free_endpoint_verified"] is True
    assert result["selected_provider"] == "nvidia_nim"
    assert result["selected_model"] == status_payload["model"]
    assert result["configured_remote_providers"] == ["nvidia_nim"]
    assert result["fallbacks_free_only"] is True
    assert result["fallback_models_count"] == 1
    assert result["execution_ready"] is True
    assert "api_key" not in str(result).casefold()


def test_fcc_admin_status_rejects_unlisted_model_or_paid_fallback(monkeypatch):
    status_payload = {
        "status": "running",
        "provider": "nvidia_nim",
        "model": "nvidia_nim/nvidia/unknown-model",
        "provider_status": [
            {"provider_id": "nvidia_nim", "kind": "remote", "status": "configured"},
            {"provider_id": "anthropic", "kind": "remote", "status": "configured"},
        ],
    }
    config_payload = {
        "fields": [
            {"key": "MODEL_FALLBACKS", "value": '[{"model":"anthropic/claude"}]', "secret": False},
        ]
    }
    responses = iter([status_payload, config_payload])

    class Response:
        status = 200
        def __init__(self, payload): self.payload = payload
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def read(self, size): return __import__("json").dumps(self.payload).encode("utf-8")

    monkeypatch.setattr(
        probe.urllib.request,
        "urlopen",
        lambda *args, **kwargs: Response(next(responses)),
    )

    result = probe.probe_fcc_admin_status()

    assert result["free_endpoint_verified"] is False
    assert result["execution_ready"] is False
    assert result["fallbacks_free_only"] is False
    assert result["fallback_models_count"] == 1
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


def test_codex_probe_reports_version_without_auth_or_cost_claim(monkeypatch):
    class FakeProbeResult:
        def to_dict(self):
            return {
                "agent_id": "codex",
                "executable_path": "C:/tools/codex.cmd",
                "available": True,
                "status": "available",
                "version": "codex-cli 1.2.3",
                "configured_endpoint_env_names": ["OPENAI_BASE_URL"],
                "identity_verified": False,
                "billing_verified": False,
                "execution_enabled": False,
            }

    class FakeProbe:
        def probe_agent(self, agent_id):
            assert agent_id == "codex"
            return FakeProbeResult()

    monkeypatch.setattr(probe, "LocalCodingAgentProbe", FakeProbe)
    result = probe.probe_codex_cli()

    assert result["installed"] is True
    assert result["version"] == "codex-cli 1.2.3"
    assert result["authenticated"] is None
    assert result["identity_verified"] is False
    assert result["cost_status"] == "unverified"
    assert result["execution_ready"] is False
    assert result["model_requests_sent"] == 0


def test_combined_readiness_separates_fcc_inference_from_local_coding_agents(monkeypatch):
    monkeypatch.setattr(probe, "probe_codex_cli", lambda: {
        "provider_id": "codex_cli", "installed": True, "status": "available", "execution_ready": False
    })
    monkeypatch.setattr(probe, "probe_claude_code", lambda: {
        "provider_id": "claude_code_cli", "installed": True, "authenticated": True,
        "execution_ready": False, "cost_status": "unverified"
    })
    monkeypatch.setattr(probe, "probe_fcc_gateway", lambda: {
        "gateway_status": "loopback_only", "bind_scope": "loopback", "cli_installed": True
    })
    monkeypatch.setattr(probe, "probe_fcc_admin_status", lambda: {
        "free_endpoint_verified": True, "execution_ready": True,
        "cost_status": "official_free_endpoint", "quota_status": "free_endpoint_rate_limits_and_account_quota_apply"
    })

    result = probe.get_external_agent_readiness()

    assert result["fcc_inference_ready"] is True
    assert result["execution_scope"] == "fcc_inference_only"
    assert result["local_coding_agents_execution_ready"] is False
    assert result["local_coding_agents"]["execution_ready"] is False
    assert result["local_coding_agents"]["codex_cli"]["installed"] is True
    assert result["local_coding_agents"]["claude_code_cli"]["authenticated"] is True


def test_claude_command_refuses_cmd_wrapper_without_launching(monkeypatch):
    monkeypatch.setattr(probe.shutil, "which", lambda _name: "/tmp/claude.cmd")

    command, executable = probe._claude_command()

    assert command is None
    assert executable == "/tmp/claude.cmd"


def test_claude_auth_probe_uses_minimal_environment_and_temporary_cwd(monkeypatch):
    monkeypatch.setattr(probe, "_claude_command", lambda: (["/opt/claude", "auth", "status"], "/opt/claude"))
    monkeypatch.setenv("ANTHROPIC_API_KEY", "must-not-be-inherited")
    monkeypatch.setenv("OPENAI_API_KEY", "must-not-be-inherited-either")
    captured = {}

    def fake_run(*args, **kwargs):
        captured["args"] = args
        captured.update(kwargs)
        return SimpleNamespace(stdout='{"loggedIn": false}', stderr="", returncode=1)

    monkeypatch.setattr(probe.subprocess, "run", fake_run)
    result = probe.probe_claude_code()

    assert result["status"] == "installed_logged_out"
    assert captured["shell"] is False
    assert captured["cwd"]
    assert "ANTHROPIC_API_KEY" not in captured["env"]
    assert "OPENAI_API_KEY" not in captured["env"]


def test_claude_cmd_wrapper_probe_fails_closed_without_subprocess(monkeypatch):
    monkeypatch.setattr(probe, "_claude_command", lambda: (None, "C:/Users/operator/AppData/Roaming/npm/claude.cmd"))
    monkeypatch.setattr(probe.subprocess, "run", lambda *_args, **_kwargs: pytest.fail("cmd wrapper must not execute"))

    result = probe.probe_claude_code()

    assert result["installed"] is True
    assert result["authenticated"] is None
    assert result["status"] == "auth_probe_unavailable"
    assert "cmd.exe reparses" in result["detail"]
    assert result["model_requests_sent"] == 0
