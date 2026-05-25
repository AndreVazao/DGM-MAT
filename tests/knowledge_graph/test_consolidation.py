import pytest
from core.knowledge_graph.graph_store import GraphStore
from core.knowledge_graph.memory_consolidator import KnowledgeConsolidator

def test_knowledge_consolidator():
    consolidator = KnowledgeConsolidator(GraphStore())
    assert consolidator is not None
