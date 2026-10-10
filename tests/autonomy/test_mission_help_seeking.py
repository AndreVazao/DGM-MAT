# Path: C:\\ProgramasGodMode\\DGM-MAT\\tests\\autonomy\\test_mission_help_seeking.py
"""Integration regression tests for MissionEngine help recommendations."""
from core.autonomy.mission_engine import MissionEngine
from core.organization.message_bus import InternalMessageBus
from core.autonomy.mission_models import Mission, MissionStatus


def test_failed_mission_records_help_recommendation_without_spending(tmp_path, monkeypatch):
    from core.organization.specialist_collaboration import SpecialistCollaborationStore

    engine = MissionEngine(organization_bus=InternalMessageBus())
    engine.collaboration_store = SpecialistCollaborationStore(tmp_path / "failed-mission-handoffs")
    monkeypatch.setattr(engine, "save_mission", lambda mission: None)
    monkeypatch.setattr(engine, "_sync_state", lambda mission: None)
    mission = Mission(
        mission_id="mission_help_policy_test",
        goal="Investigate a failing operation",
        description="Test failure handling",
    )

    engine.active_missions[mission.mission_id] = mission
    result = engine._finish_mission_failure(
        mission, RuntimeError("provider adapter unavailable")
    )

    recommendation = mission.metadata["help_seeking"]
    assert result["error"] == "provider adapter unavailable"
    assert mission.status == MissionStatus.FAILED
    assert recommendation["status"] == "RECOMMENDATION_ONLY"
    assert recommendation["action"] == "INVESTIGATE_FREE"
    assert recommendation["spending_allowed"] is False
    assert "provider adapter unavailable" in recommendation["help_request"]
    assert any("no automatic external call or spending" in entry.lower() for entry in mission.logs)
    handoff = mission.metadata["specialist_collaboration"]
    assert handoff["status"] == "PACKET_PREPARED_NO_EXTERNAL_CALL"
    assert handoff["free_only"] is True
    persisted = engine.collaboration_store.get(handoff["collaboration_id"])
    assert persisted.collaborator == "Claude Code Free"


def test_mission_can_prepare_persistent_free_only_specialist_handoff(tmp_path, monkeypatch):
    from core.organization.specialist_collaboration import (
        CollaborationStatus,
        SpecialistCollaborationStore,
    )

    engine = MissionEngine(organization_bus=InternalMessageBus())
    engine.collaboration_store = SpecialistCollaborationStore(tmp_path / "handoffs")
    monkeypatch.setattr(engine, "save_mission", lambda mission: None)
    monkeypatch.setattr(engine, "_sync_state", lambda mission: None)
    mission = Mission(
        mission_id="mission_specialist_handoff_test",
        goal="Investigate provider execution failure",
        description="The provider adapter failed during a focused test.",
        metadata={
            "project_id": "DGM-MAT",
            "known_facts": ["Local backend remains loopback-only"],
            "help_seeking": {
                "help_request": "Identify the safe next diagnostic step."
            },
        },
        logs=["Ran focused provider tests", "Observed adapter reservation failure"],
    )
    engine.active_missions[mission.mission_id] = mission

    packet = engine.prepare_specialist_collaboration(mission.mission_id)

    assert packet["policy"]["mode"] == "FREE_ONLY"
    assert packet["collaborator"] == "Claude Code Free"
    assert packet["acceptance_criteria"]
    assert mission.metadata["specialist_collaboration"]["status"] == "PACKET_PREPARED_NO_EXTERNAL_CALL"
    assert mission.metadata["specialist_collaboration"]["free_only"] is True
    assert "no external call or spending performed" in mission.logs[-1]
    persisted = engine.collaboration_store.get(packet["collaboration_id"])
    assert persisted.status == CollaborationStatus.PREPARED
    assert "Identify the safe next diagnostic step" in persisted.context
