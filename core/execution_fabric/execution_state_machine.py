from enum import Enum
from typing import Dict, Any

class ExecutionStatus(Enum):
    PENDING = "pending"
    VALIDATING = "validating"
    SANDBOXING = "sandboxing"
    EXECUTING = "executing"
    PATCHING = "patching"
    COMPLETED = "completed"
    FAILED = "failed"
    RECOVERING = "recovering"

class ExecutionStateMachine:
    """
    Tracks the state transitions of an autonomous execution.
    """
    def __init__(self, execution_id: str):
        self.execution_id = execution_id
        self.status = ExecutionStatus.PENDING
        self.history = []

    def transition_to(self, new_status: ExecutionStatus):
        self.history.append({"from": self.status, "to": new_status})
        self.status = new_status
