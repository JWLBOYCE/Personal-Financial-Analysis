from __future__ import annotations

import sqlite3
from PyQt5 import QtWidgets, QtCore

from .monthly_tabbed_window import TableSection
from logic.month_manager import _ensure_db
from config import get_db_path


class DataTableSection(TableSection):
    """TableSection connected to the SQLite backend."""

    TABLE_NAME = "monthly_entries"

    def __init__(self, title: str, key: str, month: str) -> None:
        super().__init__(title)
        self.key = key
        self.setObjectName(key)
        self.month = month
        self.table.cellChanged.connect(self._item_changed)
        self.table.model().rowsInserted.connect(self._rows_inserted)
        self.table.model().rowsRemoved.connect(self._rows_removed)
        self._load_data()

    # ------------------------------------------------------------------
    # Database helpers
    # ------------------------------------------------------------------
    def _get_conn(self) -> sqlite3.Connection:
        db_path = get_db_path()
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        _ensure_db(conn)
        conn.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {self.TABLE_NAME} (
                id INTEGER PRIMARY KEY,
                month TEXT NOT NULL,
                table_key TEXT NOT NULL,
                date TEXT,
                description TEXT,
                amount REAL,
                category TEXT,
                notes TEXT
            )
            """
        )
        return conn

    def _load_data(self) -> None:
        conn = self._get_conn()
        cur = conn.execute(
            f"SELECT id, date, description, amount, category, notes FROM {self.TABLE_NAME} "
            "WHERE month = ? AND table_key = ? ORDER BY id",
            (self.month, self.key),
        )
        rows = cur.fetchall()
        conn.close()
        self.table.blockSignals(True)
        for row in rows:
            idx = self.manager.add_row([
                row["date"] or "",
                row["description"] or "",
                f"{row['amount']:.2f}" if row["amount"] is not None else "",
                row["category"] or "",
                row["notes"] or "",
            ])
            for col in range(self.table.columnCount()):
                item = self.table.item(idx, col)
                if item:
                    item.setData(QtCore.Qt.UserRole, row["id"])
        self.table.blockSignals(False)
        self.update_total()

    # ------------------------------------------------------------------
    # Row helpers
    # ------------------------------------------------------------------
    def _row_values(self, row: int) -> tuple[str, str, float, str, str]:
        def txt(col: int) -> str:
            item = self.table.item(row, col)
            return item.text().strip() if item else ""

        date = txt(0)
        desc = txt(1)
        amt_str = txt(2)
        try:
            amt = float(amt_str)
        except ValueError:
            amt = 0.0
        cat = txt(3)
        notes = txt(4)
        return date, desc, amt, cat, notes

    def _insert_row(self, row: int) -> None:
        date, desc, amt, cat, notes = self._row_values(row)
        conn = self._get_conn()
        cur = conn.execute(
            f"INSERT INTO {self.TABLE_NAME} (month, table_key, date, description, amount, category, notes) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (self.month, self.key, date, desc, amt, cat, notes),
        )
        row_id = cur.lastrowid
        conn.commit()
        conn.close()
        for col in range(self.table.columnCount()):
            item = self.table.item(row, col)
            if item:
                item.setData(QtCore.Qt.UserRole, row_id)

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------
    def _rows_inserted(self, parent: QtCore.QModelIndex, start: int, end: int) -> None:  # noqa: D401 - Qt slot
        for row in range(start, end + 1):
            self._insert_row(row)

    def _item_changed(self, _row: int, _col: int) -> None:  # noqa: D401 - Qt slot
        row = _row
        item = self.table.item(row, 0)
        if not item:
            return
        row_id = item.data(QtCore.Qt.UserRole)
        if row_id is None:
            self._insert_row(row)
            return
        date, desc, amt, cat, notes = self._row_values(row)
        conn = self._get_conn()
        conn.execute(
            f"UPDATE {self.TABLE_NAME} SET date = ?, description = ?, amount = ?, category = ?, notes = ? WHERE id = ?",
            (date, desc, amt, cat, notes, row_id),
        )
        conn.commit()
        conn.close()
        self.update_total()

    def _rows_removed(self, parent: QtCore.QModelIndex, start: int, end: int) -> None:  # noqa: D401 - Qt slot
        conn = self._get_conn()
        for row in range(start, end + 1):
            id_item = self.table.item(row, 0)
            if id_item is None:
                continue
            row_id = id_item.data(QtCore.Qt.UserRole)
            if row_id is not None:
                conn.execute(
                    f"DELETE FROM {self.TABLE_NAME} WHERE id = ?",
                    (row_id,),
                )
        conn.commit()
        conn.close()


__all__ = ["DataTableSection"]
