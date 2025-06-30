"""Application entry point for Personal Financial Analysis."""

from PyQt5 import QtWidgets

from gui import LoginWindow


def main():
    app = QtWidgets.QApplication([])
    login = LoginWindow()
    login.show()
    app.exec_()


if __name__ == '__main__':
    main()
