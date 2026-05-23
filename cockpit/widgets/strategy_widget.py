from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QListWidget

class StrategyWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.label = QLabel("Strategic Orchestration & Roadmap")
        self.layout.addWidget(self.label)

        self.roadmap_list = QListWidget()
        self.layout.addWidget(self.roadmap_list)

        self.debt_panel = QLabel("Technical Debt Forecast: Nominal")
        self.layout.addWidget(self.debt_panel)
