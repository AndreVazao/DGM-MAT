"""Read-only discovery of the locally installed Codex and Claude Code CLIs.

This module deliberately does not execute coding tasks, inspect credential files,
read secret environment values, or claim that a provider/model is free. It only
locates the fixed CLI names and runs their documented version probe.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class LocalCodingAgentProbeResult:
    agent_id: str
    executable_path: str | None
    available: bool
    status: str
    version: str | None
    probe_error: str | None
    configured_endpoint_env_names: tuple[str, ...]
    identity_verified: bool = False
    billing_verified: bool = False
    execution_enabled: bool = False

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["configured_endpoint_env_names"] = list(self.configured_endpoint_env_names)
        return value


class LocalCodingAgentProbe:
    """Discover only the two operator-authorized local coding-agent CLIs."""

    AGENT_COMMANDS = {
        "codex": ("codex", "codex.exe", "codex.ps1", "codex.cmd"),
        "claude_code": ("claude", "claude.exe", "claude.ps1", "claude.cmd"),
    }
    ENDPOINT_ENV_NAMES = (
        "DGM_FCC_BASE_URL",
        "ANTHROPIC_BASE_URL",
        "OPENAI_BASE_URL",
        "FCC_BASE_URL",
    )
    MAX_VERSION_CHARS = 200
    DEFAULT_TIMEOUT_SECONDS = 5

    def __init__(self, *, timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS) -> None:
        if isinstance(timeout_seconds, bool) or not isinstance(timeout_seconds, (int, float)):
            raise ValueError("timeout_seconds must be a number")
        if not 1 <= float(timeout_seconds) <= 15:
            raise ValueError("timeout_seconds must be between 1 and 15 seconds")
        self.timeout_seconds = float(timeout_seconds)

    @staticmethod
    def _minimal_environment() -> dict[str, str]:
        """Pass process plumbing only; never inherit API keys or arbitrary secrets."""
        allowed = {"PATH"}
        if os.name == "nt":
            allowed.update({"SYSTEMROOT", "WINDIR", "COMSPEC", "PATHEXT", "TEMP", "TMP"})
        environment = {
            key: value
            for key, value in os.environ.items()
            if key.upper() in allowed and isinstance(value, str)
        }
        environment.setdefault("PATH", "")
        return environment

    @classmethod
    def _configured_endpoint_names(cls) -> tuple[str, ...]:
        # Presence only. Values may contain private endpoints or embedded secrets.
        return tuple(name for name in cls.ENDPOINT_ENV_NAMES if name in os.environ)

    @staticmethod
    def _clean_version(output: str) -> str | None:
        if not isinstance(output, str):
            return None
        first_line = next((line.strip() for line in output.splitlines() if line.strip()), "")
        cleaned = re.sub(r"[\x00-\x1f\x7f]", " ", first_line)
        cleaned = " ".join(cleaned.split())
        if not cleaned:
            return None
        return cleaned[: LocalCodingAgentProbe.MAX_VERSION_CHARS]

    @staticmethod
    def _is_windows() -> bool:
        return os.name == "nt"

    @classmethod
    def _locate(cls, agent_id: str) -> str | None:
        unsupported_wrapper: str | None = None
        if cls._is_windows():
            appdata = os.getenv("APPDATA")
            if appdata:
                binary = "codex" if agent_id == "codex" else "claude"
                for suffix in (".ps1", ".exe", ".cmd"):
                    candidate = Path(appdata) / "npm" / (binary + suffix)
                    if not candidate.is_file():
                        continue
                    resolved = str(candidate.resolve())
                    if suffix == ".cmd":
                        unsupported_wrapper = unsupported_wrapper or resolved
                        continue
                    return resolved
        for command in cls.AGENT_COMMANDS[agent_id]:
            found = shutil.which(command)
            if not found:
                continue
            try:
                resolved = str(Path(found).expanduser().resolve(strict=True))
            except (OSError, RuntimeError):
                resolved = str(found)
            if Path(resolved).suffix.casefold() in {".cmd", ".bat"}:
                unsupported_wrapper = unsupported_wrapper or resolved
                continue
            return resolved
        return unsupported_wrapper

    @classmethod
    def _version_command(cls, executable: str) -> list[str] | None:
        suffix = Path(executable).suffix.casefold()
        if cls._is_windows() and suffix == ".ps1":
            shell = shutil.which("powershell") or shutil.which("pwsh")
            if not shell:
                return None
            return [
                shell, "-NoLogo", "-NoProfile", "-NonInteractive",
                "-File", executable, "--version",
            ]
        if cls._is_windows() and suffix in {".cmd", ".bat"}:
            # cmd.exe reparses its command tail; do not execute a wrapper path
            # that could contain shell metacharacters. Prefer the paired .ps1
            # or .exe shim; otherwise report it without launching a process.
            return None
        return [executable, "--version"]

    def probe_agent(self, agent_id: str) -> LocalCodingAgentProbeResult:
        if agent_id not in self.AGENT_COMMANDS:
            raise ValueError(f"Unsupported local coding agent: {agent_id}")
        executable = self._locate(agent_id)
        endpoint_names = self._configured_endpoint_names()
        if executable is None:
            return LocalCodingAgentProbeResult(
                agent_id=agent_id,
                executable_path=None,
                available=False,
                status="not_installed",
                version=None,
                probe_error=None,
                configured_endpoint_env_names=endpoint_names,
            )

        command = self._version_command(executable)
        if command is None:
            return LocalCodingAgentProbeResult(
                agent_id, executable, True, "version_probe_unavailable", None,
                "cmd_wrapper_not_executed_for_safety" if Path(executable).suffix.casefold() in {".cmd", ".bat"} else "safe_interpreter_unavailable", endpoint_names,
            )
        try:
            completed = subprocess.run(
                command,
                cwd=tempfile.gettempdir(),
                env=self._minimal_environment(),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
                shell=False,
                timeout=self.timeout_seconds,
            )
        except subprocess.TimeoutExpired:
            return LocalCodingAgentProbeResult(
                agent_id, executable, True, "version_probe_timeout", None,
                "timeout", endpoint_names,
            )
        except OSError as exc:
            return LocalCodingAgentProbeResult(
                agent_id, executable, True, "version_probe_failed", None,
                type(exc).__name__, endpoint_names,
            )

        if completed.returncode != 0:
            return LocalCodingAgentProbeResult(
                agent_id, executable, True, "version_probe_failed", None,
                f"exit_code_{completed.returncode}", endpoint_names,
            )
        version = self._clean_version(completed.stdout)
        return LocalCodingAgentProbeResult(
            agent_id=agent_id,
            executable_path=executable,
            available=True,
            status="available" if version else "version_unreported",
            version=version,
            probe_error=None,
            configured_endpoint_env_names=endpoint_names,
        )

    def probe_all(self) -> dict[str, dict[str, Any]]:
        """Return independent probe results; one unavailable CLI never hides the other."""
        return {
            agent_id: self.probe_agent(agent_id).to_dict()
            for agent_id in self.AGENT_COMMANDS
        }
