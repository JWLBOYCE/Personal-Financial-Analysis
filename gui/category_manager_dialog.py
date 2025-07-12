from __future__ import annotations

from PyQt5 import QtWidgets, QtCore
import sqlite3

from logic.categoriser import DB_PATH, _ensure_db


class CategoryManagerDialog(QtWidgets.QDialog):
    """Dialog for managing income and expense categories."""

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Category Manager")
        self.resize(400, 300)

        layout = QtWidgets.QVBoxLayout(self)

        # Table of existing categories
        self.table = QtWidgets.QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Category Name", "Type", "Usage Count"])
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)

        # form for new category
        form_layout = QtWidgets.QHBoxLayout()
        self.name_edit = QtWidgets.QLineEdit()
        self.type_combo = QtWidgets.QComboBox()
        self.type_combo.addItems(["income", "expense"])
        self.add_btn = QtWidgets.QPushButton("Add")
        form_layout.addWidget(self.name_edit)
        form_layout.addWidget(self.type_combo)
        form_layout.addWidget(self.add_btn)
        layout.addLayout(form_layout)

        # action buttons
        btn_layout = QtWidgets.QHBoxLayout()
        self.edit_btn = QtWidgets.QPushButton("Edit Selected")
        self.merge_btn = QtWidgets.QPushButton("Merge")
        self.delete_btn = QtWidgets.QPushButton("Delete")
        for b in (self.edit_btn, self.merge_btn, self.delete_btn):
            btn_layout.addWidget(b)
        layout.addLayout(btn_layout)

        self.add_btn.clicked.connect(self.add_category)
        self.edit_btn.clicked.connect(self.edit_category)
        self.merge_btn.clicked.connect(self.merge_categories)
        self.delete_btn.clicked.connect(self.delete_category)

        self._load_categories()

    # ------------------------------------------------------------------
    # DB helpers
    # ------------------------------------------------------------------
    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        _ensure_db(conn)
        return conn

    def _load_categories(self) -> None:
        """Load all categories and their usage counts."""
        self.table.setRowCount(0)
        conn = self._get_conn()
        cur = conn.execute(
            """
            SELECT c.id, c.name, c.type,
                   (SELECT COUNT(*) FROM transactions t WHERE t.category = c.id) AS usage
            FROM categories c
            ORDER BY c.type, c.name
            """
        )
        for row_idx, row in enumerate(cur.fetchall()):
            self.table.insertRow(row_idx)
            item = QtWidgets.QTableWidgetItem(row["name"])
            item.setData(QtCore.Qt.UserRole, row["id"])
            self.table.setItem(row_idx, 0, item)
            self.table.setItem(row_idx, 1, QtWidgets.QTableWidgetItem(row["type"]))
            self.table.setItem(
                row_idx, 2, QtWidgets.QTableWidgetItem(str(row["usage"]))
            )
        conn.close()
        self.table.resizeColumnsToContents()

    # ------------------------------------------------------------------
    # Button callbacks
    # ------------------------------------------------------------------
    def add_category(self) -> None:
        name = self.name_edit.text().strip()
        if not name:
            return
        ctype = self.type_combo.currentText()
        conn = self._get_conn()
        cur = conn.execute(
            "SELECT id FROM categories WHERE name = ? AND type = ?",
            (name, ctype),
        )
        row = cur.fetchone()
        if row is None:
            conn.execute(
                "INSERT INTO categories (name, type) VALUES (?, ?)",
                (name, ctype),
            )
            conn.commit()
        conn.close()
        self.name_edit.clear()
        self._load_categories()

    def _selected_ids(self) -> list[int]:
        ids: list[int] = []
        for item in self.table.selectedItems():
            if item.column() == 0:
                cid = item.data(QtCore.Qt.UserRole)
                if cid is not None:
                    ids.append(int(cid))
        return ids

    def edit_category(self) -> None:
        ids = self._selected_ids()
        if len(ids) != 1:
            return
        row = self.table.currentRow()
        name_item = self.table.item(row, 0)
        type_item = self.table.item(row, 1)
        name, ok = QtWidgets.QInputDialog.getText(
            self, "Edit Category Name", "Name:", text=name_item.text()
        )
        if not ok or not name.strip():
            return
        type_idx = self.type_combo.findText(type_item.text())
        type_idx = 0 if type_idx == -1 else type_idx
        type_choice, ok = QtWidgets.QInputDialog.getItem(
            self,
            "Edit Category Type",
            "Type:",
            ["income", "expense"],
            current=type_idx,
            editable=False,
        )
        if not ok:
            return
        conn = self._get_conn()
        conn.execute(
            "UPDATE categories SET name = ?, type = ? WHERE id = ?",
            (name.strip(), type_choice, ids[0]),
        )
        conn.commit()
        conn.close()
        self._load_categories()

    def merge_categories(self) -> None:
        ids = self._selected_ids()
        if len(ids) != 2:
            return
        row1 = self.table.selectedIndexes()[0].row()
        row2 = self.table.selectedIndexes()[1].row()
        name1 = self.table.item(row1, 0).text()
        name2 = self.table.item(row2, 0).text()
        keep, ok = QtWidgets.QInputDialog.getItem(
            self,
            "Merge Categories",
            "Keep which category?",
            [name1, name2],
            editable=False,
        )
        if not ok:
            return
        keep_id = ids[0] if keep == name1 else ids[1]
        drop_id = ids[1] if keep == name1 else ids[0]
        conn = self._get_conn()
        conn.execute(
            "UPDATE transactions SET category = ? WHERE category = ?",
            (keep_id, drop_id),
        )
        conn.execute("DELETE FROM categories WHERE id = ?", (drop_id,))
        conn.commit()
        conn.close()
        self._load_categories()

    def delete_category(self) -> None:
        ids = self._selected_ids()
        if len(ids) != 1:
            return
        row = self.table.currentRow()
        name = self.table.item(row, 0).text()
        reply = QtWidgets.QMessageBox.question(
            self,
            "Delete Category",
            f"Delete category '{name}'? Transactions will be uncategorised.",
        )
        if reply != QtWidgets.QMessageBox.Yes:
            return
        conn = self._get_conn()
        conn.execute("UPDATE transactions SET category = NULL WHERE category = ?", (ids[0],))
        conn.execute("DELETE FROM categories WHERE id = ?", (ids[0],))
        conn.commit()
        conn.close()
        self._load_categories()


__all__ = ["CategoryManagerDialog"]
