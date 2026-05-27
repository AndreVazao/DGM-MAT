import asyncio
import json
import threading
from PySide6.QtWidgets import QMainWindow, QTabWidget, QVBoxLayout, QWidget
from PySide6.QtCore import Signal, QObject, Slot
from cockpit.widgets.execution_feed import ExecutionFeed
from cockpit.widgets.health_graph import HealthGraph
from cockpit.widgets.tech_debt_dashboard import TechDebtDashboard
from cockpit.widgets.autonomy_dashboard import AutonomyDashboard
from cockpit.widgets.cognitive_dashboard import CognitiveDashboard, StrategicRoadmapWidget
from cockpit.widgets.architecture_graph_view import ArchitectureGraphView
from cockpit.widgets.operational_dashboard import OperationalDashboard
from cockpit.app.websocket_client import CockpitWebSocketClient
from core.observability.logger import dgm_logger

class WebSocketSignals(QObject):
    message_received = Signal(dict)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DGM-MAT Real-Time Operations Center")
        self.resize(1200, 800)

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.operational_dashboard = OperationalDashboard()
        self.execution_feed = ExecutionFeed()
        self.health_graph = HealthGraph()
        self.tech_debt_dashboard = TechDebtDashboard()
        self.autonomy_dashboard = AutonomyDashboard()

        # New Cognitive and Strategic Tabs
        self.cognitive_dashboard = CognitiveDashboard()
        self.architecture_graph = ArchitectureGraphView()
        self.strategic_roadmap = StrategicRoadmapWidget()

        self.tabs.addTab(self.operational_dashboard, "Operational Center")
        self.tabs.addTab(self.execution_feed, "Execution Feed")
        self.tabs.addTab(self.health_graph, "Ecosystem Health")
        self.tabs.addTab(self.tech_debt_dashboard, "Technical Debt")
        self.tabs.addTab(self.autonomy_dashboard, "Autonomous Ops")
        self.tabs.addTab(self.cognitive_dashboard, "Cognitive Intelligence")
        self.tabs.addTab(self.architecture_graph, "Architecture Graph")
        self.tabs.addTab(self.strategic_roadmap, "Strategic Roadmap")

        # Initialize WebSocket
        self.signals = WebSocketSignals()
        self.signals.message_received.connect(self.dispatch_message)
        self.ws_client = CockpitWebSocketClient()
        self.ws_client.on_message(lambda msg: self.signals.message_received.emit(msg))

        # Start WS thread
        self.ws_thread = threading.Thread(target=self.start_ws, daemon=True)
        self.ws_thread.start()

    def start_ws(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.ws_client.connect())

    @Slot(dict)
    def dispatch_message(self, message: dict):
        # Route message to appropriate widgets
        msg_type = message.get("type")
        payload = message.get("payload", {})

        if msg_type == "execution_event":
            self.execution_feed.add_execution_event(payload)
        elif msg_type == "runtime_status":
            self.operational_dashboard.update_status(payload)
        elif msg_type == "autonomy_cycle":
            self.autonomy_dashboard.update_cycle(payload)
        elif msg_type == "provider_health":
            self.operational_dashboard.update_provider_health(payload)
