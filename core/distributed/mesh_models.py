from pydantic import BaseModel

class NodeModel(BaseModel):
    id: str
    type: str
    ip: str
    trusted: bool
