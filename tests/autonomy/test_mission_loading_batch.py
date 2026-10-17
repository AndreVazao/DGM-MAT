from datetime import datetime
from unittest.mock import patch

from core.autonomy.mission_engine import MissionEngine
from core.autonomy.mission_models import Mission, MissionStatus
from core.runtime.runtime_state_store import StateEvents, state_store

def test_mission_load_publishes_one_snapshot_instead_of_per_mission_events(tmp_path):
    engine = MissionEngine()
    engine.missions_path = tmp_path
    engine.active_missions = {}
    for index in range(5):
        mission = Mission(
            mission_id=f"batch-load-{index}",
            goal=f"Batch load mission {index}",
            description="test only",
            status=MissionStatus.FAILED,
            metadata={"source": "test"},
            created_at=datetime.now(),
        )
        engine.active_missions[mission.mission_id] = mission
        engine.save_mission(mission)
    engine.active_missions = {}
    with patch.object(state_store, "dispatch", wraps=state_store.dispatch) as dispatch:
        engine._load_missions()
    event_types = [call.args[0] for call in dispatch.call_args_list]
    assert event_types.count(StateEvents.MISSIONS_RECONCILED) == 1
    assert StateEvents.MISSION_UPDATED not in event_types
    snapshot = state_store.get_snapshot().missions
    for index in range(5):
        assert snapshot[f"batch-load-{index}"]["status"] == "FAILED"
