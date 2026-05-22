import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication
from cockpit.main_window import MainWindow

def load_styles(app):
    style_path = Path(
        "cockpit/styles/theme.qss"
    )
    if style_path.exists():
        with open(
            style_path,
            "r",
            encoding="utf-8",
        ) as file:
            app.setStyleSheet(
                file.read()
            )

def run_cockpit():
    app = QApplication(sys.argv)
    load_styles(app)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
