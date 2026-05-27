from typing import List, Dict, Any
from datetime import datetime
from core.autonomy.models import RepoAnalysisReport
from core.realtime.realtime_broadcast import safe_broadcast
from core.observability.logger import dgm_logger

class OperationalFeed:
    """
    Aggregates repository insights into an actionable intelligence feed.
    """
    def __init__(self):
        self.insights: List[Dict[str, Any]] = []

    def process_report(self, report: RepoAnalysisReport):
        dgm_logger.info(f"OperationalFeed: Processing report for {report.repo_id}")

        new_insights = []

        if report.dead_code:
            new_insights.append({
                "type": "DEAD_CODE",
                "severity": "MEDIUM",
                "message": f"Detected {len(report.dead_code)} dead code segments",
                "details": report.dead_code[:5]
            })

        if report.duplicates:
            new_insights.append({
                "type": "DUPLICATE_CODE",
                "severity": "HIGH",
                "message": f"Found {len(report.duplicates)} code duplications",
                "details": [d.get("file") for d in report.duplicates[:3]]
            })

        if report.score < 60:
             new_insights.append({
                "type": "HEALTH_CRITICAL",
                "severity": "CRITICAL",
                "message": f"Repository health score dropped to {report.score}",
                "details": []
            })

        for insight in new_insights:
            insight["timestamp"] = datetime.now().strftime("%H:%M:%S")
            self.insights.append(insight)
            self._broadcast_insight(insight)

    def _broadcast_insight(self, insight: Dict[str, Any]):
        safe_broadcast({
            "type": "operational_insight",
            "payload": insight
        })

operational_feed = OperationalFeed()
