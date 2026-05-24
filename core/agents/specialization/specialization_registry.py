from core.observability.logger import dgm_logger

class SpecializationRegistry:
    """
    Registry for tracking specialized agent capabilities and roles.
    """
    def __init__(self):
        self.registry = {
            "repository": ["analysis", "restructuring", "cleanup"],
            "execution": ["patching", "validation", "orchestration"],
            "memory": ["semantic_linking", "knowledge_extraction"],
            "research": ["ecosystem_analysis", "benchmarking"]
        }

    def get_agents_by_role(self, role: str):
        return self.registry.get(role, [])

    def register_capability(self, agent_id: str, capability: str):
        dgm_logger.info(f"Registry: Registering capability '{capability}' for agent {agent_id}")
