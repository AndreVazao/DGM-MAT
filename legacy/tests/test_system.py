import sys
import os
import time
from core.event_bus.bus import Event, EventBus
from core.validation.engine import ValidationEngine
from core.overseer.overseer import Overseer
from core.agents.base import BaseAgent
from core.observability.logger import EventLogger
from core.validation.drift import DriftMonitor

def run_test():
    print("--- STARTING DGM-MAT CORE INTEGRATION TEST ---")

    # 1. Setup
    bus = EventBus()
    logger = EventLogger(bus)
    validator = ValidationEngine("schemas/event.schema.json")
    bus.set_validation_engine(validator)

    overseer = Overseer(bus)
    agent = BaseAgent("mobile_worker_1", "worker", bus)
    drift_monitor = DriftMonitor(bus, ".")

    # 2. Test Event Flow: Publish a task
    print("\n[TEST] Publishing a valid task...")
    task = Event(
        source="user_interface",
        target="mobile_worker_1",
        type="task",
        payload={"action": "build", "timeout": 2},
        priority="high"
    )
    bus.publish(task)

    # 3. Simulate Loop
    print("\n[TEST] Running system loop iterations...")
    for i in range(3):
        print(f"\n--- Iteration {i+1} ---")
        overseer.run_once()
        agent.update()
        # Drift check
        drift_monitor.check_drift({"mobile_worker_1", "overseer"})

    # 4. Test Validation: Invalid Event
    print("\n[TEST] Publishing an invalid event (invalid priority)...")
    invalid_event = Event(
        source="rogue_agent",
        type="task",
        priority="extreme" # Invalid priority
    )
    bus.publish(invalid_event)

    # 5. Test Timeout Detection
    print("\n[TEST] Simulating a task timeout...")
    timeout_task = Event(
        source="overseer",
        target="unknown_agent",
        type="task",
        payload={"timeout": 0}, # Immediate timeout
        priority="medium"
    )
    bus.publish(timeout_task)
    time.sleep(0.1)
    overseer.run_once()

    print("\n--- TEST COMPLETE ---")

if __name__ == "__main__":
    run_test()
