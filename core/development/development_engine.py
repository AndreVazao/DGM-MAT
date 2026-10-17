from core.development.feature_planner import FeaturePlanner
from core.development.implementation_engine import ImplementationEngine
from core.development.validation_engine import ValidationEngine
from core.development.execution_fabric import ExecutionFabric
from core.development.development_memory import DevelopmentMemory
from core.observability.logger import dgm_logger

class DevelopmentEngine:
    def __init__(self):
        self.planner = FeaturePlanner()
        self.implementation_engine = ImplementationEngine()
        self.validation_engine = ValidationEngine()
        self.execution_fabric = ExecutionFabric()
        self.memory = DevelopmentMemory()

    def process_request(self, request: str):
        dgm_logger.info(f"DEVELOPMENT ENGINE: New request - {request}")
        plan = self.planner.plan_feature(request)
        self.execution_fabric.dispatch({"id": plan.feature_id, "action": "implement"})

        # In a real scenario, this would be asynchronous
        status = self.implementation_engine.execute_implementation(plan.feature_id)
        self.memory.record_feature(plan.feature_id, status)

        return plan.feature_id
