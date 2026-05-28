from typing import Dict, List, Any
from core.observability.logger import dgm_logger

class RuntimeHealthScore:
    """
    Lightweight health scoring for the DGM-MAT runtime.
    Weights:
    - Bootstrap / Canonical Paths = 25
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

        # 1. Bootstrap & Canonical Paths (25)
        # Requirement: Health system must consume same logic used by bootstrap
        is_healthy = snapshot_summary.get("is_runtime_healthy", False)
        paths_valid = snapshot_summary.get("canonical_paths_valid", False)

        if is_healthy and paths_valid:
            score += self.weights["bootstrap"]
        else:
            if not is_healthy:
                critical.append("Bootstrap: Runtime folders (storage, config, etc) are missing or invalid.")
            if not paths_valid:
                critical.append("Bootstrap: Canonical paths (C:/DevopGodMode, etc) are missing.")

        # 2. State Store (20)
        # Assuming if we have a summary, state store is alive
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
        score += self.weights["agents"]

        # 6. Memory (10)
        if snapshot_summary.get("is_runtime_healthy"):
             score += self.weights["memory"]

        return {
            "score": score,
            "warnings": warnings,
            "critical": critical
        }
