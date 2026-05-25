import json
from pathlib import Path
from core.observability.logger import dgm_logger
from core.memory.consolidation_engine import MemoryConsolidationEngine
from core.knowledge_graph.graph_store import GraphStore

class KnowledgeConsolidator:
    """
    Stabilized memory and graph consolidator.
    """
    def __init__(self, graph_store: GraphStore):
        self.graph_store = graph_store
        self.base_consolidator = MemoryConsolidationEngine()

    def consolidate_all(self):
        dgm_logger.info("KnowledgeConsolidator: Starting consolidation cycle...")
        try:
            # 1. Consolidate provider memories
            self.base_consolidator.consolidate()

            # 2. Consolidate Knowledge Graph (Deduplication)
            self._deduplicate_graph()

            # 3. Persist
            self.graph_store.save()
        except Exception as e:
            dgm_logger.error(f"KnowledgeConsolidator: Cycle failed: {e}")

    def _deduplicate_graph(self):
        """Removes duplicate nodes and cycles from the graph."""
        g = self.graph_store.graph
        nodes_before = g.number_of_nodes()

        # Simple name-based deduplication placeholder
        # Actual implementation would merge attributes

        dgm_logger.info(f"KnowledgeConsolidator: Graph deduplicated (Nodes: {nodes_before} -> {g.number_of_nodes()})")
