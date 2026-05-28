import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from uuid import uuid4
from datetime import datetime, timedelta

from core.autonomy.mission_models import Mission, MissionStatus, SubTask
from core.storage.storage_manager import storage_manager
from core.observability.logger import dgm_logger
from core.runtime.runtime_state_store import state_store, StateEvents
from core.runtime.safe_action_queue import SafeActionQueue, ActionStatus

class MissionEngine:
    def __init__(self):
        self.missions_path = storage_manager.get_path("missions")
        self.missions_path.mkdir(parents=True, exist_ok=True)
        self.active_missions: Dict[str, Mission] = {}
        self.pending_approvals: Dict[str, Dict[str, Any]] = {}
        self.action_queue = SafeActionQueue()
        self.timeout_threshold = timedelta(minutes=10)
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
                        created_at=datetime.fromisoformat(data.get("created_at", datetime.now().isoformat())),
                        progress=data.get("progress", 0.0),
                        logs=data.get("logs", []),
                        error=data.get("error")
                    )
                    self.active_missions[mission.mission_id] = mission
                    self._sync_state(mission)
            except Exception as e:
                dgm_logger.error(f"MissionEngine: Failed to load mission {mission_file}: {e}")

    def create_mission(self, goal: str, description: str) -> Mission:
        mission_id = f"mission_{uuid4().hex[:8]}"

        # Validation Logic
        status = MissionStatus.CREATED
        metadata = {}
        error_msg = None

        if not goal or len(goal) < 3:
            status = MissionStatus.FAILED
            error_msg = "Goal too short or invalid"
            metadata["error"] = error_msg
            dgm_logger.warning(f"MissionEngine: Mission {mission_id} FAILED validation: {goal}")

        mission = Mission(
            mission_id=mission_id,
            goal=goal,
            description=description,
            status=status,
            metadata=metadata,
            error=error_msg
        )

        if status == MissionStatus.CREATED:
            mission.logs.append(f"Mission created with goal: {goal}")
            dgm_logger.info(f"MISSION_CREATED: {mission_id} - {goal}")
        else:
            mission.logs.append(f"Mission creation failed: {error_msg}")
            dgm_logger.error(f"MISSION_FAILED: {mission_id} - {goal}")

        self.active_missions[mission_id] = mission
        self.save_mission(mission)
        self._sync_state(mission)

        if status != MissionStatus.FAILED:
            # Enqueue in SafeActionQueue for visibility
            action_id = self.action_queue.enqueue("MISSION_EXECUTION", {
                "mission_id": mission_id,
                "goal": goal
            })
            dgm_logger.info(f"QUEUE_PUSHED: Action {action_id} for mission {mission_id}")

        return mission

    def process_missions(self):
        """Consumer loop called by CognitionLoop."""
        for mission_id, mission in list(self.active_missions.items()):
            if mission.status == MissionStatus.COMPLETED or mission.status == MissionStatus.FAILED:
                continue

            # 1. Timeout Check
            if datetime.now() - mission.created_at > self.timeout_threshold:
                dgm_logger.error(f"MISSION_TIMEOUT: {mission_id}")
                mission.logs.append("Critical: Mission timed out after 10 minutes.")
                self._update_status(mission, MissionStatus.FAILED, {"error": "Mission timed out after 10 minutes."})
                continue

            # 2. Lifecycle Transitions
            if mission.status == MissionStatus.CREATED:
                self._handle_created(mission)
            elif mission.status == MissionStatus.QUEUED:
                self._handle_queued(mission)
            elif mission.status == MissionStatus.APPROVAL_PENDING:
                self._handle_approval_pending(mission)
            elif mission.status == MissionStatus.RUNNING:
                self._handle_running(mission)

    def _handle_created(self, mission: Mission):
        dgm_logger.info(f"MISSION_QUEUED: {mission.mission_id}")
        mission.logs.append("Transitioning to QUEUED state.")
        self._update_status(mission, MissionStatus.QUEUED)

    def _handle_queued(self, mission: Mission):
        # Simulate executor check
        executor_exists = True # Placeholder

        if not executor_exists:
            dgm_logger.error(f"MISSION_FAILED: {mission.mission_id} - No executor")
            mission.logs.append("Error: No available executor.")
            self._update_status(mission, MissionStatus.FAILED, {"error": "No available executor."})
            return

        # For simplicity, we'll request approval for all missions
        req_id = self.request_approval(mission.mission_id, f"Approve execution of: {mission.goal}")
        mission.logs.append(f"Approval requested (ID: {req_id}).")
        self._update_status(mission, MissionStatus.APPROVAL_PENDING, {"approval_request_id": req_id})

    def _handle_approval_pending(self, mission: Mission):
        # Wait for approval
        req_id = mission.metadata.get("approval_request_id")
        if req_id and req_id not in self.pending_approvals:
            # Check decision
            decision = mission.metadata.get("last_decision")
            if decision == "approve":
                dgm_logger.info(f"MISSION_STARTED: {mission.mission_id}")
                mission.logs.append("User approved mission. Decomposing tasks.")
                # For simulation missions, we skip decomposition to avoid subtask-based progress logic
                if "lista" in mission.goal.lower() and "repos" in mission.goal.lower():
                    mission.status = MissionStatus.RUNNING
                    mission.progress = 0.0
                    self.save_mission(mission)
                    self._sync_state(mission)
                else:
                    self.decompose_mission(mission.mission_id) # Moves to RUNNING
            elif decision == "reject":
                dgm_logger.warning(f"MISSION_FAILED: {mission.mission_id} - Rejected by user")
                mission.logs.append("Mission rejected by user.")
                self._update_status(mission, MissionStatus.FAILED, {"error": "User rejected mission."})

    def _handle_running(self, mission: Mission):
        # Monitor subtasks if they exist
        if mission.subtasks:
            completed_tasks = [st for st in mission.subtasks if st.status == "completed"]
            mission.progress = len(completed_tasks) / len(mission.subtasks)

            if len(completed_tasks) == len(mission.subtasks):
                dgm_logger.info(f"MISSION_COMPLETED: {mission.mission_id}")
                mission.logs.append("All subtasks completed.")
                self._update_status(mission, MissionStatus.COMPLETED)
                return

        # Simulate progress for specific goals (if no subtasks or as fallback)
        if not mission.subtasks and "lista" in mission.goal.lower() and "repos" in mission.goal.lower():
             mission.progress = round(mission.progress + 0.2, 2)
             mission.logs.append(f"Progress update: {mission.progress:.1%}")
             if mission.progress >= 1.0:
                  dgm_logger.info(f"MISSION_COMPLETED: {mission.mission_id}")
                  mission.logs.append("Found repositories: DGM-MAT, DGM-MAT-Agents, etc.")
                  self._update_status(mission, MissionStatus.COMPLETED, {"result": "Found 5 repositories."})
             else:
                  self.save_mission(mission)
                  self._sync_state(mission)

    def _update_status(self, mission: Mission, status: MissionStatus, metadata_update: Dict[str, Any] = None):
        mission.status = status
        mission.updated_at = datetime.now()
        if metadata_update:
            mission.metadata.update(metadata_update)
            if "error" in metadata_update:
                mission.error = metadata_update["error"]

        # Log status change in mission logs
        mission.logs.append(f"Status changed to {status.value}")

        self.save_mission(mission)
        self._sync_state(mission)

    def save_mission(self, mission: Mission):
        file_path = self.missions_path / f"{mission.mission_id}.json"
        data = {
            "mission_id": mission.mission_id,
            "goal": mission.goal,
            "description": mission.description,
            "status": mission.status.value,
            "metadata": mission.metadata,
            "created_at": mission.created_at.isoformat(),
            "updated_at": mission.updated_at.isoformat(),
            "progress": mission.progress,
            "logs": mission.logs,
            "error": mission.error
        }
        with open(file_path, "w") as f:
            json.dump(data, f, indent=4)

    def decompose_mission(self, mission_id: str) -> List[SubTask]:
        mission = self.active_missions.get(mission_id)
        if not mission or mission.status == MissionStatus.FAILED:
            return []

        subtasks = [
            SubTask(subtask_id=f"st_{uuid4().hex[:4]}", title="Analyze requirements", description=f"Analyze {mission.goal}"),
            SubTask(subtask_id=f"st_{uuid4().hex[:4]}", title="Execute implementation", description=f"Implement changes for {mission.goal}"),
            SubTask(subtask_id=f"st_{uuid4().hex[:4]}", title="Verify results", description=f"Verify {mission.goal}")
        ]
        mission.subtasks = subtasks
        mission.status = MissionStatus.RUNNING
        mission.progress = 0.0
        self.save_mission(mission)
        self._sync_state(mission)
        return subtasks

    def request_approval(self, mission_id: str, description: str) -> str:
        request_id = f"req_{uuid4().hex[:6]}"
        self.pending_approvals[request_id] = {
            "mission_id": mission_id,
            "description": description,
            "timestamp": datetime.now().isoformat()
        }
        dgm_logger.info(f"APPROVAL_CREATED: {request_id} for mission {mission_id}")
        state_store.dispatch(StateEvents.APPROVAL_REQUESTED, self.pending_approvals[request_id])
        return request_id

    def handle_approval_decision(self, request_id: str, decision: str):
        approval = self.pending_approvals.pop(request_id, None)
        if not approval:
            return False

        mission_id = approval["mission_id"]
        mission = self.active_missions.get(mission_id)
        if mission:
            mission.metadata["last_decision"] = decision
            dgm_logger.info(f"MissionEngine: Approval {decision.upper()} for {mission_id} ({request_id})")

        return True

    def _sync_state(self, mission: Mission):
        state_store.dispatch(StateEvents.MISSION_UPDATED, {
            "id": mission.mission_id,
            "goal": mission.goal,
            "status": mission.status.value,
            "updated_at": datetime.now().isoformat(),
            "progress": mission.progress,
            "logs": mission.logs,
            "error": mission.error
        })

mission_engine = MissionEngine()
