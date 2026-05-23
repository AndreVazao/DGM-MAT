from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTabWidget,
)
from cockpit.widgets.dashboard_widget import (
    DashboardWidget,
)
from cockpit.widgets.logs_widget import (
    LogsWidget,
)
from cockpit.widgets.event_stream_widget import (
    EventStreamWidget,
)
from cockpit.widgets.agent_widget import (
    AgentWidget,
)
from cockpit.widgets.execution_queue_widget import (
    ExecutionQueueWidget,
)
from cockpit.widgets.mesh_monitor_widget import (
    MeshMonitorWidget,
)
from cockpit.widgets.learning_dashboard_widget import (
    LearningDashboardWidget,
)
# Phase 21 & 22 widgets
from cockpit.widgets.governance_widget import (
    GovernanceWidget,
)
from cockpit.widgets.knowledge_graph_widget import (
    KnowledgeGraphWidget,
)
from cockpit.widgets.operational_search_widget import (
    OperationalSearchWidget,
)

# Phase 23, 24, 25 widgets
from cockpit.widgets.strategy_widget import StrategyWidget
from cockpit.widgets.research_widget import ResearchWidget
from cockpit.widgets.federation_widget import FederationWidget

from cockpit.realtime_client import (
    RealtimeClient,
)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(
            "DGM-MAT Cockpit"
        )
        self.resize(1600, 1000)
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QHBoxLayout()

        # Tabs for better organization
        self.tabs = QTabWidget()

        # --- TAB 1: CORE RUNTIME ---
        runtime_tab = QWidget()
        runtime_layout = QHBoxLayout(runtime_tab)

        left_layout = QVBoxLayout()
        right_layout = QVBoxLayout()

        self.dashboard = DashboardWidget()
        self.logs = LogsWidget()
        self.events = EventStreamWidget()
        self.agents = AgentWidget()
        self.execution_queue = ExecutionQueueWidget()
        self.mesh_monitor = MeshMonitorWidget()

        left_layout.addWidget(self.dashboard)
        left_layout.addWidget(self.agents)
        left_layout.addWidget(self.mesh_monitor)

        right_layout.addWidget(self.events)
        right_layout.addWidget(self.execution_queue)
        right_layout.addWidget(self.logs)

        runtime_layout.addLayout(left_layout, 1)
        runtime_layout.addLayout(right_layout, 2)

        self.tabs.addTab(runtime_tab, "Runtime")

        # --- TAB 2: GOVERNANCE & SAFETY ---
        governance_tab = QWidget()
        gov_layout = QVBoxLayout(governance_tab)
        self.governance_monitor = GovernanceWidget()
        gov_layout.addWidget(self.governance_monitor)
        self.tabs.addTab(governance_tab, "Governance")

        # --- TAB 3: KNOWLEDGE FABRIC ---
        knowledge_tab = QWidget()
        know_layout = QVBoxLayout(knowledge_tab)
        self.knowledge_graph = KnowledgeGraphWidget()
        self.operational_search = OperationalSearchWidget()
        know_layout.addWidget(self.operational_search)
        know_layout.addWidget(self.knowledge_graph)
        self.tabs.addTab(knowledge_tab, "Knowledge")

        # --- TAB 4: STRATEGIC & RESEARCH ---
        strategy_tab = QWidget()
        strat_layout = QVBoxLayout(strategy_tab)
        self.strategy_viewer = StrategyWidget()
        self.research_lab = ResearchWidget()
        strat_layout.addWidget(self.strategy_viewer)
        strat_layout.addWidget(self.research_lab)
        self.tabs.addTab(strategy_tab, "Strategy & Research")

        # --- TAB 5: FEDERATION ---
        federation_tab = QWidget()
        fed_layout = QVBoxLayout(federation_tab)
        self.federation_map = FederationWidget()
        fed_layout.addWidget(self.federation_map)
        self.tabs.addTab(federation_tab, "Federation")

        # --- TAB 6: INTELLIGENCE ---
        intelligence_tab = QWidget()
        intel_layout = QVBoxLayout(intelligence_tab)
        self.learning_dashboard = LearningDashboardWidget()
        intel_layout.addWidget(self.learning_dashboard)
        self.tabs.addTab(intelligence_tab, "Intelligence")

        root_layout.addWidget(self.tabs)
        central.setLayout(root_layout)

        self.client = RealtimeClient(
            self.handle_message
        )
        QTimer.singleShot(
            1000,
            self.client.start,
        )

    def handle_message(
        self,
        message: dict,
    ):
        event_type = message.get(
            "event_type",
            "unknown",
        )
        source = message.get(
            "source",
            "unknown",
        )
        self.events.add_event(
            f"{event_type} ← {source}"
        )
        self.logs.append_log(
            f"[EVENT] {event_type}"
        )
