from typing import Any
from core.agents.base import BaseAgent
from core.event_bus.bus import Event, EventBus

class OverseerAgent(BaseAgent):
    def __init__(self, agent_id: str, event_bus: EventBus):
        super().__init__(agent_id, "overseer", event_bus)
        self.bus.subscribe("update", self._handle_ecosystem_update)
        self.bus.subscribe("error", self._handle_error)

    def _handle_ecosystem_update(self, event: Event):
        self._log(f"Overseer observing update from {event.source}")

    def _handle_error(self, event: Event):
        self._log(f"Overseer handling error from {event.source}: {event.payload.get('error')}", level="error")
        # Trigger recovery logic here

    def execute_logic(self, task: Event) -> Any:
        task_type = task.payload.get("task_type")
        if task_type == "orchestrate":
            return "Orchestration command processed"
        return f"Overseer processed {task_type}"
