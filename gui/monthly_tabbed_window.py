from PyQt5 import QtWidgets, QtCore, QtGui

# Custom role used to store whether a row is marked as recurring
IS_RECURRING_ROLE = QtCore.Qt.UserRole + 1


class TableSection(QtWidgets.QGroupBox):
    """A group box containing a transaction table and total label."""

    def __init__(self, title: str) -> None:
        super().__init__(title)
        layout = QtWidgets.QVBoxLayout(self)

        self.table = QtWidgets.QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(
            ["Date", "Description", "Amount", "Category", "Notes"]
        )
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)

        self.total_label = QtWidgets.QLabel("Total: 0.00")
        layout.addWidget(self.total_label, alignment=QtCore.Qt.AlignRight)

        self.table.itemChanged.connect(self.update_total)

    # ------------------------------------------------------------------
    # Recurring row helpers
    # ------------------------------------------------------------------
    def set_row_recurring(self, row: int, recurring: bool) -> None:
        """Mark a row as recurring and update its font style."""
        for col in range(self.table.columnCount()):
            item = self.table.item(row, col)
            if item is None:
                continue
            item.setData(IS_RECURRING_ROLE, recurring)
            font = QtGui.QFont(item.font())
            font.setItalic(recurring)
            item.setFont(font)

    def toggle_selected_recurring(self) -> None:
        """Toggle the recurring flag for all selected rows."""
        rows = {idx.row() for idx in self.table.selectedIndexes()}
        for row in rows:
            first_item = self.table.item(row, 0)
            current = bool(first_item.data(IS_RECURRING_ROLE)) if first_item else False
            self.set_row_recurring(row, not current)

    def update_total(self) -> None:
        """Recalculate the total for the Amount column."""
        total = 0.0
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 2)
            if item is None:
                continue
            try:
                total += float(item.text())
            except (TypeError, ValueError):
                pass
        self.total_label.setText(f"Total: {total:.2f}")


class MonthlyTab(QtWidgets.QWidget):
    """Widget representing a single month's data."""

    SECTION_TITLES = [
        "Income Table",
        "Expenses Table",
        "Credit Card Transactions",
        "Monthly Summary",
    ]

    def __init__(self, month_name: str) -> None:
        super().__init__()
        layout = QtWidgets.QVBoxLayout(self)

        self.sections = []
        for title in self.SECTION_TITLES:
            section = TableSection(title)
            layout.addWidget(section)
            self.sections.append(section)

        layout.addStretch(1)


class MonthlyTabbedWindow(QtWidgets.QMainWindow):
    """Main window showing each month as a tab."""

    def __init__(self, months=None) -> None:
        super().__init__()
        self.setWindowTitle("Personal Financial Analysis")
        self.resize(1000, 700)
        months = months or ["March 2024"]
        self._setup_ui(months)

    def _setup_ui(self, months) -> None:
        self.tabs = QtWidgets.QTabWidget()
        self.setCentralWidget(self.tabs)

        for month in months:
            tab = MonthlyTab(month)
            self.tabs.addTab(tab, month)


__all__ = ["MonthlyTabbedWindow", "MonthlyTab", "TableSection"]
