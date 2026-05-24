from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QListWidget
from PySide6.QtCore import Qt

class AutonomousTasksWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.title = QLabel("Autonomous Tasks")
        self.title.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.layout.addWidget(self.title)

        self.task_list = QListWidget()
        self.layout.addWidget(self.task_list)
