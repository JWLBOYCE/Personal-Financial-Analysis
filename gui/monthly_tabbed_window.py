from PyQt5 import QtWidgets, QtCore, QtGui
import os

DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"
import pandas as pd
from .navigation_table_widget import (
    NavigationTableWidget,
    ORIGINAL_DESC_ROLE,
    CATEGORY_METHOD_ROLE,
    IS_RECURRING_ROLE,
)
from .dashboard_tab import DashboardTab
from .recurring_tab import RecurringTab
from .table_manager import TransactionTableManager
from datetime import datetime
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

# Custom role used to store whether a row is marked as recurring is imported
# above as ``IS_RECURRING_ROLE``.
# Role used to flag the separator row that indicates the last classified point
SEPARATOR_ROLE = QtCore.Qt.UserRole + 2


class TableSection(QtWidgets.QGroupBox):
    """A group box containing a transaction table and total label."""

    def __init__(self, title: str) -> None:
        super().__init__(title)
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum
        )
        layout = QtWidgets.QVBoxLayout(self)

        self.table = NavigationTableWidget(0, 5)
        self.table.setSizeAdjustPolicy(
            QtWidgets.QAbstractScrollArea.AdjustToContents
        )
        self.total_label = QtWidgets.QLabel("Total: 0.00")
        label_policy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum
        )
        self.total_label.setSizePolicy(label_policy)
        self.manager = TransactionTableManager(self.table, self.total_label)
        self.manager.set_headers([
            "Date",
            "Description",
            "Amount",
            "Category",
            "Notes",
        ])
        layout.addWidget(self.table)
        layout.addWidget(self.total_label, alignment=QtCore.Qt.AlignRight)
        layout.setStretch(0, 1)
        layout.setStretch(1, 0)

        # Keep the summary table in sync
        self.table.cellChanged.connect(lambda *_: self.update_total())
        self.table.model().rowsInserted.connect(lambda *_: self.update_total())
        self.table.model().rowsRemoved.connect(lambda *_: self.update_total())

        # Track the row index of the last classified transaction
        self.last_classified_row: int = -1
        self._separator_row: int | None = None

    # ------------------------------------------------------------------
    # Recurring row helpers
    # ------------------------------------------------------------------
    def set_row_recurring(self, row: int, recurring: bool) -> None:
        """Mark a row as recurring and update its font style."""
        self.manager.apply_recurring_format(row, recurring)

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
        self.manager.update_total()


from .data_table_section import DataTableSection


class SummarySection(QtWidgets.QGroupBox):
    """Panel showing monthly totals."""

    def __init__(self, month_name: str) -> None:
        super().__init__("Monthly Summary")
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum
        )
        layout = QtWidgets.QGridLayout(self)
        self.month_name = month_name

        self._labels = {}
        rows = [
            ("Total Income", "income"),
            ("Total Expenses", "expenses"),
            ("Net Cashflow", "net"),
            ("Total Credit Card Charges", "credit"),
        ]
        for i, (title, key) in enumerate(rows):
            header = QtWidgets.QLabel(title + ":")
            header.setSizePolicy(
                QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum
            )
            value = QtWidgets.QLabel("0.00")
            value.setSizePolicy(
                QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum
            )
            font = QtGui.QFont(value.font())
            font.setBold(True)
            value.setFont(font)
            layout.addWidget(header, i, 0)
            layout.addWidget(value, i, 1)
            self._labels[key] = value

        self.export_btn = QtWidgets.QPushButton("Export")
        layout.addWidget(
            self.export_btn,
            len(rows),
            0,
            1,
            2,
            alignment=QtCore.Qt.AlignRight,
        )
        self.export_btn.clicked.connect(self.export_summary)

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

    def export_summary(self) -> None:
        """Write the summary values to a CSV file."""
        income = float(self._labels["income"].text())
        expenses = float(self._labels["expenses"].text())
        net = float(self._labels["net"].text())
        credit = float(self._labels["credit"].text())

        data = {
            "Total Income": [income],
            "Total Expenses": [expenses],
            "Net Cashflow": [net],
            "Credit Card Spend": [credit],
        }
        df = pd.DataFrame(data)

        os.makedirs("exports", exist_ok=True)
        month = self.month_name.replace(" ", "_")
        path = os.path.join("exports", f"summary_{month}.csv")
        df.to_csv(path, index=False)
        QtWidgets.QMessageBox.information(
            self,
            "Export",
            f"Summary exported to {path}",
        )


