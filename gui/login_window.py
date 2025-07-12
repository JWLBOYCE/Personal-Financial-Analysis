import os
from PyQt5 import QtWidgets, QtGui, QtCore
import hashlib
from dotenv import dotenv_values

from .main_window import MainWindow


class LoginWindow(QtWidgets.QWidget):
    """Login screen for Personal Financial Analysis."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Personal Financial Analysis – Login")
        self.setStyleSheet("background-color: #ffffff; color: #000000;")
        self._load_password_hash()
        self._setup_ui()
        self.main_window = None

    def _load_password_hash(self):
        """Load password hash from .env file."""
        config = dotenv_values(".env")
        self.password_hash = config.get("PASSWORD_HASH", "")

    def _setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setAlignment(QtCore.Qt.AlignCenter)

        self.image_label = QtWidgets.QLabel()
        img_path = os.path.join(os.path.dirname(__file__), "..", "welcome.png")
        pixmap = QtGui.QPixmap(img_path)
        if not pixmap.isNull():
            pixmap = pixmap.scaledToWidth(300, QtCore.Qt.SmoothTransformation)
            self.image_label.setPixmap(pixmap)
        else:
            self.image_label.setText("Welcome image not found.")
        self.image_label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(self.image_label)

        self.welcome_label = QtWidgets.QLabel("Welcome James")
        self.welcome_label.setAlignment(QtCore.Qt.AlignCenter)
        self.welcome_label.setStyleSheet("font-size: 18px;")
        layout.addWidget(self.welcome_label)

        self.password_edit = QtWidgets.QLineEdit()
        self.password_edit.setEchoMode(QtWidgets.QLineEdit.Password)
        self.password_edit.setPlaceholderText("Enter password")
        self.password_edit.setStyleSheet(
            "background-color: #ffffff; color: #000000; padding: 4px;"
        )
        layout.addWidget(self.password_edit)

        self.login_btn = QtWidgets.QPushButton("Login")
        self.login_btn.setStyleSheet(
            "background-color: #dddddd; color: #000000; padding: 4px;"
        )
        self.login_btn.clicked.connect(self.check_password)
        layout.addWidget(self.login_btn)

    def check_password(self):
        password = self.password_edit.text()
        if hashlib.sha256(password.encode()).hexdigest() == self.password_hash:
            self.main_window = MainWindow()
            self.main_window.show()
            self.close()
        else:
            QtWidgets.QMessageBox.warning(self, "Error", "Incorrect password")


__all__ = ["LoginWindow"]
