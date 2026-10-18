from typing import Any
from core.observability.logger import dgm_logger


class SafetyValidator:
    """Reject patches unless a real, structurally valid diff exists."""

    def validate(self, patch: dict[str, Any]) -> bool:
        if not isinstance(patch, dict):
            dgm_logger.warning("SafetyValidator: Patch candidate is not a mapping.")
            return False

        module = patch.get("module")
        diff = patch.get("diff")
        if not isinstance(module, str) or not module.strip():
            dgm_logger.warning("SafetyValidator: Patch target is missing.")
            return False

        # A placeholder string, a missing diff, or arbitrary text is not a patch.
        if not isinstance(diff, str) or not diff.startswith("diff --git a/"):
            dgm_logger.warning("SafetyValidator: No real unified diff was generated.")
            return False
        if "\n--- a/" not in diff or "\n+++ b/" not in diff:
            dgm_logger.warning("SafetyValidator: Unified diff headers are incomplete.")
            return False

        normalized_target = module.replace("\\", "/")
        if "/" not in normalized_target and not normalized_target.endswith(".py"):
            normalized_target = normalized_target.replace(".", "/")
        if normalized_target.endswith(".py"):
            normalized_target = normalized_target[:-3]
        protected = (
            "core/governance",
            "core/kernel/live_kernel",
            "core/storage/storage_manager",
            "core/self_evolution/safety_validator",
        )
        if any(path in normalized_target for path in protected):
            dgm_logger.error("SafetyValidator: Patch targets a protected subsystem.")
            return False

        risk_score = patch.get("risk_score", 100)
        if not isinstance(risk_score, (int, float)) or risk_score >= 50:
            dgm_logger.warning("SafetyValidator: Patch risk score is missing or too high.")
            return False
        return True
