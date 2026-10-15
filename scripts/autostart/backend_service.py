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
from urllib.request import Request, urlopen

PROJECT_ROOT = Path(__file__).resolve().parents[2]
# Explicit overrides allow isolated local smoke tests without touching live service state.
STATE_DIR = Path(os.getenv("DGM_BACKEND_SERVICE_STATE_DIR", str(PROJECT_ROOT / "storage" / "runtime")))
STATE_FILE = STATE_DIR / "backend_service.json"
LOG_DIR = Path(os.getenv("DGM_BACKEND_SERVICE_LOG_DIR", str(PROJECT_ROOT / "logs")))
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


def _is_loopback_host(host: str) -> bool:
    return host.strip("[]").casefold() in {"127.0.0.1", "localhost", "::1"}


def _pid_is_full_runtime(pid: int) -> bool:
    """Fail closed unless process metadata proves this is the headless full runtime."""
    try:
        import psutil
        process = psutil.Process(pid)
        command_line = " ".join(process.cmdline()).casefold()
        executable = process.exe().casefold()
        return (
            process.is_running()
            and "main.py" in command_line
            and "--headless" in command_line
            and str(PROJECT_ROOT).casefold() in command_line
            and (executable.endswith("python.exe") or executable.endswith("pythonw.exe"))
        )
    except Exception:
        return False


def _pid_is_dgm_process(pid: int) -> bool:
    return _pid_is_dgm_api(pid) or _pid_is_full_runtime(pid)


def _runtime_readiness(host: str, port: int) -> tuple[bool, str]:
    """Verify the full runtime and its queue worker through a protected loopback session."""
    if not _is_loopback_host(host):
        return False, "Full runtime mode is loopback-only."
    healthy, message = _health(host, port)
    if not healthy:
        return False, message
    try:
        local_app_data = os.getenv("LOCALAPPDATA", "")
        bootstrap_path = Path(os.getenv("DGM_LOCAL_BOOTSTRAP_FILE") or (Path(local_app_data) / "DGM-MAT" / "security" / "bootstrap.token"))
        bootstrap = bootstrap_path.read_text(encoding="utf-8")
        if len(bootstrap) < 60 or bootstrap != bootstrap.strip():
            return False, "Local bootstrap credential is missing or invalid."

        def request_json(path: str, *, token: str | None = None, body: dict | None = None) -> dict:
            headers = {"Content-Type": "application/json"}
            if token:
                headers["Authorization"] = f"Bearer {token}"
            data = json.dumps(body).encode("utf-8") if body is not None else None
            request = Request(f"http://{host}:{port}{path}", data=data, headers=headers, method="POST" if body is not None else "GET")
            with urlopen(request, timeout=HEALTH_TIMEOUT_SECONDS) as response:
                result = json.loads(response.read().decode("utf-8"))
            if not isinstance(result, dict):
                raise ValueError("API returned a non-object response")
            return result

        session = request_json("/auth/session", token=bootstrap, body={"client_id": "dgm-runtime-service-health"})
        access_token = session.get("access_token")
        if not isinstance(access_token, str) or not access_token:
            return False, "Local API session exchange failed."
        status_payload = request_json("/runtime/status", token=access_token)
        queue_payload = request_json("/runtime/queue", token=access_token)
        if status_payload.get("status") != "running":
            return False, f"HTTP API is healthy but runtime status is {status_payload.get('status', 'unknown')}."
        queue_health = queue_payload.get("health")
        if not isinstance(queue_health, dict) or queue_health.get("worker_alive") is not True:
            return False, "Runtime reports running, but the durable action-queue worker is not alive."
        return True, "DGM-MAT full runtime ready; queue worker alive"
    except (OSError, URLError, TimeoutError, ValueError, KeyError, TypeError) as exc:
        return False, f"Full runtime readiness check failed: {type(exc).__name__}: {exc}"


def _command_for_mode(mode: str, host: str, port: int) -> list[str]:
    if mode == "api":
        return [sys.executable, "-m", "uvicorn", "core.api.api_server:app", "--host", host, "--port", str(port), "--log-level", "info"]
    if mode == "full":
        return [sys.executable, str(PROJECT_ROOT / "main.py"), "--headless"]
    raise ValueError("mode must be 'api' or 'full'")


