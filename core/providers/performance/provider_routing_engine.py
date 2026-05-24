from core.observability.logger import dgm_logger

class ProviderRoutingEngine:
    """
    Routes requests to the optimal provider based on task requirements.
    """
    def route_request(self, task_type: str):
        dgm_logger.info(f"ProviderRoutingEngine: Routing task {task_type}")
        if task_type == "coding":
            return "claude-3-5-sonnet"
        return "gpt-4o"
