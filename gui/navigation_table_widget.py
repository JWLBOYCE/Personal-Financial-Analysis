from PyQt5 import QtWidgets, QtCore, QtGui


class NavigationTableWidget(QtWidgets.QTableWidget):
    """QTableWidget with simple keyboard navigation helpers."""

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:  # type: ignore[name-defined]
        key = event.key()
        row = self.currentRow()
        col = self.currentColumn()

        if key in (QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter):
            if self.state() == QtWidgets.QAbstractItemView.EditingState:
                self.closePersistentEditor(self.currentItem())
            if row < self.rowCount() - 1:
                self.setCurrentCell(row + 1, col)
            event.accept()
            return

        if key == QtCore.Qt.Key_Escape and self.state() == QtWidgets.QAbstractItemView.EditingState:
            self.closePersistentEditor(self.currentItem())
            event.accept()
            return

        if key == QtCore.Qt.Key_Tab:
            if self.state() == QtWidgets.QAbstractItemView.EditingState:
                self.closePersistentEditor(self.currentItem())
            r, c = row, col + 1
            while r < self.rowCount():
                while c < self.columnCount():
                    item = self.item(r, c)
                    if not item or not (item.flags() & QtCore.Qt.ItemIsEditable):
                        c += 1
                        continue
                    self.setCurrentCell(r, c)
                    event.accept()
                    return
                r += 1
                c = 0
            event.accept()
            return

        if key in (
            QtCore.Qt.Key_Up,
            QtCore.Qt.Key_Down,
            QtCore.Qt.Key_Left,
            QtCore.Qt.Key_Right,
        ):
            if self.state() == QtWidgets.QAbstractItemView.EditingState:
                self.closePersistentEditor(self.currentItem())
            if key == QtCore.Qt.Key_Up and row > 0:
                self.setCurrentCell(row - 1, col)
            elif key == QtCore.Qt.Key_Down and row < self.rowCount() - 1:
                self.setCurrentCell(row + 1, col)
            elif key == QtCore.Qt.Key_Left and col > 0:
                self.setCurrentCell(row, col - 1)
            elif key == QtCore.Qt.Key_Right and col < self.columnCount() - 1:
                self.setCurrentCell(row, col + 1)
            event.accept()
            return

        super().keyPressEvent(event)
