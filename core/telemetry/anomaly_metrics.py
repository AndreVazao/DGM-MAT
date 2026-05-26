from typing import List, Dict, Any
from core.observability.logger import dgm_logger

class AnomalyMetrics:
    def detect_anomalies(self, metrics: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        anomalies = []
        # Basic threshold-based detection
        for m in metrics:
            if m["type"] == "cpu" and m["value"] > 90:
                anomalies.append({"type": "high_cpu", "description": "CPU usage exceeded 90%", "metric": m})
        return anomalies
