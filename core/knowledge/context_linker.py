from typing import List
from core.knowledge.knowledge_models import KnowledgeNode, KnowledgeEdge, RelationshipType
from core.observability.logger import dgm_logger

class ContextLinker:
    def link_nodes(self, nodes: List[KnowledgeNode]) -> List[KnowledgeEdge]:
        edges = []
        # Link nodes by shared metadata or categories
        for i, node_a in enumerate(nodes):
            for node_b in nodes[i+1:]:
                if node_a.category == node_b.category:
                    edges.append(KnowledgeEdge(
                        source=node_a.id,
                        target=node_b.id,
                        relation=RelationshipType.RELATED_TO,
                        metadata={"reason": "shared_category"}
                    ))

                # Link by concepts in metadata if available
                concepts_a = set(node_a.metadata.get("concepts", []))
                concepts_b = set(node_b.metadata.get("concepts", []))
                if concepts_a & concepts_b:
                    edges.append(KnowledgeEdge(
                        source=node_a.id,
                        target=node_b.id,
                        relation=RelationshipType.RELATED_TO,
                        metadata={"reason": "shared_concepts", "concepts": list(concepts_a & concepts_b)}
                    ))
        return edges
