from core.runtime.safe_action_queue import SafeActionQueue
from dgm_contracts import ExecutionResult


def test_queue_exposes_execution_request_contract():
    queue = SafeActionQueue()
    action_id = queue.enqueue("MISSION_EXECUTION", {"mission_id": "mission_contract", "goal": "contract boundary"})
    request = queue.get_execution_request(action_id)
    assert request.request_id.startswith("exec_")
    assert request.mission_id == "mission_contract"
    assert request.tool_name == "MISSION_EXECUTION"


def test_queue_persists_execution_result_contract():
    queue = SafeActionQueue()
    action_id = queue.enqueue("MISSION_EXECUTION", {"mission_id": "mission_result", "goal": "result boundary"})
    result = ExecutionResult(request_id=f"exec_{action_id}", success=True, status="COMPLETED", message="ok")
    queue.record_execution_result(action_id, result)
    stored = queue.get_action(action_id)
    assert stored is not None
    assert any(entry.get("event") == "EXECUTION_RESULT" for entry in stored["audit_trail"])
