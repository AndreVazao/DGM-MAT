import psutil
from typing import Dict, Any

class ResourceMonitor:
    def get_resource_usage(self) -> Dict[str, Any]:
        return {
            "cpu_percent": psutil.cpu_percent(interval=None),
            "memory_usage_mb": psutil.Process().memory_info().rss / (1024 * 1024),
            "disk_usage_percent": psutil.disk_usage('/').percent
        }
