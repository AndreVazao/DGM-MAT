from core.storage.storage_manager import storage_manager
from core.storage.init_db import init_database

def initialize_storage_subsystem():
    storage_manager._ensure_structure()
    init_database()
