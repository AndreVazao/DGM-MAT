# Path: C:\\ProgramasGodMode\\DGM-MAT\\scripts\\autostart\\ollama_service.py
"""Hidden, loopback-only lifecycle helper for the installed local Ollama server."""
from __future__ import annotations
import argparse
import json
import os
import subprocess
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OLLAMA_HOST = "127.0.0.1:11434"
BASE_URL = "http://127.0.0.1:11434"
LOG_DIR = PROJECT_ROOT / "logs"
LOG_FILE = LOG_DIR / "ollama-service.log"
READY_TIMEOUT_SECONDS = 20.0


def installed_models() -> list[str] | None:
    try:
        with urlopen(f"{BASE_URL}/api/tags", timeout=1.5) as response:
            payload = json.loads(response.read().decode("utf-8"))
        models = payload.get("models", [])
        return sorted({item["name"] for item in models if isinstance(item, dict) and isinstance(item.get("name"), str) and item["name"]})
    except (OSError, URLError, TimeoutError, ValueError, TypeError):
        return None


def _ollama_executable() -> Path:
    local = Path(os.getenv("LOCALAPPDATA", "")) / "Programs" / "Ollama" / "ollama.exe"
    if local.is_file():
        return local
    raise FileNotFoundError("Installed Ollama executable not found at the expected per-user installation path.")


def start() -> int:
    models = installed_models()
    if models is not None:
        print(f"ALREADY_RUNNING: local Ollama API on 127.0.0.1:11434; models={len(models)}")
        return 0
    executable = _ollama_executable()
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["OLLAMA_HOST"] = OLLAMA_HOST
    env["OLLAMA_ORIGINS"] = "http://127.0.0.1,http://localhost"
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0
    with LOG_FILE.open("a", encoding="utf-8", buffering=1) as log:
        log.write(f"\\nOllama start requested: host={OLLAMA_HOST} executable={executable}\\n")
        process = subprocess.Popen([str(executable), "serve"], cwd=str(executable.parent), env=env, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, creationflags=flags, close_fds=(os.name != "nt"))
    deadline = time.monotonic() + READY_TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        if process.poll() is not None:
            print(f"START_FAILED: ollama serve exited with code {process.returncode}; log={LOG_FILE}")
            return 1
        models = installed_models()
        if models is not None:
            print(f"STARTED: Ollama API on 127.0.0.1:11434; models={len(models)}; console hidden; log={LOG_FILE}")
            for model in models:
                print(f"MODEL: {model}")
            return 0
        time.sleep(0.5)
    try:
        process.terminate()
        process.wait(timeout=3)
    except Exception:
        try:
            process.kill()
        except Exception:
            pass
    print(f"START_TIMEOUT: local Ollama API did not become ready in {READY_TIMEOUT_SECONDS:.0f}s; log={LOG_FILE}")
    return 1


def status() -> int:
    models = installed_models()
    if models is None:
        print("NOT_RUNNING: Ollama API is not responding on loopback.")
        return 1
    print(f"RUNNING: Ollama API on 127.0.0.1:11434; models={len(models)}")
    for model in models:
        print(f"MODEL: {model}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Manage the local loopback-only Ollama server.")
    parser.add_argument("action", choices=("start", "status"))
    args = parser.parse_args()
    return start() if args.action == "start" else status()


if __name__ == "__main__":
    raise SystemExit(main())
