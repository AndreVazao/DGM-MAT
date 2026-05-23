import os
from pathlib import Path
from core.storage.storage_manager import storage_manager

# Dynamic base path resolution from the central storage manager
BASE_PATH = storage_manager.base_path

# Data paths now use storage_manager domains
DATA_PATH = BASE_PATH
DB_PATH = storage_manager.get_path("temp", "dgm_mat.db")
LOG_PATH = storage_manager.get_path("logs")
RUNTIME_PATH = storage_manager.get_path("temp")

API_HOST = os.getenv("DGM_API_HOST", "127.0.0.1")
API_PORT = int(os.getenv("DGM_API_PORT", 8181))
