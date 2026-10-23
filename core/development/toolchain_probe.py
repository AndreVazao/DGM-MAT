"""Safe, allowlisted and bounded toolchain probes for Programming & Engineering.

No arbitrary command, executable path, shell expression, package installation, or
source execution can be supplied by a caller. A probe only asks an allowlisted
tool to print its version and must be invoked explicitly.
"""
from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ToolchainProbeResult:
    tool_id: str
    status: str
    executable_path: str | None = None
    version: str | None = None
    detail: str | None = None


# Fixed argument lists only. No caller-provided command or shell is accepted.
_PROBES: dict[str, tuple[str, tuple[str, ...]]] = {
    "python": ("python", ("--version",)),
    "python3": ("python3", ("--version",)),
    "node": ("node", ("--version",)),
    "npm": ("npm", ("--version",)),
    "tsc": ("tsc", ("--version",)),
    "javac": ("javac", ("-version",)),
    "java": ("java", ("-version",)),
    "kotlinc": ("kotlinc", ("-version",)),
    "go": ("go", ("version",)),
    "rustc": ("rustc", ("--version",)),
    "cargo": ("cargo", ("--version",)),
    "gcc": ("gcc", ("--version",)),
    "clang": ("clang", ("--version",)),
    "pwsh": ("pwsh", ("-NoLogo", "-NoProfile", "-NonInteractive", "-Command", "$PSVersionTable.PSVersion.ToString()")),
    "powershell": ("powershell", ("-NoLogo", "-NoProfile", "-NonInteractive", "-Command", "$PSVersionTable.PSVersion.ToString()")),
    "bash": ("bash", ("--version",)),
    "shellcheck": ("shellcheck", ("--version",)),
    "sqlite3": ("sqlite3", ("--version",)),
}


def supported_tool_ids() -> tuple[str, ...]:
    """List known probe IDs; this is a catalogue, not an availability assertion."""
    return tuple(sorted(_PROBES))


def probe_toolchain(tool_id: str, *, timeout_seconds: float = 2.0) -> ToolchainProbeResult:
    """Run one fixed version probe, bounded to 0.2–5 seconds and without a shell."""
    if not isinstance(tool_id, str) or tool_id not in _PROBES:
        return ToolchainProbeResult(
            tool_id=str(tool_id),
            status="unsupported_probe",
            detail="Tool ID is not in the fixed allowlist.",
        )

    executable, args = _PROBES[tool_id]
    resolved = shutil.which(executable)
    if not resolved:
        return ToolchainProbeResult(
            tool_id=tool_id,
            status="unavailable",
            detail=f"Executable '{executable}' was not found on PATH.",
        )

    try:
        timeout = max(0.2, min(float(timeout_seconds), 5.0))
    except (TypeError, ValueError):
        timeout = 2.0

    try:
        completed = subprocess.run(
            [resolved, *args],
            shell=False,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return ToolchainProbeResult(
            tool_id=tool_id,
            status="timeout",
            executable_path=resolved,
            detail=f"Version probe exceeded {timeout:g} seconds.",
        )
    except OSError as exc:
        return ToolchainProbeResult(
            tool_id=tool_id,
            status="failed",
            executable_path=resolved,
            detail=f"Could not start the version probe: {type(exc).__name__}.",
        )

    output = (completed.stdout or "").strip() or (completed.stderr or "").strip()
    version_line = next((line.strip() for line in output.splitlines() if line.strip()), "")
    version_line = version_line[:300] or None
    if completed.returncode != 0:
        return ToolchainProbeResult(
            tool_id=tool_id,
            status="failed",
            executable_path=resolved,
            version=version_line,
            detail=f"Version probe exited with code {completed.returncode}.",
        )
    return ToolchainProbeResult(
        tool_id=tool_id,
        status="available",
        executable_path=resolved,
        version=version_line,
    )
