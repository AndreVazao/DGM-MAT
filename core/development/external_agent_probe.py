"""Read-only readiness probes for external coding agents.

These probes inspect executable/authentication/listener state only. They never
submit prompts, read credential files, start services, or authorize paid usage.
"""
from __future__ import annotations

import json
import os
import shutil
from datetime import datetime, timezone
import subprocess
import tempfile
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from core.execution.local_coding_agent_probe import LocalCodingAgentProbe


def _timeout(value: float) -> float:
    try:
        return max(0.2, min(float(value), 5.0))
    except (TypeError, ValueError):
        return 2.0


def _claude_command() -> tuple[list[str] | None, str | None]:
    executable = None
    if os.name == "nt":
        appdata = os.getenv("APPDATA")
        if appdata:
            # Prefer the PowerShell shim: it avoids cmd.exe argument parsing.
            for candidate in (
                Path(appdata) / "npm" / "claude.ps1",
            ):
                if candidate.is_file():
                    executable = str(candidate)
                    break
    if not executable:
        executable = shutil.which("claude")
    if not executable:
        return None, None

    suffix = Path(executable).suffix.casefold()
    if os.name == "nt" and suffix == ".ps1":
        shell = shutil.which("powershell") or shutil.which("pwsh")
        if not shell:
            return None, executable
        return [shell, "-NoLogo", "-NoProfile", "-NonInteractive", "-File", executable, "auth", "status"], executable
    if suffix in {".cmd", ".bat"}:
        # cmd.exe reparses its command tail; never execute .cmd/.bat wrappers.
        return None, executable
    return [executable, "auth", "status"], executable


def _probe_environment() -> dict[str, str]:
    """Keep process plumbing/profile paths but omit inherited secret values."""
    allowed = {"PATH"}
    if os.name == "nt":
        allowed.update({"SYSTEMROOT", "WINDIR", "PATHEXT", "TEMP", "TMP", "APPDATA", "LOCALAPPDATA", "USERPROFILE"})
    else:
        allowed.update({"HOME", "TMPDIR"})
    return {key: value for key, value in os.environ.items() if key.upper() in allowed and isinstance(value, str)}

def _json_object(output: str) -> dict[str, Any] | None:
    if not isinstance(output, str):
        return None
    start = output.find("{")
    end = output.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        value = json.loads(output[start:end + 1])
    except json.JSONDecodeError:
        return None
    return value if isinstance(value, dict) else None


def probe_claude_code(*, timeout_seconds: float = 5.0) -> dict[str, Any]:
    """Check CLI presence and supported auth status without issuing a model request."""
    command, executable = _claude_command()
    if not executable:
        return {
            "provider_id": "claude_code_cli",
            "installed": False,
            "authenticated": False,
            "status": "not_installed",
            "executable_path": None,
            "auth_method": None,
            "api_provider": None,
            "cost_status": "unverified",
            "execution_ready": False,
            "detail": "Claude Code CLI was not found on PATH or in the standard npm user bin.",
            "model_requests_sent": 0,
        }
    if command is None:
        return {
            "provider_id": "claude_code_cli",
            "installed": True,
            "authenticated": None,
            "status": "auth_probe_unavailable",
            "executable_path": executable,
            "auth_method": None,
            "api_provider": None,
            "cost_status": "unverified",
            "execution_ready": False,
            "detail": ("The command wrapper was detected but deliberately not executed because cmd.exe reparses command arguments." if Path(executable).suffix.casefold() in {".cmd", ".bat"} else "The CLI wrapper was found but no safe interpreter was available to run its fixed auth-status command."),
            "model_requests_sent": 0,
        }

    try:
        result = subprocess.run(
            command,
            cwd=Path(tempfile.gettempdir()),
            env=_probe_environment(),
            shell=False,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=_timeout(timeout_seconds),
        )
    except subprocess.TimeoutExpired:
        return {
            "provider_id": "claude_code_cli",
            "installed": True,
            "authenticated": None,
            "status": "auth_probe_timeout",
            "executable_path": executable,
            "auth_method": None,
            "api_provider": None,
            "cost_status": "unverified",
            "execution_ready": False,
            "detail": "The fixed authentication-status probe timed out.",
            "model_requests_sent": 0,
        }
    except OSError as exc:
        return {
            "provider_id": "claude_code_cli",
            "installed": True,
            "authenticated": None,
            "status": "auth_probe_failed",
            "executable_path": executable,
            "auth_method": None,
            "api_provider": None,
            "cost_status": "unverified",
            "execution_ready": False,
            "detail": f"Authentication-status probe could not start ({type(exc).__name__}).",
            "model_requests_sent": 0,
        }

    payload = _json_object((result.stdout or "") + "\n" + (result.stderr or ""))
    if payload is None or not isinstance(payload.get("loggedIn"), bool):
        return {
            "provider_id": "claude_code_cli",
            "installed": True,
            "authenticated": None,
            "status": "auth_probe_unrecognized",
            "executable_path": executable,
            "auth_method": None,
            "api_provider": None,
            "cost_status": "unverified",
            "execution_ready": False,
            "detail": "The CLI did not return the expected authentication-status schema.",
            "model_requests_sent": 0,
        }

    authenticated = payload["loggedIn"]
    return {
        "provider_id": "claude_code_cli",
        "installed": True,
        "authenticated": authenticated,
        "status": "authenticated_cost_unverified" if authenticated else "installed_logged_out",
        "executable_path": executable,
        "auth_method": payload.get("authMethod") if isinstance(payload.get("authMethod"), str) else None,
        "api_provider": payload.get("apiProvider") if isinstance(payload.get("apiProvider"), str) else None,
        "cost_status": "unverified",
        "execution_ready": False,
        "detail": (
            "Authentication is present, but the zero-cost policy has not been verified; execution remains disabled."
            if authenticated else
            "Claude Code is installed but not authenticated; no model request was attempted."
        ),
        "model_requests_sent": 0,
        "probe_exit_code": result.returncode,
    }


