from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QProgressBar,
    QTextEdit, QTableWidget, QTableWidgetItem
)

class AutonomousMonitor(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Autonomous Cycle Monitor"))

        self.status_label = QLabel("Status: Idle")
        layout.addWidget(self.status_label)

        self.progress = QProgressBar()
        layout.addWidget(self.progress)

        self.task_table = QTableWidget(0, 3)
        self.task_table.setHorizontalHeaderLabels(["Task ID", "Status", "Confidence"])
        layout.addWidget(self.task_table)

    def update_status(self, status: str, progress: int):
        self.status_label.setText(f"Status: {status}")
        self.progress.setValue(progress)
