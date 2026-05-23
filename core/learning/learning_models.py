from pydantic import BaseModel

class LearningModel(BaseModel):
    id: str
    category: str
    confidence: float
