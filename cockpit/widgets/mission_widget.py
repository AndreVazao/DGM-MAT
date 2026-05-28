from PySide6.QtWidgets import QWidget, QVBoxLayout, QListWidget, QLabel, QProgressBar
from PySide6.QtCore import Qt

class MissionWidget(QWidget):
    """
    Displays active missions and system progress.
    Uses non-blocking data updates.
    """
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.layout.addWidget(QLabel("<b>ACTIVE MISSIONS</b>"))
        self.mission_list = QListWidget()
        self.mission_list.setStyleSheet("background-color: #f8f9fa; border: 1px solid #dee2e6;")
        self.layout.addWidget(self.mission_list)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.layout.addWidget(self.progress_bar)

    def update_missions(self, missions: list):
        self.mission_list.clear()
        if not missions:
            self.mission_list.addItem("No active missions.")
            self.progress_bar.setValue(0)
            return

        for mission in missions:
            goal = mission.get('goal', 'Unknown')
            status = mission.get('status', 'unknown')
            self.mission_list.addItem(f"• {goal} [{status.upper()}]")

        # Simple progress heuristic for now
        active_count = sum(1 for m in missions if m.get('status') in ["active", "RUNNING"])
        total = len(missions)
        if total > 0:
            self.progress_bar.setValue(int((active_count / total) * 100))
