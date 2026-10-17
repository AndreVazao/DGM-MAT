from pydantic import BaseModel
from datetime import datetime

class ExecutionTask(BaseModel):
    id: str
    agent_name: str
    status: str
    created_at: datetime = datetime.now()
