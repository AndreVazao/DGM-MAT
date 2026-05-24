from core.observability.logger import dgm_logger

class ProviderAffinity:
    """
    Maps agents to providers based on task type performance.
    """
    def get_preferred_provider(self, agent_role: str):
        # Example: Coding tasks -> Claude, Reasoning -> GPT-4
        return "claude-3-opus"
