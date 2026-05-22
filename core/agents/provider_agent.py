from shared.models.event import Event

from core.agents.base_agent import (
    BaseAgent,
)

from core.providers.provider_runtime import (
    ProviderRuntime,
)


class ProviderAgent(BaseAgent):

    def handle_event(
        self,
        event: Event,
    ):

        self.emit_log(
            "Scanning providers..."
        )

        ProviderRuntime().run()
