from core.agents.base_agent import BaseAgent
from shared.models.event import Event

class RepoAgent(BaseAgent):
    def handle_event(self, event: Event):
        self.emit_log("Managing repository health and structure...")
