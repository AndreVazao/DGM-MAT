from typing import Any
from core.agents.base import BaseAgent
from core.event_bus.bus import Event, EventBus

class ProviderConnectorAgent(BaseAgent):
    def __init__(self, agent_id: str, event_bus: EventBus):
        super().__init__(agent_id, "provider_connector", event_bus)

    def execute_logic(self, task: Event) -> Any:
        provider = task.payload.get("provider")
        session_id = task.payload.get("session_id")

        # Implementation for Task 4
        self.bus.publish(Event(
            source=self.id,
            type="provider_session",
            payload={
                "session_id": session_id,
                "provider": provider,
                "status": "active"
            }
        ))

        return f"Started isolated session for {provider}"
