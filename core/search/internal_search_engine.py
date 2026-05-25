import json
import os
from typing import Dict, Any, List, Optional
from pathlib import Path

from core.storage.storage_manager import storage_manager
from core.observability.logger import dgm_logger

class InternalSearchEngine:
    """
    Provides semantic and keyword search capabilities across:
    - Memories
    - Repositories
    - Provider Knowledge
    - Architecture Graphs
    - Reports
    - Patterns
    - Tasks
    - Execution History
    """
    def __init__(self):
        self.storage = storage_manager
        # In a real implementation, this would use a vector DB like Chroma or FAISS.
        # For this local-first baseline, we implement a multi-domain keyword index.
        self.index: Dict[str, List[Dict[str, Any]]] = {}

    def index_domain(self, domain: str):
        """Indexes all files in a specific storage domain."""
        dgm_logger.info(f"InternalSearchEngine: Indexing domain {domain}...")
        path = self.storage.get_path(domain)
        if not path.exists():
            return

        domain_items = []
        for file in path.glob("*.json"):
            try:
                content = json.loads(file.read_text(encoding="utf-8"))
                domain_items.append({
                    "id": file.stem,
                    "content": str(content),
                    "path": str(file)
                })
            except Exception as e:
                dgm_logger.error(f"InternalSearchEngine: Failed to index {file}: {e}")

        self.index[domain] = domain_items
        dgm_logger.info(f"InternalSearchEngine: Indexed {len(domain_items)} items in {domain}")

    def search(self, query: str, domains: Optional[List[str]] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Searches across specified domains (or all) for a query string."""
        results = []
        target_domains = domains or list(self.index.keys())
        query = query.lower()

        for domain in target_domains:
            if domain not in self.index:
                self.index_domain(domain)

            for item in self.index.get(domain, []):
                if query in item["content"].lower():
                    results.append({
                        "domain": domain,
                        "id": item["id"],
                        "path": item["path"],
                        "score": self._calculate_relevance(query, item["content"])
                    })

        # Sort by score
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:limit]

    def _calculate_relevance(self, query: str, content: str) -> float:
        # Simple keyword frequency / position scoring
        content_lower = content.lower()
        count = content_lower.count(query)
        if count == 0: return 0.0

        # Bonus for query at the beginning
        score = count * 1.0
        if content_lower.startswith(query):
            score += 2.0

        return score

    def refresh_all(self):
        """Refreshes indexes for all domains."""
        domains = ["memory", "cognition", "federation", "graphs", "patterns", "tasks", "evolution_memory", "provider_knowledge"]
        for d in domains:
            self.index_domain(d)

# Singleton instance
internal_search = InternalSearchEngine()
