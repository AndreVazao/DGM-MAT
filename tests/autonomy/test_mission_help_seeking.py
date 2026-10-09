# Path: C:\\ProgramasGodMode\\DGM-MAT\\tests\\autonomy\\test_mission_help_seeking.py
"""Integration regression tests for MissionEngine help recommendations."""
from core.autonomy.mission_engine import MissionEngine
from core.autonomy.mission_models import Mission, MissionStatus


def test_failed_mission_records_help_recommendation_without_spending():
    engine = MissionEngine()
    mission = Mission(
        mission_id="mission_help_policy_test",
        goal="Investigate a failing operation",
        description="Test failure handling",
    )

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
