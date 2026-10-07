from dgm_contracts import Event, NullProviderService, ProviderService

from core.agents.base_agent import BaseAgent


class ProviderAgent(BaseAgent):
    def __init__(self, agent_id: str, logger=None, provider_service: ProviderService | None = None):
        super().__init__(agent_id, logger)
        self.provider_service = provider_service or NullProviderService()

    def handle_event(
        self,
        event: Event,
    ):

        self.emit_log(
            "Scanning providers..."
        )

        self.provider_service.run()
