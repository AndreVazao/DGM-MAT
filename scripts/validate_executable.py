"""Deep startup validation for the frozen Windows executable.

The child process output is captured to a temporary file to avoid pipe-buffer
deadlocks. On failure, only a short redacted tail is emitted to CI logs.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import requests

from core.observability.logger import dgm_logger


_SECRET_PATTERNS = (
    re.compile(r"(?i)(authorization\s*[:=]\s*bearer\s+)\S+"),
    re.compile(r"(?i)((?:token|secret|password|api[_-]?key)\s*[:=]\s*)\S+"),
)


def _redacted_tail(path: Path, *, max_lines: int = 80) -> str:
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()[-max_lines:]
    except OSError as exc:
        return f"<unable to read child output: {type(exc).__name__}>"
    redacted = []
    for line in lines:
        for pattern in _SECRET_PATTERNS:
            line = pattern.sub(r"\1[REDACTED]", line)
        redacted.append(line[:2000])
    return "\n".join(redacted)


def _stop_process(process: subprocess.Popen) -> None:
    if process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


def validate_executable(exe_path: str | os.PathLike[str]) -> bool:
    executable = Path(exe_path).expanduser().resolve()
    dgm_logger.info(f"Validating executable at {executable}...")

    if not executable.is_file():
        dgm_logger.error(f"Executable not found at {executable}")
        return False

    log_path = Path(tempfile.gettempdir()) / f"dgm-mat-exe-validation-{os.getpid()}.log"
    process = None
    succeeded = False

    try:
        with log_path.open("w", encoding="utf-8", errors="replace") as child_output:
            child_env = os.environ.copy()
            child_env["DGM_HEADLESS"] = "1"
            child_env["DGM_REPOSITORY_ROOT"] = str(Path.cwd().resolve())
            process = subprocess.Popen(
                [str(executable), "--headless"],
                cwd=str(Path.cwd()),
                env=child_env,
                stdout=child_output,
                stderr=subprocess.STDOUT,
                text=True,
            )

            max_retries = 30
            retry_interval = 5
            health_url = os.getenv(
                "DGM_VALIDATION_HEALTH_URL",
                "http://127.0.0.1:8181/health",
            )
            dgm_logger.info(
                f"Waiting for executable to initialize (max {max_retries * retry_interval}s)..."
            )

            for attempt in range(1, max_retries + 1):
                time.sleep(retry_interval)
                child_output.flush()

                return_code = process.poll()
                if return_code is not None:
                    dgm_logger.error(
                        f"Executable exited prematurely with code {return_code}. "
                        f"Redacted child output follows:\n{_redacted_tail(log_path)}"
                    )
                    return False

                try:
                    response = requests.get(health_url, timeout=15)
                    if response.status_code != 200:
                        dgm_logger.warning(
                            f"Attempt {attempt}: Health check returned {response.status_code}"
                        )
                        continue

                    health_data = response.json()
                    if health_data.get("status") != "healthy":
                        dgm_logger.warning(
                            f"Attempt {attempt}: Health status: {health_data.get('status')!r}"
                        )
                        continue

                    dgm_logger.info(
                        f"Executable health check PASSED on attempt {attempt}"
                    )
                    runtime_dir = Path.cwd() / ".runtime"
                    storage_dir = Path.cwd() / "storage" / "runtime"
                    if runtime_dir.exists() or storage_dir.exists():
                        dgm_logger.info("Runtime directory initialization verified.")
                    else:
                        dgm_logger.warning(
                            "Could not verify runtime directory, but health is OK."
                        )
                    succeeded = True
                    return True
                except (requests.RequestException, ValueError) as exc:
                    dgm_logger.warning(
                        f"Attempt {attempt}: Executable health probe failed: "
                        f"{type(exc).__name__}: {exc}"
                    )

            dgm_logger.error(
                "Max retries reached. Executable failed to become healthy. "
                f"Redacted child output follows:\n{_redacted_tail(log_path)}"
            )
            return False
    except Exception as exc:
        dgm_logger.error(
            f"Executable validation failed: {type(exc).__name__}: {exc}. "
            f"Redacted child output follows:\n{_redacted_tail(log_path)}"
        )
        return False
    finally:
        if process is not None:
            _stop_process(process)
        if succeeded:
            try:
                log_path.unlink(missing_ok=True)
            except OSError:
                pass


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/validate_executable.py <path_to_executable>")
        raise SystemExit(1)

    raise SystemExit(0 if validate_executable(sys.argv[1]) else 1)
