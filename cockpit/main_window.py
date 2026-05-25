from PySide6.QtWidgets import QMainWindow, QTabWidget, QVBoxLayout, QWidget
from cockpit.widgets.execution_feed import ExecutionFeed
from cockpit.widgets.health_graph import HealthGraph
from cockpit.widgets.tech_debt_dashboard import TechDebtDashboard
from cockpit.widgets.autonomy_dashboard import AutonomyDashboard
from cockpit.widgets.cognitive_dashboard import CognitiveDashboard, StrategicRoadmapWidget
from cockpit.widgets.architecture_graph_view import ArchitectureGraphView

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DGM-MAT Real-Time Operations Center")
        self.resize(1200, 800)

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.execution_feed = ExecutionFeed()
        self.health_graph = HealthGraph()
        self.tech_debt_dashboard = TechDebtDashboard()
        self.autonomy_dashboard = AutonomyDashboard()

        # New Cognitive and Strategic Tabs
        self.cognitive_dashboard = CognitiveDashboard()
        self.architecture_graph = ArchitectureGraphView()
        self.strategic_roadmap = StrategicRoadmapWidget()

        self.tabs.addTab(self.execution_feed, "Execution Feed")
        self.tabs.addTab(self.health_graph, "Ecosystem Health")
        self.tabs.addTab(self.tech_debt_dashboard, "Technical Debt")
        self.tabs.addTab(self.autonomy_dashboard, "Autonomous Ops")
        self.tabs.addTab(self.cognitive_dashboard, "Cognitive Intelligence")
        self.tabs.addTab(self.architecture_graph, "Architecture Graph")
        self.tabs.addTab(self.strategic_roadmap, "Strategic Roadmap")
