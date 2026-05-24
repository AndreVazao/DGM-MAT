import threading
import time
import sys
import argparse
from core.runtime.runtime import Runtime
from core.observability.logger import dgm_logger

def run_runtime():
    dgm_logger.info("Main: Starting Runtime Service...")
    runtime = Runtime()
    runtime.bootstrap()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        dgm_logger.info("Main: Shutdown requested.")
        runtime.shutdown()

def main():
    parser = argparse.ArgumentParser(description="DGM-MAT AI Operating System")
    parser.add_argument("--headless", action="store_true", help="Run in headless mode (no Cockpit UI)")
    args = parser.parse_args()

    if args.headless or os.getenv("DGM_HEADLESS") == "1":
        run_runtime()
    else:
        # Import cockpit only if needed to avoid dependency issues in headless environments
        try:
            from cockpit.app import run_cockpit

            runtime_thread = threading.Thread(
                target=run_runtime,
                daemon=True,
            )
            runtime_thread.start()

            dgm_logger.info("Main: Launching Cockpit UI...")
            run_cockpit()
        except ImportError as e:
            dgm_logger.error(f"Main: Failed to load Cockpit UI: {e}. Falling back to headless mode.")
            run_runtime()

if __name__ == "__main__":
    import os
    main()
