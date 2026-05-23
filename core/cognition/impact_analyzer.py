from typing import List, Dict, Any
from core.cognition.cognition_graph import CognitionGraph

class ImpactAnalyzer:
    def analyze_impact(self, graph: CognitionGraph, change_target: str) -> Dict[str, Any]:
        affected_nodes = graph.get_dependents(change_target)
        blast_radius = len(affected_nodes)

        return {
            "target": change_target,
            "affected_components": affected_nodes,
            "blast_radius": blast_radius,
            "risk_score": self._calculate_impact_risk(blast_radius)
        }

    def _calculate_impact_risk(self, radius: int) -> float:
        if radius == 0: return 0.0
        if radius < 3: return 0.3
        if radius < 7: return 0.7
        return 1.0
