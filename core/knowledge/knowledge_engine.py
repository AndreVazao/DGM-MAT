from typing import List, Dict, Any
from shared.models.event import Event
from core.knowledge.knowledge_models import KnowledgeNode, KnowledgeEdge, KnowledgeCategory, SemanticSnapshot
from core.knowledge.semantic_graph import SemanticGraph
from core.knowledge.semantic_memory import SemanticMemory
from core.knowledge.concept_extractor import ConceptExtractor
from core.knowledge.context_linker import ContextLinker
from core.knowledge.relationship_inference import RelationshipInference
from core.knowledge.memory_indexer import MemoryIndexer
from core.knowledge.semantic_search import SemanticSearch
from core.knowledge.knowledge_query import KnowledgeQueryEngine
from core.knowledge.temporal_memory import TemporalMemory
from core.knowledge.operational_context import OperationalContext
from core.observability.logger import dgm_logger

class KnowledgeEngine:
    def __init__(self):
        self.graph = SemanticGraph()
        self.memory = SemanticMemory()
        self.concept_extractor = ConceptExtractor()
        self.linker = ContextLinker()
        self.inference = RelationshipInference()
        self.indexer = MemoryIndexer()
        self.search = SemanticSearch(self.indexer)
        self.query_engine = KnowledgeQueryEngine(self.graph)
        self.temporal_memory = TemporalMemory()
        self.operational_context = OperationalContext()

    def process_event(self, event: Event):
        """Defensive ingestion (Requirement 5)."""
        try:
            if not event or not hasattr(event, 'id'):
                return

            payload_str = ""
            try:
                payload_str = str(event.payload)
            except Exception:
                payload_str = "[CORRUPTED PAYLOAD]"

            concepts = self.concept_extractor.extract(payload_str)

            # Defensive field extraction
            event_type = getattr(event, 'event_type', 'unknown')
            source = getattr(event, 'source', 'unknown')
            trace_id = getattr(event, 'trace_id', 'none')
            timestamp = getattr(event, 'timestamp', None)

            node = KnowledgeNode(
                id=f"event_{event.id}",
                category=KnowledgeCategory.RUNTIME,
                name=f"Event: {event_type}",
                metadata={
                    "event_type": event_type,
                    "source": source,
                    "trace_id": trace_id,
                    "concepts": list(concepts)
                },
                timestamp=timestamp if timestamp else None
            )

            self.temporal_memory.add(node)
            self.indexer.index_nodes([node])

            # Link context - Defensively
            try:
                related_nodes = self.temporal_memory.get_recent(hours=1)
                edges = self.linker.link_nodes([node] + related_nodes)
                self.graph.update([node], edges)
            except Exception as exc:
                dgm_logger.error(f"KnowledgeEngine: Graph update failed: {exc}")

            # Periodically persist snapshots
            if len(self.temporal_memory.history) % 50 == 0:
                try:
                    snapshot = SemanticSnapshot(
                        nodes=self.temporal_memory.history[-100:], # Cap snapshot size
                        edges=[] # Simplified
                    )
                    self.memory.persist(snapshot)
                except Exception as exc:
                    dgm_logger.error(f"KnowledgeEngine: Snapshot persistence failed: {exc}")

        except Exception as exc:
            dgm_logger.error(f"KnowledgeEngine: Critical ingestion failure (handled): {exc}")

    def query_knowledge(self, query: str) -> List[Any]:
        return self.query_engine.query(query)

    def shutdown(self):
        self.indexer.shutdown()
