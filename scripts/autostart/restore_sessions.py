from core.storage.storage_manager import storage_manager
from core.observability.logger import dgm_logger
from core.autonomy.mission_engine import mission_engine

def restore():
    dgm_logger.info("PHASE 41-LITE: Restoring missions and operational state...")
    try:
        # MissionEngine __init__ already calls _load_missions()
        mission_count = len(mission_engine.active_missions)
        dgm_logger.info(f"Restored {mission_count} missions.")
    except Exception as e:
        dgm_logger.error(f"Failed to restore missions: {e}")

if __name__ == "__main__":
    restore()
