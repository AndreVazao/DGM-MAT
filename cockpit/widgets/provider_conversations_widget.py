from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QListWidget

class ProviderConversationsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.title = QLabel("Provider Conversations")
        self.title.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.layout.addWidget(self.title)

        self.conv_list = QListWidget()
        self.layout.addWidget(self.conv_list)
