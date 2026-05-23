from typing import List
from core.cognition.cognition_models import EcosystemHealthMetrics, ArchitecturalRisk, RiskLevel

class HealthEngine:
    def calculate_health(self, risks: List[ArchitecturalRisk], fragmentation_count: int) -> EcosystemHealthMetrics:
        critical_risks = len([r for r in risks if r.level == RiskLevel.CRITICAL])
        high_risks = len([r for r in risks if r.level == RiskLevel.HIGH])

        stability = max(0.0, 1.0 - (critical_risks * 0.4 + high_risks * 0.1))
        fragmentation_score = max(0.0, 1.0 - (fragmentation_count * 0.05))

        # Simplified metrics
        return EcosystemHealthMetrics(
            fragmentation_score=fragmentation_score,
            duplication_score=fragmentation_score, # tied for now
            stability_score=stability,
            consistency_score=1.0,
            overall_health=(stability + fragmentation_score) / 2
        )
