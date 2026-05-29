from sqlalchemy import inspect
from core.storage.database import engine
from core.storage.models import Base
from core.observability.logger import dgm_logger
from threading import Lock

_db_init_lock = Lock()
_db_initialized = False

def init_database():
    """
    Initializes the database schema.
    Requirement 42.5.4: Idempotent initialization with explicit logging.
    """
    global _db_initialized

    with _db_init_lock:
        dgm_logger.info("DB_SINGLETON_LOCK_ACQUIRED")

        if _db_initialized:
            dgm_logger.info("DB_SINGLETON_ALREADY_INITIALIZED")
            return

        dgm_logger.info("DB_INIT_STARTED")
        try:
            inspector = inspect(engine)
            existing_tables = set(inspector.get_table_names())
            required_tables = set(Base.metadata.tables.keys())

            if required_tables and required_tables.issubset(existing_tables):
                dgm_logger.info(f"DB_ALREADY_EXISTS: Found {len(existing_tables)} tables.")
                dgm_logger.info("DB_REUSED")
                _db_initialized = True
                return

            Base.metadata.create_all(bind=engine)
            _db_initialized = True
            dgm_logger.info("DB_INIT_COMPLETE")
        except Exception as e:
            # Requirement: Existing storage structures must not trigger critical failure.
            dgm_logger.error(f"DB_INIT_NON_CRITICAL_FAILURE: {e}")
