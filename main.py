"""Application entry point for Personal Financial Analysis."""

from PyQt5 import QtWidgets


def main():
    app = QtWidgets.QApplication([])
    # TODO: implement GUI initialization
    window = QtWidgets.QMainWindow()
    window.setWindowTitle('Personal Financial Analysis')
    window.show()
    app.exec_()


if __name__ == '__main__':
    main()
