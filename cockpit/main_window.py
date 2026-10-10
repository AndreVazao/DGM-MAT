from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QLabel, QStatusBar, QFrame
)
from PySide6.QtCore import Qt, Signal, Slot, QTimer
from PySide6.QtGui import QIcon, QPalette, QColor
import asyncio
import threading

from cockpit.widgets.dashboard_widget import DashboardWidget
from cockpit.widgets.agent_widget import AgentWidget
from cockpit.widgets.mission_widget import MissionWidget
from cockpit.widgets.command_console import CommandConsoleWidget
from cockpit.widgets.runtime_health_widget import RuntimeHealthWidget
from cockpit.widgets.event_stream_widget import EventStreamWidget
from cockpit.widgets.execution_feed import ExecutionFeed
from cockpit.widgets.imported_repos_widget import ImportedReposWidget
from cockpit.widgets.autonomy_dashboard import AutonomyDashboard
from cockpit.widgets.knowledge_graph_widget import KnowledgeGraphWidget
from cockpit.widgets.federation_widget import FederationWidget
from cockpit.widgets.governance_widget import GovernanceWidget
from cockpit.providers.management_widget import ProviderManagementWidget

from cockpit.app.websocket_client import CockpitWebSocketClient
from core.observability.logger import dgm_logger

