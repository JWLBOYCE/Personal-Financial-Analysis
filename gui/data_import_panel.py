from PyQt5 import QtWidgets
import os
import sqlite3

from parser import parse_csv
from logic.categoriser import DB_PATH, _ensure_db


class DataImportPanel(QtWidgets.QWidget):
    """Widget for uploading and importing CSV/Numbers files."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QtWidgets.QVBoxLayout(self)

        self.upload_btn = QtWidgets.QPushButton("Upload CSVs or Numbers Exports")
        self.upload_btn.clicked.connect(self.select_files)
        layout.addWidget(self.upload_btn)

        self.file_list = QtWidgets.QListWidget()
        layout.addWidget(self.file_list)

        self.import_btn = QtWidgets.QPushButton("Import Files")
        self.import_btn.clicked.connect(self.import_files)
        layout.addWidget(self.import_btn)

        self.selected_files = []

    def select_files(self) -> None:
        paths, _ = QtWidgets.QFileDialog.getOpenFileNames(
            self,
            "Select Files",
            "",
            "CSV or Numbers (*.csv *.numbers)",
        )
        if paths:
            self.selected_files = paths
            self.file_list.clear()
            for p in paths:
                self.file_list.addItem(os.path.basename(p))

    def import_files(self) -> None:
        if not self.selected_files:
            return
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        _ensure_db(conn)
        for path in self.selected_files:
            try:
                transactions = parse_csv(path)
            except Exception as exc:
                QtWidgets.QMessageBox.warning(
                    self,
                    "Import Error",
                    f"Failed to parse {os.path.basename(path)}:\n{exc}",
                )
                continue
            for tx in transactions:
                tx_type = "income" if tx["amount"] >= 0 else "expense"
                conn.execute(
                    "INSERT INTO transactions (date, description, amount, type) VALUES (?, ?, ?, ?)",
                    (tx["date"], tx["description"], tx["amount"], tx_type),
                )
        conn.commit()
        conn.close()
        QtWidgets.QMessageBox.information(self, "Import", "Files imported successfully")
        self.selected_files = []
        self.file_list.clear()


__all__ = ["DataImportPanel"]

