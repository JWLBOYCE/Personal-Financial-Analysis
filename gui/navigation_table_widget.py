from PyQt5 import QtWidgets, QtCore, QtGui

# Roles used by NavigationTableWidget to store extra data
IS_RECURRING_ROLE = QtCore.Qt.UserRole + 1
ORIGINAL_DESC_ROLE = QtCore.Qt.UserRole + 10
CATEGORY_METHOD_ROLE = QtCore.Qt.UserRole + 11


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

    # --------------------------------------------------------------
    # Tooltip helpers
    # --------------------------------------------------------------
    def _find_column(self, name: str) -> int | None:
        """Return the column index whose header matches name."""
        for i in range(self.columnCount()):
            header = self.horizontalHeaderItem(i)
            if header and header.text().strip().lower() == name.lower():
                return i
        return None

    def update_row_tooltip(self, row: int) -> None:
        """Set a tooltip on all items in the row with extra info."""
        desc_col = self._find_column("description")
        if desc_col is None:
            return
        desc_item = self.item(row, desc_col)
        if desc_item is None:
            return
        orig_desc = desc_item.data(ORIGINAL_DESC_ROLE) or desc_item.text()

        cat_col = self._find_column("category")
        method = "manual"
        if cat_col is not None:
            cat_item = self.item(row, cat_col)
            if cat_item and cat_item.data(CATEGORY_METHOD_ROLE):
                method = cat_item.data(CATEGORY_METHOD_ROLE)

        recurring = False
        for c in range(self.columnCount()):
            item = self.item(row, c)
            if item and item.data(IS_RECURRING_ROLE):
                recurring = True
                break

        tooltip = (
            f"Original: {orig_desc}\n"
            f"Category Source: {method}\n"
            f"Recurring: {'Yes' if recurring else 'No'}"
        )
        for c in range(self.columnCount()):
            item = self.item(row, c)
            if item:
                item.setToolTip(tooltip)

