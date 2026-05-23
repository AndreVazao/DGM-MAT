from pydantic import BaseModel
from typing import Dict, List, Any

class ProviderMetrics(BaseModel):
    response_quality: float
    architecture_quality: float
    stability: float
    hallucination_rate: float
    latency_ms: float
    token_efficiency: float

class BenchmarkResult(BaseModel):
    provider_id: str
    model_name: str
    metrics: ProviderMetrics
    timestamp: Any
