import threading
import time
import sys
import argparse
import os
from core.observability.logger import dgm_logger
from core.observability.trace_utils import trace_runtime_activation

trace_runtime_activation("RUNTIME_ENTRY:main.py")


def run_runtime(profile="FULL"):
    from core.bootstrap import BootstrapEngine
    dgm_logger.info(f"Main: Preparing system via BootstrapEngine (Profile: {profile})...")
    bootstrap_engine = BootstrapEngine(profile=profile)
    trace_runtime_activation("TRACE_RUNTIME_OWNER:BootstrapEngine:core/bootstrap/runtime/bootstrap_engine.py")
    context = bootstrap_engine.prepare()

    if context.runtime_state == "failed":
        dgm_logger.critical("Main: System preparation failed. Exiting.")
        sys.exit(1)

    from core.runtime.runtime import Runtime
    runtime = Runtime()
    trace_runtime_activation("TRACE_RUNTIME_OWNER:Runtime:core/runtime/runtime.py")
    trace_runtime_activation("TRACE_RUNTIME_ACTIVATE:core.runtime.runtime")
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
    parser.add_argument(
        "--cockpit-only",
        action="store_true",
        help="Run only the local chat cockpit; connect to an already running backend.",
    )
    parser.add_argument("--profile", type=str, default="FULL", help="Runtime profile (FULL, HEADLESS, COCKPIT, etc.)")
    args = parser.parse_args()

    if args.cockpit_only and args.headless:
        parser.error("--cockpit-only and --headless cannot be used together")

    # The independent cockpit is a client process. It must never start a second
    # backend or terminate the separately managed headless runtime when closed.
    if args.cockpit_only:
        from cockpit.app import run_cockpit

        dgm_logger.info("Main: Launching independent chat cockpit (backend remains external).")
        trace_runtime_activation("TRACE_RUNTIME_ACTIVATE:cockpit.app:client-only")
        run_cockpit()
        return

    profile = args.profile
    if args.headless or os.getenv("DGM_HEADLESS") == "1":
        profile = "HEADLESS"

    if profile == "HEADLESS":
        run_runtime(profile=profile)
    else:
        try:
            from cockpit.app import run_cockpit

            runtime_thread = threading.Thread(
                target=run_runtime,
                args=(profile,),
                daemon=True,
            )
            runtime_thread.start()

            dgm_logger.info("Main: Launching Cockpit UI...")
            trace_runtime_activation("TRACE_RUNTIME_ACTIVATE:cockpit.app")
            run_cockpit()
        except ImportError as e:
            dgm_logger.error(f"Main: Failed to load Cockpit UI: {e}. Falling back to HEADLESS mode.")
            run_runtime(profile="HEADLESS")


if __name__ == "__main__":
    main()