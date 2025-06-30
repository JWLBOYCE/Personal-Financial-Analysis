from PyQt5 import QtWidgets
import hashlib
from dotenv import dotenv_values

from .main_window import MainWindow
from .monthly_tabbed_window import MonthlyTabbedWindow


class LoginWindow(QtWidgets.QWidget):
    """Login screen for Personal Financial Analysis."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Personal Financial Analysis – Login")
        self._load_password_hash()
        self._setup_ui()
        self.main_window = None

    def _load_password_hash(self):
        """Load password hash from .env file."""
        config = dotenv_values(".env")
        self.password_hash = config.get("PASSWORD_HASH", "")

    def _setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)

        self.password_edit = QtWidgets.QLineEdit()
        self.password_edit.setEchoMode(QtWidgets.QLineEdit.Password)
        self.password_edit.setPlaceholderText("Enter password")
        layout.addWidget(self.password_edit)

        self.login_btn = QtWidgets.QPushButton("Login")
        self.login_btn.clicked.connect(self.check_password)
        layout.addWidget(self.login_btn)

    def check_password(self):
        password = self.password_edit.text()
        if hashlib.sha256(password.encode()).hexdigest() == self.password_hash:
            self.main_window = MonthlyTabbedWindow()
            self.main_window.show()
            self.close()
        else:
            QtWidgets.QMessageBox.warning(self, "Error", "Incorrect password")


__all__ = ["LoginWindow"]
