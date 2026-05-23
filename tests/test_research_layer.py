import pytest
from core.research.research_engine import ResearchEngine
from core.research.research_models import Experiment, ExperimentType, ExperimentStatus

def test_research_execution():
    engine = ResearchEngine()
    exp = Experiment(
        id="EXP-001",
        name="Test Provider Quality",
        type=ExperimentType.PROVIDER_BENCHMARK,
        status=ExperimentStatus.PENDING,
        isolation_id="sandbox-1"
    )
    engine.run_experiment(exp)
    assert exp.status == ExperimentStatus.COMPLETED

def test_isolation_controller():
    from core.research.isolation_controller import IsolationController
    ctrl = IsolationController()
    assert ctrl.prepare_sandbox("test") is True
