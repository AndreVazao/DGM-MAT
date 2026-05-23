from typing import List, Any
from core.knowledge.semantic_graph import SemanticGraph
from core.knowledge.knowledge_models import KnowledgeCategory

class KnowledgeQueryEngine:
    def __init__(self, graph: SemanticGraph):
        self.graph = graph

    def query(self, text: str) -> List[Any]:
        # Simple rule-based query parser
        text = text.lower()
        if "related to" in text:
            node_id = text.split("related to")[-1].strip()
            return self.graph.find_related(node_id)

        if "failures" in text or "errors" in text:
            subgraph = self.graph.get_subgraph_by_category(KnowledgeCategory.RUNTIME)
            return list(subgraph.nodes())

        return []
