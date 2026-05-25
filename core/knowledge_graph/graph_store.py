import json
import networkx as nx
from pathlib import Path
from core.observability.logger import dgm_logger

class GraphStore:
    """
    Hardened Knowledge Graph storage with atomic persistence.
    """
    def __init__(self, storage_path: str = ".runtime/knowledge_graph/graph.json"):
        self.path = Path(storage_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.graph = nx.MultiDiGraph()
        self.load()

    def save(self):
        try:
            data = nx.node_link_data(self.graph)
            temp_file = self.path.with_suffix(".tmp")
            temp_file.write_text(json.dumps(data, indent=2))
            temp_file.replace(self.path)
            dgm_logger.info(f"GraphStore: Saved graph to {self.path}")
        except Exception as e:
            dgm_logger.error(f"GraphStore: Failed to save graph: {e}")

    def load(self):
        if not self.path.exists():
            return
        try:
            content = self.path.read_text()
            if not content: return
            data = json.loads(content)
            self.graph = nx.node_link_graph(data)
            dgm_logger.info(f"GraphStore: Loaded graph with {self.graph.number_of_nodes()} nodes")
        except (json.JSONDecodeError, Exception) as e:
            dgm_logger.error(f"GraphStore: Corruption detected on load: {e}")
            # Recovery: Start with empty graph instead of crashing
            self.graph = nx.MultiDiGraph()
