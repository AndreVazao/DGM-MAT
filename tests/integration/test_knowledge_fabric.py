import pytest
from shared.models.event import Event
from core.runtime.runtime import Runtime
from core.knowledge.knowledge_models import KnowledgeCategory

def test_knowledge_extraction():
    runtime = Runtime()

    # Event with specific keywords
    payload = {"message": "websocket mesh failure in runtime"}
    event = Event(source="test", target="test", event_type="test.info", payload=payload)

    runtime.knowledge_engine.process_event(event)

    # Check if concepts were extracted
    nodes = runtime.knowledge_engine.temporal_memory.history
    assert len(nodes) > 0
    concepts = nodes[0].metadata.get("concepts", [])
    assert "websocket" in concepts
    assert "mesh" in concepts
    assert "runtime" in concepts

def test_semantic_query():
    runtime = Runtime()
    # Add some knowledge
    event = Event(source="s", target="t", event_type="e", payload={"text": "recovery loop"})
    runtime.knowledge_engine.process_event(event)

    results = runtime.knowledge_engine.query_knowledge("failures")
    # Should return nodes with RUNTIME category
    assert isinstance(results, list)
