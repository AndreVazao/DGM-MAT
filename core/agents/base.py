from typing import Dict, List, Any
from core.event_bus.bus import Event, EventBus

class BaseAgent:
    def __init__(self, agent_id: str, agent_type: str, event_bus: EventBus):
        self.id = agent_id
        self.type = agent_type
        self.bus = event_bus
        self.status = "idle"
        self.input_queue: List[Event] = []
        self.output_queue: List[Event] = []
        self.state: Dict[str, Any] = {"status": "initialized"}

        # Subscribe to tasks targeted at this agent or broadcast
        self.bus.subscribe("task", self._on_task)

    def _on_task(self, event: Event):
        if event.target == self.id or event.target == "broadcast":
            self.input_queue.append(event)
            self._log(f"Received task {event.id}")

    def update(self):
        """Simulate agent lifecycle iteration."""
        if self.input_queue:
            task = self.input_queue.pop(0)
            self._process_task(task)

        # Emit health status periodically or on state change
        self.bus.publish(Event(
            source=self.id,
            type="update",
            payload={"agent_id": self.id, "status": self.status, "state": self.state},
            priority="low"
        ))

    def _process_task(self, task: Event):
        self.status = "busy"
        self._log(f"Processing task {task.id}")

        # Simulation: In real system, this is where work happens
        response_payload = {
            "task_id": task.id,
            "result": f"Simulated execution of {task.type} complete",
            "agent_id": self.id
        }

        response = Event(
            source=self.id,
            target=task.source,
            type="response",
            payload=response_payload,
            priority="medium",
            trace_id=task.trace_id
        )

        self.bus.publish(response)
        self.status = "idle"

    def _log(self, message: str):
        self.bus.publish(Event(
            source=self.id,
            type="log",
            payload={"message": message, "agent_id": self.id},
            priority="low"
        ))
