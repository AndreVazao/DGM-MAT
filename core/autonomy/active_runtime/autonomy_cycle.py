import uuid
from datetime import datetime
from typing import Dict, Any, List
from pathlib import Path
import json

class AutonomyCycle:
    def __init__(self, cycle_id: str = None):
        self.cycle_id = cycle_id or str(uuid.uuid4())
        self.start_time = datetime.now()
        self.end_time = None
        self.objectives = []
        self.results = []
        self.status = "INITIALIZING"
        self.metadata = {}

    def complete(self):
        self.end_time = datetime.now()
        self.status = "COMPLETED"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cycle_id": self.cycle_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "objectives": self.objectives,
            "results": self.results,
            "status": self.status,
            "metadata": self.metadata
        }

    def persist(self, storage_path: Path):
        path = storage_path / f"cycle_{self.cycle_id}.json"
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)
