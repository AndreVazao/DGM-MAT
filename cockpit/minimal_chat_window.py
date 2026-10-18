"""Minimal PC cockpit: a single chat surface over the local DGM-MAT backend."""
from PySide6.QtWidgets import QMainWindow

from cockpit.widgets.command_console import CommandConsoleWidget


class MinimalChatWindow(QMainWindow):
    """Keep the current cockpit focused on submitting and observing missions."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("DGM-MAT — Chat")
        self.resize(920, 720)
        self.setMinimumSize(620, 480)

        self.chat = CommandConsoleWidget()
        self.setCentralWidget(self.chat)
        self.statusBar().showMessage(
            "Backend local | Missões, estados reais e decisões explícitas"
        )
