from core.node_runtime.node_identity import NodeIdentity
from core.telemetry.metrics_collector import MetricsCollector
import os

def test_node_identity():
    identity = NodeIdentity()
    info = identity.get_identity()
    assert "node_id" in info
    assert info["role"] == "CORE"

def test_telemetry_collection():
    collector = MetricsCollector()
    collector.collect("test_metric", 100)
    assert collector.telemetry_dir.exists()
