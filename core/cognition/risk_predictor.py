from typing import List, Dict, Any
from core.cognition.cognition_models import ArchitecturalRisk, RiskLevel
from core.cognition.cognition_graph import CognitionGraph

class RiskPredictor:
    def predict_risks(self, graph: CognitionGraph) -> List[ArchitecturalRisk]:
        risks = []

        # Detect single points of failure (high centrality)
        centrality = graph.calculate_centrality()
        for node_id, score in centrality.items():
            if score > 0.5:
                risks.append(ArchitecturalRisk(
                    risk_id=f"SPOF_{node_id}",
                    description=f"Potential single point of failure: {node_id}",
                    level=RiskLevel.HIGH,
                    affected_components=[node_id] + graph.get_dependents(node_id),
                    remediation="Decouple dependencies or introduce redundancy."
                ))

        # Detect dependency cycles
        cycles = graph.find_cycles()
        if cycles:
            risks.append(ArchitecturalRisk(
                risk_id="CIRCULAR_DEPENDENCY",
                description=f"Circular dependencies detected: {cycles}",
                level=RiskLevel.CRITICAL,
                affected_components=[node for cycle in cycles for node in cycle],
                remediation="Refactor components to break the cycle."
            ))

        return risks
