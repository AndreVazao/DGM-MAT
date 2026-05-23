from typing import List, Dict, Any
from core.cognition.cognition_models import CognitionNode, NodeCategory

class FragmentationDetector:
    def detect(self, nodes: List[CognitionNode]) -> List[Dict[str, Any]]:
        fragmentation_events = []
        repo_names = [n.id for n in nodes if n.category == NodeCategory.REPOSITORY]

        # Simple naming collision/similarity detection
        for i, name1 in enumerate(repo_names):
            for name2 in repo_names[i+1:]:
                similarity = self._calculate_similarity(name1, name2)
                if similarity > 0.8:
                    fragmentation_events.append({
                        "type": "naming_collision",
                        "repos": [name1, name2],
                        "similarity": similarity
                    })

        return fragmentation_events

    def _calculate_similarity(self, s1: str, s2: str) -> float:
        # Placeholder for more complex string similarity
        from difflib import SequenceMatcher
        return SequenceMatcher(None, s1, s2).ratio()
