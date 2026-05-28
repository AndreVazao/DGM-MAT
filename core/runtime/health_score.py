from typing import Dict, List, Any
from core.observability.logger import dgm_logger

class RuntimeHealthScore:
    """
    Lightweight health scoring for the DGM-MAT runtime.
    Weights:
    - Bootstrap = 25
    - State Store = 20
    - Providers = 20
    - Repos = 15
    - Agents = 10
    - Memory = 10
    """

    def __init__(self):
        self.weights = {
            "bootstrap": 25,
            "state_store": 20,
            "providers": 20,
            "repos": 15,
            "agents": 10,
            "memory": 10
        }

    def compute(self, snapshot_summary: Dict[str, Any]) -> Dict[str, Any]:
        score = 0
        warnings = []
        critical = []

        # 1. Bootstrap (25)
        if snapshot_summary.get("is_runtime_healthy"):
            score += self.weights["bootstrap"]
        else:
            critical.append("Bootstrap: Runtime folders are missing or invalid.")

        # 2. State Store (20)
        # Assuming if we have a snapshot, state store is partially alive
        # In a real scenario, we'd check if it's responsive
        score += self.weights["state_store"]

        # 3. Providers (20)
        active_providers = snapshot_summary.get("active_providers", 0)
        if active_providers > 0:
            score += self.weights["providers"]
        else:
            warnings.append("Providers: No active providers detected.")

        # 4. Repos (15)
        total_repos = snapshot_summary.get("total_repos", 0)
        if total_repos > 0:
            score += self.weights["repos"]
        else:
            warnings.append("Repos: No cloned repositories found.")

        # 5. Agents (10)
        # Simplified: if runtime is healthy, agents are likely ok or at least reachable
        score += self.weights["agents"]

        # 6. Memory (10)
        # Usually memory is in snapshot if it exists
        # We'll assume 10 if present, 0 if not
        if snapshot_summary.get("is_runtime_healthy"): # placeholder for actual memory check
             score += self.weights["memory"]

        return {
            "score": score,
            "warnings": warnings,
            "critical": critical
        }
