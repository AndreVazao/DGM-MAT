import os
import psutil
import time
import platform
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime
from core.observability.logger import dgm_logger
from core.ecosystem.ecosystem_registry import EcosystemRegistry
from core.runtime.runtime_state_store import state_store

class RealitySnapshotService:
    def __init__(self, workspace_root: str = "C:/ProgramasGodMode"):
        self.workspace_root = Path(workspace_root)
        self.registry = EcosystemRegistry()
        self.runtime_root = Path("C:/DevopGodMode")

    def snapshot(self) -> Dict[str, Any]:
        """
        Collects actual observed state.
        """
        dgm_logger.debug("RealitySnapshotService: Capturing snapshot...")
        start_time = time.time()

        try:
            snapshot_data = {
                "timestamp": datetime.now().isoformat(),
                "machine": platform.node(),
                "runtime": self._get_runtime_folders(),
                "providers": self._get_providers_status(),
                "repos": self._get_cloned_repos(),
                "agents": self._get_agent_status(),
                "workspaces": self._get_workspace_state(),
                "processes": self._get_running_processes(),
                "memory": self._get_memory_folders()
            }

            elapsed = time.time() - start_time
            dgm_logger.debug(f"RealitySnapshotService: Snapshot captured in {elapsed:.2f}s")
            return snapshot_data
        except Exception as e:
            dgm_logger.error(f"RealitySnapshotService: Failed to capture snapshot: {e}")
            return {}

    def snapshot_summary(self) -> Dict[str, Any]:
        data = self.snapshot()
        if not data:
            return {"status": "error"}

        return {
            "timestamp": data.get("timestamp"),
            "total_repos": len(data.get("repos", [])),
            "total_processes": len(data.get("processes", [])),
            "active_providers": len([p for p in data.get("providers", []) if p.get("status") == "active"]),
            "is_runtime_healthy": all(v.get("exists") for v in data.get("runtime", {}).values())
        }

    def _get_runtime_folders(self) -> Dict[str, Any]:
        folders = ["runtime", "storage", "config", "logs"]
        result = {}
        for folder in folders:
            path = self.runtime_root / folder
            try:
                exists = path.exists()
                result[folder] = {
                    "path": str(path),
                    "exists": exists,
                    "is_dir": path.is_dir() if exists else False
                }
            except PermissionError:
                result[folder] = {"path": str(path), "exists": False, "is_dir": False, "error": "PermissionDenied"}
        return result

    def _get_providers_status(self) -> List[Dict[str, Any]]:
        # Get from state_store
        snapshot = state_store.get_snapshot()
        providers = []
        for name, data in snapshot.providers.items():
            providers.append({
                "name": name,
                "status": data.get("status", "unknown"),
                "latency": data.get("latency", 0)
            })
        return providers

    def _get_cloned_repos(self) -> List[str]:
        repos = []
        if self.workspace_root.exists():
            try:
                for item in self.workspace_root.iterdir():
                    try:
                        if item.is_dir() and (item / ".git").exists():
                            repos.append(item.name)
                    except PermissionError:
                        continue
            except PermissionError:
                pass

        manual_clones = self.workspace_root / "manual_clones"
        if manual_clones.exists():
            try:
                for item in manual_clones.iterdir():
                    try:
                        if item.is_dir() and (item / ".git").exists():
                            repos.append(f"manual_clones/{item.name}")
                    except PermissionError:
                        continue
            except PermissionError:
                pass
        return repos

    def _get_agent_status(self) -> List[Dict[str, Any]]:
        snapshot = state_store.get_snapshot()
        agents = []
        for agent_id, data in snapshot.agents.items():
            agents.append({
                "id": agent_id,
                "status": data.get("status", "unknown")
            })
        return agents

    def _get_workspace_state(self) -> List[str]:
        # Simple listing of workspace root
        if not self.workspace_root.exists():
            return []
        try:
            return [item.name for item in self.workspace_root.iterdir() if item.is_dir()]
        except PermissionError:
            return []

    def _get_running_processes(self) -> List[Dict[str, Any]]:
        processes = []
        try:
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    name = proc.info.get('name')
                    if name and ("python" in name.lower() or "dgm" in name.lower()):
                        processes.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception:
            pass
        return processes[:50]

    def _get_memory_folders(self) -> Dict[str, Any]:
        memory_root = self.workspace_root / "andreos-memory"
        try:
            exists = memory_root.exists()
            return {
                "path": str(memory_root),
                "exists": exists,
                "is_dir": memory_root.is_dir() if exists else False
            }
        except PermissionError:
            return {"path": str(memory_root), "exists": False, "is_dir": False, "error": "PermissionDenied"}
