"""Cheap, read-only snapshot of the host capabilities available to DGM-MAT.

This module intentionally uses only the Python standard library. Optional host
metrics must never prevent the core API from starting on constrained machines.
"""
from __future__ import annotations

import os
import platform
import shutil
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class RuntimeCapabilityProfile:
    """Observed host facts; these describe capability, not guaranteed performance."""

    operating_system: str
    operating_system_release: str
    architecture: str
    python_version: str
    logical_cpu_count: int
    memory_total_bytes: int | None
    memory_available_bytes: int | None
    ollama_available: bool
    claude_code_available: bool
    capability_source: str = "python-standard-library"
    profile_kind: str = "observed-host-snapshot"

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable snapshot for the read-only governance API."""
        return asdict(self)


def _memory_snapshot() -> tuple[int | None, int | None]:
    """Read memory metrics where the host exposes a supported interface."""
    try:
        if os.name == "nt":
            import ctypes
            from ctypes import wintypes

            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [
                    ("dwLength", wintypes.DWORD),
                    ("dwMemoryLoad", wintypes.DWORD),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
                ]

            status = MEMORYSTATUSEX()
            status.dwLength = ctypes.sizeof(status)
            if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
                return int(status.ullTotalPhys), int(status.ullAvailPhys)
        else:
            meminfo = Path("/proc/meminfo")
            if meminfo.is_file():
                values: dict[str, int] = {}
                for line in meminfo.read_text(encoding="ascii").splitlines():
                    key, _, remainder = line.partition(":")
                    parts = remainder.strip().split()
                    if parts and parts[0].isdigit():
                        values[key] = int(parts[0]) * 1024
                total = values.get("MemTotal")
                available = values.get("MemAvailable", values.get("MemFree"))
                return total, available
    except (OSError, ValueError, AttributeError, ImportError):
        pass
    return None, None


def collect_runtime_capability_profile() -> RuntimeCapabilityProfile:
    """Collect cheap host facts without starting services or making network calls."""
    total, available = _memory_snapshot()
    return RuntimeCapabilityProfile(
        operating_system=platform.system() or "unknown",
        operating_system_release=platform.release() or "unknown",
        architecture=platform.machine() or "unknown",
        python_version=platform.python_version(),
        logical_cpu_count=max(1, os.cpu_count() or 1),
        memory_total_bytes=total,
        memory_available_bytes=available,
        ollama_available=shutil.which("ollama") is not None,
        claude_code_available=shutil.which("claude") is not None,
    )
