from pathlib import Path
import os

# Default to Windows path as requested, but allow override for local dev/tests
BASE_PATH = Path(os.getenv("DGM_BASE_PATH", "C:/DevopsGodMode"))

DATA_PATH = BASE_PATH / "data"
DB_PATH = DATA_PATH / "dgm_mat.db"
LOG_PATH = DATA_PATH / "logs"
RUNTIME_PATH = DATA_PATH / "runtime"

API_HOST = "127.0.0.1"
API_PORT = 8181
