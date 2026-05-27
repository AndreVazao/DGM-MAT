import threading
from typing import Dict, List, Optional
from core.federation.node_identity import NodeIdentity, local_node
from core.observability.logger import dgm_logger

class NodeRegistry:
    """
    Secure registry of known nodes in the federation.
    Phase 42.3-LITE - Federation Preparation.
    """
    def __init__(self):
        self.nodes: Dict[str, NodeIdentity] = {local_node.node_id: local_node}
        self.lock = threading.Lock()

    def register_node(self, identity: NodeIdentity):
        with self.lock:
            self.nodes[identity.node_id] = identity
            dgm_logger.info(f"NodeRegistry: Registered node {identity.node_id} ({identity.hostname})")

    def unregister_node(self, node_id: str):
        with self.lock:
            if node_id in self.nodes:
                del self.nodes[node_id]
                dgm_logger.info(f"NodeRegistry: Unregistered node {node_id}")

    def get_all_nodes(self) -> List[NodeIdentity]:
        with self.lock:
            return list(self.nodes.values())

# Global registry
node_registry = NodeRegistry()
