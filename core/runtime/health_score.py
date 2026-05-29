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
        breakdown = {}
        warnings = []
        critical = []
        degradation_reasons = []

        # 1. Bootstrap & Canonical Paths (25)
        is_healthy = snapshot_summary.get("is_runtime_healthy", False)
        paths_valid = snapshot_summary.get("canonical_paths_valid", False)

        bootstrap_score = 0
        if is_healthy and paths_valid:
            bootstrap_score = self.weights["bootstrap"]
        else:
            if not is_healthy:
                critical.append("Bootstrap: Runtime folders (storage, config, etc) are missing or invalid.")
                degradation_reasons.append("RUNTIME_FOLDERS_MISSING")
            if not paths_valid:
                critical.append("Bootstrap: Canonical paths (C:/DevopGodMode, etc) are missing.")
                degradation_reasons.append("CANONICAL_PATHS_INVALID")

        score += bootstrap_score
        breakdown["bootstrap"] = f"{bootstrap_score}/{self.weights['bootstrap']}"

        # 2. State Store (20)
        # Assuming if we have a summary, state store is alive
        score += self.weights["state_store"]
        breakdown["state_store"] = f"{self.weights['state_store']}/{self.weights['state_store']}"

        # 3. Providers (20)
        active_providers = snapshot_summary.get("active_providers", 0)
        low_memory_profile = snapshot_summary.get("low_memory_profile", False)
        provider_score = 0
        if active_providers > 0:
            provider_score = self.weights["providers"]
        elif low_memory_profile:
            provider_score = self.weights["providers"]
            warnings.append("Providers: Startup provider scan deferred by low-memory profile.")
        else:
            warnings.append("Providers: No active providers detected.")
            degradation_reasons.append("NO_ACTIVE_PROVIDER")

        score += provider_score
        breakdown["providers"] = f"{provider_score}/{self.weights['providers']}"

        # 4. Repos (15)
        total_repos = snapshot_summary.get("total_repos", 0)
        repo_score = 0
        if total_repos > 0:
            repo_score = self.weights["repos"]
        else:
            warnings.append("Repos: No cloned repositories found.")
            degradation_reasons.append("NO_REPOS_FOUND")

        score += repo_score
        breakdown["repos"] = f"{repo_score}/{self.weights['repos']}"

        # 5. Agents (10)
        # Placeholder for agent health logic
        score += self.weights["agents"]
        breakdown["agents"] = f"{self.weights['agents']}/{self.weights['agents']}"

        # 6. Memory (10)
        memory_score = 0
        if snapshot_summary.get("is_runtime_healthy"):
             memory_score = self.weights["memory"]

        score += memory_score
        breakdown["memory"] = f"{memory_score}/{self.weights['memory']}"

        # 7. Queue Health (Bonus or Penalty - not in weights but affects status)
        queue_health = snapshot_summary.get("queue_health", {})
        if not queue_health.get("worker_alive", True):
            critical.append("Queue: SafeActionQueue consumer is DOWN.")
            degradation_reasons.append("QUEUE_CONSUMER_DOWN")
            score = min(score, 49)

        # Requirement 5: Strict consistency.
        if critical:
            score = min(score, 49) # Force score below 50 if critical issues exist
            status = "CRITICAL"
        elif score < 75:
            status = "DEGRADED"
        else:
            status = "NOMINAL"

        return {
            "score": score,
            "status": status,
            "breakdown": breakdown,
            "warnings": warnings,
            "critical": critical,
            "degradation_reasons": degradation_reasons
        }
