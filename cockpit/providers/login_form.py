from PySide6.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QPushButton, QLabel, QFormLayout

class ProviderLoginForm(QWidget):
    """Dynamic login form for adding and authenticating new providers."""
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Provider Authentication"))

        form = QFormLayout()
        self.provider_name = QLineEdit()
        self.api_key = QLineEdit()
        self.api_key.setEchoMode(QLineEdit.Password)

        form.addRow("Provider Name:", self.provider_name)
        form.addRow("API Key / Session:", self.api_key)
        layout.addLayout(form)

        self.submit_btn = QPushButton("Authenticate & Save")
        layout.addWidget(self.submit_btn)