class MainWindow(QMainWindow):
    server_message_received = Signal(dict)
    connection_state_received = Signal(bool, str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("DGM-MAT | Cognitive Operating System Cockpit")
        self.resize(1400, 900)

        self.ws_client = CockpitWebSocketClient()
        self.is_connected = False
        self.runtime_status = "offline"
        self.system_state = "UNKNOWN"
        self.boot_phase = "UNKNOWN"
        self.node_status = "UNKNOWN"
        self.is_degraded = False
        self.degradation_reasons = []
        self.connection_reason = "UNKNOWN"

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
        self.status_badge.setFixedSize(350, 30)
        self.status_badge.setAlignment(Qt.AlignCenter)
        self.status_badge.setStyleSheet("background-color: #f44336; color: white; border-radius: 5px; font-weight: bold; font-size: 11px;")

        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.status_badge)
        main_layout.addLayout(header_layout)

        # Main horizontal split
        content_layout = QHBoxLayout()

        # Left side: Navigation and Tools (Tabs)
        self.tabs = QTabWidget()
        self.dashboard_widget = DashboardWidget()
        self.mission_widget = MissionWidget()
        self.agent_widget = AgentWidget()
        self.provider_widget = ProviderManagementWidget()
        self.autonomy_dashboard = AutonomyDashboard()
        self.governance_widget = GovernanceWidget()
        self.execution_feed = ExecutionFeed()

        self.tabs.addTab(self.dashboard_widget, "Dashboard")
        self.tabs.addTab(self.mission_widget, "Missions")
        self.tabs.addTab(self.agent_widget, "Agents")
        self.tabs.addTab(ImportedReposWidget(), "Repositories")
        self.tabs.addTab(self.provider_widget, "Providers")
        self.tabs.addTab(self.autonomy_dashboard, "Autonomy")
        self.tabs.addTab(KnowledgeGraphWidget(), "Knowledge")
        self.tabs.addTab(FederationWidget(), "Federation")
        self.tabs.addTab(self.governance_widget, "Governance")
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
        # Qt widgets must only be touched on the GUI thread. Realtime callbacks
        # emit signals so Qt queues UI updates safely across threads.
        self.server_message_received.connect(self._handle_server_message)
        self.connection_state_received.connect(self._on_connection_changed)
        self.ws_client.client.add_connection_callback(self._queue_connection_state)
        self.ws_client.on_message(self._queue_server_message)
        self._realtime_thread = threading.Thread(
            target=self._run_realtime_client,
            name="dgm-cockpit-realtime",
            daemon=True,
        )
        self._realtime_thread.start()

    def _run_realtime_client(self):
        try:
            asyncio.run(self.ws_client.connect())
        except Exception as exc:
            dgm_logger.error(f"Cockpit: Realtime client stopped ({type(exc).__name__}).")

    def _queue_connection_state(self, connected: bool, reason: str = "UNKNOWN"):
        self.connection_state_received.emit(bool(connected), str(reason))

    def _queue_server_message(self, data: dict):
        if isinstance(data, dict):
            self.server_message_received.emit(data)

    def _fetch_initial_state(self):
        """Priority 2: Manual state hydration on connect."""
        from cockpit.api_client import authenticated_request
        import threading
        from shared.config.settings import API_HOST, API_PORT
        def run_fetch():
            try:
                response = authenticated_request("GET", f"http://{API_HOST}:{API_PORT}/runtime/truth", timeout=2)
                if response.status_code == 200:
                    self.server_message_received.emit({"type": "state_update", "data": response.json()})
                    dgm_logger.info("Cockpit: Initial state hydration complete.")
            except Exception as e:
                dgm_logger.warning(f"Cockpit: Initial hydration failed: {e}")

        threading.Thread(target=run_fetch, daemon=True).start()

    @Slot(bool, str)
    def _on_connection_changed(self, connected, reason="UNKNOWN"):
        self.is_connected = connected
        self.connection_reason = reason
        if not connected:
            self.runtime_status = "offline"
            self.system_state = "OFFLINE"

        self._update_status_badge()

        if connected:
            self._fetch_initial_state()

    def _handle_server_message(self, data):
        """Requirement 5: Cockpit connection state based on Truth."""
        if data.get("type") == "state_update":
            state = data.get("data", {})
            self.runtime_status = state.get("runtime_status", "unknown")
            self.system_state = state.get("system_state", "UNKNOWN")
            self.boot_phase = state.get("boot_phase", "STARTUP")
            self.node_status = state.get("node_status", "UNKNOWN")
            self.is_degraded = state.get("is_degraded", False)

            # Extract reasons from degradation dict
            degradation = state.get("degradation", {})
            self.degradation_reasons = degradation.get("reasons", [])

            self._update_status_badge()
            self._update_child_widgets(state)
        elif data.get("type") == "mission_result":
            payload = data.get("payload", {})
            output = payload.get("output") or payload.get("summary")
            if output:
                lines = output.splitlines()
                rendered = "\n".join(lines[:120])
                if len(lines) > 120:
                    rendered += f"\n... output truncated ({len(lines) - 120} more lines)"
                self.command_console._append_message("Runtime", rendered, "info")
                dgm_logger.info(f"MISSION_OUTPUT_RENDERED: {payload.get('mission_id')}")
        elif data.get("type") == "execution_event":
            self.execution_feed.add_execution_event(data.get("payload", {}))
        elif data.get("type") == "provider_health":
            self.provider_widget.refresh_providers()
        elif data.get("type") == "autonomy_cycle":
            self.autonomy_dashboard.update_cycle(data.get("payload", {}))

    def dispatch_message(self, data):
        """Public message-dispatch boundary used by realtime clients and tests."""
        if data.get("type") == "runtime_status":
            payload = data.get("payload", {})
            data = {
                "type": "state_update",
                "data": {
                    "runtime_status": payload.get("status", "unknown"),
                    "health": {"resources": {
                        "cpu": payload.get("cpu", 0),
                        "memory": payload.get("memory", 0),
                    }},
                },
            }
        self._handle_server_message(data)

    def _update_child_widgets(self, state):
        missions = list(state.get("missions", {}).values())
        if missions:
            self.mission_widget.update_missions(missions)

        resources = state.get("health", {}).get("resources", {})
        if not resources:
            resources = state.get("cockpit", {}).get("resources", {})

        cpu = resources.get("cpu", 0)
        mem = resources.get("memory", 0)
        self.governance_widget.update_metrics(cpu, mem, state.get("is_degraded", False))
        self.autonomy_dashboard.update_state({
            "status": state.get("runtime_status", "UNKNOWN"),
            "config": {"execution_mode": "LOW_MEMORY" if state.get("health", {}).get("low_memory_profile") else "STANDARD"}
        })

    def closeEvent(self, event):
        """Stop the realtime client when the desktop cockpit closes; Core stays alive."""
        try:
            self.ws_client.stop()
        except Exception as exc:
            dgm_logger.warning(f"Cockpit: Realtime shutdown issue ({type(exc).__name__}).")
        event.accept()

    def _update_status_badge(self):
        if self.is_connected:
            if self.runtime_status == "running":
                if self.is_degraded:
                    reason = self.degradation_reasons[0] if self.degradation_reasons else "DEGRADED"
                    self.status_badge.setText(f"CONNECTED | DEGRADED ({reason})")
                    self.status_badge.setStyleSheet("background-color: #ff9800; color: white; border-radius: 5px; font-weight: bold;")
                else:
                    self.status_badge.setText(f"CONNECTED | {self.system_state} ({self.boot_phase})")
                    self.status_badge.setStyleSheet("background-color: #4caf50; color: white; border-radius: 5px; font-weight: bold;")
                self.command_console.set_enabled(True)
            else:
                self.status_badge.setText(f"CONNECTED | {self.system_state} ({self.boot_phase})")
                self.status_badge.setStyleSheet("background-color: #2196f3; color: white; border-radius: 5px; font-weight: bold;")
                self.command_console.set_enabled(False)
        else:
            self.status_badge.setText(f"OFFLINE | {self.connection_reason}")
            self.status_badge.setStyleSheet("background-color: #f44336; color: white; border-radius: 5px; font-weight: bold;")
            self.command_console.set_enabled(False)
