import pytest
from core.autonomy.task_generator import TaskGenerator
from core.autonomy.priority_engine import PriorityEngine
from core.autonomy.models import AutonomousTask

def test_task_generation():
    tg = TaskGenerator()
    task = tg.create_task("Test", "Desc", 10, "manual")
    assert task.task_id is not None
    assert task.status == "PENDING"

def test_priority_scoring():
    pe = PriorityEngine()
    task = AutonomousTask(task_id="1", title="T", description="D", priority=0,
                          assigned_agent="A", status="S", origin="failed_execution", risk="HIGH")
    score = pe.calculate_score(task)
    assert score > 90

def test_ranking():
    pe = PriorityEngine()
    tg = TaskGenerator()
    t1 = tg.create_task("T1", "D1", 0, "manual")
    t2 = tg.create_task("T2", "D2", 0, "failed_execution")
    ranked = pe.rank_tasks([t1, t2])
    assert ranked[0].origin == "failed_execution"
