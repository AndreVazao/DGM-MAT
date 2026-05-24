from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTreeWidget, QTreeWidgetItem
from core.federation.ecosystem_registry import EcosystemRegistry

class FederationWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.registry = EcosystemRegistry()
        self.layout = QVBoxLayout(self)
        self.label = QLabel("Federated Multi-Ecosystem Fabric")
        self.layout.addWidget(self.label)

        self.ecosystem_tree = QTreeWidget()
        self.ecosystem_tree.setHeaderLabels(["Ecosystem", "Status", "Specialization"])
        self.layout.addWidget(self.ecosystem_tree)

        self._refresh_ecosystems()

    def _refresh_ecosystems(self):
        self.ecosystem_tree.clear()
        ecosystems = self.registry.get_ecosystems()

        # Sort so ACTIVE comes first
        sorted_ecosystems = sorted(ecosystems, key=lambda x: (x.status != "active", x.id))

        for eco in sorted_ecosystems:
            item = QTreeWidgetItem([
                eco.id,
                eco.status.value,
                ", ".join(eco.specialization[:2]) + ("..." if len(eco.specialization) > 2 else "")
            ])
            self.ecosystem_tree.addTopLevelItem(item)
