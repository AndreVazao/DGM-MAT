from typing import List, Dict, Any, Optional
from core.ecosystem.ecosystem_registry import EcosystemRegistry
from core.ecosystem.ecosystem_models import EcosystemRole, EcosystemNode
from core.observability.logger import dgm_logger
from core.repository_intelligence.external_repos import EXTERNAL_REPOSITORIES

class IntelligenceEngine:
    """
    DGM-MAT Intelligence Engine (v2-v4).
    Handles ecosystem scanning, gap detection, and repository scoring.
    """
    def __init__(self, registry: Optional[EcosystemRegistry] = None):
        self.registry = registry or EcosystemRegistry()

    def scan_ecosystem(self) -> Dict[str, List[str]]:
        """
        [v2] Scans the ecosystem to map current capabilities.
        """
        nodes = self.registry.list_nodes()
        capabilities = {}
        for node in nodes:
            role = node.role.value
            if role not in capabilities:
                capabilities[role] = []
            capabilities[role].append(node.name)
        return capabilities

    def detect_gaps(self) -> List[EcosystemRole]:
        """
        [v3] Detects architectural gaps in the ecosystem.
        """
        capabilities = self.scan_ecosystem()
        all_roles = [role for role in EcosystemRole]
        gaps = []

        # Heuristic: If a role has 0 or very few nodes, it's a gap
        for role in all_roles:
            if role.value not in capabilities or len(capabilities[role.value]) < 1:
                gaps.append(role)

        return gaps

    def score_repository(self, name: str, description: str, role: str) -> int:
        """
        [v2] Scores a repository based on its potential fit.
        """
        score = 50 # Base score

        text = (name + " " + (description or "")).lower()

        # Architectural fit scoring
        if role == "core": score += 30
        if role == "finance": score += 25
        if role == "labs": score += 20
        if role == "agents": score += 25
        if role == "memory": score += 20

        # Keyword bonuses
        if any(k in text for k in ["autonomous", "agent", "orchestrator"]): score += 15
        if any(k in text for k in ["llm", "ai", "gpt"]): score += 10

        return min(score, 100)

    def discover_opportunities(self) -> List[Dict[str, Any]]:
        """
        [v4] Global Discovery Layer.
        Suggests repositories to fill detected gaps using the centralized intake list.
        """
        gaps = self.detect_gaps()
        opportunities = []

        # Use the centralized intake list instead of mock data
        for gap in gaps:
            for repo in EXTERNAL_REPOSITORIES:
                if repo["classification"] == gap.value:
                    score = self.score_repository(repo["name"], repo["description"], repo["classification"])
                    opportunities.append({
                        **repo,
                        "score": score,
                        "gap_filled": gap.value
                    })

        return sorted(opportunities, key=lambda x: x["score"], reverse=True)
