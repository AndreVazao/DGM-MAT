import concurrent.futures
from typing import List, Dict
from core.knowledge.knowledge_models import KnowledgeNode
from core.knowledge.memory_indexer import MemoryIndexer
from core.observability.logger import dgm_logger

class SemanticSearch:
    def __init__(self, indexer: MemoryIndexer):
        self.indexer = indexer
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)

    def find_nodes(self, query: str, nodes: List[KnowledgeNode], limit: int = 50) -> List[KnowledgeNode]:
        """Bounded search with timeout (Requirement 10)."""
        try:
            future = self.executor.submit(self._run_search, query, nodes, limit)
            return future.result(timeout=1.0) # 1s max search
        except Exception as exc:
            dgm_logger.error(f"SemanticSearch: Search failure: {exc}")
            return []

    def _run_search(self, query: str, nodes: List[KnowledgeNode], limit: int) -> List[KnowledgeNode]:
        query = query.lower()
        results = []

        node_ids = self.indexer.search_concept(query)

        for node in nodes:
            if len(results) >= limit:
                break

            if node.id in node_ids:
                results.append(node)
                continue

            if query in node.name.lower() or query in node.id.lower():
                results.append(node)

        return results
