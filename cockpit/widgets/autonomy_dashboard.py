from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QListWidget, QHBoxLayout, QProgressBar
from PySide6.QtCore import Qt, Slot
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
        self.status_label = QLabel("Status: INITIALIZING")
        self.mode_label = QLabel("Mode: UNKNOWN")
        status_layout.addWidget(self.status_label)
        status_layout.addWidget(self.mode_label)
        layout.addLayout(status_layout)

        # Progress
        self.progress_label = QLabel("Current Cycle: N/A")
        layout.addWidget(self.progress_label)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 10)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        # Task Queue
        layout.addWidget(QLabel("Live Task Queue"))
        self.task_list = QListWidget()
        layout.addWidget(self.task_list)

        # Memory Growth
        layout.addWidget(QLabel("Memory Status"))
        self.memory_metrics = QLabel("Total Memories: 0 | Consolidated: 0")
        layout.addWidget(self.memory_metrics)

    @Slot(dict)
    def update_cycle(self, data: dict):
        """Updates the dashboard with cycle progress from websocket."""
        cycle_id = data.get("cycle_id", "Unknown")
        stage = data.get("stage", 0)
        stage_name = data.get("stage_name", "Idle")

        self.progress_label.setText(f"Current Cycle: {cycle_id} - Stage {stage}: {stage_name}")
        self.progress_bar.setValue(stage)

        if "status" in data:
            self.status_label.setText(f"Status: {data['status']}")

        if "task_results" in data:
            self.task_list.clear()
            for res in data["task_results"]:
                self.task_list.addItem(f"{res.get('task_id')}: {res.get('status')}")

    @Slot(dict)
    def update_state(self, state: dict):
        self.status_label.setText(f"Status: {state.get('status', 'UNKNOWN')}")
        self.mode_label.setText(f"Mode: {state.get('config', {}).get('execution_mode', 'UNKNOWN')}")
