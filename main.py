import threading
import time
from core.runtime.runtime import Runtime
from cockpit.app import run_cockpit

def run_runtime():
    runtime = Runtime()
    runtime.bootstrap()
    while True:
        time.sleep(1)

def main():
    runtime_thread = threading.Thread(
        target=run_runtime,
        daemon=True,
    )
    runtime_thread.start()

    # Restoring cockpit entry point
    run_cockpit()

if __name__ == "__main__":
    main()
