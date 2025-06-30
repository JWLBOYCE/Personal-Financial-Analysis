from PyQt5 import QtWidgets, QtCore
import hashlib


class UnlockDialog(QtWidgets.QDialog):
    """Simple password dialog displayed when the screen is locked."""

    def __init__(self, password_hash: str) -> None:
        super().__init__()
        self.setWindowTitle("Unlock")
        self._hash = password_hash

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(QtWidgets.QLabel("Enter password to unlock:"))
        self.edit = QtWidgets.QLineEdit()
        self.edit.setEchoMode(QtWidgets.QLineEdit.Password)
        layout.addWidget(self.edit)
        btn = QtWidgets.QPushButton("Unlock")
        layout.addWidget(btn)
        btn.clicked.connect(self._check)

    def _check(self) -> None:
        text = self.edit.text()
        if hashlib.sha256(text.encode()).hexdigest() == self._hash:
            self.accept()
        else:
            QtWidgets.QMessageBox.warning(self, "Error", "Incorrect password")


class InactivityFilter(QtCore.QObject):
    """Event filter that locks the screen after a period of inactivity."""

    def __init__(self, password_hash: str, timeout_ms: int = 600_000) -> None:
        super().__init__()
        self._hash = password_hash
        self._timer = QtCore.QTimer(self)
        self._timer.setInterval(timeout_ms)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._lock)
        self._timer.start()

    def eventFilter(self, obj: QtCore.QObject, event: QtCore.QEvent) -> bool:  # type: ignore[override]
        if event.type() in (
            QtCore.QEvent.MouseMove,
            QtCore.QEvent.MouseButtonPress,
            QtCore.QEvent.KeyPress,
            QtCore.QEvent.Wheel,
        ):
            self._timer.start()
        return False

    def _lock(self) -> None:
        dlg = UnlockDialog(self._hash)
        dlg.exec_()
        self._timer.start()
