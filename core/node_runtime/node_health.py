from typing import Dict, Any

class NodeHealth:
    def get_status(self) -> Dict[str, Any]:
        return {
            "status": "HEALTHY",
            "load": 0.1,
            "uptime": "..."
        }
