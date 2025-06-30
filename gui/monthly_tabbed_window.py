from PyQt5 import QtWidgets, QtCore, QtGui
from .navigation_table_widget import NavigationTableWidget
from .dashboard_tab import DashboardTab
from .navigation_table_widget import (
    NavigationTableWidget,
    ORIGINAL_DESC_ROLE,
    CATEGORY_METHOD_ROLE,
    IS_RECURRING_ROLE,
)
from datetime import datetime

# Custom role used to store whether a row is marked as recurring is imported
# above as ``IS_RECURRING_ROLE``.
# Role used to flag the separator row that indicates the last classified point
SEPARATOR_ROLE = QtCore.Qt.UserRole + 2


class TableSection(QtWidgets.QGroupBox):
    """A group box containing a transaction table and total label."""

    def __init__(self, title: str) -> None:
        super().__init__(title)
        layout = QtWidgets.QVBoxLayout(self)

        self.table = NavigationTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(
            ["Date", "Description", "Amount", "Category", "Notes"]
        )
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)

        self.total_label = QtWidgets.QLabel("Total: 0.00")
        layout.addWidget(self.total_label, alignment=QtCore.Qt.AlignRight)

        self.table.itemChanged.connect(self.update_total)
        self.table.itemChanged.connect(
            lambda item: self.table.update_row_tooltip(item.row())
        )

        # Track the row index of the last classified transaction
        self.last_classified_row: int = -1
        self._separator_row: int | None = None

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
        self.table.update_row_tooltip(row)

    def toggle_selected_recurring(self) -> None:
        """Toggle the recurring flag for all selected rows."""
        rows = {idx.row() for idx in self.table.selectedIndexes()}
        for row in rows:
            first_item = self.table.item(row, 0)
            current = bool(first_item.data(IS_RECURRING_ROLE)) if first_item else False
            self.set_row_recurring(row, not current)

    # ------------------------------------------------------------------
    # Classification helpers
    # ------------------------------------------------------------------
    def set_last_classified_row(self, row: int) -> None:
        """Update the last classified row index and redraw the separator."""
        self.last_classified_row = max(-1, min(row, self.table.rowCount() - 1))
        self._draw_separator()

    def _draw_separator(self) -> None:
        """Insert a grey separator row above the first unclassified entry."""
        if self._separator_row is not None:
            self.table.removeRow(self._separator_row)
            self._separator_row = None

        insert_at = self.last_classified_row + 1
        insert_at = max(0, min(insert_at, self.table.rowCount()))
        self.table.insertRow(insert_at)
        for col in range(self.table.columnCount()):
            item = QtWidgets.QTableWidgetItem()
            item.setFlags(QtCore.Qt.NoItemFlags)
            item.setBackground(QtGui.QColor("#d0d0d0"))
            item.setData(SEPARATOR_ROLE, True)
            self.table.setItem(insert_at, col, item)
        self.table.setRowHeight(insert_at, 4)
        self._separator_row = insert_at

    def update_total(self) -> None:
        """Recalculate the total for the Amount column."""
        total = 0.0
        for row in range(self.table.rowCount()):
            # Skip the grey separator row
            first = self.table.item(row, 0)
            if first and first.data(SEPARATOR_ROLE):
                continue
            item = self.table.item(row, 2)
            if item is None:
                continue
            try:
                total += float(item.text())
            except (TypeError, ValueError):
                pass
        self.total_label.setText(f"Total: {total:.2f}")


class SummarySection(QtWidgets.QGroupBox):
    """Panel showing monthly totals."""

    def __init__(self) -> None:
        super().__init__("Monthly Summary")
        layout = QtWidgets.QGridLayout(self)

        self._labels = {}
        rows = [
            ("Total Income", "income"),
            ("Total Expenses", "expenses"),
            ("Net Cashflow", "net"),
            ("Total Credit Card Charges", "credit"),
        ]
        for i, (title, key) in enumerate(rows):
            header = QtWidgets.QLabel(title + ":")
            value = QtWidgets.QLabel("0.00")
            font = QtGui.QFont(value.font())
            font.setBold(True)
            value.setFont(font)
            layout.addWidget(header, i, 0)
            layout.addWidget(value, i, 1)
            self._labels[key] = value

    def set_values(
        self,
        income: float,
        expenses: float,
        net: float,
        credit: float,
    ) -> None:
        self._labels["income"].setText(f"{income:.2f}")
        self._labels["expenses"].setText(f"{expenses:.2f}")
        self._labels["net"].setText(f"{net:.2f}")
        self._labels["credit"].setText(f"{credit:.2f}")


