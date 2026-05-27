import requests
import threading
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QProgressBar, QHBoxLayout,
    QFrame, QLineEdit, QPushButton, QMessageBox
)
from PySide6.QtCore import Qt, Slot, Signal
from cockpit.widgets.mission_widget import MissionWidget
from cockpit.widgets.agent_widget import AgentWidget
from cockpit.widgets.knowledge_feed_widget import KnowledgeFeedWidget
from cockpit.approvals.queue_widget import ApprovalQueueWidget
from shared.config.settings import API_HOST, API_PORT

class OperationalDashboard(QWidget):
    """
    Main operational dashboard (Mission Control) for DGM-MAT.
    """
    mission_updated = Signal()

    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)

        # Command Surface
        self.cmd_frame = QFrame()
        self.cmd_frame.setFrameShape(QFrame.StyledPanel)
        self.cmd_frame.setStyleSheet("background-color: #2c3e50; border-radius: 5px; padding: 5px;")
        cmd_layout = QHBoxLayout(self.cmd_frame)

        self.command_input = QLineEdit()
        self.command_input.setPlaceholderText("Enter goal or mission command...")
        self.command_input.setStyleSheet("color: white; padding: 5px; border: 1px solid #34495e;")
        self.command_input.returnPressed.connect(self.dispatch_mission)

        self.dispatch_btn = QPushButton("DISPATCH")
        self.dispatch_btn.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold; padding: 5px 15px;")
        self.dispatch_btn.clicked.connect(self.dispatch_mission)

        cmd_layout.addWidget(QLabel("<b style='color: white;'>GOAL:</b>"))
        cmd_layout.addWidget(self.command_input, 1)
        cmd_layout.addWidget(self.dispatch_btn)

        self.layout.addWidget(self.cmd_frame)

        self.title = QLabel("MISSION CONTROL")
        self.title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        self.layout.addWidget(self.title, alignment=Qt.AlignCenter)

        content = QHBoxLayout()

        # LEFT: Missions & Feed
        left = QVBoxLayout()
        self.mission_widget = MissionWidget()
        self.knowledge_feed = KnowledgeFeedWidget()
        left.addWidget(self.mission_widget, 1)
        left.addWidget(self.knowledge_feed, 1)

        # RIGHT: Agents, Approvals & Resources
        right = QVBoxLayout()
        self.agent_widget = AgentWidget()
        self.approval_queue = ApprovalQueueWidget()
        right.addWidget(self.agent_widget, 1)
        right.addWidget(self.approval_queue, 1)

        res_frame = QFrame()
        res_frame.setFrameShape(QFrame.StyledPanel)
        res_layout = QVBoxLayout(res_frame)
        res_layout.addWidget(QLabel("<b>RESOURCE PULSE</b>"))
        self.cpu_bar = QProgressBar()
        self.mem_bar = QProgressBar()
        res_layout.addWidget(self.cpu_bar)
        res_layout.addWidget(self.mem_bar)

        # Runtime Controls
        ctrl_layout = QHBoxLayout()
        self.refresh_btn = QPushButton("Refresh Status")
        self.refresh_btn.clicked.connect(self.refresh_missions)
        ctrl_layout.addWidget(self.refresh_btn)
        res_layout.addLayout(ctrl_layout)

        right.addWidget(res_frame, 1)

        content.addLayout(left, 2)
        content.addLayout(right, 1)
        self.layout.addLayout(content)

        self.mission_updated.connect(self.refresh_missions)

    def dispatch_mission(self):
        goal = self.command_input.text().strip()
        if not goal:
            return

        self.command_input.clear()
        self.dispatch_btn.setEnabled(False)

        def run_dispatch():
            try:
                url = f"http://{API_HOST}:{API_PORT}/runtime/missions"
                response = requests.post(url, json={"goal": goal}, timeout=5)
                if response.status_code == 200:
                    self.mission_updated.emit()
            except Exception as e:
                print(f"Dispatch failed: {e}")
            finally:
                self.dispatch_btn.setEnabled(True)

        threading.Thread(target=run_dispatch, daemon=True).start()

    def refresh_missions(self):
        def run_refresh():
            try:
                url = f"http://{API_HOST}:{API_PORT}/runtime/missions"
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    missions = response.json()
                    self.mission_widget.update_missions(missions)
            except Exception as e:
                print(f"Refresh failed: {e}")

        threading.Thread(target=run_refresh, daemon=True).start()

    @Slot(dict)
    def update_resources(self, data: dict):
        if "cpu" in data: self.cpu_bar.setValue(int(data["cpu"]))
        if "memory" in data: self.mem_bar.setValue(int(data["memory"]))

    def update_status(self, payload: dict):
        # Placeholder for handling runtime status updates
        pass

    def update_provider_health(self, payload: dict):
        # Placeholder for handling provider health updates
        pass
