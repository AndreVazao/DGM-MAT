from shared.models.event import Event

from core.agents.base_agent import BaseAgent


class RepoAgent(BaseAgent):

    def handle_event(self, event: Event) -> None:

        self.emit_log(
            f"Processing repo event: "
            f"{event.event_type}"
        )
