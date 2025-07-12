from PyQt5 import QtWidgets, QtCore
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import sqlite3
from logic.categoriser import DB_PATH, _ensure_db
from .data_import_panel import DataImportPanel


class MainWindow(QtWidgets.QMainWindow):
    """Main window for Personal Financial Analysis."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Personal Financial Analysis")
        self.resize(1000, 600)
        self.setStyleSheet("background-color: lightblue;")
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
        self.tabs = [
            "Income",
            "Expenses",
            "Credit Card",
            "Summary",
            "Admin",
            "Data Import",
        ]
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
            elif tab == "Admin":
                admin_widget = QtWidgets.QWidget()
                admin_layout = QtWidgets.QVBoxLayout(admin_widget)
                self.mapping_table = QtWidgets.QTableWidget(0, 3)
                self.mapping_table.setHorizontalHeaderLabels(
                    ["Keyword", "Category", "Last Used"]
                )
                self.mapping_table.horizontalHeader().setStretchLastSection(True)
                admin_layout.addWidget(self.mapping_table)

                btn_layout = QtWidgets.QHBoxLayout()
                self.edit_mapping_btn = QtWidgets.QPushButton("Edit")
                self.delete_mapping_btn = QtWidgets.QPushButton("Delete")
                self.retrain_btn = QtWidgets.QPushButton("Retrain Classifier")
                for b in (
                    self.edit_mapping_btn,
                    self.delete_mapping_btn,
                    self.retrain_btn,
                ):
                    btn_layout.addWidget(b)
                admin_layout.addLayout(btn_layout)

                self.edit_mapping_btn.clicked.connect(self.edit_mapping)
                self.delete_mapping_btn.clicked.connect(self.delete_mapping)
                self.retrain_btn.clicked.connect(self.retrain_classifier)

                self.stack.addWidget(admin_widget)
                self.admin_widget = admin_widget
            elif tab == "Data Import":
                import_widget = DataImportPanel()
                self.stack.addWidget(import_widget)
                self.import_widget = import_widget
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
        if self.tabs[index] == "Admin":
            self.load_mappings()

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

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        _ensure_db(conn)
        return conn

    def load_mappings(self) -> None:
        """Load keyword mappings into the admin table."""
        conn = self._get_conn()
        cur = conn.execute(
            """
            SELECT m.id, m.keyword, c.name AS category, m.last_used
            FROM mappings m LEFT JOIN categories c ON m.category_id = c.id
            ORDER BY m.keyword
            """
        )
        rows = cur.fetchall()
        self.mapping_table.setRowCount(0)
        for i, row in enumerate(rows):
            self.mapping_table.insertRow(i)
            item = QtWidgets.QTableWidgetItem(row["keyword"])
            item.setData(QtCore.Qt.UserRole, row["id"])
            self.mapping_table.setItem(i, 0, item)
            self.mapping_table.setItem(
                i, 1, QtWidgets.QTableWidgetItem(row["category"] or "")
            )
            self.mapping_table.setItem(
                i, 2, QtWidgets.QTableWidgetItem(row["last_used"] or "")
            )
        self.mapping_table.resizeColumnsToContents()
        conn.close()

    def delete_mapping(self) -> None:
        row = self.mapping_table.currentRow()
        if row < 0:
            return
        item = self.mapping_table.item(row, 0)
        mid = item.data(QtCore.Qt.UserRole)
        conn = self._get_conn()
        conn.execute("DELETE FROM mappings WHERE id = ?", (mid,))
        conn.commit()
        conn.close()
        self.mapping_table.removeRow(row)

    def edit_mapping(self) -> None:
        row = self.mapping_table.currentRow()
        if row < 0:
            return
        item_keyword = self.mapping_table.item(row, 0)
        item_category = self.mapping_table.item(row, 1)
        keyword, ok = QtWidgets.QInputDialog.getText(
            self, "Edit Keyword", "Keyword:", text=item_keyword.text()
        )
        if not ok or not keyword.strip():
            return
        category, ok = QtWidgets.QInputDialog.getText(
            self, "Edit Category", "Category:", text=item_category.text()
        )
        if not ok or not category.strip():
            return
        conn = self._get_conn()
        cur = conn.execute(
            "SELECT id FROM categories WHERE name = ?", (category.strip(),)
        )
        cat_row = cur.fetchone()
        if cat_row:
            cat_id = cat_row["id"]
        else:
            cur = conn.execute(
                "INSERT INTO categories (name, type) VALUES (?, 'expense')",
                (category.strip(),),
            )
            cat_id = cur.lastrowid
        mid = item_keyword.data(QtCore.Qt.UserRole)
        conn.execute(
            "UPDATE mappings SET keyword = ?, category_id = ? WHERE id = ?",
            (keyword.strip(), cat_id, mid),
        )
        conn.commit()
        conn.close()
        self.load_mappings()

    def retrain_classifier(self) -> None:
        reply = QtWidgets.QMessageBox.question(
            self,
            "Retrain",
            "Delete all mappings and retrain from scratch?",
        )
        if reply != QtWidgets.QMessageBox.Yes:
            return
        conn = self._get_conn()
        conn.execute("DELETE FROM mappings")
        conn.commit()
        conn.close()
        QtWidgets.QMessageBox.information(
            self, "Retrain", "Classifier retrained from scratch."
        )
        self.load_mappings()


__all__ = ["MainWindow"]

