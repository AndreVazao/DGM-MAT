from typing import List, Dict, Any
from core.cognition.topology_engine import TopologyEngine
from core.cognition.dependency_mapper import DependencyMapper
from core.cognition.fragmentation_detector import FragmentationDetector
from core.cognition.convergence_engine import ConvergenceEngine
from core.cognition.risk_predictor import RiskPredictor
from core.cognition.impact_analyzer import ImpactAnalyzer
from core.cognition.ecosystem_health import HealthEngine
from core.cognition.architecture_memory import ArchitectureMemory
from core.cognition.cognition_snapshot import CognitionSnapshot
from core.observability.logger import dgm_logger

class EcosystemEngine:
    def __init__(self):
        self.topology_engine = TopologyEngine()
        self.dependency_mapper = DependencyMapper()
        self.fragmentation_detector = FragmentationDetector()
        self.convergence_engine = ConvergenceEngine()
        self.risk_predictor = RiskPredictor()
        self.impact_analyzer = ImpactAnalyzer()
        self.health_engine = HealthEngine()
        self.memory = ArchitectureMemory()

    def perform_cognition(self, repos: List[Dict[str, Any]], agents: List[Dict[str, Any]], providers: List[Dict[str, Any]]) -> CognitionSnapshot:
        dgm_logger.info("Starting ecosystem cognition cycle...")

        # 1. Build Topology
        graph = self.topology_engine.build_topology(repos, agents, providers)

        # 2. Map Dependencies
        # Assuming we can find paths to repos from metadata
        # deps = self.dependency_mapper.map_dependencies(".")
        # graph.update([], deps)

        # 3. Detect Fragmentation
        nodes = [self.topology_engine.graph.graph.nodes[n] for n in self.topology_engine.graph.graph.nodes]
        # (Actually we need CognitionNode objects)
        from core.cognition.cognition_models import CognitionNode, NodeCategory
        c_nodes = [CognitionNode(id=n, category=graph.graph.nodes[n]['category'], metadata=graph.graph.nodes[n]) for n in graph.graph.nodes]

        frag_events = self.fragmentation_detector.detect(c_nodes)

        # 4. Predict Risks
        risks = self.risk_predictor.predict_risks(graph)

        # 5. Convergence Suggestions
        suggestions = self.convergence_engine.suggest_convergence(frag_events)

        # 6. Calculate Health
        health = self.health_engine.calculate_health(risks, len(frag_events))

        # 7. Create Snapshot
        edges = [] # Map from graph edges if needed

        snapshot = CognitionSnapshot(
            nodes=c_nodes,
            edges=[], # Simplified for now
            risks=risks,
            health=health,
            convergence_opportunities=suggestions
        )

        # 8. Record Memory
        self.memory.record_evolution(snapshot)

        dgm_logger.info(f"Cognition cycle complete. Ecosystem Health: {health.overall_health}")
        return snapshot
