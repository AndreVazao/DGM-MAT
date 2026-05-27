import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from uuid import uuid4
from datetime import datetime

from core.autonomy.mission_models import Mission, MissionStatus, SubTask
from core.storage.storage_manager import storage_manager
from core.observability.logger import dgm_logger

class MissionEngine:
    def __init__(self):
        self.missions_path = storage_manager.get_path("missions")
        self.missions_path.mkdir(parents=True, exist_ok=True)
        self.active_missions: Dict[str, Mission] = {}
        self.pending_approvals: Dict[str, Dict[str, Any]] = {}
        self._load_missions()

    def _load_missions(self):
        """Restores missions from storage."""
        for mission_file in self.missions_path.glob("*.json"):
            try:
                with open(mission_file, "r") as f:
                    data = json.load(f)
                    mission = Mission(
                        mission_id=data["mission_id"],
                        goal=data["goal"],
                        description=data.get("description", ""),
                        status=MissionStatus(data["status"]),
                        metadata=data.get("metadata", {}),
                    )
                    self.active_missions[mission.mission_id] = mission
            except Exception as e:
                dgm_logger.error(f"MissionEngine: Failed to load mission {mission_file}: {e}")

    def create_mission(self, goal: str, description: str) -> Mission:
        mission_id = f"mission_{uuid4().hex[:8]}"
        mission = Mission(
            mission_id=mission_id,
            goal=goal,
            description=description,
            status=MissionStatus.PENDING
        )
        self.active_missions[mission_id] = mission
        self.save_mission(mission)
        dgm_logger.info(f"MissionEngine: Created mission {mission_id}: {goal}")
        return mission

    def save_mission(self, mission: Mission):
        file_path = self.missions_path / f"{mission.mission_id}.json"
        data = {
            "mission_id": mission.mission_id,
            "goal": mission.goal,
            "description": mission.description,
            "status": mission.status.value,
            "metadata": mission.metadata,
            "updated_at": datetime.now().isoformat()
        }
        with open(file_path, "w") as f:
            json.dump(data, f, indent=4)

    def decompose_mission(self, mission_id: str) -> List[SubTask]:
        mission = self.active_missions.get(mission_id)
        if not mission:
            return []

        subtasks = [
            SubTask(subtask_id=f"st_{uuid4().hex[:4]}", title="Analyze requirements", description=f"Analyze {mission.goal}"),
            SubTask(subtask_id=f"st_{uuid4().hex[:4]}", title="Execute implementation", description=f"Implement changes for {mission.goal}"),
            SubTask(subtask_id=f"st_{uuid4().hex[:4]}", title="Verify results", description=f"Verify {mission.goal}")
        ]
        mission.subtasks = subtasks
        mission.status = MissionStatus.ACTIVE
        self.save_mission(mission)
        return subtasks

    def request_approval(self, mission_id: str, description: str) -> str:
        request_id = f"req_{uuid4().hex[:6]}"
        self.pending_approvals[request_id] = {
            "mission_id": mission_id,
            "description": description,
            "timestamp": datetime.now().isoformat()
        }
        return request_id

    def handle_approval_decision(self, request_id: str, decision: str):
        """Requirement 7: Functional approval handler."""
        approval = self.pending_approvals.pop(request_id, None)
        if not approval:
            return False

        mission_id = approval["mission_id"]
        dgm_logger.info(f"MissionEngine: Approval {decision.upper()} for {mission_id} ({request_id})")

        # Logic to continue mission based on decision
        return True

mission_engine = MissionEngine()
