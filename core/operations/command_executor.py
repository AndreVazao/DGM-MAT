"""Allowlisted, bounded, read-only local command execution.

This v1 deliberately does not expose arbitrary shell text or administrator elevation.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable


@dataclass(frozen=True)
class CommandSpec:
    command_id: str
    description: str
    risk: str
    requires_target: bool = False


CATALOG: tuple[CommandSpec, ...] = (
    CommandSpec("system.summary", "Read Windows/host and PowerShell runtime summary", "READ"),
    CommandSpec("process.top", "List a bounded sample of processes", "READ"),
    CommandSpec("engines.inventory", "Observe running Ollama and Claude Code process names/IDs without managing them", "READ"),
    CommandSpec("git.status", "Read Git status for an authorized repository path", "READ", True),
    CommandSpec("ollama.status", "Check Ollama CLI availability and installed models", "READ"),
    CommandSpec("claude.status", "Check Claude Code CLI availability and version", "READ"),
)


class CommandDenied(ValueError):
    """Raised when an action or target is outside the explicit policy."""


class CommandExecutor:
    """Runs a small catalog of read-only diagnostics without shell interpolation."""

    def __init__(
        self,
        *,
        allowed_roots: list[str | Path] | None = None,
        timeout_seconds: float = 8.0,
        output_limit: int = 12_000,
        runner: Callable[..., Any] = subprocess.run,
        which: Callable[[str], str | None] = shutil.which,
        platform: str | None = None,
    ) -> None:
        if timeout_seconds <= 0 or timeout_seconds > 60:
            raise ValueError("timeout_seconds must be in (0, 60].")
        if output_limit < 512 or output_limit > 100_000:
            raise ValueError("output_limit must be between 512 and 100000.")
        self.timeout_seconds = timeout_seconds
        self.output_limit = output_limit
        self.runner = runner
        self.which = which
        self.platform = platform or os.name
        if allowed_roots is None:
            raw = os.getenv("DGM_COMMAND_ALLOWED_ROOTS", r"C:\ProgramasGodMode;C:\DevopGodMode")
            allowed_roots = [part for part in raw.split(";") if part.strip()]
        self.allowed_roots = tuple(self._normalize_path(p) for p in allowed_roots)

    @staticmethod
    def _normalize_path(value: str | Path) -> Path:
        return Path(os.path.abspath(os.path.expandvars(str(value)))).resolve(strict=False)

    def catalog(self) -> dict[str, Any]:
        return {
            "schema": "dgm-mat.command-catalog.v1",
            "mode": "read-only-allowlist",
            "arbitrary_shell": False,
            "administrator_elevation": False,
            "commands": [
                {"id": item.command_id, "description": item.description,
                 "risk": item.risk, "requires_target": item.requires_target}
                for item in CATALOG
            ],
        }

    def execute(self, command_id: str, *, target_path: str | None = None) -> dict[str, Any]:
        started = time.monotonic()
        spec = next((item for item in CATALOG if item.command_id == command_id), None)
        if spec is None:
            raise CommandDenied("Command is not in the approved catalog.")
        if spec.requires_target and not target_path:
            raise CommandDenied("This command requires target_path.")
        if not spec.requires_target and target_path:
            raise CommandDenied("This command does not accept target_path.")
        if command_id == "git.status":
            target = self._validate_target(target_path or "")
            argv = [self._require_executable("git"), "-C", str(target), "status", "--short", "--branch"]
        elif command_id == "system.summary":
            argv = self._powershell_argv(
                "$ErrorActionPreference='Stop'; "
                "[pscustomobject]@{OS=[System.Environment]::OSVersion.VersionString; "
                "PowerShell=$PSVersionTable.PSVersion.ToString(); "
                "Computer=$env:COMPUTERNAME} | ConvertTo-Json -Compress"
            )
        elif command_id == "process.top":
            argv = self._powershell_argv(
                "$ErrorActionPreference='Stop'; "
                "Get-Process | Sort-Object CPU -Descending | Select-Object -First 12 Name,Id,CPU | "
                "ConvertTo-Json -Compress"
            )
        elif command_id == "engines.inventory":
            # Never return full command lines: they may contain private arguments.
            argv = self._powershell_argv(
                "$ErrorActionPreference='Stop'; "
                "Get-CimInstance Win32_Process | Where-Object { "
                "$_.Name -match '^(ollama|claude)(\.exe)?$' -or "
                "($_.Name -match '^node(\.exe)?$' -and $_.CommandLine -match 'claude') "
                "} | Select-Object Name,ProcessId | ConvertTo-Json -Compress"
            )
        elif command_id == "ollama.status":
            executable = self.which("ollama")
            if not executable:
                return self._result(command_id, "unavailable", 127, "", "ollama executable not found", started)
            argv = [executable, "list"]
        elif command_id == "claude.status":
            executable = self.which("claude")
            if not executable:
                return self._result(command_id, "unavailable", 127, "", "Claude Code CLI executable not found", started)
            argv = [executable, "--version"]
        else:
            raise CommandDenied("Command has no execution implementation.")

        try:
            completed = self.runner(
                argv,
                cwd=str(self._safe_cwd()),
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                check=False,
                shell=False,
            )
            status = "passed" if completed.returncode == 0 else "failed"
            return self._result(
                command_id, status, int(completed.returncode),
                str(completed.stdout or ""), str(completed.stderr or ""), started,
            )
        except subprocess.TimeoutExpired as exc:
            stdout = exc.stdout.decode("utf-8", "replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
            stderr = exc.stderr.decode("utf-8", "replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
            return self._result(command_id, "timeout", None, str(stdout), str(stderr), started)
        except OSError as exc:
            return self._result(command_id, "failed", None, "", type(exc).__name__, started)

    def _validate_target(self, raw: str) -> Path:
        # Reject control characters before filesystem checks: some platforms accept
        # a NUL-containing string through normalization but then report it as merely
        # a missing directory, obscuring the actual invalid-input boundary.
        if not isinstance(raw, str) or not raw or any(ord(char) < 32 or ord(char) == 127 for char in raw):
            raise CommandDenied("Target path is invalid.")
        try:
            target = self._normalize_path(raw)
        except (OSError, RuntimeError, ValueError) as exc:
            raise CommandDenied("Target path is invalid.") from exc
        if not target.exists() or not target.is_dir():
            raise CommandDenied("Target must be an existing directory.")
        if not (target / ".git").exists() and not (target / ".git").is_file():
            raise CommandDenied("Target must be a Git working tree.")
        for root in self.allowed_roots:
            try:
                target.relative_to(root)
                return target
            except ValueError:
                continue
        raise CommandDenied("Target is outside the configured allowed roots.")

    def _safe_cwd(self) -> Path:
        for root in self.allowed_roots:
            if root.exists() and root.is_dir():
                return root
        raise CommandDenied("No configured allowed root exists; refusing to use an implicit working directory.")

    def _powershell_argv(self, script: str) -> list[str]:
        executable = self.which("powershell") or self.which("pwsh")
        if not executable:
            raise CommandDenied("PowerShell executable is unavailable.")
        return [executable, "-NoLogo", "-NoProfile", "-NonInteractive", "-Command", script]

    def _require_executable(self, name: str) -> str:
        executable = self.which(name)
        if not executable:
            raise CommandDenied(f"Required executable is unavailable: {name}.")
        return executable

    def _result(
        self, command_id: str, status: str, returncode: int | None,
        stdout: str, stderr: str, started: float,
    ) -> dict[str, Any]:
        return {
            "schema": "dgm-mat.command-result.v1",
            "command_id": command_id,
            "risk": "READ",
            "status": status,
            "returncode": returncode,
            "stdout": stdout[-self.output_limit:],
            "stderr": stderr[-self.output_limit:],
            "duration_ms": round((time.monotonic() - started) * 1000),
            "elevated": False,
        }
