import requests
import threading
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QProgressBar, QHBoxLayout,
    QFrame, QLineEdit, QPushButton, QMessageBox
)
from PySide6.QtCore import Qt, Slot, Signal, QTimer
from cockpit.widgets.mission_widget import MissionWidget
from cockpit.widgets.agent_widget import AgentWidget
from cockpit.widgets.knowledge_feed_widget import KnowledgeFeedWidget
from cockpit.approvals.queue_widget import ApprovalQueueWidget
from shared.config.settings import API_HOST, API_PORT

class OperationalDashboard(QWidget):
    """
    Main operational dashboard (Mission Control) for DGM-MAT.
    Finalized for Phase 42.1.
    """
    mission_updated = Signal()

    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)

        # 1. Command Surface (Operational Input Bar)
        self.cmd_frame = QFrame()
        self.cmd_frame.setFrameShape(QFrame.StyledPanel)
        self.cmd_frame.setStyleSheet("background-color: #2c3e50; border-radius: 5px; padding: 10px;")
        cmd_layout = QHBoxLayout(self.cmd_frame)

        self.command_input = QLineEdit()
        self.command_input.setPlaceholderText("Enter goal or mission command (e.g. 'Audit workspace health')...")
        self.command_input.setStyleSheet("color: white; padding: 8px; border: 1px solid #34495e; font-size: 14px;")
        self.command_input.returnPressed.connect(self.dispatch_mission)

        self.dispatch_btn = QPushButton("DISPATCH MISSION")
        self.dispatch_btn.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold; padding: 8px 20px;")
        self.dispatch_btn.clicked.connect(self.dispatch_mission)

        cmd_layout.addWidget(QLabel("<b style='color: white; font-size: 14px;'>GOAL:</b>"))
        cmd_layout.addWidget(self.command_input, 1)
        cmd_layout.addWidget(self.dispatch_btn)

        self.layout.addWidget(self.cmd_frame)

        # 2. Main Content Area
        content = QHBoxLayout()

        # LEFT: Missions & Feed
        left = QVBoxLayout()
        self.mission_widget = MissionWidget()
        self.knowledge_feed = KnowledgeFeedWidget()
        left.addWidget(self.mission_widget, 2)
        left.addWidget(self.knowledge_feed, 1)

        # RIGHT: Agents, Approvals & Resources
        right = QVBoxLayout()
        self.agent_widget = AgentWidget()
        self.approval_queue = ApprovalQueueWidget()
        right.addWidget(self.agent_widget, 1)
        right.addWidget(self.approval_queue, 1)

        # Resource Pulse
        res_frame = QFrame()
        res_frame.setFrameShape(QFrame.StyledPanel)
        res_frame.setStyleSheet("background-color: #fcfcfc; border: 1px solid #ddd;")
        res_layout = QVBoxLayout(res_frame)
        res_layout.addWidget(QLabel("<b>SYSTEM RESOURCE PULSE</b>"))

        self.cpu_bar = QProgressBar()
        self.cpu_bar.setFormat("CPU: %p%")
        self.mem_bar = QProgressBar()
        self.mem_bar.setFormat("RAM: %p%")
        res_layout.addWidget(self.cpu_bar)
        res_layout.addWidget(self.mem_bar)

        # Refresh & Sync Controls
        ctrl_layout = QHBoxLayout()
        self.refresh_btn = QPushButton("Refresh Status")
        self.refresh_btn.clicked.connect(self.poll_status)
        ctrl_layout.addWidget(self.refresh_btn)

        self.sync_btn = QPushButton("Sync Workspace")
        self.sync_btn.clicked.connect(self.sync_workspace)
        ctrl_layout.addWidget(self.sync_btn)
        res_layout.addLayout(ctrl_layout)

        right.addWidget(res_frame, 1)

        content.addLayout(left, 2)
        content.addLayout(right, 1)
        self.layout.addLayout(content)

        # Polling Timer
        self.poll_timer = QTimer(self)
        self.poll_timer.timeout.connect(self.poll_status)
        self.poll_timer.start(5000) # Poll every 5s

        self.mission_updated.connect(self.refresh_missions)
        self.poll_status()

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

    def poll_status(self):
        """Active status polling from API."""
        def run_poll():
            try:
                url = f"http://{API_HOST}:{API_PORT}/runtime/status"
                response = requests.get(url, timeout=3)
                if response.status_code == 200:
                    data = response.json()
                    self.update_status(data)

                # Also poll approvals
                url_app = f"http://{API_HOST}:{API_PORT}/runtime/approvals"
                res_app = requests.get(url_app, timeout=3)
                if res_app.status_code == 200:
                    apps = res_app.json()
                    # ApprovalQueueWidget update logic
            except Exception as e:
                pass

        threading.Thread(target=run_poll, daemon=True).start()
        self.refresh_missions()

    def refresh_missions(self):
        def run_refresh():
            try:
                url = f"http://{API_HOST}:{API_PORT}/runtime/missions"
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    missions = response.json()
                    self.mission_widget.update_missions(missions)
            except Exception as e:
                pass

        threading.Thread(target=run_refresh, daemon=True).start()

    def sync_workspace(self):
        def run_sync():
            try:
                url = f"http://{API_HOST}:{API_PORT}/runtime/workspace/scan"
                requests.get(url, timeout=30)
            except Exception:
                pass
        threading.Thread(target=run_sync, daemon=True).start()

    @Slot(dict)
    def update_status(self, payload: dict):
        if "resources" in payload:
            res = payload["resources"]
            self.cpu_bar.setValue(int(res.get("cpu", 0)))
            self.mem_bar.setValue(int(res.get("memory", 0)))
        if "agents" in payload:
            self.agent_widget.update_agents(payload["agents"])

    def update_provider_health(self, payload: dict):
        pass
