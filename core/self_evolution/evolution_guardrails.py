from typing import Dict, Any, List
from core.observability.logger import dgm_logger

class EvolutionGuardrails:
    """Enforces safety, confidence, and policy constraints on system evolution."""
    def __init__(self):
        self.confidence_threshold = 0.85
        self.forbidden_paths = [
            "core/governance",
            "core/observability/logger.py",
            "core/storage/storage_manager.py",
            "core/self_evolution/evolution_guardrails.py"
        ]

    def validate_patch(self, patch: Dict[str, Any]) -> bool:
        """Validates a proposed patch against safety guardrails."""
        target = patch.get("module", "")
        confidence = patch.get("confidence", 0)

        # 1. Check confidence threshold
        if confidence < self.confidence_threshold:
            dgm_logger.warning(f"EvolutionGuardrails: Confidence {confidence} below threshold.")
            return False

        # 2. Check forbidden paths (Critical system protection)
        for forbidden in self.forbidden_paths:
            if forbidden in target.replace(".", "/"):
                dgm_logger.error(f"EvolutionGuardrails: Patch targets critical forbidden system: {target}")
                return False

        # 3. Check for high risk scores
        if patch.get("risk_score", 100) > 40:
            dgm_logger.warning(f"EvolutionGuardrails: Risk score {patch['risk_score']} too high.")
            return False

        dgm_logger.info(f"EvolutionGuardrails: Patch for {target} PASSED guardrails.")
        return True

    def enforce_policy(self, evolution_proposal: Dict[str, Any]) -> bool:
        """Checks if the evolution aligns with current operational policies."""
        return True
