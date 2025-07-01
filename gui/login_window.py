from PyQt5 import QtWidgets, QtGui, QtCore
import hashlib
import base64
from dotenv import dotenv_values

from .monthly_tabbed_window import MonthlyTabbedWindow

WELCOME_IMAGE_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4nGNgYAAAAAMAASsJTYQA"
    "AAAASUVORK5CYII="
)


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
        layout = QtWidgets.QVBoxLayout()
        layout.setAlignment(QtCore.Qt.AlignCenter)
        self.setLayout(layout)

        # Welcome image
        image_label = QtWidgets.QLabel()
        pixmap = QtGui.QPixmap()
        pixmap.loadFromData(base64.b64decode(WELCOME_IMAGE_B64))
        image_label.setPixmap(pixmap)
        image_label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(image_label)

        # Welcome text
        text_label = QtWidgets.QLabel("Welcome James")
        text_label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(text_label)

        # Password entry
        self.password_edit = QtWidgets.QLineEdit()
        self.password_edit.setEchoMode(QtWidgets.QLineEdit.Password)
        self.password_edit.setPlaceholderText("Enter password")
        self.password_edit.setStyleSheet(
            "color: #111; background-color: white;"
        )
        pal = self.password_edit.palette()
        pal.setColor(QtGui.QPalette.Text, QtGui.QColor("#111"))
        pal.setColor(QtGui.QPalette.Base, QtGui.QColor("white"))
        pal.setColor(QtGui.QPalette.PlaceholderText, QtGui.QColor("#111"))
        self.password_edit.setPalette(pal)
        font = self.password_edit.font()
        font.setPointSize(font.pointSize() + 2)
        self.password_edit.setFont(font)
        self.password_edit.setFixedHeight(40)
        layout.addWidget(self.password_edit)

        # Login button
        self.login_btn = QtWidgets.QPushButton("Login")
        btn_font = self.login_btn.font()
        btn_font.setPointSize(font.pointSize())
        self.login_btn.setFont(btn_font)
        self.login_btn.setFixedHeight(40)
        self.login_btn.clicked.connect(self.check_password)
        layout.addWidget(self.login_btn)

        # High contrast styling
        self.setStyleSheet("background-color: #ffffff; color: #111;")

    def check_password(self):
        password = self.password_edit.text()
        if hashlib.sha256(password.encode()).hexdigest() == self.password_hash:
            self.main_window = MonthlyTabbedWindow()
            self.main_window.show()
            self.close()
        else:
            QtWidgets.QMessageBox.warning(self, "Error", "Incorrect password")


__all__ = ["LoginWindow"]
