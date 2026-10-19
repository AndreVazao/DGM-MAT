from typing import Any
from core.observability.logger import dgm_logger


class PromotionEngine:
    """Fail-closed promotion boundary until a real, tested promotion flow exists."""

    def promote(self, patch: Any) -> bool:
        """Return False without mutating production; promotion is not implemented."""
        if not isinstance(patch, dict) or not isinstance(patch.get("module"), str) or not patch["module"].strip():
            dgm_logger.warning("PromotionEngine: Invalid patch candidate; promotion refused.")
            return False

        # Never log a promotion as if it happened when no patch application,
        # isolated regression run, rollback path, or approval flow is connected.
        dgm_logger.error(
            f"PromotionEngine: Promotion for {patch['module']} is not implemented; no changes were applied."
        )
        return False
