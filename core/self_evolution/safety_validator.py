from typing import Dict, Any
from core.observability.logger import dgm_logger

class SafetyValidator:
    def validate(self, patch: Dict[str, Any]) -> bool:
        # Check against protected modules
        protected = ["core/governance", "core/kernel/live_kernel.py"]
        if any(p in patch["module"] for p in protected):
            dgm_logger.error(f"SafetyValidator: Patch targets protected module {patch['module']}")
            return False
        return patch["risk_score"] < 50
