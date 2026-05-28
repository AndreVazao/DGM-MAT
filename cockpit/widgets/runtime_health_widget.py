from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar, QGridLayout, QFrame
from PySide6.QtCore import Qt, QTimer
from core.runtime.reality_snapshot import RealitySnapshotService
from core.runtime.health_score import RuntimeHealthScore
from core.runtime.safe_action_queue import SafeActionQueue

class RuntimeHealthWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.snapshot_service = RealitySnapshotService()
        self.health_engine = RuntimeHealthScore()
        self.action_queue = SafeActionQueue()

        self.init_ui()

        # Periodic update timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_stats)
        self.timer.start(5000) # Every 5 seconds

    def init_ui(self):
        self.layout = QVBoxLayout(self)

        # Title
        self.title = QLabel("Runtime Reality Layer")
        self.title.setStyleSheet("font-weight: bold; font-size: 16px; color: #2ecc71;")
        self.layout.addWidget(self.title)

        # Health Section
        self.health_group = QFrame()
        self.health_group.setFrameStyle(QFrame.StyledPanel | QFrame.Plain)
        health_layout = QVBoxLayout(self.health_group)

        health_layout.addWidget(QLabel("Global Health Score"))
        self.health_bar = QProgressBar()
        self.health_bar.setValue(0)
        self.health_bar.setTextVisible(True)
        self.health_bar.setFormat("%p%")
        health_layout.addWidget(self.health_bar)

        # Score Breakdown Area
        self.breakdown_label = QLabel("Breakdown: Loading...")
        self.breakdown_label.setStyleSheet("font-family: monospace; font-size: 10px; color: #95a5a6;")
        health_layout.addWidget(self.breakdown_label)

        self.layout.addWidget(self.health_group)

        # Stats Grid
        self.stats_grid = QGridLayout()

        self.reality_status_label = QLabel("Reality Status: Unknown")
        self.drift_count_label = QLabel("Drift Count: 0")
        self.queue_status_label = QLabel("Queue Status: 0 Pending")

        self.stats_grid.addWidget(self.reality_status_label, 0, 0)
        self.stats_grid.addWidget(self.drift_count_label, 0, 1)
        self.stats_grid.addWidget(self.queue_status_label, 1, 0)

        self.layout.addLayout(self.stats_grid)

        # Warnings Area
        self.warnings_label = QLabel("")
        self.warnings_label.setWordWrap(True)
        self.warnings_label.setStyleSheet("color: #e67e22;")
        self.layout.addWidget(self.warnings_label)

        self.layout.addStretch()

    def update_stats(self):
        try:
            summary = self.snapshot_service.snapshot_summary()
            health_result = self.health_engine.compute(summary)
            queued_actions = self.action_queue.list_queued()

            # Update Score
            score = health_result.get("score", 0)
            self.health_bar.setValue(score)

            # Update Colors based on score
            if score > 80:
                self.health_bar.setStyleSheet("QProgressBar::chunk { background-color: #2ecc71; }")
            elif score > 50:
                self.health_bar.setStyleSheet("QProgressBar::chunk { background-color: #f1c40f; }")
            else:
                self.health_bar.setStyleSheet("QProgressBar::chunk { background-color: #e74c3c; }")

            # Update Breakdown
            breakdown = health_result.get("breakdown", {})
            breakdown_text = " | ".join([f"{k.capitalize()}: {v}" for k, v in breakdown.items()])
            self.breakdown_label.setText(f"Breakdown: {breakdown_text}")

            # Update Stats
            status = health_result.get("status", "Unknown")
            self.reality_status_label.setText(f"Reality Status: {status}")

            # Drift calculation (simplified for UI)
            drift_count = len(health_result.get("critical", [])) + len(health_result.get("warnings", []))
            self.drift_count_label.setText(f"Drift Count: {drift_count}")

            self.queue_status_label.setText(f"Queue Status: {len(queued_actions)} Pending")

            # Update Warnings
            all_warnings = health_result.get("critical", []) + health_result.get("warnings", [])
            if all_warnings:
                self.warnings_label.setText("Warnings: " + "; ".join(all_warnings[:3]))
            else:
                self.warnings_label.setText("")

        except Exception as e:
            self.reality_status_label.setText(f"Status Error: {str(e)}")
