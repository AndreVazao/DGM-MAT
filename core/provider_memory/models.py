from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class MemoryNode(BaseModel):
    id: str
    type: str  # conversation, file, repository, agent, task
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)

class MemoryRelationship(BaseModel):
    source: str
    target: str
    relation_type: str  # links_to, part_of, created_by, references
    weight: float = 1.0

class MemoryGraph(BaseModel):
    nodes: List[MemoryNode] = Field(default_factory=list)
    relationships: List[MemoryRelationship] = Field(default_factory=list)
