import os
import sys
import time
from core.bootstrap import BootstrapEngine
from core.runtime.runtime import Runtime
from core.observability.logger import dgm_logger

def run_smoke_test():
    dgm_logger.info("SMOKE TEST: Starting BootstrapEngine...")
    engine = BootstrapEngine(profile="HEADLESS")
    context = engine.prepare()

    if context.runtime_state != "prepared":
        dgm_logger.error(f"SMOKE TEST: Bootstrap failed with state {context.runtime_state}")
        return False

    dgm_logger.info("SMOKE TEST: Initializing Runtime...")
    runtime = Runtime()

    # We'll simulate a minimal bootstrap without the blocking loops
    # runtime.bootstrap() would start API and loops.
    # For smoke test, we just want to see if it starts and we can publish an event.

    try:
        runtime.event_bus.start()
        dgm_logger.info("SMOKE TEST: Event Bus started.")

        # Execute a dummy task via event
        from shared.models.event import Event
        test_event = Event(
            source="smoke_test",
            target="knowledge",
            event_type="test.ping",
            payload={"message": "hello"}
        )
        runtime.event_bus.publish(test_event)
        dgm_logger.info("SMOKE TEST: Test event published.")

        # Verify health output
        from core.storage.storage_manager import storage_manager
        health_file = storage_manager.get_path("temp", "startup_health.json")
        if not health_file.exists():
            dgm_logger.error("SMOKE TEST: Health file missing.")
            return False

        dgm_logger.info(f"SMOKE TEST: Health file verified at {health_file}")

        dgm_logger.info("SMOKE TEST: Shutting down...")
        runtime.shutdown()
        dgm_logger.info("SMOKE TEST: PASSED")
        return True
    except Exception as e:
        dgm_logger.error(f"SMOKE TEST: FAILED with error: {e}")
        return False

if __name__ == "__main__":
    # Ensure project root is in path
    sys.path.append(os.getcwd())
    success = run_smoke_test()
    sys.exit(0 if success else 1)
