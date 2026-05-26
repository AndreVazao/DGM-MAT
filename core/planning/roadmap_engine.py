import json
from typing import List, Dict, Any, Optional
from pathlib import Path
from core.storage.storage_manager import storage_manager
from core.observability.logger import dgm_logger

class RoadmapEngine:
    def __init__(self):
        self.storage_path = storage_manager.get_path("roadmaps")
        self.roadmaps_file = self.storage_path / "global_roadmap.json"
        self._load()

    def _load(self):
        if self.roadmaps_file.exists():
            with open(self.roadmaps_file, "r") as f:
                self.data = json.load(f)
        else:
            self.data = {"objectives": [], "milestones": [], "version": "1.0"}

    def persist(self):
        with open(self.roadmaps_file, "w") as f:
            json.dump(self.data, f, indent=2)
        dgm_logger.info(f"RoadmapEngine: Persisted roadmap to {self.roadmaps_file}")

    def add_objective(self, title: str, description: str, target_date: str):
        objective = {
            "title": title,
            "description": description,
            "target_date": target_date,
            "status": "PLANNED"
        }
        self.data["objectives"].append(objective)
        self.persist()

    def get_roadmap(self) -> Dict[str, Any]:
        return self.data
