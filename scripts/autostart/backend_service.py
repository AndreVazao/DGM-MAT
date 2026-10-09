# Path: C:\\ProgramasGodMode\\DGM-MAT\\scripts\\autostart\\backend_service.py
"""Headless, bounded lifecycle manager for the DGM-MAT HTTP API.

This manages only the API process. It deliberately does not start the cockpit,
autonomous cognition loop, action-queue consumer, or external providers.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

PROJECT_ROOT = Path(__file__).resolve().parents[2]
STATE_DIR = PROJECT_ROOT / "storage" / "runtime"
STATE_FILE = STATE_DIR / "backend_service.json"
LOG_DIR = PROJECT_ROOT / "logs"
LOG_FILE = LOG_DIR / "backend-service.log"
DEFAULT_HOST = os.getenv("DGM_API_HOST", "127.0.0.1")
DEFAULT_PORT = int(os.getenv("DGM_API_PORT", "8181"))
HEALTH_TIMEOUT_SECONDS = 2.0


def _health_url(host: str, port: int) -> str:
    # The service manager is intentionally loopback-only by default.
    return f"http://{host}:{port}/health"


def _health(host: str, port: int) -> tuple[bool, str]:
    try:
        with urlopen(_health_url(host, port), timeout=HEALTH_TIMEOUT_SECONDS) as response:
            payload = json.loads(response.read().decode("utf-8"))
        if response.status == 200 and payload.get("service") == "dgm-mat":
            return True, "DGM-MAT API healthy"
        return False, "Port answered, but response did not identify DGM-MAT"
    except (OSError, URLError, TimeoutError, ValueError) as exc:
        return False, f"API health check failed: {exc}"


def _read_state() -> dict | None:
    try:
        payload = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else None
    except (OSError, ValueError):
        return None


def _write_state(payload: dict) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    temporary = STATE_FILE.with_suffix(".tmp")
    temporary.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    os.replace(temporary, STATE_FILE)


def _pid_is_dgm_api(pid: int) -> bool:
    """Fail closed unless process metadata proves this is our Uvicorn API."""
    try:
        import psutil

        process = psutil.Process(pid)
        command_line = " ".join(process.cmdline()).casefold()
        executable = process.exe().casefold()
        return (
            process.is_running()
            and ("uvicorn" in command_line)
            and ("core.api.api_server:app" in command_line)
            and (executable.endswith("python.exe") or executable.endswith("pythonw.exe"))
        )
    except Exception:
        return False


def start(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> int:
    healthy, message = _health(host, port)
    if healthy:
        print(f"ALREADY_RUNNING: {message} at {host}:{port}")
        return 0

    old_state = _read_state()
    if old_state:
        old_pid = old_state.get("pid")
        if isinstance(old_pid, int) and _pid_is_dgm_api(old_pid):
            print(f"START_REFUSED: recorded API process PID {old_pid} exists but health is failing. Inspect log: {LOG_FILE}")
            return 2

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    command = [
        sys.executable,
        "-m",
        "uvicorn",
        "core.api.api_server:app",
        "--host",
        host,
        "--port",
        str(port),
        "--log-level",
        "info",
    ]
    creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0
    with LOG_FILE.open("a", encoding="utf-8", buffering=1) as log_handle:
        log_handle.write(
            f"\n[{datetime.now(timezone.utc).isoformat()}] START requested: "
            f"host={host} port={port} python={sys.executable}\n"
        )
        process = subprocess.Popen(
            command,
            cwd=str(PROJECT_ROOT),
            stdin=subprocess.DEVNULL,
            stdout=log_handle,
            stderr=subprocess.STDOUT,
            creationflags=creation_flags,
            close_fds=(os.name != "nt"),
        )

    _write_state({
        "service": "dgm-mat-api",
        "pid": process.pid,
        "host": host,
        "port": port,
        "project_root": str(PROJECT_ROOT),
        "python_executable": sys.executable,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "command": command,
    })

    deadline = time.monotonic() + 12.0
    while time.monotonic() < deadline:
        code = process.poll()
        if code is not None:
            print(f"START_FAILED: API process exited with code {code}. Inspect log: {LOG_FILE}")
            return 1
        healthy, message = _health(host, port)
        if healthy:
            print(f"STARTED: {message} at {host}:{port}; PID={process.pid}; console hidden; log={LOG_FILE}")
            return 0
        time.sleep(0.4)

    print(f"START_TIMEOUT: API did not become healthy within 12 seconds. Inspect log: {LOG_FILE}")
    return 1


def status(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> int:
    healthy, message = _health(host, port)
    state = _read_state() or {}
    if healthy:
        print(f"RUNNING: {message} at {host}:{port}")
        if state.get("pid"):
            print(f"Recorded PID: {state['pid']}")
        return 0
    print(f"NOT_HEALTHY: {message}")
    if state:
        print(f"Recorded PID: {state.get('pid', 'unknown')}")
        print(f"Log: {LOG_FILE}")
    return 1


def stop() -> int:
    state = _read_state()
    if not state or not isinstance(state.get("pid"), int):
        print("NOT_RUNNING: no valid backend service state file")
        return 0
    pid = state["pid"]
    if not _pid_is_dgm_api(pid):
        healthy, _ = _health(str(state.get("host", DEFAULT_HOST)), int(state.get("port", DEFAULT_PORT)))
        if healthy:
            print("STOP_REFUSED: health is available, but process identity cannot be verified safely.")
            return 2
        print("NOT_RUNNING: recorded PID is not verifiably the DGM-MAT API; no process was terminated.")
        return 0

    try:
        import psutil

        process = psutil.Process(pid)
        process.terminate()
        try:
            process.wait(timeout=5)
        except psutil.TimeoutExpired:
            process.kill()
            process.wait(timeout=3)
    except Exception as exc:
        print(f"STOP_FAILED: {exc}")
        return 1

    healthy, _ = _health(str(state.get("host", DEFAULT_HOST)), int(state.get("port", DEFAULT_PORT)))
    if healthy:
        print("STOP_WARNING: another process still answers the configured health endpoint.")
        return 1
    try:
        STATE_FILE.unlink(missing_ok=True)
    except OSError:
        pass
    print(f"STOPPED: DGM-MAT API PID {pid}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Manage the DGM-MAT API without a visible console.")
    parser.add_argument("action", choices=("start", "status", "stop"))
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    args = parser.parse_args()
    if args.action == "start":
        return start(args.host, args.port)
    if args.action == "status":
        return status(args.host, args.port)
    return stop()


if __name__ == "__main__":
    raise SystemExit(main())
