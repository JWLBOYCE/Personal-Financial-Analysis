from PyQt5 import QtWidgets, QtCore
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class MainWindow(QtWidgets.QMainWindow):
    """Main window for Personal Financial Analysis."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Personal Financial Analysis")
        self.resize(1000, 600)
        self._setup_menu()
        self._setup_ui()

    def _setup_menu(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")
        import_csv = QtWidgets.QAction("Import CSV", self)
        import_pdf = QtWidgets.QAction("Import PDF", self)
        archive = QtWidgets.QAction("Archive", self)
        exit_action = QtWidgets.QAction("Exit", self)
        file_menu.addAction(import_csv)
        file_menu.addAction(import_pdf)
        file_menu.addAction(archive)
        file_menu.addSeparator()
        file_menu.addAction(exit_action)
        exit_action.triggered.connect(QtWidgets.qApp.quit)
        menubar.addMenu("Help")

    def _setup_ui(self):
        main_widget = QtWidgets.QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QtWidgets.QHBoxLayout(main_widget)

        # Left sidebar with months
        self.month_list = QtWidgets.QListWidget()
        months = [
            "Jan 2023",
            "Feb 2023",
            "Mar 2023",
            "Apr 2023",
        ]
        self.month_list.addItems(months)
        self.month_list.currentTextChanged.connect(self.load_dummy_data)
        main_layout.addWidget(self.month_list, 1)

        # Right side layout
        right_widget = QtWidgets.QWidget()
        right_layout = QtWidgets.QVBoxLayout(right_widget)
        main_layout.addWidget(right_widget, 4)

        # Top tab bar
        self.tab_bar = QtWidgets.QTabBar(movable=False)
        self.tabs = ["Income", "Expenses", "Credit Card", "Summary"]
        for tab in self.tabs:
            self.tab_bar.addTab(tab)
        self.tab_bar.currentChanged.connect(self.switch_tab)
        right_layout.addWidget(self.tab_bar)

        # Stacked widget for pages
        self.stack = QtWidgets.QStackedWidget()
        right_layout.addWidget(self.stack)

        self.tables = []  # transaction tables for Income/Expenses/Credit Card
        for tab in self.tabs:
            if tab == "Summary":
                summary_widget = QtWidgets.QWidget()
                summary_layout = QtWidgets.QVBoxLayout(summary_widget)
                self.summary_table = QtWidgets.QTableWidget(0, 3)
                self.summary_table.setHorizontalHeaderLabels(
                    ["Category", "Income", "Expense"]
                )
                self.summary_table.horizontalHeader().setStretchLastSection(True)
                summary_layout.addWidget(self.summary_table)

                self.net_label = QtWidgets.QLabel("Net Cashflow: 0.00")
                summary_layout.addWidget(self.net_label)

                self.figure = Figure(figsize=(5, 3))
                self.canvas = FigureCanvas(self.figure)
                summary_layout.addWidget(self.canvas)

                self.stack.addWidget(summary_widget)
                self.summary_widget = summary_widget
            else:
                table = QtWidgets.QTableWidget(0, 4)
                table.setHorizontalHeaderLabels(
                    ["Date", "Description", "Category", "Amount"]
                )
                table.horizontalHeader().setStretchLastSection(True)
                self.stack.addWidget(table)
                self.tables.append(table)

        # Bottom action buttons
        button_widget = QtWidgets.QWidget()
        button_layout = QtWidgets.QHBoxLayout(button_widget)
        self.save_btn = QtWidgets.QPushButton("Save Changes")
        self.new_month_btn = QtWidgets.QPushButton("New Month")
        self.recurring_btn = QtWidgets.QPushButton("Mark Recurring")
        self.export_btn = QtWidgets.QPushButton("Export")
        for btn in (
            self.save_btn,
            self.new_month_btn,
            self.recurring_btn,
            self.export_btn,
        ):
            button_layout.addWidget(btn)
        right_layout.addWidget(button_widget)
        right_layout.setStretchFactor(self.stack, 1)

        # Initialize with dummy data for the first month
        self.month_list.setCurrentRow(0)

    def switch_tab(self, index: int):
        self.stack.setCurrentIndex(index)

    def load_dummy_data(self, month: str):
        """Populate tables with dummy transaction data."""
        for table in self.tables:
            table.setRowCount(0)
            for i in range(5):
                table.insertRow(i)
                date_item = QtWidgets.QTableWidgetItem(f"2023-01-{i+1:02d}")
                desc_item = QtWidgets.QTableWidgetItem(
                    f"{month} transaction {i+1}"
                )
                cat_item = QtWidgets.QTableWidgetItem("Misc")
                amt_item = QtWidgets.QTableWidgetItem(f"{(i+1)*10:.2f}")
                for col, item in enumerate(
                    [date_item, desc_item, cat_item, amt_item]
                ):
                    table.setItem(i, col, item)

        self._update_summary()

    def _update_summary(self) -> None:
        """Update the summary table and chart."""
        totals = {}
        # First table corresponds to Income
        if self.tables:
            income_table = self.tables[0]
            for row in range(income_table.rowCount()):
                category = income_table.item(row, 2).text()
                amount = float(income_table.item(row, 3).text())
                totals.setdefault(category, {"income": 0.0, "expense": 0.0})
                totals[category]["income"] += amount

        # Remaining tables are expenses
        for table in self.tables[1:]:
            for row in range(table.rowCount()):
                category = table.item(row, 2).text()
                amount = float(table.item(row, 3).text())
                totals.setdefault(category, {"income": 0.0, "expense": 0.0})
                totals[category]["expense"] += amount

        self.summary_table.setRowCount(0)
        categories = sorted(totals.keys())
        for i, cat in enumerate(categories):
            self.summary_table.insertRow(i)
            self.summary_table.setItem(i, 0, QtWidgets.QTableWidgetItem(cat))
            self.summary_table.setItem(
                i, 1, QtWidgets.QTableWidgetItem(f"{totals[cat]['income']:.2f}")
            )
            self.summary_table.setItem(
                i, 2, QtWidgets.QTableWidgetItem(f"{totals[cat]['expense']:.2f}")
            )

        total_income = sum(v["income"] for v in totals.values())
        total_expense = sum(v["expense"] for v in totals.values())
        net = total_income - total_expense
        self.net_label.setText(f"Net Cashflow: {net:.2f}")

        # Update bar chart
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        x = range(len(categories))
        incomes = [totals[c]["income"] for c in categories]
        expenses = [totals[c]["expense"] for c in categories]
        ax.bar(x, incomes, width=0.4, label="Income", align="edge")
        ax.bar([i + 0.4 for i in x], expenses, width=0.4, label="Expense", align="edge")
        ax.set_xticks([i + 0.2 for i in x])
        ax.set_xticklabels(categories, rotation=45, ha="right")
        ax.legend()
        ax.set_ylabel("Amount")
        self.figure.tight_layout()
        self.canvas.draw()


__all__ = ["MainWindow"]

