from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTreeWidget, QTreeWidgetItem

class FederationWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.label = QLabel("Federated Multi-Ecosystem Fabric")
        self.layout.addWidget(self.label)

        self.ecosystem_tree = QTreeWidget()
        self.ecosystem_tree.setHeaderLabels(["Ecosystem", "Trust", "Status"])
        self.layout.addWidget(self.ecosystem_tree)

        core_node = QTreeWidgetItem(["DGM-MAT (Core)", "Verified", "Active"])
        self.ecosystem_tree.addTopLevelItem(core_node)
