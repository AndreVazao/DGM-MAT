import pytest
from core.self_evolution.self_analysis_engine import SelfAnalysisEngine
from core.self_evolution.architecture_optimizer import ArchitectureOptimizer

def test_self_analysis():
    engine = SelfAnalysisEngine()
    analysis = engine.analyze_self()
    assert "health" in analysis
    assert "weak_points" in analysis

def test_architecture_optimizer():
    optimizer = ArchitectureOptimizer()
    upgrades = optimizer.propose_upgrades({"health": 90})
    assert len(upgrades) > 0
    assert "target" in upgrades[0]
