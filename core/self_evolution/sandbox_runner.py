from typing import Any
from core.observability.logger import dgm_logger


class SandboxRunner:
    """Fail closed until real isolated patch application and tests are implemented."""

    async def run(self, patch: dict[str, Any]) -> bool:
        if not isinstance(patch, dict) or not isinstance(patch.get("diff"), str):
            dgm_logger.warning("SandboxRunner: No real patch diff supplied; refusing validation.")
            return False

        # The previous implementation slept for one second and returned True.
        # That was a simulation, not a sandbox, so it must never authorize promotion.
        dgm_logger.error(
            "SandboxRunner: Real isolated patch application and regression tests are not wired; refusing success."
        )
        return False
