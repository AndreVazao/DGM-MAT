from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTreeWidget

class ProjectFamiliesWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.title = QLabel("Project Families")
        self.title.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.layout.addWidget(self.title)

        self.family_tree = QTreeWidget()
        self.layout.addWidget(self.family_tree)
