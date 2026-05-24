from datetime import datetime
from typing import Optional
from core.ecosystem.ecosystem_models import EcosystemNode, EcosystemStatus
from core.ecosystem.ecosystem_registry import EcosystemRegistry

class EcosystemLifecycle:
    def __init__(self, registry: EcosystemRegistry):
        self.registry = registry

    def provision(self, name: str, role_str: str, description: Optional[str] = None) -> EcosystemNode:
        from core.ecosystem.ecosystem_models import EcosystemRole
        role = EcosystemRole(role_str)
        node = EcosystemNode(
            name=name,
            role=role,
            status=EcosystemStatus.PLANNED,
            description=description
        )
        self.registry.register_node(node)
        self.registry.save()
        return node

    def activate(self, name: str):
        self.registry.update_node(name, status=EcosystemStatus.ACTIVE)

    def deprecate(self, name: str):
        self.registry.update_node(name, status=EcosystemStatus.DEPRECATED)

    def archive(self, name: str):
        self.registry.update_node(name, status=EcosystemStatus.ARCHIVED)

    def health_check(self, name: str, score: float):
        self.registry.update_node(name, health_score=score)
