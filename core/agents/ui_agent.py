from core.agents.base_agent import BaseAgent
from dgm_contracts import Event

class UIAgent(BaseAgent):
    def handle_event(self, event: Event):
        self.emit_log("Optimizing cockpit interface...")
