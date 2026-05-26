import pytest
from core.cognition.cognitive_analysis_engine import CognitiveAnalysisEngine

@pytest.mark.asyncio
async def test_cognition_engine_init():
    engine = CognitiveAnalysisEngine()
    assert engine is not None
