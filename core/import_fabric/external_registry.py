import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

class ExternalRegistry:
    """
    Manages the registry of external repositories imported into the ecosystem.
    """
    def __init__(self, registry_path: Path = Path(".runtime/external_registry.json")):
        self.registry_path = registry_path
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        self.data: Dict[str, Any] = self._load()

    def _load(self) -> Dict[str, Any]:
        if self.registry_path.exists():
            try:
                with open(self.registry_path, "r") as f:
                    return json.load(f)
            except Exception:
                return {"repositories": {}, "last_updated": None}
        return {"repositories": {}, "last_updated": None}

    def save(self):
        self.data["last_updated"] = datetime.now().isoformat()
        with open(self.registry_path, "w") as f:
            json.dump(self.data, f, indent=2)

    def register_repo(self, name: str, metadata: Dict[str, Any]):
        self.data["repositories"][name] = metadata
        self.save()

    def get_repo(self, name: str) -> Optional[Dict[str, Any]]:
        return self.data["repositories"].get(name)

    def list_repos(self) -> List[str]:
        return list(self.data["repositories"].keys())