class MonthlyTab(QtWidgets.QMainWindow):
    """Dockable monthly view with movable panels."""

    def __init__(self, month_name: str) -> None:
        super().__init__()
        self.month_name = month_name
        self.setObjectName(f"MonthlyTab_{month_name}")
        self.setDockOptions(
            QtWidgets.QMainWindow.AllowNestedDocks
            | QtWidgets.QMainWindow.AnimatedDocks
        )
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)

        def make_dock(title: str, widget: QtWidgets.QWidget, area: QtCore.Qt.DockWidgetArea) -> QtWidgets.QDockWidget:
            dock = QtWidgets.QDockWidget(title, self)
            dock.setObjectName(title.replace(" ", "") + "Dock")
            dock.setWidget(widget)
            dock.setAllowedAreas(QtCore.Qt.AllDockWidgetAreas)
            dock.setFeatures(
                QtWidgets.QDockWidget.DockWidgetMovable
                | QtWidgets.QDockWidget.DockWidgetFloatable
            )
            self.addDockWidget(area, dock)
            return dock

        sections_info = [
            ("Income Table", "income"),
            ("Expenses Table", "expenses"),
            ("Withdrawals Table", "withdrawals"),
            ("Assets Table", "assets"),
            ("Liabilities Table", "liabilities"),
            ("Provisions Table", "provisions"),
            ("Credit Card Classifier Table", "credit_card"),
            ("Cash at Month End Table", "cash_end"),
            ("Cash Crosscheck Table", "cash_crosscheck"),
            ("Net Worth Table", "net_worth"),
            ("Asset Allocation Table", "asset_allocation"),
        ]

        self.sections = [DataTableSection(title, key, self.month_name) for title, key in sections_info]
        for section in self.sections:
            section.set_last_classified_row(-1)

        income_section = self.sections[0]

        passive_group = QtWidgets.QGroupBox("Passive Income")
        passive_group.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum
        )
        passive_layout = QtWidgets.QVBoxLayout(passive_group)
        self.passive_fig = Figure(figsize=(4, 3))
        self.passive_canvas = FigureCanvas(self.passive_fig)
        policy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum
        )
        self.passive_canvas.setSizePolicy(policy)
        passive_layout.addWidget(self.passive_canvas)
        passive_layout.setStretch(0, 1)

        income_section.table.cellChanged.connect(lambda *_: self.update_passive_chart())
        income_section.table.model().rowsInserted.connect(lambda *_: self.update_passive_chart())
        income_section.table.model().rowsRemoved.connect(lambda *_: self.update_passive_chart())

        aa_chart_group = QtWidgets.QGroupBox("Asset Allocation Pie Charts")
        aa_chart_group.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum
        )
        aa_chart_layout = QtWidgets.QHBoxLayout(aa_chart_group)
        self.target_fig = Figure(figsize=(3, 3))
        self.target_canvas = FigureCanvas(self.target_fig)
        self.target_canvas.setSizePolicy(policy)
        self.actual_fig = Figure(figsize=(3, 3))
        self.actual_canvas = FigureCanvas(self.actual_fig)
        self.actual_canvas.setSizePolicy(policy)
        aa_chart_layout.addWidget(self.target_canvas)
        aa_chart_layout.addWidget(self.actual_canvas)
        aa_chart_layout.setStretch(0, 1)
        aa_chart_layout.setStretch(1, 1)


        self.asset_table_section = TableSection("Asset Allocation Table")
        self.asset_table_section.manager.set_headers([
            "Asset Class",
            "Target",
            "Actual",
        ])
        table = self.asset_table_section.table
        table.cellChanged.connect(lambda *_: self.update_asset_charts())
        table.model().rowsInserted.connect(lambda *_: self.update_asset_charts())
        table.model().rowsRemoved.connect(lambda *_: self.update_asset_charts())
        self.update_asset_charts()

        provisions_section = TableSection("Provisions Table")
        cc_classifier_section = TableSection("Credit Card Classifier Table")

        dock_map = {
            "Income Table": QtCore.Qt.LeftDockWidgetArea,
            "Expenses Table": QtCore.Qt.LeftDockWidgetArea,
            "Withdrawals Table": QtCore.Qt.LeftDockWidgetArea,
            "Assets Table": QtCore.Qt.LeftDockWidgetArea,
            "Liabilities Table": QtCore.Qt.LeftDockWidgetArea,
            "Net Worth Table": QtCore.Qt.LeftDockWidgetArea,
            "Provisions Table": QtCore.Qt.RightDockWidgetArea,
            "Credit Card Classifier Table": QtCore.Qt.RightDockWidgetArea,
            "Cash at Month End Table": QtCore.Qt.RightDockWidgetArea,
            "Cash Crosscheck Table": QtCore.Qt.RightDockWidgetArea,
            "Asset Allocation Table": QtCore.Qt.RightDockWidgetArea,
        }


        make_dock("Passive Income", passive_group, QtCore.Qt.RightDockWidgetArea)
        make_dock("Asset Allocation Charts", aa_chart_group, QtCore.Qt.RightDockWidgetArea)
        make_dock("Asset Allocation Table", self.asset_table_section, QtCore.Qt.RightDockWidgetArea)
        make_dock("Provisions Table", provisions_section, QtCore.Qt.RightDockWidgetArea)
        make_dock("Credit Card Classifier", cc_classifier_section, QtCore.Qt.RightDockWidgetArea)

        self._load_layout()

    def _load_layout(self) -> None:
        """Restore dock layout from settings."""
        settings = QtCore.QSettings("PFA", "DockLayout")
        settings.beginGroup(self.objectName())
        geom = settings.value("geometry")
        state = settings.value("state")
        if isinstance(geom, QtCore.QByteArray):
            self.restoreGeometry(geom)
        if isinstance(state, QtCore.QByteArray):
            self.restoreState(state)
        settings.endGroup()

    def save_layout(self) -> None:
        """Persist the current dock layout."""
        settings = QtCore.QSettings("PFA", "DockLayout")
        settings.beginGroup(self.objectName())
        settings.setValue("geometry", self.saveGeometry())
        settings.setValue("state", self.saveState())
        settings.endGroup()

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:  # type: ignore[override]
        self.save_layout()
        super().closeEvent(event)

        self.update_passive_chart()

    def update_summary(self) -> None:
        """Placeholder for compatibility."""
        pass

    def _gather_passive_income(self) -> dict[str, float]:
        table = self.sections[0].table
        headers = {table.horizontalHeaderItem(i).text().strip().lower(): i for i in range(table.columnCount())}
        desc_col = headers.get("description")
        amount_col = headers.get("amount")
        if desc_col is None or amount_col is None:
            return {}
        totals: dict[str, float] = {}
        for row in range(table.rowCount()):
            if table.item(row, 0) and table.item(row, 0).data(SEPARATOR_ROLE):
                continue
            desc_item = table.item(row, desc_col)
            amt_item = table.item(row, amount_col)
            if desc_item is None or amt_item is None:
                continue
            desc = desc_item.text().lower()
            try:
                amt = float(amt_item.text())
            except ValueError:
                continue
            if "chip" in desc:
                key = "Chip Interest"
            elif "premium" in desc and "bond" in desc:
                key = "Premium Bonds"
            elif "interest" in desc:
                key = "Interest"
            elif "dividend" in desc:
                key = "Dividends"
            else:
                continue
            totals[key] = totals.get(key, 0.0) + amt
        return totals

    def update_passive_chart(self) -> None:
        totals = self._gather_passive_income()
        self.passive_fig.clear()
        ax = self.passive_fig.add_subplot(111)
        labels = list(totals.keys())
        amounts = [totals[l] for l in labels]
        ax.bar(labels, amounts)
        ax.set_ylabel("Amount")
        ax.set_title("Passive Income Sources")
        self.passive_fig.tight_layout()
        self.passive_canvas.draw()

    def _gather_asset_allocation(self) -> tuple[dict[str, float], dict[str, float]]:
        table = self.asset_table_section.table
        headers = {
            table.horizontalHeaderItem(i).text().strip().lower(): i
            for i in range(table.columnCount())
        }
        asset_col = headers.get("asset class") or headers.get("asset")
        target_col = headers.get("target")
        actual_col = headers.get("actual")
        if asset_col is None or target_col is None or actual_col is None:
            return {}, {}

        targets: dict[str, float] = {}
        actuals: dict[str, float] = {}
        for row in range(table.rowCount()):
            if table.item(row, 0) and table.item(row, 0).data(SEPARATOR_ROLE):
                continue
            asset_item = table.item(row, asset_col)
            target_item = table.item(row, target_col)
            actual_item = table.item(row, actual_col)
            if asset_item is None or target_item is None or actual_item is None:
                continue
            asset = asset_item.text()
            try:
                target_val = float(target_item.text().rstrip("%"))
                actual_val = float(actual_item.text().rstrip("%"))
            except ValueError:
                continue
            targets[asset] = target_val
            actuals[asset] = actual_val

        return targets, actuals

    def update_asset_charts(self) -> None:
        targets, actuals = self._gather_asset_allocation()

        self.target_fig.clear()
        ax1 = self.target_fig.add_subplot(111)
        labels = list(targets.keys())
        values = [targets[l] for l in labels]
        if values:
            ax1.pie(values, labels=labels, autopct="%1.1f%%")
        ax1.set_title("Target Asset Allocation")
        self.target_fig.tight_layout()
        self.target_canvas.draw()

        self.actual_fig.clear()
        ax2 = self.actual_fig.add_subplot(111)
        labels_a = list(actuals.keys())
        values_a = [actuals[l] for l in labels_a]
        if values_a:
            ax2.pie(values_a, labels=labels_a, autopct="%1.1f%%")
        ax2.set_title("Actual Asset Allocation")
        self.actual_fig.tight_layout()
        self.actual_canvas.draw()


