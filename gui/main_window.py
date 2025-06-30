from PyQt5 import QtWidgets, QtCore, QtGui
from .navigation_table_widget import (
    NavigationTableWidget,
    ORIGINAL_DESC_ROLE,
    CATEGORY_METHOD_ROLE,
)
from .table_manager import TransactionTableManager

# Custom role used to store whether a transaction is recurring
IS_RECURRING_ROLE = QtCore.Qt.UserRole + 1
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import sqlite3
from logic.categoriser import DB_PATH, _ensure_db


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
        self.month_list.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum
        )
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
        # Ensure tab text is dark for readability
        self.tab_bar.setStyleSheet("QTabBar::tab{color:#111;}")
        self.tabs = ["Income", "Expenses", "Credit Card", "Summary", "Admin"]
        for tab in self.tabs:
            self.tab_bar.addTab(tab)
        self.tab_bar.currentChanged.connect(self.switch_tab)
        right_layout.addWidget(self.tab_bar)

        # Stacked widget for pages
        self.stack = QtWidgets.QStackedWidget()
        right_layout.addWidget(self.stack)
        right_layout.setStretchFactor(self.stack, 1)

        self.tables = []  # transaction tables for Income/Expenses/Credit Card
        self.total_labels = []  # labels showing total amounts for each table
        self.table_managers = []
        for tab in self.tabs:
            if tab == "Summary":
                summary_widget = QtWidgets.QWidget()
                summary_layout = QtWidgets.QVBoxLayout(summary_widget)
                self.summary_table = NavigationTableWidget(0, 3)
                self.summary_table.setHorizontalHeaderLabels(
                    ["Category", "Income", "Expense"]
                )
                self.summary_table.horizontalHeader().setStretchLastSection(True)
                self.summary_table.setSizeAdjustPolicy(
                    QtWidgets.QAbstractScrollArea.AdjustToContents
                )
                summary_layout.addWidget(self.summary_table)

                self.net_label = QtWidgets.QLabel("Net Cashflow: 0.00")
                self.net_label.setSizePolicy(
                    QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum
                )
                summary_layout.addWidget(self.net_label)

                self.figure = Figure(figsize=(5, 3))
                self.canvas = FigureCanvas(self.figure)
                policy = QtWidgets.QSizePolicy(
                    QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum
                )
                self.canvas.setSizePolicy(policy)
                summary_layout.addWidget(self.canvas)

                self.stack.addWidget(summary_widget)
                self.summary_widget = summary_widget
            elif tab == "Admin":
                admin_widget = QtWidgets.QWidget()
                admin_layout = QtWidgets.QVBoxLayout(admin_widget)

                self.admin_tabs = QtWidgets.QTabWidget()
                admin_layout.addWidget(self.admin_tabs)
                admin_layout.setStretchFactor(self.admin_tabs, 1)

                self.mapping_table = NavigationTableWidget(0, 4)
                self.mapping_table.setHorizontalHeaderLabels(
                    ["Keyword", "Min", "Max", "Category"]
                )
                self.mapping_table.horizontalHeader().setStretchLastSection(True)
                self.mapping_table.setSizeAdjustPolicy(
                    QtWidgets.QAbstractScrollArea.AdjustToContents
                )
                self.admin_tabs.addTab(self.mapping_table, "Mappings")

                btn_layout = QtWidgets.QHBoxLayout()
                self.save_mapping_btn = QtWidgets.QPushButton("Save")
                self.delete_mapping_btn = QtWidgets.QPushButton("Delete")
                self.retrain_btn = QtWidgets.QPushButton("Retrain Classifier")
                for b in (
                    self.save_mapping_btn,
                    self.delete_mapping_btn,
                    self.retrain_btn,
                ):
                    btn_layout.addWidget(b)
                admin_layout.addLayout(btn_layout)
                admin_layout.setStretchFactor(btn_layout, 0)

                self.save_mapping_btn.clicked.connect(self.save_mappings)
                self.delete_mapping_btn.clicked.connect(self.delete_mapping)
                self.retrain_btn.clicked.connect(self.retrain_classifier)

                self.stack.addWidget(admin_widget)
                self.admin_widget = admin_widget
            else:
                page = QtWidgets.QWidget()
                page_layout = QtWidgets.QVBoxLayout(page)

                table = NavigationTableWidget(0, 4)
                table.setSizeAdjustPolicy(
                    QtWidgets.QAbstractScrollArea.AdjustToContents
                )
                total_label = QtWidgets.QLabel("Total: 0.00")
                total_label.setSizePolicy(
                    QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum
                )
                manager = TransactionTableManager(table, total_label)
                manager.set_headers(["Date", "Description", "Category", "Amount"])
                page_layout.addWidget(table)
                page_layout.addWidget(total_label, alignment=QtCore.Qt.AlignRight)
                page_layout.setStretch(0, 1)
                page_layout.setStretch(1, 0)

                self.stack.addWidget(page)
                self.tables.append(table)
                self.total_labels.append(total_label)
                self.table_managers.append(manager)

                table.cellChanged.connect(lambda *_: self._update_table_total(table))
                model = table.model()
                model.rowsInserted.connect(lambda *_: self._update_table_total(table))
                model.rowsRemoved.connect(lambda *_: self._update_table_total(table))

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
        self.recurring_btn.clicked.connect(self.toggle_recurring)
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
        for table, manager in zip(self.tables, self.table_managers):
            table.setRowCount(0)
            for i in range(5):
                values = [
                    f"2023-01-{i+1:02d}",
                    f"{month} transaction {i+1}",
                    "Misc",
                    f"{(i+1)*10:.2f}",
                ]
                manager.add_row(values, recurring=(i == 0))
            manager.update_total()

        self._update_summary()

    def _update_table_total(
        self,
        table: QtWidgets.QTableWidget,
        *,
        update_summary: bool = True,
    ) -> None:
        """Recalculate and display the total for a table's Amount column."""
        try:
            index = self.tables.index(table)
        except ValueError:
            return
        manager = self.table_managers[index]
        manager.update_total()
        if update_summary:
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
            SELECT m.id, m.keyword, m.min_amount, m.max_amount,
                   c.name AS category
            FROM mappings m LEFT JOIN categories c ON m.category_id = c.id
            ORDER BY m.keyword
            """
        )
        rows = cur.fetchall()
        self.mapping_table.setRowCount(0)
        for i, row in enumerate(rows):
            self.mapping_table.insertRow(i)
            kw_item = QtWidgets.QTableWidgetItem(row["keyword"])
            kw_item.setData(QtCore.Qt.UserRole, row["id"])
            self.mapping_table.setItem(i, 0, kw_item)
            self.mapping_table.setItem(
                i, 1, QtWidgets.QTableWidgetItem(f"{row['min_amount']:.2f}")
            )
            self.mapping_table.setItem(
                i, 2, QtWidgets.QTableWidgetItem(f"{row['max_amount']:.2f}")
            )
            self.mapping_table.setItem(
                i, 3, QtWidgets.QTableWidgetItem(row["category"] or "")
            )
        self.mapping_table.resizeColumnsToContents()
        conn.close()

    def delete_mapping(self) -> None:
        rows = sorted({idx.row() for idx in self.mapping_table.selectedIndexes()}, reverse=True)
        if not rows:
            return
        conn = self._get_conn()
        for row in rows:
            item = self.mapping_table.item(row, 0)
            if item:
                mid = item.data(QtCore.Qt.UserRole)
                conn.execute("DELETE FROM mappings WHERE id = ?", (mid,))
            self.mapping_table.removeRow(row)
        conn.commit()
        conn.close()

    def save_mappings(self) -> None:
        conn = self._get_conn()
        for row in range(self.mapping_table.rowCount()):
            kw_item = self.mapping_table.item(row, 0)
            min_item = self.mapping_table.item(row, 1)
            max_item = self.mapping_table.item(row, 2)
            cat_item = self.mapping_table.item(row, 3)
            if kw_item is None or cat_item is None:
                continue
            keyword = kw_item.text().strip()
            try:
                min_amt = float(min_item.text()) if min_item else 0.0
            except ValueError:
                min_amt = 0.0
            try:
                max_amt = float(max_item.text()) if max_item else 0.0
            except ValueError:
                max_amt = 0.0
            category = cat_item.text().strip()
            cat_id = None
            if category:
                cur = conn.execute("SELECT id FROM categories WHERE name = ?", (category,))
                row_cat = cur.fetchone()
                if row_cat:
                    cat_id = row_cat["id"]
                else:
                    cur = conn.execute(
                        "INSERT INTO categories (name, type) VALUES (?, 'expense')",
                        (category,),
                    )
                    cat_id = cur.lastrowid
            mid = kw_item.data(QtCore.Qt.UserRole)
            if mid is None:
                cur = conn.execute(
                    "INSERT INTO mappings (keyword, min_amount, max_amount, category_id) VALUES (?, ?, ?, ?)",
                    (keyword, min_amt, max_amt, cat_id),
                )
                kw_item.setData(QtCore.Qt.UserRole, cur.lastrowid)
            else:
                conn.execute(
                    "UPDATE mappings SET keyword = ?, min_amount = ?, max_amount = ?, category_id = ? WHERE id = ?",
                    (keyword, min_amt, max_amt, cat_id, mid),
                )
        conn.commit()
        conn.close()

    def toggle_recurring(self) -> None:
        """Toggle recurring flag for selected rows in the current table."""
        index = self.tab_bar.currentIndex()
        if index >= len(self.tables):
            return
        table = self.tables[index]
        manager = self.table_managers[index]
        rows = {idx.row() for idx in table.selectedIndexes()}
        for row in rows:
            first_item = table.item(row, 0)
            current = bool(first_item.data(IS_RECURRING_ROLE)) if first_item else False
            manager.apply_recurring_format(row, not current)

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

