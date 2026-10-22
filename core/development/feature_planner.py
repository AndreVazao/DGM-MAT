"""Deterministic planning metadata; this module does not implement code changes."""
import hashlib

from core.development.development_models import FeaturePlan, ImplementationStatus


class FeaturePlanner:
    def plan_feature(self, feature_request: str) -> FeaturePlan:
        # Stable IDs survive process restarts and are independent of Python hash randomization.
        normalized_request = feature_request.strip()
        digest = hashlib.sha256(normalized_request.encode("utf-8")).hexdigest()[:20]
        return FeaturePlan(
            feature_id=f"feat_{digest}",
            description=feature_request,
            steps=[{"step": "analyze"}, {"step": "implement"}, {"step": "validate"}],
            assigned_agents=["backend-agent", "testing-agent"],
            estimated_impact=0.5,
            status=ImplementationStatus.PLANNING,
        )
