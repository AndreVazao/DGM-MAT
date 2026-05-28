from typing import Dict, List, Any
from datetime import datetime
from enum import Enum

class DiffSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFORMATIONAL = "informational"

class RealityDiffEngine:
    """
    Compares desired state vs observed state and outputs drift information.
    Pure functions preferred, deterministic output, no side effects.
    """

    def diff(self, desired: Dict[str, Any], observed: Dict[str, Any]) -> List[Dict[str, Any]]:
        drifts = []

        # Check Runtime Folders
        desired_runtime = desired.get("runtime", {})
        observed_runtime = observed.get("runtime", {})
        for folder, d_state in desired_runtime.items():
            o_state = observed_runtime.get(folder, {})
            if not o_state.get("exists"):
                drifts.append({
                    "type": "runtime_drift",
                    "item": folder,
                    "severity": DiffSeverity.CRITICAL,
                    "message": f"Critical runtime folder missing: {folder}"
                })

        # Check Repos
        desired_repos = set(desired.get("repos", []))
        observed_repos = set(observed.get("repos", []))

        missing_repos = desired_repos - observed_repos
        for repo in missing_repos:
            drifts.append({
                "type": "missing_repo",
                "item": repo,
                "severity": DiffSeverity.HIGH,
                "message": f"Required repository missing: {repo}"
            })

        orphan_repos = observed_repos - desired_repos
        for repo in orphan_repos:
            drifts.append({
                "type": "orphan_repo",
                "item": repo,
                "severity": DiffSeverity.INFORMATIONAL,
                "message": f"Unregistered repository found: {repo}"
            })

        # Check Providers
        desired_providers = desired.get("providers", [])
        observed_providers = {p.get("name"): p for p in observed.get("providers", [])}

        for p_name in desired_providers:
            if p_name not in observed_providers:
                drifts.append({
                    "type": "missing_provider",
                    "item": p_name,
                    "severity": DiffSeverity.MEDIUM,
                    "message": f"Required provider not configured: {p_name}"
                })
            elif observed_providers[p_name].get("status") != "active":
                drifts.append({
                    "type": "provider_inactive",
                    "item": p_name,
                    "severity": DiffSeverity.MEDIUM,
                    "message": f"Provider is not active: {p_name}"
                })

        # Check Memory
        desired_memory = desired.get("memory", {})
        observed_memory = observed.get("memory", {})
        if desired_memory.get("required") and not observed_memory.get("exists"):
            drifts.append({
                "type": "memory_missing",
                "item": "andreos-memory",
                "severity": DiffSeverity.HIGH,
                "message": "Strategic memory folder missing."
            })

        # Sort drifts by severity (Critical first)
        severity_map = {
            DiffSeverity.CRITICAL: 0,
            DiffSeverity.HIGH: 1,
            DiffSeverity.MEDIUM: 2,
            DiffSeverity.LOW: 3,
            DiffSeverity.INFORMATIONAL: 4
        }
        drifts.sort(key=lambda x: (severity_map.get(x["severity"], 99), x["type"], x["item"]))

        return drifts
