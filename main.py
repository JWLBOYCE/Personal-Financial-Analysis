"""Application entry point for Personal Financial Analysis."""

from PyQt5 import QtWidgets

from gui import MainWindow


def main():
    app = QtWidgets.QApplication([])
    window = MainWindow()
    window.show()
    app.exec_()


if __name__ == '__main__':
    main()
