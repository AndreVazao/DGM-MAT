from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QListWidget, QListWidgetItem
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QColor

class KnowledgeFeedWidget(QWidget):
    """
    Operational intelligence feed for repo insights.
    """
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.addWidget(QLabel("<b>INTELLIGENCE FEED</b>"))

        self.feed_list = QListWidget()
        self.layout.addWidget(self.feed_list)

        self._mock_data()

    def _mock_data(self):
        self.add_insight({
            "type": "TECH_DEBT",
            "severity": "MEDIUM",
            "message": "Missing unit tests for core/storage",
            "timestamp": "12:00"
        })

    @Slot(dict)
    def add_insight(self, insight: dict):
        msg = insight.get("message", "Unknown insight")
        severity = insight.get("severity", "LOW")
        timestamp = insight.get("timestamp", "N/A")

        item_text = f"[{timestamp}] {severity}: {msg}"
        item = QListWidgetItem(item_text)

        colors = {
            "CRITICAL": "#e74c3c",
            "HIGH": "#e67e22",
            "MEDIUM": "#f1c40f",
            "LOW": "#3498db"
        }
        item.setForeground(QColor(colors.get(severity, "#7f8c8d")))
        self.feed_list.insertItem(0, item)
