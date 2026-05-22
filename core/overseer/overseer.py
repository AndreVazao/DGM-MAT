import time
import datetime
from typing import Dict, List, Optional
from core.event_bus.bus import Event, EventBus

class Overseer:
    def __init__(self, event_bus: EventBus):
        self.bus = event_bus
        self.active_tasks: Dict[str, Dict] = {} # task_id -> {start_time, timeout, status}
        self.last_heartbeat = datetime.datetime.utcnow()
        self.is_running = False

        # Subscribe to relevant events
        self.bus.subscribe("task", self.on_task_received)
        self.bus.subscribe("response", self.on_response_received)

    def on_task_received(self, event: Event):
        task_id = event.id
        self.active_tasks[task_id] = {
            "start_time": datetime.datetime.utcnow(),
            "timeout": event.payload.get("timeout", 30),
            "status": "pending",
            "source": event.source
        }
        self._log_decision(f"Task {task_id} assigned by {event.source}")

    def on_response_received(self, event: Event):
        task_id = event.payload.get("task_id")
        if task_id in self.active_tasks:
            self.active_tasks[task_id]["status"] = "completed"
            self._log_decision(f"Task {task_id} completed")
            del self.active_tasks[task_id]

    def monitor_health(self):
        """Check for stalled events and system health."""
        now = datetime.datetime.utcnow()
        self.last_heartbeat = now

        # Heartbeat event
        self.bus.publish(Event(
            source="overseer",
            type="heartbeat",
            payload={"status": "healthy", "timestamp": now.isoformat()},
            priority="low"
        ))

        # Stalled tasks detection
        stalled = []
        for tid, info in self.active_tasks.items():
            elapsed = (now - info["start_time"]).total_seconds()
            if elapsed > info["timeout"]:
                stalled.append(tid)

        for tid in stalled:
            self._trigger_recovery(tid)

    def _trigger_recovery(self, task_id: str):
        self._log_decision(f"Task {task_id} timed out. Triggering recovery.")
        self.bus.publish(Event(
            source="overseer",
            type="error",
            payload={"task_id": task_id, "error": "timeout"},
            priority="high"
        ))
        if task_id in self.active_tasks:
            del self.active_tasks[task_id]

    def _log_decision(self, message: str):
        # Event-driven logging
        self.bus.publish(Event(
            source="overseer",
            type="log",
            payload={"message": message, "category": "decision"},
            priority="medium"
        ))

    def run_once(self):
        """Single loop iteration for the minimal brain."""
        self.monitor_health()
        self.bus.process_queue()
