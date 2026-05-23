from core.storage.storage_manager import storage_manager
from core.storage.init_db import init_database

def bootstrap_environment():
    """
    Bootstraps the runtime environment by ensuring the storage structure
    exists and initializing the database.
    """
    storage_manager._ensure_structure()
    init_database()
