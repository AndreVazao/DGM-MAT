from typing import Dict, List, Any
from core.fabric.resource_models import FabricNode, Workload
from core.observability.logger import dgm_logger

class ResourceFabric:
    """
    Manages civilization-scale resource distribution and cluster execution.
    """
    def __init__(self):
        self.nodes: Dict[str, FabricNode] = {}
        self.active_workloads: Dict[str, Workload] = {}
        self.responsibility_map = self._initialize_responsibility_map()
        dgm_logger.info("Resource Fabric: Initialized.")

    def _initialize_responsibility_map(self) -> Dict[str, str]:
        return {
            "DGM-MAT-Cluster": "distributed execution",
            "DGM-MAT-Memory": "semantic persistence",
            "DGM-MAT-Runtime": "execution kernel",
            "DGM-MAT-Orchestrator": "orchestration authority",
            "DGM-MAT-Agents": "specialization execution",
            "DGM-MAT-OS": "local machine integration"
        }

    def register_node(self, node: FabricNode):
        self.nodes[node.node_id] = node
        dgm_logger.info(f"Resource Fabric: Node registered: {node.node_id}")

    def route_workload(self, workload: Workload) -> str:
        """Routes a workload to the best available node."""
        dgm_logger.info(f"Resource Fabric: Routing workload {workload.workload_id}...")
        return "local-node"

    def get_resource_plan(self) -> Dict[str, Any]:
        return {
            "responsibilities": self.responsibility_map,
            "node_count": len(self.nodes)
        }
