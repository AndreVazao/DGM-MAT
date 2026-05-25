import pytest
from core.autonomy.self_improvement_planner import improvement_planner
from core.autonomy.task_generator import TaskGenerator
from core.autonomy.priority_engine import PriorityEngine

def test_self_improvement_planning():
    weaknesses = [{"repo": "test_repo", "weakness": "monolith", "impact": "high"}]
    improvement_planner.generate_strategic_goals(weaknesses)
    summary = improvement_planner.get_roadmap_summary()
    assert summary["total_goals"] > 0
    assert "Address bottleneck: monolith" in summary["highest_priority"]

def test_strategic_task_generation():
    tg = TaskGenerator()
    task = tg.create_strategic_task("Improve Graph", "Better visualization", "test_repo")
    assert "STRATEGIC" in task.title
    assert task.metadata["category"] == "strategic"

def test_priority_engine_scoring():
    pe = PriorityEngine()
    from core.autonomy.models import AutonomousTask
    task = AutonomousTask(
        task_id="t1", title="T", description="D", priority=0,
        assigned_agent="A", status="P", origin="strategic_planner",
        metadata={"category": "strategic", "strategic_impact": 0.9, "cognitive_gain": 0.8}
    )
    score = pe.calculate_score(task)
    assert score > 80
