import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import core.runtime.safe_action_queue as safe_action_queue_module
from core.runtime.safe_action_queue import SafeActionQueue
from core.storage.database import Base
from dgm_contracts import ExecutionResult


@pytest.fixture
def isolated_queue(tmp_path, monkeypatch):
    """Keep contract tests away from the developer's persistent runtime queue."""
    engine = create_engine(
        f"sqlite:///{tmp_path / 'queue-boundary.sqlite3'}",
        connect_args={"check_same_thread": False},
        future=True,
    )
    Base.metadata.create_all(bind=engine)
    test_session_local = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
    )

    monkeypatch.setattr(safe_action_queue_module, "SessionLocal", test_session_local)
    monkeypatch.setattr(
        safe_action_queue_module,
        "init_database",
        lambda: Base.metadata.create_all(bind=engine),
    )
    monkeypatch.setattr(SafeActionQueue, "_instance", None)

    queue = SafeActionQueue()
    yield queue

    queue.stop_consumer()
    engine.dispose()


def test_queue_exposes_execution_request_contract(isolated_queue):
    action_id = isolated_queue.enqueue(
        "MISSION_EXECUTION",
        {"mission_id": "mission_contract", "goal": "contract boundary"},
    )
    request = isolated_queue.get_execution_request(action_id)

    assert request.request_id.startswith("exec_")
    assert request.mission_id == "mission_contract"
    assert request.tool_name == "MISSION_EXECUTION"


def test_queue_persists_execution_result_contract(isolated_queue):
    action_id = isolated_queue.enqueue(
        "MISSION_EXECUTION",
        {"mission_id": "mission_result", "goal": "result boundary"},
    )
    result = ExecutionResult(
        request_id=f"exec_{action_id}",
        success=True,
        status="COMPLETED",
        message="ok",
    )
    isolated_queue.record_execution_result(action_id, result)
    stored = isolated_queue.get_action(action_id)

    assert stored is not None
    assert any(entry.get("event") == "EXECUTION_RESULT" for entry in stored["audit_trail"])
