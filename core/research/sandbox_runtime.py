from core.research.research_models import Experiment
from core.observability.logger import dgm_logger

class SandboxRuntime:
    def execute(self, experiment: Experiment):
        dgm_logger.info(f"Sandbox executing experiment: {experiment.id}")
        # Isolated execution logic here
