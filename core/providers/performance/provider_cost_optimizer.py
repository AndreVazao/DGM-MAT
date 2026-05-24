from core.observability.logger import dgm_logger

class ProviderCostOptimizer:
    """
    Optimizes provider selection for cost efficiency without sacrificing quality.
    """
    def optimize_cost(self, task_priority: str):
        if task_priority == "low":
            return "local-llama-3"
        return "claude-3-5-sonnet"
