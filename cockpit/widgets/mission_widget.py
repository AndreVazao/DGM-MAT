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
        self.layout.addWidget(self.mission_list)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.layout.addWidget(self.progress_bar)

        self._mock_data()

    def _mock_data(self):
        self.mission_list.addItem("Stabilize Repository CI [Active]")
        self.progress_bar.setValue(35)

    def update_missions(self, missions: list):
        self.mission_list.clear()
        for mission in missions:
            self.mission_list.addItem(f"{mission.get('goal')} [{mission.get('status')}]")
