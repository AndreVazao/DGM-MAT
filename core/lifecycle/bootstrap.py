from pathlib import Path
from shared.config.settings import (
    DATA_PATH,
    LOG_PATH,
    RUNTIME_PATH,
)
from core.storage.init_db import (
    init_database,
)

def bootstrap_environment():
    Path(DATA_PATH).mkdir(
        parents=True,
        exist_ok=True,
    )
    Path(LOG_PATH).mkdir(
        parents=True,
        exist_ok=True,
    )
    Path(RUNTIME_PATH).mkdir(
        parents=True,
        exist_ok=True,
    )
    init_database()
