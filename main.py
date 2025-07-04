"""Application entry point for Personal Financial Analysis."""

from PyQt5 import QtWidgets
from dotenv import dotenv_values
import hashlib

from gui import LoginWindow


def main():
    app = QtWidgets.QApplication([])

    config = dotenv_values(".env")
    password_hash = config.get("PASSWORD_HASH")
    if not password_hash:
        pwd, ok = QtWidgets.QInputDialog.getText(
            None,
            "Create Password",
            "Set a new password:",
            QtWidgets.QLineEdit.Password,
        )
        if not ok or not pwd:
            return
        confirm, ok = QtWidgets.QInputDialog.getText(
            None,
            "Confirm Password",
            "Re-enter password:",
            QtWidgets.QLineEdit.Password,
        )
        if not ok or pwd != confirm:
            QtWidgets.QMessageBox.warning(None, "Error", "Passwords do not match")
            return
        password_hash = hashlib.sha256(pwd.encode()).hexdigest()
        with open(".env", "w") as f:
            f.write(f"PASSWORD_HASH={password_hash}\n")

    login = LoginWindow()
    login.show()
    app.exec_()


if __name__ == '__main__':
    main()
