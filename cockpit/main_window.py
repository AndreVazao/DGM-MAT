import sys
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QLabel, QStatusBar, QFrame
)
from PySide6.QtCore import Qt, Signal, Slot, QTimer
from PySide6.QtGui import QIcon, QPalette, QColor

from cockpit.widgets.dashboard_widget import DashboardWidget
from cockpit.widgets.agent_widget import AgentWidget
from cockpit.widgets.mission_widget import MissionWidget
from cockpit.widgets.command_console import CommandConsoleWidget
from cockpit.widgets.runtime_health_widget import RuntimeHealthWidget
from cockpit.widgets.event_stream_widget import EventStreamWidget
from cockpit.widgets.imported_repos_widget import ImportedReposWidget
from cockpit.widgets.autonomy_dashboard import AutonomyDashboard
from cockpit.widgets.knowledge_graph_widget import KnowledgeGraphWidget
from cockpit.widgets.federation_widget import FederationWidget
from cockpit.widgets.governance_widget import GovernanceWidget
from cockpit.providers.management_widget import ProviderManagementWidget

from cockpit.app.websocket_client import CockpitWebSocketClient
from core.observability.logger import dgm_logger

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DGM-MAT | Cognitive Operating System Cockpit")
        self.resize(1400, 900)

        self.ws_client = CockpitWebSocketClient()
        self.is_connected = False
        self.runtime_prepared = False

        self._setup_ui()
        self._setup_connections()

    def _setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Header with connection status
        header_layout = QHBoxLayout()
        title_label = QLabel("DGM-MAT COCKPIT")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #007acc;")

        self.status_badge = QLabel("DISCONNECTED")
        self.status_badge.setFixedSize(140, 25)
        self.status_badge.setAlignment(Qt.AlignCenter)
        self.status_badge.setStyleSheet("background-color: #f44336; color: white; border-radius: 5px; font-weight: bold;")

        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.status_badge)
        main_layout.addLayout(header_layout)

        # Main horizontal split
        content_layout = QHBoxLayout()

        # Left side: Navigation and Tools (Tabs)
        self.tabs = QTabWidget()
        self.tabs.addTab(DashboardWidget(), "Dashboard")
        self.tabs.addTab(MissionWidget(), "Missions")
        self.tabs.addTab(AgentWidget(), "Agents")
        self.tabs.addTab(ImportedReposWidget(), "Repositories")
        self.tabs.addTab(ProviderManagementWidget(), "Providers")
        self.tabs.addTab(AutonomyDashboard(), "Autonomy")
        self.tabs.addTab(KnowledgeGraphWidget(), "Knowledge")
        self.tabs.addTab(FederationWidget(), "Federation")
        self.tabs.addTab(GovernanceWidget(), "Governance")
        self.tabs.addTab(EventStreamWidget(), "Events")
        self.tabs.addTab(RuntimeHealthWidget(), "System Health")

        content_layout.addWidget(self.tabs, 3)

        # Right side: Command Console (Always visible)
        console_container = QFrame()
        console_container.setFrameShape(QFrame.StyledPanel)
        console_container.setStyleSheet("background-color: #1e1e1e; border: 1px solid #3e3e3e;")
        console_layout = QVBoxLayout(console_container)

        self.command_console = CommandConsoleWidget()
        console_layout.addWidget(self.command_console)

        content_layout.addWidget(console_container, 1)

        main_layout.addLayout(content_layout)

        # Status Bar
        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage("Initializing subsystems...")

    def _setup_connections(self):
        self.ws_client.client.add_connection_callback(self._on_connection_changed)
        self.ws_client.on_message(self._handle_server_message)

        # Start connection attempt
        import asyncio
        loop = asyncio.get_event_loop()
        asyncio.run_coroutine_threadsafe(self.ws_client.connect(), loop)

    @Slot(bool)
    def _on_connection_changed(self, connected):
        self.is_connected = connected
        self._update_status_badge()

    def _handle_server_message(self, data):
        """Requirement 3: Connection status based on API reachability AND Runtime prepared."""
        if data.get("type") == "state_update":
            state = data.get("data", {})
            self.runtime_prepared = state.get("status") == "running"
            self._update_status_badge()

        # Dispatch to other widgets as needed

    def _update_status_badge(self):
        if self.is_connected and self.runtime_prepared:
            self.status_badge.setText("CONNECTED | READY")
            self.status_badge.setStyleSheet("background-color: #4caf50; color: white; border-radius: 5px; font-weight: bold;")
            self.command_console.set_enabled(True)
            self.statusBar().showMessage("System Operational.")
        elif self.is_connected:
            self.status_badge.setText("API CONNECTED")
            self.status_badge.setStyleSheet("background-color: #ff9800; color: white; border-radius: 5px; font-weight: bold;")
            self.command_console.set_enabled(False)
            self.statusBar().showMessage("Waiting for Runtime to prepare...")
        else:
            self.status_badge.setText("OFFLINE")
            self.status_badge.setStyleSheet("background-color: #f44336; color: white; border-radius: 5px; font-weight: bold;")
            self.command_console.set_enabled(False)
            self.statusBar().showMessage("Disconnected from API.")
