from typing import Dict, List, Any
from core.knowledge.knowledge_models import KnowledgeNode
from core.observability.logger import dgm_logger

class OperationalContext:
    def __init__(self):
        self.active_context: Dict[str, Any] = {}

    def update(self, key: str, value: Any):
        self.active_context[key] = value

    def get_summary(self) -> str:
        summary = "OPERATIONAL CONTEXT:\n"
        for k, v in self.active_context.items():
            summary += f"- {k}: {v}\n"
        return summary

    def reconstruct_failure_context(self, failure_node: KnowledgeNode, related_nodes: List[KnowledgeNode]) -> str:
        ctx = f"FAILURE CONTEXT for {failure_node.id}:\n"
        ctx += f"- Type: {failure_node.category}\n"
        ctx += f"- Related events: {[n.id for n in related_nodes]}\n"
        return ctx
