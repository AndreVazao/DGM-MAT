"""Read-only readiness probes for external coding agents.

These probes inspect executable/authentication/listener state only. They never
submit prompts, read credential files, start services, or authorize paid usage.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any


def _timeout(value: float) -> float:
    try:
        return max(0.2, min(float(value), 5.0))
    except (TypeError, ValueError):
        return 2.0


def _claude_command() -> tuple[list[str] | None, str | None]:
    executable = shutil.which("claude")
    if not executable and os.name == "nt":
        appdata = os.getenv("APPDATA")
        if appdata:
            for candidate in (
                Path(appdata) / "npm" / "claude.ps1",
                Path(appdata) / "npm" / "claude.cmd",
            ):
                if candidate.is_file():
                    executable = str(candidate)
                    break
    if not executable:
        return None, None

    suffix = Path(executable).suffix.casefold()
    if os.name == "nt" and suffix == ".ps1":
        shell = shutil.which("powershell") or shutil.which("pwsh")
        if not shell:
            return None, executable
        return [shell, "-NoLogo", "-NoProfile", "-NonInteractive", "-File", executable, "auth", "status"], executable
    if os.name == "nt" and suffix in {".cmd", ".bat"}:
        shell = shutil.which("cmd") or os.getenv("COMSPEC")
        if not shell:
            return None, executable
        return [shell, "/d", "/c", executable, "auth", "status"], executable
    return [executable, "auth", "status"], executable


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


def probe_claude_code(*, timeout_seconds: float = 3.0) -> dict[str, Any]:
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
            "detail": "The CLI wrapper was found but no safe interpreter was available to run its fixed auth-status command.",
            "model_requests_sent": 0,
        }

    try:
        result = subprocess.run(
            command,
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


def get_external_agent_readiness() -> dict[str, Any]:
    """Return truthful, non-invasive readiness for the configured external agents."""
    claude = probe_claude_code()
    fcc = probe_fcc_gateway()
    blockers = []
    if not claude["authenticated"]:
        blockers.append("claude_code_not_authenticated")
    if fcc["gateway_status"] == "network_exposed":
        blockers.append("fcc_gateway_not_loopback_only")
    elif fcc["gateway_status"] != "loopback_only":
        blockers.append("fcc_gateway_not_running_loopback")
    blockers.append("provider_zero_cost_not_verified")
    return {
        "schema": "dgm-mat.external-agent-readiness.v1",
        "generated_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
        "execution_ready": False,
        "policy": "FREE_ONLY_PAID_DENY",
        "provider_calls_performed": 0,
        "claude_code": claude,
        "fcc": fcc,
        "blockers": blockers,
        "limitations": [
            "Authentication status does not prove model quota, price, or free-tier availability.",
            "A CLI or gateway being installed does not prove that an agent can safely edit and validate a repository.",
            "This endpoint never starts a provider, sends a prompt, reads credential files, or authorizes paid usage.",
        ],
    }
