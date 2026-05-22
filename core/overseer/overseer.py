import time
import datetime
from typing import Dict, List, Optional, Any
from core.event_bus.bus import Event, EventBus

class Overseer:
    def __init__(self, event_bus: EventBus):
        self.bus = event_bus
        self.active_tasks: Dict[str, Dict] = {} # task_id -> {start_time, timeout, status}
        self.last_heartbeat = datetime.datetime.utcnow()
        self.is_running = False
        self.system_health_score = 1.0
        self.unsafe_operations_paused = False

        # Subscribe to relevant events
        self.bus.subscribe("task", self.on_task_received)
        self.bus.subscribe("response", self.on_response_received)
        self.bus.subscribe("health_update", self.on_health_update)
        self.bus.subscribe("error", self.on_error_received)

    def on_task_received(self, event: Event):
        if self.unsafe_operations_paused and event.priority != "critical":
            self._log_decision(f"Task {event.id} rejected: System in UNSAFE state")
            return

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

    def on_health_update(self, event: Event):
        self.system_health_score = event.payload.get("global_score", 1.0)
        if self.system_health_score < 0.5:
            self._trigger_immune_response("Critical health drop")

    def on_error_received(self, event: Event):
        self._log_decision(f"Overseer analyzing error from {event.source}")
        if event.priority == "critical":
            self._trigger_self_healing(event.payload.get("category", "unknown_failure"), event.payload)

    def monitor_health(self):
        """Check for stalled events and system health."""
        now = datetime.datetime.utcnow()
        self.last_heartbeat = now

        # Heartbeat event
        self.bus.publish(Event(
            source="overseer",
            type="heartbeat",
            payload={"status": "healthy", "timestamp": now.isoformat(), "health_score": self.system_health_score},
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

    def _trigger_immune_response(self, reason: str):
        self.unsafe_operations_paused = True
        self._log_decision(f"IMMUNE RESPONSE TRIGGERED: {reason}. Pausing unsafe operations.")
        self.bus.publish(Event(
            source="overseer",
            type="immune_response",
            payload={"reason": reason, "action": "pause_operations"},
            priority="critical"
        ))

    def _trigger_self_healing(self, failure_type: str, context: Dict[str, Any]):
        self._log_decision(f"Initiating self-healing workflow for {failure_type}")
        self.bus.publish(Event(
            source="overseer",
            type="self_healing_request",
            payload={"failure_type": failure_type, "context": context},
            priority="high"
        ))

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
