import pytest
from core.strategy.strategy_engine import StrategyEngine
from core.strategy.roadmap_models import StrategicObjective, PlanningHorizon, PriorityCategory

def test_strategy_generation():
    engine = StrategyEngine()
    objective = StrategicObjective(
        id="OBJ-001",
        title="Stabilize Mesh",
        description="Ensure all nodes are connected",
        horizon=PlanningHorizon.SHORT,
        priority=PriorityCategory.CRITICAL
    )
    engine.roadmap_engine.add_objective(objective)

    snapshot = engine.generate_strategy({"health": 0.9})
    assert snapshot.sustainability_index == 0.85
    assert len(snapshot.active_objectives) == 1
    assert snapshot.active_objectives[0].id == "OBJ-001"

def test_debt_prediction_placeholder():
    from core.strategy.debt_predictor import DebtPredictor
    predictor = DebtPredictor()
    debt = predictor.forecast_debt({})
    assert isinstance(debt, list)
