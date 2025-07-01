from __future__ import annotations

from PyQt5 import QtWidgets, QtCore, QtGui
import sqlite3

from logic.month_manager import _ensure_db
from config import get_db_path


class AmountDelegate(QtWidgets.QStyledItemDelegate):
    """Delegate for editing monetary amounts with validation."""

    def createEditor(self, parent, option, index):
        editor = QtWidgets.QLineEdit(parent)
        validator = QtGui.QDoubleValidator(editor)
        editor.setValidator(validator)
        return editor

    def setEditorData(self, editor, index):
        value = index.data(QtCore.Qt.EditRole) or "0.00"
        editor.setText(str(value))

    def setModelData(self, editor, model, index):
        text = editor.text().strip()
        model.setData(index, text)


class DateDelegate(QtWidgets.QStyledItemDelegate):
    """Delegate providing a date editor."""

    def createEditor(self, parent, option, index):
        editor = QtWidgets.QDateEdit(parent)
        editor.setDisplayFormat("yyyy-MM-dd")
        editor.setCalendarPopup(True)
        return editor

    def setEditorData(self, editor, index):
        text = index.data(QtCore.Qt.EditRole)
        date = QtCore.QDate.fromString(str(text), "yyyy-MM-dd")
        if not date.isValid():
            date = QtCore.QDate.currentDate()
        editor.setDate(date)

    def setModelData(self, editor, model, index):
        model.setData(index, editor.date().toString("yyyy-MM-dd"))


class CategoryDelegate(QtWidgets.QStyledItemDelegate):
    """Delegate providing a dropdown of categories."""

    def _categories(self):
        db_path = get_db_path()
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        _ensure_db(conn)
        cur = conn.execute("SELECT name FROM categories ORDER BY name")
        names = [r["name"] for r in cur.fetchall()]
        conn.close()
        return names

    def createEditor(self, parent, option, index):
        editor = QtWidgets.QComboBox(parent)
        editor.addItems(self._categories())
        editor.setEditable(True)
        editor.setInsertPolicy(QtWidgets.QComboBox.NoInsert)
        editor.setAutoCompletion(True)
        return editor

    def setEditorData(self, editor, index):
        value = index.data(QtCore.Qt.EditRole) or ""
        idx = editor.findText(value)
        if idx >= 0:
            editor.setCurrentIndex(idx)
        else:
            editor.setEditText(value)

    def setModelData(self, editor, model, index):
        model.setData(index, editor.currentText().strip())

