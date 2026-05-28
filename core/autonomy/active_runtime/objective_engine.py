from typing import List, Dict, Any, Optional
from core.observability.logger import dgm_logger
from core.autonomy.mission_models import Mission, MissionStatus

class ObjectiveEngine:
    """
    Decomposes analysis and active missions into actionable objectives.
    Ensures all mission tasks are flagged for approval.
    """
    def generate_objectives(self, analysis: Dict[str, Any], active_missions: Optional[List[Mission]] = None) -> List[Dict[str, Any]]:
        dgm_logger.info("ObjectiveEngine: Generating objectives.")
        objectives = []

        # 1. Process Repository Gaps
        for gap in analysis.get("detected_gaps", []):
            objectives.append({
                "type": "IMPROVEMENT",
                "target": gap,
                "priority": 70,
                "status": "OPEN",
                "origin": "repo_analysis",
                "approval_required": True
            })

        # 2. Process Active Missions
        if active_missions:
            for mission in active_missions:
                if mission.status == MissionStatus.RUNNING:
                    for st in mission.subtasks:
                        if st.status == "pending":
                            objectives.append({
                                "type": "MISSION_TASK",
                                "mission_id": mission.mission_id,
                                "subtask_id": st.subtask_id,
                                "title": st.title,
                                "description": st.description,
                                "priority": 90,
                                "status": "OPEN",
                                "origin": "mission_system",
                                "approval_required": True
                            })

        return objectives