def probe_codex_cli() -> dict[str, Any]:
    """Run the fixed Codex version probe only; auth, route and cost remain unverified."""
    result = LocalCodingAgentProbe().probe_agent("codex").to_dict()
    installed = bool(result.get("available"))
    return {
        "provider_id": "codex_cli",
        "installed": installed,
        "authenticated": None,
        "status": result.get("status", "probe_unavailable"),
        "executable_path": result.get("executable_path"),
        "version": result.get("version"),
        "configured_endpoint_env_names": result.get("configured_endpoint_env_names", []),
        "identity_verified": False,
        "api_provider": None,
        "cost_status": "unverified",
        "execution_ready": False,
        "detail": (
            "Codex CLI version was discovered; authentication, provider/model identity and zero-cost policy remain unverified."
            if installed else
            "Codex CLI was not found; no prompt or model request was attempted."
        ),
        "model_requests_sent": 0,
    }


def _listener_addresses(output: str, port: int) -> list[str]:
    addresses: set[str] = set()
    for line in output.splitlines():
        fields = line.split()
        if len(fields) < 4:
            continue
        if fields[0].casefold() not in {"tcp", "tcp4", "tcp6"}:
            continue
        local = fields[1]
        state = next((item.casefold() for item in fields if item.casefold() in {"listen", "listening"}), None)
        if state is None or not local.endswith(f":{port}"):
            continue
        address = local.rsplit(":", 1)[0].strip("[]")
        if address:
            addresses.add(address.casefold())
    return sorted(addresses)


