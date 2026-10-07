from sqlalchemy import inspect, text
from core.storage.database import engine
from core.storage.models import Base
from core.observability.logger import dgm_logger
from threading import Lock

_db_init_lock = Lock()
_db_initialized = False

def _ensure_event_envelope_column():
    inspector=inspect(engine)
    if "events" not in inspector.get_table_names():
        return
    columns={c["name"] for c in inspector.get_columns("events")}
    if "envelope_json" not in columns:
        with engine.begin() as connection:
            connection.execute(text("ALTER TABLE events ADD COLUMN envelope_json TEXT"))
        dgm_logger.info("DB_MIGRATION_EVENTS_ENVELOPE_JSON_ADDED")

def init_database():
    global _db_initialized
    with _db_init_lock:
        if _db_initialized:
            return
        try:
            existing=set(inspect(engine).get_table_names())
            Base.metadata.create_all(bind=engine)
            if "events" in existing:
                _ensure_event_envelope_column()
            _db_initialized=True
            dgm_logger.info("DB_INIT_COMPLETE")
        except Exception as e:
            dgm_logger.error(f"DB_INIT_NON_CRITICAL_FAILURE: {e}")
