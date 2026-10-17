from typing import List, Dict, Any, Optional
from core.observability.logger import dgm_logger
from core.provider_mesh.provider_ranker import provider_ranker

class CapabilityRouter:
    """Routes missions based on specialized provider capabilities."""
    def __init__(self):
        pass

    def select_best_provider(self, mission_type: str, preferred: Optional[str] = None) -> Optional[str]:
        """
        Selects the best provider for a given mission type.
        Types: 'coding', 'research', 'autonomy', 'fast_response'
        """
        dgm_logger.info(f"CapabilityRouter: Selecting best provider for mission type: {mission_type}")

        requirement = "reasoning"
        if mission_type == "coding":
            requirement = "coding"
        elif mission_type == "fast_response":
            requirement = "speed"

        ranked = provider_ranker.rank_for_mission(requirement, preferred)
        if ranked:
            return ranked[0]
        return None

# Singleton
capability_router = CapabilityRouter()
