from typing import List, Dict, Any

class ConvergenceEngine:
    def suggest_convergence(self, fragmentation_events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        suggestions = []
        for event in fragmentation_events:
            if event['type'] == 'naming_collision':
                suggestions.append({
                    "action": "merge_repos",
                    "target_repos": event['repos'],
                    "reason": f"High naming similarity ({event['similarity']:.2f})"
                })
        return suggestions
