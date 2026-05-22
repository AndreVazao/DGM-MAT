from typing import Dict, List, Any, Optional
import datetime
import uuid
from core.event_bus.bus import Event, EventBus

class BaseAgent:
    def __init__(self, agent_id: str, agent_type: str, event_bus: EventBus):
        self.id = agent_id
        self.type = agent_type
        self.bus = event_bus
        self.status = "idle"
        self.input_queue: List[Event] = []
        self.capabilities: List[str] = []
        self.state: Dict[str, Any] = {
            "status": "initialized",
            "last_update": datetime.datetime.utcnow().isoformat(),
            "capabilities": self.capabilities
        }

        # Subscribe to tasks targeted at this agent or broadcast
        self.bus.subscribe("task", self._on_task)
        # Subscribe to knowledge integration for dynamic upgrades
        self.bus.subscribe("knowledge_integrated", self._handle_upgrade)

    def _on_task(self, event: Event):
        if event.target == self.id or event.target == "broadcast":
            self.input_queue.append(event)
            self._log(f"Received task {event.id} of type {event.payload.get('task_type')}")

    def _handle_upgrade(self, event: Event):
        """Dynamic agent capability upgrade."""
        if event.payload.get("original_agent") == self.id or event.payload.get("type") == "agent_capability":
            new_capability = event.payload.get("solution")
            if new_capability and new_capability not in self.capabilities:
                self.capabilities.append(new_capability)
                self.state["capabilities"] = self.capabilities
                self._log(f"Agent {self.id} upgraded with new capability: {new_capability[:50]}...")

                # Report evolution
                self.bus.publish(Event(
                    source=self.id,
                    type="agent_upgraded",
                    payload={
                        "agent_id": self.id,
                        "new_capability": new_capability,
                        "is_evolution": True
                    },
                    priority="medium"
                ))

    def update(self):
        """Active agent lifecycle iteration."""
        if self.input_queue:
            task = self.input_queue.pop(0)
            self._process_task(task)

        self._report_state()

    def _report_state(self):
        """Report agent state to the ecosystem state engine via events."""
        self.bus.publish(Event(
            source=self.id,
            type="agent_update",
            payload={
                "agent_id": self.id,
                "type": self.type,
                "status": self.status,
                "state": self.state
            },
            priority="low"
        ))

    def _process_task(self, task: Event):
        self.status = "busy"
        task_type = task.payload.get("task_type")
        self._log(f"Processing task {task.id} ({task_type})")

        # Concrete agents will override this or register handlers
        result = self.execute_logic(task)

        response = Event(
            source=self.id,
            target=task.source,
            type="response",
            payload={
                "task_id": task.id,
                "result": result,
                "agent_id": self.id,
                "status": "success" if result else "failure"
            },
            priority="medium",
            trace_id=task.trace_id
        )

        self.bus.publish(response)

        # Snapshot state after task
        self.persist_memory_snapshot()

        self.status = "idle"

    def execute_logic(self, task: Event) -> Any:
        """Override in subclasses to implement real logic."""
        return f"Base logic executed for {task.id}"

    def persist_memory_snapshot(self):
        """Emit an event to trigger a memory snapshot by the Memory Sync Agent."""
        self.bus.publish(Event(
            source=self.id,
            type="memory_snapshot_request",
            payload={
                "agent_id": self.id,
                "category": f"agent_state_{self.type}",
                "data": self.state
            },
            priority="medium"
        ))

    def _log(self, message: str, level: str = "info"):
        self.bus.publish(Event(
            source=self.id,
            type="log",
            payload={"message": message, "agent_id": self.id, "level": level},
            priority="low"
        ))
