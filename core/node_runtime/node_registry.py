from typing import Dict, Any, List

class NodeRegistry:
    def __init__(self):
        self.nodes: Dict[str, Dict[str, Any]] = {}

    def register_node(self, identity: Dict[str, Any], capabilities: List[str]):
        node_id = identity["node_id"]
        self.nodes[node_id] = {
            "identity": identity,
            "capabilities": capabilities,
            "status": "ONLINE"
        }

    def get_available_nodes(self) -> List[str]:
        return [nid for nid, info in self.nodes.items() if info["status"] == "ONLINE"]
