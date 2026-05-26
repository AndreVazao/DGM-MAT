from typing import List, Dict, Any
from core.observability.logger import dgm_logger

class LearningLoop:
    def process_feedback(self, results: List[Dict[str, Any]]):
        dgm_logger.info("LearningLoop: Processing execution feedback.")
        for result in results:
            if result.get("status") == "FAILED":
                dgm_logger.warning(f"LearningLoop: Learning from failure in {result.get('task_id')}")
                # Store failure patterns for future avoidance
