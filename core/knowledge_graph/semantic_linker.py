from typing import List, Tuple
from core.observability.logger import dgm_logger

class SemanticLinker:
    """
    Bounded semantic linker to prevent memory explosion.
    """
    def __init__(self, max_links_per_node: int = 50):
        self.max_links = max_links_per_node

    def link_entities(self, source_id: str, target_ids: List[str]) -> List[Tuple[str, str, str]]:
        links = []
        # Hard cap on links to prevent recursive explosion
        for target_id in target_ids[:self.max_links]:
            links.append((source_id, target_id, "related_to"))

        if len(target_ids) > self.max_links:
            dgm_logger.warning(f"SemanticLinker: Capped links for {source_id} at {self.max_links}")

        return links
