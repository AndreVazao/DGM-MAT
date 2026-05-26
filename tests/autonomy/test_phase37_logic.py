import pytest
import asyncio
from core.autonomy.active_runtime.cognition_loop import CognitionLoop
from core.planning.roadmap_engine import RoadmapEngine
from core.model_router.routing_engine import RoutingEngine
from core.self_evolution.safety_validator import SafetyValidator

@pytest.mark.asyncio
async def test_cognition_loop_cycle():
    loop = CognitionLoop()
    # Mocking or adjusting cooldown for test
    loop.cooldown = 0.1
    await loop.run_cycle()
    assert loop.cycle_count == 1

def test_roadmap_persistence():
    engine = RoadmapEngine()
    engine.add_objective("Test Objective", "Desc", "2026-01-01")
    roadmap = engine.get_roadmap()
    assert any(o["title"] == "Test Objective" for o in roadmap["objectives"])

def test_model_routing():
    router = RoutingEngine()
    # Low complexity should pick local small model or remote if none
    model = router.route_task(task_complexity=30)
    assert model in ["phi3", "llama3", "gpt-4o-mini"]

    # High complexity should pick larger model or remote
    model_high = router.route_task(task_complexity=95)
    assert model_high == "gpt-4o-mini"

def test_self_evolution_safety():
    validator = SafetyValidator()
    # Protected module should be rejected
    patch_unsafe = {"module": "core/governance/execution_governor.py", "risk_score": 10}
    assert validator.validate(patch_unsafe) is False

    # High risk should be rejected
    patch_high_risk = {"module": "shared/utils.py", "risk_score": 90}
    assert validator.validate(patch_high_risk) is False

    # Safe patch should be accepted
    patch_safe = {"module": "shared/utils.py", "risk_score": 10}
    assert validator.validate(patch_safe) is True
