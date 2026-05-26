from typing import List, Dict, Any

class ExecutionAnalytics:
    def analyze_success_rate(self, execution_logs: List[Dict[str, Any]]) -> float:
        if not execution_logs:
            return 1.0
        successes = sum(1 for log in execution_logs if log.get("status") == "SUCCESS")
        return successes / len(execution_logs)
