from __future__ import annotations

from PyQt5 import QtWidgets, QtCore
import sqlite3
from datetime import datetime

from logic.month_manager import _ensure_db
from config import get_db_path
from .navigation_table_widget import NavigationTableWidget


class RecurringTab(QtWidgets.QWidget):
    """Tab for managing recurring transaction templates."""

    def __init__(self) -> None:
        super().__init__()
        layout = QtWidgets.QVBoxLayout(self)

        self.table = NavigationTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(
            ["Description", "Amount", "Category", "Type"]
        )
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSizeAdjustPolicy(
            QtWidgets.QAbstractScrollArea.AdjustToContents
        )
        layout.addWidget(self.table)
        layout.setStretch(0, 1)

        btn_layout = QtWidgets.QHBoxLayout()
        self.add_btn = QtWidgets.QPushButton("Add Template")
        self.remove_btn = QtWidgets.QPushButton("Remove Selected")
        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.remove_btn)
        layout.addLayout(btn_layout)

        self.add_btn.clicked.connect(self.add_template)
        self.remove_btn.clicked.connect(self.remove_selected)
        self.table.cellChanged.connect(self._cell_changed)

    # ------------------------------------------------------------------
    # Database helpers
    # ------------------------------------------------------------------
    def _get_conn(self) -> sqlite3.Connection:
        db_path = get_db_path()
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        _ensure_db(conn)
        return conn

    def _category_id(self, name: str) -> int | None:
        if not name.strip():
            return None
        conn = self._get_conn()
        cur = conn.execute("SELECT id FROM categories WHERE name = ?", (name.strip(),))
        row = cur.fetchone()
        if row:
            cid = row["id"]
        else:
            cur = conn.execute(
                "INSERT INTO categories (name, type) VALUES (?, 'expense')",
                (name.strip(),),
            )
            cid = cur.lastrowid
            conn.commit()
        conn.close()
        return cid

    # ------------------------------------------------------------------
    # Data loading/saving
    # ------------------------------------------------------------------
    def load_data(self) -> None:
        conn = self._get_conn()
        cur = conn.execute(
            """
            SELECT t.id, t.description, t.amount, c.name AS category, t.type
            FROM transactions t
            LEFT JOIN categories c ON t.category = c.id
            WHERE t.is_recurring = 1
            ORDER BY t.date, t.description
            """
        )
        rows = cur.fetchall()
        conn.close()

        self.table.blockSignals(True)
        self.table.setRowCount(0)
        for i, row in enumerate(rows):
            self.table.insertRow(i)
            desc_item = QtWidgets.QTableWidgetItem(row["description"] or "")
            amt_item = QtWidgets.QTableWidgetItem(f"{row['amount']:.2f}")
            cat_item = QtWidgets.QTableWidgetItem(row["category"] or "")
            type_item = QtWidgets.QTableWidgetItem(row["type"])
            for it in (desc_item, amt_item, cat_item, type_item):
                it.setData(QtCore.Qt.UserRole, row["id"])
            self.table.setItem(i, 0, desc_item)
            self.table.setItem(i, 1, amt_item)
            self.table.setItem(i, 2, cat_item)
            self.table.setItem(i, 3, type_item)
        self.table.blockSignals(False)

    def _cell_changed(self, row: int, column: int) -> None:
        item = self.table.item(row, column)
        if item is None:
            return
        tid = item.data(QtCore.Qt.UserRole)
        if tid is None:
            return
        desc = self.table.item(row, 0).text()
        try:
            amount = float(self.table.item(row, 1).text())
        except ValueError:
            amount = 0.0
        cat_name = self.table.item(row, 2).text()
        cat_id = self._category_id(cat_name)
        typ_item = self.table.item(row, 3)
        typ = typ_item.text().strip() if typ_item else "expense"
        conn = self._get_conn()
        conn.execute(
            "UPDATE transactions SET description=?, amount=?, category=?, type=? WHERE id=?",
            (desc, amount, cat_id, typ, tid),
        )
        conn.commit()
        conn.close()

    # ------------------------------------------------------------------
    # Button callbacks
    # ------------------------------------------------------------------
    def add_template(self) -> None:
        conn = self._get_conn()
        cur = conn.execute(
            """
            INSERT INTO transactions (date, description, amount, category, type, is_recurring)
            VALUES (?, '', 0.0, NULL, 'expense', 1)
            """,
            (datetime.now().strftime("%Y-%m-%d"),),
        )
        tid = cur.lastrowid
        conn.commit()
        conn.close()

        row = self.table.rowCount()
        self.table.blockSignals(True)
        self.table.insertRow(row)
        for col, text in enumerate(["", "0.00", "", "expense"]):
            it = QtWidgets.QTableWidgetItem(text)
            it.setData(QtCore.Qt.UserRole, tid)
            self.table.setItem(row, col, it)
        self.table.blockSignals(False)
        self.table.setCurrentCell(row, 0)
        self.table.editItem(self.table.item(row, 0))

    def remove_selected(self) -> None:
        rows = {idx.row() for idx in self.table.selectedIndexes()}
        if not rows:
            return
        conn = self._get_conn()
        for row in sorted(rows, reverse=True):
            item = self.table.item(row, 0)
            if item is None:
                continue
            tid = item.data(QtCore.Qt.UserRole)
            conn.execute(
                "UPDATE transactions SET is_recurring = 0 WHERE id = ?",
                (tid,),
            )
            self.table.removeRow(row)
        conn.commit()
        conn.close()


__all__ = ["RecurringTab"]
