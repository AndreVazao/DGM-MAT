from core.agents.base_agent import BaseAgent
from shared.models.event import Event

class ResearchAgent(BaseAgent):
    def handle_event(self, event: Event):
        self.emit_log("Researching new technologies and benchmarks...")
