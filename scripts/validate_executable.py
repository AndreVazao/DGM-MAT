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

        # Give it some time to boot with retries
        max_retries = 20
        retry_interval = 5
        dgm_logger.info(f"Waiting for executable to initialize (max {max_retries * retry_interval}s)...")

        for i in range(max_retries):
            time.sleep(retry_interval)

            # Check if process is still running
            if process.poll() is not None:
                stdout, stderr = process.communicate()
                dgm_logger.error(f"Executable exited prematurely with code {process.poll()}")
                dgm_logger.error(f"STDOUT: {stdout}")
                dgm_logger.error(f"STDERR: {stderr}")
                return False

            # Try to hit the health endpoint
            try:
                response = requests.get("http://127.0.0.1:8181/health", timeout=10)
                if response.status_code == 200:
                    health_data = response.json()
                    if health_data.get("status") == "healthy":
                        dgm_logger.info(f"Executable health check PASSED on attempt {i+1}")

                        # Validate deeper state
                        # Check for critical services in health report
                        services = health_data.get("services", {})
                        critical_services = ["daemon", "event_bus", "storage"]
                        for service in critical_services:
                            if services.get(service, {}).get("status") != "active":
                                dgm_logger.error(f"Critical service '{service}' not active: {services.get(service)}")
                                return False

                        # Verify runtime directories were created
                        if os.path.exists(".runtime"):
                            dgm_logger.info("Runtime directory initialization verified.")
                        else:
                            dgm_logger.error("Runtime directory (.runtime) NOT found.")
                            return False

                        dgm_logger.info("Executable deep validation successful. Terminating...")
                        process.terminate()
                        return True
                    else:
                        dgm_logger.warning(f"Attempt {i+1}: Health status: {health_data.get('status')}")
                else:
                    dgm_logger.warning(f"Attempt {i+1}: Health check returned {response.status_code}")
            except requests.exceptions.RequestException as e:
                dgm_logger.warning(f"Attempt {i+1}: Failed to connect to executable API: {e}")

        dgm_logger.error("Max retries reached. Executable failed to become healthy.")
        process.terminate()
        return False

    except Exception as e:
        dgm_logger.error(f"Validation failed with error: {e}")
        if 'process' in locals() and process.poll() is None:
            process.terminate()
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/validate_executable.py <path_to_executable>")
        sys.exit(1)

    success = validate_executable(sys.argv[1])
    sys.exit(0 if success else 1)
