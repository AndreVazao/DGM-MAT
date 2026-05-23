from typing import List
from core.knowledge.knowledge_models import KnowledgeNode, KnowledgeEdge, RelationshipType
from core.observability.logger import dgm_logger

class RelationshipInference:
    def infer_causality(self, failures: List[KnowledgeNode], events: List[KnowledgeNode]) -> List[KnowledgeEdge]:
        edges = []
        # Simple temporal inference: if an event happened just before a failure
        for failure in failures:
            for event in events:
                time_diff = failure.timestamp - event.timestamp
                if 0 < time_diff.total_seconds() < 5:
                    edges.append(KnowledgeEdge(
                        source=failure.id,
                        target=event.id,
                        relation=RelationshipType.CAUSED_BY,
                        metadata={"time_diff": time_diff.total_seconds()}
                    ))
        if edges:
            dgm_logger.info(f"RelationshipInference: Inferred {len(edges)} causal links.")
        return edges
