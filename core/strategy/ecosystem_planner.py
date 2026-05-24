from typing import List, Dict, Any
from core.federation.ecosystem_registry import EcosystemRegistry
from core.federation.federation_models import EcosystemStatus

class EcosystemPlanner:
    def __init__(self):
        self.registry = EcosystemRegistry()

    def plan_evolution(self, graph_data: Dict[str, Any]) -> Dict[str, Any]:
        ecosystems = self.registry.get_ecosystems()

        active = [e.id for e in ecosystems if e.status == EcosystemStatus.ACTIVE]
        reserved = [e.id for e in ecosystems if e.status == EcosystemStatus.RESERVED]

        return {
            "current_active_count": len(active),
            "reserved_capacity": len(reserved),
            "expansion_roadmap": reserved[:3], # Suggest next 3 for activation
            "topology_recommendation": "hub-and-spoke-federated"
        }

    def get_strategic_topology(self) -> Dict[str, Any]:
        ecosystems = self.registry.get_ecosystems()
        return {
            "total_defined_ecosystems": len(ecosystems),
            "status_distribution": {
                status.value: len([e for e in ecosystems if e.status == status])
                for status in EcosystemStatus
            }
        }
