from dataclasses import dataclass


@dataclass
class AutonomousTask:

    task_id: str

    title: str

    description: str

    priority: int

    assigned_agent: str

    status: str
