import os
import subprocess
import sys
import uuid
from core.autonomy.mission_engine import MissionEngine
from core.storage.database import SessionLocal
from core.storage.models import ActionRecord


def test_mission_created_in_one_process_is_executed_in_another():
    marker = f"cross_process_{uuid.uuid4().hex[:10]}"
    engine = MissionEngine()
    mission = engine.create_mission(marker, "Cross-process contract lifecycle")
    action_id = mission.metadata["action_id"]
    child_code = r'''
import os, sys, time
sys.path.insert(0, os.environ["DGM_ROOT"])
sys.path.insert(0, os.environ["DGM_CONTRACTS"])
from core.autonomy.mission_engine import MissionEngine
from core.storage.database import SessionLocal
from core.storage.models import ActionRecord
engine = MissionEngine()
mission_id = os.environ["MISSION_ID"]
assert mission_id in engine.active_missions
queue = engine.action_queue
queue.approve(int(os.environ["ACTION_ID"]), operator="cross_process_test")
queue.start_consumer()
try:
    deadline = time.time() + 15
    while time.time() < deadline:
        with SessionLocal() as session:
            action = session.get(ActionRecord, int(os.environ["ACTION_ID"]))
            if action and action.status == "COMPLETED":
                break
        time.sleep(0.25)
    else:
        raise AssertionError("durable action was not completed")
finally:
    queue.stop_consumer()
'''
    env = os.environ.copy()
    env["DGM_ROOT"] = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    env["DGM_CONTRACTS"] = os.path.join(os.path.dirname(env["DGM_ROOT"]), "DGM-Contracts", "src")
    env["MISSION_ID"] = mission.mission_id
    env["ACTION_ID"] = str(action_id)
    completed = subprocess.run([sys.executable, "-c", child_code], env=env, capture_output=True, text=True, timeout=30)
    assert completed.returncode == 0, completed.stdout + "\n" + completed.stderr
    with SessionLocal() as session:
        action = session.get(ActionRecord, action_id)
        assert action.status == "COMPLETED"
