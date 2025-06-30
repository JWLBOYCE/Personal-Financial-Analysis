from __future__ import annotations

from typing import Iterable, Sequence, Any, Optional
from PyQt5 import QtWidgets, QtGui, QtCore

from .navigation_table_widget import (
    NavigationTableWidget,
    IS_RECURRING_ROLE,
    ORIGINAL_DESC_ROLE,
    CATEGORY_METHOD_ROLE,
)


class TransactionTableManager:
    """Utility class for managing a transaction table."""

    def __init__(self, table: NavigationTableWidget, total_label: QtWidgets.QLabel | None = None) -> None:
        self.table = table
        self.total_label = total_label

        if self.total_label is not None:
            self.table.cellChanged.connect(lambda _r, _c: self.update_total())
            self.table.model().rowsInserted.connect(lambda *_: self.update_total())
            self.table.model().rowsRemoved.connect(lambda *_: self.update_total())

        self.table.cellChanged.connect(lambda r, _c: self.table.update_row_tooltip(r))

    # ------------------------------------------------------------------
    # Header/row helpers
    # ------------------------------------------------------------------
    def set_headers(self, headers: Sequence[str]) -> None:
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(list(headers))
        self.table.horizontalHeader().setStretchLastSection(True)

    def add_row(self, row_data: Sequence[Any], *, recurring: bool = False) -> int:
        row = self.table.rowCount()
        self.table.insertRow(row)
        for col, value in enumerate(row_data):
            item = QtWidgets.QTableWidgetItem(str(value))
            header_item = self.table.horizontalHeaderItem(col)
            header = header_item.text().strip().lower() if header_item else ""
            if header == "description":
                item.setData(ORIGINAL_DESC_ROLE, item.text())
            if header == "category":
                item.setData(CATEGORY_METHOD_ROLE, "manual")
            if recurring:
                item.setData(IS_RECURRING_ROLE, True)
                font = QtGui.QFont(item.font())
                font.setItalic(True)
                item.setFont(font)
            self.table.setItem(row, col, item)
        self.table.update_row_tooltip(row)
        self.update_total()
        return row

    def populate(self, rows: Iterable[Sequence[Any]], recurring_rows: Optional[set[int]] = None) -> None:
        self.table.setRowCount(0)
        recurring_rows = recurring_rows or set()
        for idx, data in enumerate(rows):
            self.add_row(data, recurring=idx in recurring_rows)

    # ------------------------------------------------------------------
    # Formatting helpers
    # ------------------------------------------------------------------
    def apply_recurring_format(self, row: int, recurring: bool) -> None:
        for col in range(self.table.columnCount()):
            item = self.table.item(row, col)
            if item is None:
                continue
            item.setData(IS_RECURRING_ROLE, recurring)
            font = QtGui.QFont(item.font())
            font.setItalic(recurring)
            item.setFont(font)
        self.table.update_row_tooltip(row)
        self.update_total()

    # ------------------------------------------------------------------
    # Totals
    # ------------------------------------------------------------------
    def _amount_column(self) -> Optional[int]:
        for i in range(self.table.columnCount()):
            header = self.table.horizontalHeaderItem(i)
            if header and header.text().strip().lower() == "amount":
                return i
        return None

    def update_total(self) -> None:
        if self.total_label is None:
            return
        amount_col = self._amount_column()
        if amount_col is None:
            self.total_label.setText("Total: 0.00")
            return
        total = 0.0
        for row in range(self.table.rowCount()):
            item = self.table.item(row, amount_col)
            if item is None:
                continue
            try:
                total += float(item.text())
            except ValueError:
                pass
        self.total_label.setText(f"Total: {total:.2f}")


__all__ = ["TransactionTableManager"]
