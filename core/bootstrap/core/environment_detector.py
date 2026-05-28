import platform
import os
import psutil
import shutil
import socket
from core.observability.logger import dgm_logger

def detect_environment():
    return {
        "os": platform.system(),
        "memory_total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
        "cpu_count": os.cpu_count()
    }

def assign_node_role(metadata):
    if metadata["memory_total_gb"] > 16:
        return "DESKTOP_BRAIN"
    return "HEADLESS_NODE"
