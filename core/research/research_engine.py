from typing import List, Dict, Any
from core.research.experimentation_engine import ExperimentationEngine
from core.research.sandbox_runtime import SandboxRuntime
from core.research.isolation_controller import IsolationController
from core.research.research_models import Experiment, ExperimentStatus
from core.observability.logger import dgm_logger

class ResearchEngine:
    def __init__(self):
        self.experiment_engine = ExperimentationEngine()
        self.sandbox = SandboxRuntime()
        self.isolation = IsolationController()

    def run_experiment(self, experiment: Experiment):
        dgm_logger.info(f"Initiating research experiment: {experiment.name}")

        # Ensure isolation
        if self.isolation.prepare_sandbox(experiment.isolation_id):
            try:
                self.sandbox.execute(experiment)
                experiment.status = ExperimentStatus.COMPLETED
            except Exception as exc:
                dgm_logger.error(f"Experiment {experiment.id} failed: {exc}")
                experiment.status = ExperimentStatus.FAILED
            finally:
                self.isolation.cleanup(experiment.isolation_id)
        else:
            dgm_logger.error("Failed to secure isolation for experiment.")
            experiment.status = ExperimentStatus.FAILED
