from core.agents.base_agent import BaseAgent
from shared.models.event import Event

class ArchitectAgent(BaseAgent):
    def handle_event(self, event: Event):
        self.emit_log("Architecting system changes...")
