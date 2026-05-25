from typing import List, Dict, Any
from core.provider_memory.models import MemoryNode, MemoryRelationship, MemoryGraph
from core.provider_memory.project_manager import ProjectManager
from core.observability.logger import dgm_logger

class RelationshipManager:
    """
    Manages the graph relationships between provider conversations, repos, and files.
    """
    def __init__(self):
        self.graph = MemoryGraph()

    def add_link(self, source_id: str, target_id: str, relation: str):
        rel = MemoryRelationship(source=source_id, target=target_id, relation_type=relation)
        self.graph.relationships.append(rel)
        dgm_logger.info(f"Memory: Linked {source_id} -> {target_id} ({relation})")

    def register_node(self, node_id: str, node_type: str, metadata: Dict[str, Any] = None):
        node = MemoryNode(id=node_id, type=node_type, metadata=metadata or {})
        self.graph.nodes.append(node)
        return node

    def get_links(self, node_id: str) -> List[MemoryRelationship]:
        return [r for r in self.graph.relationships if r.source == node_id or r.target == node_id]
