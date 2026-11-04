from datetime import datetime, timedelta, timezone

from core.knowledge.knowledge_models import KnowledgeCategory, KnowledgeNode
from core.knowledge.temporal_memory import TemporalMemory


def _node(timestamp: datetime) -> KnowledgeNode:
    return KnowledgeNode(
        id="event-test",
        category=KnowledgeCategory.RUNTIME,
        name="Test event",
        timestamp=timestamp,
    )


def test_temporal_memory_accepts_timezone_aware_event_timestamp():
    memory = TemporalMemory()
    node = _node(datetime.now(timezone.utc))

    memory.add(node)

    assert memory.get_recent(hours=1) == [node]


def test_temporal_memory_accepts_legacy_naive_event_timestamp():
    memory = TemporalMemory()
    node = _node(datetime.now())

    memory.add(node)

    assert memory.get_recent(hours=1) == [node]


def test_temporal_memory_prunes_old_naive_and_aware_events_consistently():
    memory = TemporalMemory()
    old_aware = datetime.now(timezone.utc) - timedelta(days=31)
    old_naive = old_aware.replace(tzinfo=None)
    current = datetime.now(timezone.utc)

    memory.add(_node(old_aware))
    memory.add(_node(old_naive))
    memory.add(_node(current))

    assert len(memory.history) == 1
    assert memory.get_recent(hours=1) == [memory.history[0]]
