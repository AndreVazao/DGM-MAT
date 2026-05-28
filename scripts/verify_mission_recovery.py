import asyncio
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).parent.parent))

from core.autonomy.mission_engine import mission_engine
from core.autonomy.mission_models import MissionStatus
from core.observability.logger import dgm_logger

async def verify_mission_lifecycle():
    dgm_logger.info("Starting Mission Lifecycle Verification...")

    # 1. Create Mission
    goal = "lista as minhas repos"
    mission = mission_engine.create_mission(goal, "Test mission for verification")
    mid = mission.mission_id
    dgm_logger.info(f"Created mission: {mid}")
    assert mission.status == MissionStatus.CREATED
    assert len(mission.logs) > 0

    # 2. Process - Move to QUEUED
    mission_engine.process_missions()
    mission = mission_engine.active_missions[mid]
    dgm_logger.info(f"Status after 1st process: {mission.status}")
    assert mission.status == MissionStatus.QUEUED

    # 3. Process - Move to APPROVAL_PENDING
    mission_engine.process_missions()
    mission = mission_engine.active_missions[mid]
    dgm_logger.info(f"Status after 2nd process: {mission.status}")
    assert mission.status == MissionStatus.APPROVAL_PENDING
    req_id = mission.metadata.get("approval_request_id")
    assert req_id is not None

    # 4. Approve Mission
    dgm_logger.info(f"Approving mission {mid} (Request: {req_id})")
    mission_engine.handle_approval_decision(req_id, "approve")

    # 5. Process - Move to RUNNING
    mission_engine.process_missions()
    mission = mission_engine.active_missions[mid]
    dgm_logger.info(f"Status after approval process: {mission.status}")
    assert mission.status == MissionStatus.RUNNING
    assert mission.progress == 0.0

    # 6. Simulate Execution - Process multiple times to see progress
    for i in range(5):
        mission_engine.process_missions()
        mission = mission_engine.active_missions[mid]
        dgm_logger.info(f"Step {i+1} - Progress: {mission.progress:.1%}, Status: {mission.status}")
        if mission.status == MissionStatus.COMPLETED:
            break

    assert mission.status == MissionStatus.COMPLETED
    assert mission.progress >= 1.0
    dgm_logger.info("Mission Lifecycle Verification SUCCESSFUL.")

if __name__ == "__main__":
    asyncio.run(verify_mission_lifecycle())
