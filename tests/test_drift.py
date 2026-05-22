import sys
import os
from core.event_bus.bus import Event, EventBus
from core.validation.drift import DriftMonitor
from core.observability.logger import EventLogger

def test_drift():
    print("--- TESTING DRIFT MONITOR ---")
    bus = EventBus()
    logger = EventLogger(bus)

    # Force drift: expected satellite not in repo
    monitor = DriftMonitor(bus, "/tmp") # Use empty dir to trigger "missing"
    print("\n[TEST] Checking drift in empty directory...")
    monitor.check_drift({"some_random_agent"})

    # Verify the output in the log
    print("\n--- DRIFT TEST COMPLETE ---")

if __name__ == "__main__":
    test_drift()
