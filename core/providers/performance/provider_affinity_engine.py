from core.observability.logger import dgm_logger

class ProviderAffinityEngine:
    """
    Manages long-term affinity between specific agents and providers.
    """
    def get_affinity(self, agent_id: str):
        return "claude-3-5-sonnet"