def start(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT, mode: str = "api") -> int:
    if mode not in {"api", "full"}:
        print("START_REFUSED: mode must be 'api' or 'full'")
        return 2
    if mode == "full" and not _is_loopback_host(host):
        print("START_REFUSED: full runtime mode is loopback-only; no network exposure is permitted")
        return 2

    healthy, message = _health(host, port)
    if healthy:
        if mode == "api":
            print(f"ALREADY_RUNNING: {message} at {host}:{port}")
            return 0
        ready, readiness_message = _runtime_readiness(host, port)
        if ready:
            print(f"ALREADY_RUNNING: {readiness_message} at {host}:{port}")
            return 0
        print(f"START_REFUSED: API already answers but full runtime is not ready: {readiness_message}. No second process was started.")
        return 2

    old_state = _read_state()
    if old_state:
        old_pid = old_state.get("pid")
        if isinstance(old_pid, int) and _pid_is_dgm_process(old_pid):
            print(f"START_REFUSED: recorded DGM-MAT process PID {old_pid} exists but health is failing. Inspect log: {LOG_FILE}")
            return 2

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    command = _command_for_mode(mode, host, port)
    creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0
    with LOG_FILE.open("a", encoding="utf-8", buffering=1) as log_handle:
        log_handle.write(
            f"\n[{datetime.now(timezone.utc).isoformat()}] START requested: "
            f"mode={mode} host={host} port={port} python={sys.executable}\n"
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
        "service": "dgm-mat-runtime" if mode == "full" else "dgm-mat-api",
        "mode": mode,
        "pid": process.pid,
        "host": host,
        "port": port,
        "project_root": str(PROJECT_ROOT),
        "python_executable": sys.executable,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "command": command,
    })

    timeout = 180.0 if mode == "full" else 120.0
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        code = process.poll()
        if code is not None:
            print(f"START_FAILED: {mode} process exited with code {code}. Inspect log: {LOG_FILE}")
            return 1
        try:
            ready, readiness_message = _runtime_readiness(host, port) if mode == "full" else _health(host, port)
        except Exception as exc:
            ready, readiness_message = False, f"Readiness check raised {type(exc).__name__}: {exc}"
        if ready:
            print(f"STARTED: {readiness_message} at {host}:{port}; mode={mode}; PID={process.pid}; console hidden; log={LOG_FILE}")
            return 0
        time.sleep(0.4)

    print(f"START_TIMEOUT: {mode} service did not become ready within {timeout:.0f} seconds. Last check: {readiness_message}. Inspect log: {LOG_FILE}")
    # Never leave a child process running after a failed startup/readiness check.
    try:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=3)
    except Exception as exc:
        print(f"START_CLEANUP_WARNING: child process cleanup failed: {type(exc).__name__}")
    try:
        STATE_FILE.unlink(missing_ok=True)
    except OSError:
        pass
    return 1

def status(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT, mode: str | None = None) -> int:
    state = _read_state() or {}
    effective_mode = mode or state.get("mode", "api")
    if effective_mode not in {"api", "full"}:
        print("NOT_HEALTHY: invalid recorded service mode")
        return 1
    if effective_mode == "full":
        healthy, message = _runtime_readiness(host, port)
    else:
        healthy, message = _health(host, port)
    if healthy:
        print(f"RUNNING: {message} at {host}:{port}; mode={effective_mode}")
        if state.get("pid"):
            print(f"Recorded PID: {state['pid']}")
        return 0
    print(f"NOT_HEALTHY: {message}")
    if state:
        print(f"Recorded PID: {state.get('pid', 'unknown')}")
        print(f"Mode: {state.get('mode', 'api')}")
        print(f"Log: {LOG_FILE}")
    return 1

def stop() -> int:
    state = _read_state()
    if not state or not isinstance(state.get("pid"), int):
        print("NOT_RUNNING: no valid backend service state file")
        return 0
    pid = state["pid"]
    mode = state.get("mode", "api")
    identity_ok = _pid_is_full_runtime(pid) if mode == "full" else _pid_is_dgm_api(pid)
    if not identity_ok:
        healthy, _ = _health(str(state.get("host", DEFAULT_HOST)), int(state.get("port", DEFAULT_PORT)))
        if healthy:
            print("STOP_REFUSED: health is available, but recorded process identity cannot be verified safely.")
            return 2
        print("NOT_RUNNING: recorded PID is not verifiably the selected DGM-MAT service; no process was terminated.")
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
    print(f"STOPPED: DGM-MAT {mode} service PID {pid}")
    return 0

def main() -> int:
    parser = argparse.ArgumentParser(description="Manage the DGM-MAT API without a visible console.")
    parser.add_argument("action", choices=("start", "status", "stop"))
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--mode", choices=("api", "full"), default=None, help="api: HTTP only; full: headless Runtime, agents and durable queue worker")
    args = parser.parse_args()
    if args.action == "start":
        return start(args.host, args.port, args.mode or "api")
    if args.action == "status":
        return status(args.host, args.port, args.mode)
    return stop()


if __name__ == "__main__":
    raise SystemExit(main())