class MonthlyTab(QtWidgets.QWidget):
    """Widget representing a single month's data."""

    SECTION_TITLES = [
        "Income Table",
        "Expenses Table",
        "Credit Card Transactions",
    ]

    def __init__(self, month_name: str) -> None:
        super().__init__()
        layout = QtWidgets.QVBoxLayout(self)

        self.sections = []
        for title in self.SECTION_TITLES:
            section = TableSection(title)
            layout.addWidget(section)
            self.sections.append(section)
            # Show a separator at the top by default
            section.set_last_classified_row(-1)
            section.table.itemChanged.connect(self.update_summary)

        self.summary = SummarySection()
        layout.addWidget(self.summary)

        layout.addStretch(1)

        self.update_summary()

    # --------------------------------------------------------------
    # Summary helpers
    # --------------------------------------------------------------
    def _calc_total(self, section: TableSection) -> float:
        total = 0.0
        for row in range(section.table.rowCount()):
            first = section.table.item(row, 0)
            if first and first.data(SEPARATOR_ROLE):
                continue
            item = section.table.item(row, 2)
            if item is None:
                continue
            try:
                total += float(item.text())
            except (TypeError, ValueError):
                pass
        return total

    def update_summary(self) -> None:
        if len(self.sections) < 3:
            return
        income = self._calc_total(self.sections[0])
        expenses = self._calc_total(self.sections[1])
        credit = self._calc_total(self.sections[2])
        net = income - expenses
        self.summary.set_values(income, expenses, net, credit)


class MonthlyTabbedWindow(QtWidgets.QMainWindow):
    """Main window showing each month as a tab."""

    def __init__(self, months=None) -> None:
        super().__init__()
        self.setWindowTitle("Personal Financial Analysis")
        self.resize(1000, 700)
        months = months or ["March 2024"]
        self._setup_ui(months)
        self.current_month = months[0]

    def _setup_ui(self, months) -> None:
        self.tabs = QtWidgets.QTabWidget()
        self.setCentralWidget(self.tabs)

        toolbar = self.addToolBar("Main")
        new_month_action = QtWidgets.QAction("New Month", self)
        toolbar.addAction(new_month_action)
        new_month_action.triggered.connect(self.add_new_month)

        self.dashboard = DashboardTab()
        self.tabs.addTab(self.dashboard, "Dashboard")

        for month in months:
            tab = MonthlyTab(month)
            self.tabs.addTab(tab, month)

        self.tabs.currentChanged.connect(self._tab_changed)

    def add_new_month(self) -> None:
        """Create a new tab based on the most recent month's data."""
        suggested = datetime.now().strftime("%B %Y")
        name, ok = QtWidgets.QInputDialog.getText(
            self, "New Month", "Month name:", text=suggested
        )
        if not ok or not name.strip():
            return

        if self.tabs.count() == 0:
            tab = MonthlyTab(name.strip())
            self.tabs.addTab(tab, name.strip())
            self.tabs.setCurrentIndex(self.tabs.count() - 1)
            return

        last_tab = self.tabs.widget(self.tabs.count() - 1)
        new_tab = MonthlyTab(name.strip())

        for idx, section in enumerate(last_tab.sections):
            src_table = section.table
            dst_section = new_tab.sections[idx]
            for row in range(src_table.rowCount()):
                first = src_table.item(row, 0)
                if not first or first.data(SEPARATOR_ROLE):
                    continue
                if not first.data(IS_RECURRING_ROLE):
                    continue
                dest_row = dst_section.table.rowCount()
                dst_section.table.insertRow(dest_row)
                for col in range(src_table.columnCount()):
                    src_item = src_table.item(row, col)
                    text = src_item.text() if src_item else ""
                    item = QtWidgets.QTableWidgetItem(text)
                    item.setData(IS_RECURRING_ROLE, True)
                    if src_item is not None:
                        if col == 1:
                            item.setData(
                                ORIGINAL_DESC_ROLE,
                                src_item.data(ORIGINAL_DESC_ROLE) or src_item.text(),
                            )
                        if col == 3:
                            item.setData(
                                CATEGORY_METHOD_ROLE,
                                src_item.data(CATEGORY_METHOD_ROLE) or "manual",
                            )
                    font = QtGui.QFont(item.font())
                    font.setItalic(True)
                    item.setFont(font)
                    dst_section.table.setItem(dest_row, col, item)
                dst_section.table.update_row_tooltip(dest_row)
            dst_section.set_last_classified_row(-1)
            dst_section.update_total()

        new_tab.update_summary()

        self.tabs.addTab(new_tab, name.strip())
        self.tabs.setCurrentIndex(self.tabs.count() - 1)
        self.current_month = name.strip()
        self.dashboard.update_dashboard(self.current_month)


    def _tab_changed(self, index: int) -> None:
        if index == 0:
            self.dashboard.update_dashboard(self.current_month)
        else:
            self.current_month = self.tabs.tabText(index)


__all__ = ["MonthlyTabbedWindow", "MonthlyTab", "TableSection", "SummarySection"]
