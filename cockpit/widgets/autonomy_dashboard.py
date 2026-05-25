from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QListWidget, QHBoxLayout, QProgressBar
from PySide6.QtCore import Qt, Signal, Slot
import json

class AutonomyDashboard(QWidget):
    """
    Dashboard for monitoring autonomous operations.
    """
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        # Status Panel
        status_layout = QHBoxLayout()
        self.status_label = QLabel("Status: RUNNING")
        self.mode_label = QLabel("Mode: SAFE")
        status_layout.addWidget(self.status_label)
        status_layout.addWidget(self.mode_label)
        layout.addLayout(status_layout)

        # Progress
        layout.addWidget(QLabel("Current Cycle Progress"))
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 10)
        self.progress_bar.setValue(3)
        layout.addWidget(self.progress_bar)

        # Task Queue
        layout.addWidget(QLabel("Live Task Queue"))
        self.task_list = QListWidget()
        layout.addWidget(self.task_list)

        # Memory Growth
        layout.addWidget(QLabel("Memory Growth Metrics"))
        self.memory_metrics = QLabel("Total Memories: 154 | Consolidated: 12")
        layout.addWidget(self.memory_metrics)

    @Slot(dict)
    def update_state(self, state: dict):
        self.status_label.setText(f"Status: {state.get('status', 'UNKNOWN')}")
        self.mode_label.setText(f"Mode: {state.get('config', {}).get('execution_mode', 'UNKNOWN')}")
