from dataclasses import dataclass
from datetime import datetime

@dataclass
class RuntimeState:
    started_at: datetime
    processed_events: int = 0
    active_agents: int = 0
    runtime_status: str = "starting"
