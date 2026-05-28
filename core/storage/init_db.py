from sqlalchemy import inspect
from core.storage.database import engine
from core.storage.models import Base
from core.observability.logger import dgm_logger

def init_database():
    """
    Initializes the database schema.
    Requirement 42.5.4: Idempotent initialization with explicit logging.
    """
    dgm_logger.info("DB_INIT_STARTED")
    try:
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()

        if existing_tables:
            dgm_logger.info(f"DB_ALREADY_EXISTS: Found {len(existing_tables)} tables.")
            dgm_logger.info("DB_REUSED")

        # SQLAlchemy's create_all is naturally idempotent, but we wrap it for safety
        Base.metadata.create_all(bind=engine)
        dgm_logger.info("DB_INIT_COMPLETE")
    except Exception as e:
        # Requirement: Existing storage structures must not trigger critical failure.
        dgm_logger.error(f"DB_INIT_NON_CRITICAL_FAILURE: {e}")
