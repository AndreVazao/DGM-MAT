from pydantic import BaseModel

class RuntimeLimits(BaseModel):
    max_event_depth: int = 20
    max_parallel_repairs: int = 5
    max_browser_contexts: int = 3
    max_worktrees: int = 5
    max_provider_requests_per_min: int = 60
    cpu_degradation_threshold: float = 80.0
    storm_event_count_threshold: int = 100
    storm_time_window_seconds: int = 10
    max_recursion_depth: int = 10