def probe_fcc_gateway(*, port: int = 8082, timeout_seconds: float = 2.0) -> dict[str, Any]:
    """Observe FCC CLI and listener binding; never start FCC or call a model."""
    cli = shutil.which("fcc-claude")
    netstat = shutil.which("netstat")
    if not netstat and os.name == "nt":
        system_root = os.getenv("SystemRoot", r"C:\Windows")
        candidate = Path(system_root) / "System32" / "netstat.exe"
        if candidate.is_file():
            netstat = str(candidate)
    if not netstat:
        return {
            "provider_id": "fcc_gateway",
            "cli_installed": bool(cli),
            "cli_path": cli,
            "gateway_status": "listener_probe_unavailable",
            "bind_scope": "unknown",
            "listener_addresses": [],
            "cost_status": "unverified",
            "execution_ready": False,
            "detail": "FCC listener binding could not be inspected because netstat is unavailable.",
            "model_requests_sent": 0,
        }
    try:
        result = subprocess.run(
            [netstat, "-ano", "-p", "tcp"],
            shell=False,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=_timeout(timeout_seconds),
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {
            "provider_id": "fcc_gateway",
            "cli_installed": bool(cli),
            "cli_path": cli,
            "gateway_status": "listener_probe_failed",
            "bind_scope": "unknown",
            "listener_addresses": [],
            "cost_status": "unverified",
            "execution_ready": False,
            "detail": f"FCC listener inspection failed ({type(exc).__name__}).",
            "model_requests_sent": 0,
        }
    if result.returncode != 0:
        return {
            "provider_id": "fcc_gateway",
            "cli_installed": bool(cli),
            "cli_path": cli,
            "gateway_status": "listener_probe_failed",
            "bind_scope": "unknown",
            "listener_addresses": [],
            "cost_status": "unverified",
            "execution_ready": False,
            "detail": "netstat returned a non-zero exit code.",
            "model_requests_sent": 0,
        }

    addresses = _listener_addresses(result.stdout or "", port)
    if not addresses:
        status, scope = "stopped", "not_listening"
        detail = f"No TCP listener was observed on port {port}."
    elif any(address in {"0.0.0.0", "::", "*"} or address not in {"127.0.0.1", "::1"} for address in addresses):
        status, scope = "network_exposed", "non_loopback"
        detail = "FCC listens on a non-loopback interface; agent execution is blocked."
    else:
        status, scope = "loopback_only", "loopback"
        detail = "FCC listener is restricted to loopback, but provider cost/availability remains unverified."
    return {
        "provider_id": "fcc_gateway",
        "cli_installed": bool(cli),
        "cli_path": cli,
        "gateway_status": status,
        "bind_scope": scope,
        "listener_addresses": addresses,
        "port": port,
        "cost_status": "unverified",
        "execution_ready": False,
        "detail": detail,
        "model_requests_sent": 0,
    }


FREE_NVIDIA_NIM_MODEL_IDS = {
    # NVIDIA's public catalog marked this exact model "Free Endpoint" on 2026-11-03.
    "nvidia_nim/nvidia/nemotron-3.5-super-vl-120b-a12b",
}


def _fcc_local_admin_get(path: str, timeout_seconds: float) -> dict[str, Any]:
    request = urllib.request.Request(
        "http://127.0.0.1:8082" + path,
        headers={"Accept": "application/json"},
        method="GET",
    )
    with urllib.request.urlopen(request, timeout=_timeout(timeout_seconds)) as response:
        if response.status != 200:
            raise ValueError(f"unexpected status {response.status}")
        payload = json.loads(response.read(256 * 1024).decode("utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("invalid FCC admin response")
    return payload


def _fcc_fallback_policy(config: dict[str, Any]) -> tuple[bool, int | None]:
    """Allow no fallback or fallbacks that all resolve to the same approved free model."""
    fields = config.get("fields")
    if not isinstance(fields, list):
        return False, None
    field = next(
        (item for item in fields if isinstance(item, dict) and item.get("key") == "MODEL_FALLBACKS"),
        None,
    )
    if field is None:
        return False, None
    value = field.get("value")
    if value is None or value == "":
        return True, 0
    if isinstance(value, str):
        if value.lstrip().startswith("["):
            try:
                value = json.loads(value)
            except json.JSONDecodeError:
                return False, None
        else:
            value = [item.strip() for item in value.split(",") if item.strip()]
    if not isinstance(value, list):
        return False, None
    models = []
    for item in value:
        model = item.get("model") if isinstance(item, dict) else item
        if not isinstance(model, str) or not model.strip():
            return False, None
        models.append(model.strip())
    safe = all(model in FREE_NVIDIA_NIM_MODEL_IDS for model in models)
    return safe, len(models)


def probe_fcc_admin_status(*, timeout_seconds: float = 2.0) -> dict[str, Any]:
    """Read FCC loopback admin status and masked config; never returns credential values."""
    try:
        payload = _fcc_local_admin_get("/admin/api/status", timeout_seconds)
        config = _fcc_local_admin_get("/admin/api/config", timeout_seconds)
    except (OSError, ValueError, json.JSONDecodeError, urllib.error.URLError) as exc:
        return {
            "status": "unavailable",
            "selected_provider": None,
            "selected_model": None,
            "configured_remote_providers": [],
            "fallbacks_disabled": False,
            "fallback_models_count": None,
            "free_endpoint_verified": False,
            "cost_status": "unverified",
            "quota_status": "unknown",
            "execution_ready": False,
            "detail": f"FCC local admin status/config unavailable ({type(exc).__name__}).",
        }

    provider = payload.get("provider") if isinstance(payload.get("provider"), str) else None
    model = payload.get("model") if isinstance(payload.get("model"), str) else None
    provider_status = payload.get("provider_status")
    if not isinstance(provider_status, list):
        provider_status = []
    configured_remote = sorted({
        item.get("provider_id")
        for item in provider_status
        if isinstance(item, dict)
        and item.get("kind") == "remote"
        and item.get("status") == "configured"
        and isinstance(item.get("provider_id"), str)
    })
    selected_configured = any(
        isinstance(item, dict)
        and item.get("provider_id") == provider
        and item.get("kind") == "remote"
        and item.get("status") == "configured"
        for item in provider_status
    )
    fallbacks_free_only, fallback_count = _fcc_fallback_policy(config)
    free_endpoint = (
        provider == "nvidia_nim"
        and model in FREE_NVIDIA_NIM_MODEL_IDS
        and selected_configured
        and configured_remote == ["nvidia_nim"]
        and fallbacks_free_only
    )
    return {
        "status": "ready_free_endpoint" if free_endpoint else "configured_model_not_allowlisted",
        "selected_provider": provider,
        "selected_model": model,
        "configured_remote_providers": configured_remote,
        "fallbacks_free_only": fallbacks_free_only,
        "fallback_models_count": fallback_count,
        "free_endpoint_verified": free_endpoint,
        "cost_status": "official_free_endpoint" if free_endpoint else "unverified",
        "quota_status": "free_endpoint_rate_limits_and_account_quota_apply" if free_endpoint else "unknown",
        "execution_ready": free_endpoint,
        "detail": (
            "Selected NVIDIA NIM model is listed as a Free Endpoint, only that remote provider is configured, and all model fallbacks are pinned to that same free endpoint."
            if free_endpoint else
            "FCC is not configured exclusively for the allowlisted NVIDIA NIM free endpoint with all model fallbacks pinned to that same free endpoint."
        ),
        "model_requests_sent": 0,
    }


def get_external_agent_readiness() -> dict[str, Any]:
    """Return truthful, non-invasive readiness for the configured external agents."""
    claude = probe_claude_code()
    codex = probe_codex_cli()
    fcc = probe_fcc_gateway()
    admin = (
        probe_fcc_admin_status()
        if fcc.get("bind_scope") == "loopback"
        else {
            "status": "not_checked",
            "selected_provider": None,
            "selected_model": None,
            "configured_remote_providers": [],
            "free_endpoint_verified": False,
            "cost_status": "unverified",
            "quota_status": "unknown",
            "execution_ready": False,
            "detail": "FCC admin status is queried only after loopback-only binding is confirmed.",
            "model_requests_sent": 0,
        }
    )
    blockers = []
    if not fcc.get("cli_installed"):
        blockers.append("fcc_cli_not_installed")
    if fcc.get("gateway_status") == "network_exposed":
        blockers.append("fcc_gateway_not_loopback_only")
    elif fcc.get("gateway_status") != "loopback_only":
        blockers.append("fcc_gateway_not_running_loopback")
    if not admin.get("free_endpoint_verified"):
        blockers.append("fcc_free_endpoint_not_verified")
    # FCC's explicit Free Endpoint is the only permitted execution route.
    execution_ready = bool(
        fcc.get("cli_installed")
        and fcc.get("bind_scope") == "loopback"
        and admin.get("free_endpoint_verified")
    )
    return {
        "schema": "dgm-mat.external-agent-readiness.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "execution_ready": execution_ready,
        "fcc_inference_ready": execution_ready,
        "execution_scope": "fcc_inference_only",
        "local_coding_agents_execution_ready": False,
        "policy": "FREE_ONLY_PAID_DENY",
        "provider_calls_performed": 0,
        "claude_code": claude,
        "local_coding_agents": {
            "codex_cli": codex,
            "claude_code_cli": claude,
            "execution_ready": False,
            "status": "probe_only",
        },
        "fcc": {**fcc, "admin": admin, "cost_status": admin.get("cost_status", "unverified"), "execution_ready": bool(execution_ready)},
        "blockers": blockers,
        "limitations": [
            "The allowlisted NVIDIA NIM model is a free endpoint, but rate limits and account quota still apply.",
            "The executor must pin the exact allowlisted model and must not fall back to paid providers.",
            "A successful readiness probe does not prove that a future model request will succeed; provider errors must stop the task.",
            "This endpoint never starts a provider, sends a prompt, reads credential files, or authorizes paid usage.",
        ],
    }