class MonthlyTabbedWindow(QtWidgets.QMainWindow):
    """Main window showing each month as a tab."""

    def __init__(self, months=None) -> None:
        super().__init__()
        self.setWindowTitle("Personal Financial Analysis")
        self.resize(1000, 700)
        months = months or self._generate_default_months()
        self._setup_ui(months)
        self.current_month = months[0]

    def _generate_default_months(self):
        """Return a list of upcoming months for the sidebar."""
        start = pd.Timestamp("2025-03-01")
        dates = pd.date_range(start, periods=3, freq="MS")
        return [d.strftime("%B %Y") for d in dates]

    def _setup_ui(self, months) -> None:
        main_widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(main_widget)
        if DEMO_MODE:
            banner = QtWidgets.QLabel("DEMO MODE ACTIVE")
            banner.setAlignment(QtCore.Qt.AlignCenter)
            banner.setStyleSheet(
                "background-color: #c00; color: white; font-weight: bold; padding: 4px;"
            )
            layout.addWidget(banner)

        # Central stacked area for monthly views
        self.month_stack = QtWidgets.QStackedWidget()
        layout.addWidget(self.month_stack)

        self.tabs = QtWidgets.QTabWidget()
        # Tab labels in dark text for high contrast
        self.tabs.tabBar().setStyleSheet("QTabBar::tab{color:#111;}")
        layout.addWidget(self.tabs)

        layout.setStretch(layout.indexOf(self.month_stack), 1)
        layout.setStretch(layout.indexOf(self.tabs), 0)
        self.setCentralWidget(main_widget)

        # Sidebar dock containing month list
        self.month_list = QtWidgets.QListWidget()
        self.month_list.addItems(months)
        self.month_list.setCurrentRow(0)
        self.month_list.currentRowChanged.connect(self._month_selected)
        self.month_list.setStyleSheet(
            "QListWidget{background:#ffffff;color:#000;}"
        )
        dock = QtWidgets.QDockWidget("Months", self)
        dock.setObjectName("MonthsDock")
        dock.setWidget(self.month_list)
        dock.setFeatures(QtWidgets.QDockWidget.NoDockWidgetFeatures)
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, dock)

        toolbar = self.addToolBar("Main")
        new_month_action = QtWidgets.QAction("New Month", self)
        toolbar.addAction(new_month_action)
        new_month_action.triggered.connect(self.add_new_month)

        self.dashboard = DashboardTab()
        self.tabs.addTab(self.dashboard, "Dashboard")

        self.recurring = RecurringTab()
        self.tabs.addTab(self.recurring, "Recurring Transactions")

        for month in months:
            tab = MonthlyTab(month)
            wrapper = self._wrap_month_tab(tab)
            self.month_stack.addWidget(wrapper)

        self.tabs.currentChanged.connect(self._tab_changed)
        self.month_stack.setCurrentIndex(0)

    def _wrap_month_tab(self, tab: QtWidgets.QWidget) -> QtWidgets.QScrollArea:
        """Return a scroll area containing the given monthly tab."""
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        container = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        tab.setSizePolicy(policy)
        container.setSizePolicy(policy)
        layout.addWidget(tab)
        scroll.setWidget(container)
        return scroll

    def _unwrap_month_tab(self, widget: QtWidgets.QWidget) -> QtWidgets.QWidget:
        """Return the MonthlyTab contained in the scroll area."""
        if isinstance(widget, QtWidgets.QScrollArea):
            container = widget.widget()
            if (
                isinstance(container, QtWidgets.QWidget)
                and container.layout()
                and container.layout().count() > 0
            ):
                return container.layout().itemAt(0).widget()
        return widget

    def _month_selected(self, row: int) -> None:
        if 0 <= row < self.month_stack.count():
            self.month_stack.setCurrentIndex(row)
            self.current_month = self.month_list.item(row).text()
            self.dashboard.update_dashboard(self.current_month)

    def add_new_month(self) -> None:
        """Create a new tab based on the most recent month's data."""
        suggested = datetime.now().strftime("%B %Y")
        name, ok = QtWidgets.QInputDialog.getText(
            self, "New Month", "Month name:", text=suggested
        )
        if not ok or not name.strip():
            return

        if self.month_stack.count() == 0:
            tab = MonthlyTab(name.strip())
            wrapper = self._wrap_month_tab(tab)
            self.month_stack.addWidget(wrapper)
            self.month_stack.setCurrentIndex(0)
            return

        last_widget = self.month_stack.widget(self.month_stack.count() - 1)
        last_tab = self._unwrap_month_tab(last_widget)

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
                values = [
                    src_table.item(row, c).text() if src_table.item(row, c) else ""
                    for c in range(src_table.columnCount())
                ]
                dest_row = dst_section.manager.add_row(values, recurring=True)
                for col in range(src_table.columnCount()):
                    src_item = src_table.item(row, col)
                    dst_item = dst_section.table.item(dest_row, col)
                    if src_item is None or dst_item is None:
                        continue
                    if col == 1:
                        dst_item.setData(
                            ORIGINAL_DESC_ROLE,
                            src_item.data(ORIGINAL_DESC_ROLE) or src_item.text(),
                        )
                    if col == 3:
                        dst_item.setData(
                            CATEGORY_METHOD_ROLE,
                            src_item.data(CATEGORY_METHOD_ROLE) or "manual",
                        )
                dst_section.table.update_row_tooltip(dest_row)
            dst_section.set_last_classified_row(-1)
            dst_section.update_total()

        new_tab.update_summary()

        wrapper = self._wrap_month_tab(new_tab)
        self.month_stack.addWidget(wrapper)
        self.month_list.addItem(name.strip())
        new_index = self.month_stack.count() - 1
        self.month_stack.setCurrentIndex(new_index)
        self.month_list.setCurrentRow(new_index)
        self.current_month = name.strip()
        self.dashboard.update_dashboard(self.current_month)


    def _tab_changed(self, index: int) -> None:
        widget = self.tabs.widget(index)
        if widget is self.dashboard:
            self.dashboard.update_dashboard(self.current_month)
        elif widget is self.recurring:
            self.recurring.load_data()

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:  # type: ignore[override]
        for i in range(self.month_stack.count()):
            widget = self.month_stack.widget(i)
            tab = self._unwrap_month_tab(widget)
            if hasattr(tab, "save_layout"):
                tab.save_layout()
        super().closeEvent(event)


__all__ = [
    "MonthlyTabbedWindow",
    "MonthlyTab",
    "TableSection",
    "DataTableSection",
    "SummarySection",
    "RecurringTab",
]
