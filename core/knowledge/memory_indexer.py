import threading
from queue import Queue, Full
from typing import Dict, List
from core.knowledge.knowledge_models import KnowledgeNode
from core.observability.logger import dgm_logger

class MemoryIndexer:
    def __init__(self, queue_size: int = 1000):
        self.index: Dict[str, List[str]] = {} # concept -> list of node_ids
        self.lock = threading.Lock()
        self.queue = Queue(maxsize=queue_size)
        self.running = True
        self.worker_thread = threading.Thread(target=self._index_worker, daemon=True)
        self.worker_thread.start()

    def index_nodes(self, nodes: List[KnowledgeNode]):
        """Non-blocking queue-backed indexing (Requirement 4)."""
        try:
            self.queue.put_nowait(nodes)
        except Full:
            dgm_logger.warning("MemoryIndexer: Indexing queue full! Dropping nodes for backpressure.")

    def _index_worker(self):
        while self.running:
            try:
                nodes = self.queue.get(timeout=1)
                with self.lock:
                    for node in nodes:
                        concepts = node.metadata.get("concepts", [])
                        for concept in concepts:
                            c = concept.lower()
                            if c not in self.index:
                                self.index[c] = []
                            if node.id not in self.index[c]:
                                self.index[c].append(node.id)
                self.queue.task_done()
            except Exception as e:
                dgm_logger.error(f"MemoryIndexer: Error processing nodes: {e}")
                continue

    def search_concept(self, concept: str) -> List[str]:
        with self.lock:
            return self.index.get(concept.lower(), [])

    def shutdown(self):
        self.running = False
