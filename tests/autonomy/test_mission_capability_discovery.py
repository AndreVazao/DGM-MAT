from core.autonomy.mission_engine import MissionEngine
from core.organization.message_bus import InternalMessageBus


class FakeScout:
    agent_id = "agent:capability-scout"

    def discover(self, capability, reason, mission_id, required_skills=None):
        return {
            "schema": "dgm-mat.capability-scout.v1",
            "agent_id": self.agent_id,
            "request": {
                "request_id": "capability:test",
                "capability": capability,
                "reason": reason,
                "required_skills": required_skills or [],
            },
            "matches": [{"name": "browser-act-skill-forge", "fit_score": 0.9}],
            "overlap_clusters": [],
            "scanned_roots": [],
            "promotion": "not_performed",
            "execution": "not_performed",
        }


def test_mission_engine_routes_explicit_capability_gap_to_scout():
    engine = MissionEngine(organization_bus=InternalMessageBus())
    engine.capability_scout = FakeScout()

    mission = engine.create_mission(
        "Não temos capacidade para browser automation",
        "Precisamos recuperar esta capacidade antes de implementar a missão.",
    )

    capability = engine._capability_request_from_goal(mission.goal)
    assert capability == "browser automation"

    report = engine.discover_capability_for_mission(mission)

    assert report["request"]["capability"] == "browser automation"
    assert mission.metadata["capability_discovery"]["promotion"] == "not_performed"
    assert mission.metadata["capability_discovery"]["execution"] == "not_performed"

    messages = engine.organization_bus.receive("agent:capability-scout")
    assert len(messages) == 1
    assert messages[0].mission_id == mission.mission_id
    assert messages[0].sender_id == "agent:hq-orchestrator"
