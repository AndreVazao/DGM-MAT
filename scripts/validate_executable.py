import subprocess
import time
import sys
import os
import requests
from core.observability.logger import dgm_logger

def validate_executable(exe_path):
    dgm_logger.info(f"Validating executable at {exe_path}...")

    if not os.path.exists(exe_path):
        dgm_logger.error(f"Executable not found at {exe_path}")
        return False

    # Start the executable in headless mode
    try:
        process = subprocess.Popen(
            [exe_path, "--headless"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Give it some time to boot
        dgm_logger.info("Waiting for executable to initialize...")
        time.sleep(15)

        # Check if process is still running
        if process.poll() is not None:
            stdout, stderr = process.communicate()
            dgm_logger.error(f"Executable exited prematurely with code {process.returncode}")
            dgm_logger.error(f"STDOUT: {stdout}")
            dgm_logger.error(f"STDERR: {stderr}")
            return False

        # Try to hit the health endpoint
        try:
            # Note: API_PORT defaults to 8000 in settings, but might be different.
            # We assume default for validation.
            response = requests.get("http://127.0.0.1:8181/health", timeout=5)
            if response.status_code == 200 and response.json().get("status") == "healthy":
                dgm_logger.info("Executable health check PASSED")
            else:
                dgm_logger.error(f"Executable health check FAILED: {response.status_code} {response.text}")
                process.terminate()
                return False
        except Exception as e:
            dgm_logger.error(f"Failed to connect to executable API: {e}")
            process.terminate()
            return False

        # Verify runtime directories were created
        # (Assuming they are created in the current working directory or .runtime)
        if os.path.exists(".runtime"):
            dgm_logger.info("Runtime directory initialization verified.")
        else:
            dgm_logger.warning("Runtime directory (.runtime) not found, check storage configuration.")

        dgm_logger.info("Executable validation successful. Terminating...")
        process.terminate()
        return True

    except Exception as e:
        dgm_logger.error(f"Validation failed with error: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/validate_executable.py <path_to_executable>")
        sys.exit(1)

    success = validate_executable(sys.argv[1])
    sys.exit(0 if success else 1)
