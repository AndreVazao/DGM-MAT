from PySide6.QtWidgets import QWidget, QVBoxLayout, QListWidget, QLabel, QProgressBar
from core.observability.logger import dgm_logger


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
        self.mission_list.setUpdatesEnabled(False)
        self.mission_list.clear()
        try:
            if not missions:
                self.mission_list.addItem("No active missions.")
                self.progress_bar.setValue(0)
                return

            for mission in missions:
                goal = mission.get("goal", "Unknown")
                status = mission.get("status", "unknown")
                self.mission_list.addItem(f"- {goal} [{status.upper()}]")

                output = mission.get("output") or mission.get("metadata", {}).get("output")
                if output:
                    self._render_output(mission.get("mission_id") or mission.get("id"), output)

            active_count = sum(1 for m in missions if m.get("status") in ["active", "RUNNING"])
            total = len(missions)
            if total > 0:
                self.progress_bar.setValue(int((active_count / total) * 100))
        finally:
            self.mission_list.setUpdatesEnabled(True)

    def _render_output(self, mission_id: str, output: str):
        lines = output.splitlines()
        max_lines = 120
        for line in lines[:max_lines]:
            self.mission_list.addItem(f"  {line[:500]}")
        if len(lines) > max_lines:
            self.mission_list.addItem(f"  ... output truncated ({len(lines) - max_lines} more lines)")
        dgm_logger.info(f"MISSION_OUTPUT_RENDERED: {mission_id}")
