import os
import re
import subprocess
import sys
import tempfile
import time

import requests

from core.observability.logger import dgm_logger


def _print_process_log_tail(log_path, max_lines=100):
    """Print a bounded, lightly redacted executable log tail for CI diagnosis."""
    print("\n--- DGM-MAT executable startup log (last lines) ---", flush=True)
    try:
        with open(log_path, "r", encoding="utf-8", errors="replace") as log_file:
            lines = log_file.readlines()[-max_lines:]
        if not lines:
            print("(The executable produced no stdout/stderr.)", flush=True)
        for line in lines:
            # Avoid leaking common credential formats into public Actions logs.
            line = re.sub(
                r"(?i)(authorization\s*[:=]\s*(?:bearer\s+)?|access_token\s*[:=]\s*|refresh_token\s*[:=]\s*|api[_-]?key\s*[:=]\s*|password\s*[:=]\s*)[^\s,;]+",
                r"\1[REDACTED]",
                line.rstrip("\r\n"),
            )
            print(line, flush=True)
    except OSError as exc:
        print(f"(Could not read executable startup log: {exc})", flush=True)
    print("--- end executable startup log ---\n", flush=True)


def validate_executable(exe_path):
    dgm_logger.info(f"Validating executable at {exe_path}...")

    if not os.path.exists(exe_path):
        dgm_logger.error(f"Executable not found at {exe_path}")
        return False

    process = None
    log_path = None
    log_file = None

    try:
        # Capture startup output instead of discarding it. If the frozen app
        # exits before its health endpoint starts, CI will show the real error.
        log_file = tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            errors="replace",
            prefix="dgm-mat-exe-startup-",
            suffix=".log",
            delete=False,
        )
        log_path = log_file.name
        process = subprocess.Popen(
            [os.path.abspath(exe_path), "--headless"],
            stdout=log_file,
            stderr=subprocess.STDOUT,
            text=True,
        )

        max_retries = 30
        retry_interval = 5
        dgm_logger.info(
            f"Waiting for executable to initialize (max {max_retries * retry_interval}s)..."
        )

        for i in range(max_retries):
            time.sleep(retry_interval)

            return_code = process.poll()
            if return_code is not None:
                dgm_logger.error(
                    f"Executable exited prematurely with code {return_code}"
                )
                log_file.flush()
                log_file.close()
                log_file = None
                _print_process_log_tail(log_path)
                return False

            try:
                response = requests.get(
                    "http://127.0.0.1:8181/health", timeout=15
                )
                if response.status_code == 200:
                    health_data = response.json()
                    if health_data.get("status") == "healthy":
                        dgm_logger.info(
                            f"Executable health check PASSED on attempt {i + 1}"
                        )
                        if os.path.exists(".runtime") or os.path.exists(
                            "storage/runtime"
                        ):
                            dgm_logger.info(
                                "Runtime directory initialization verified."
                            )
                        else:
                            dgm_logger.warning(
                                "Could not verify .runtime directory, but health is OK."
                            )
                        dgm_logger.info(
                            "Executable validation successful. Terminating..."
                        )
                        process.terminate()
                        try:
                            process.wait(timeout=10)
                        except subprocess.TimeoutExpired:
                            process.kill()
                            process.wait(timeout=5)
                        return True
                    dgm_logger.warning(
                        f"Attempt {i + 1}: Health status: {health_data.get('status')}"
                    )
                else:
                    dgm_logger.warning(
                        f"Attempt {i + 1}: Health check returned {response.status_code}"
                    )
            except requests.exceptions.RequestException as exc:
                dgm_logger.warning(
                    f"Attempt {i + 1}: Failed to connect to executable API: {exc}"
                )

        dgm_logger.error("Max retries reached. Executable failed to become healthy.")
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
        log_file.flush()
        log_file.close()
        log_file = None
        _print_process_log_tail(log_path)
        return False

    except Exception as exc:
        dgm_logger.error(f"Validation failed with error: {exc}")
        if process is not None and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
        if log_file is not None:
            log_file.flush()
            log_file.close()
            log_file = None
        if log_path and os.path.exists(log_path):
            _print_process_log_tail(log_path)
        return False
    finally:
        if log_file is not None:
            log_file.close()
        if log_path and os.path.exists(log_path):
            try:
                os.remove(log_path)
            except OSError:
                pass


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/validate_executable.py <path_to_executable>")
        sys.exit(1)

    success = validate_executable(sys.argv[1])
    sys.exit(0 if success else 1)
