from PyQt5 import QtWidgets, QtCore


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
        self.tables = []
        for _ in self.tabs:
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


__all__ = ["MainWindow"]

