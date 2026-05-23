import re
from typing import List, Set
from core.observability.logger import dgm_logger

class ConceptExtractor:
    def __init__(self):
        self.keywords = {
            "websocket", "distributed", "mesh", "cognition", "recovery",
            "governance", "provider", "orchestration", "storm", "deadlock",
            "runtime", "repair", "deployment", "repository"
        }

    def extract(self, text: str) -> Set[str]:
        if not text:
            return set()

        words = re.findall(r'\w+', text.lower())
        found = {w for w in words if w in self.keywords}
        if found:
            dgm_logger.debug(f"ConceptExtractor: Extracted {found}")
        return found
