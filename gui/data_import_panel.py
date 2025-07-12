from PyQt5 import QtWidgets
import os
import sqlite3
import csv

from parser import parse_csv
from parser.auto_mapper import guess_column_mapping
from parser.profile_manager import load_profiles, match_profile, add_profile
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

    def _confirm_mapping(self, headers: list[str], mapping: dict[str, str]) -> dict[str, str]:
        headers_display = [h.strip() for h in headers]
        headers_lower = [h.lower() for h in headers_display]
        result = {}
        for key in ["date", "description", "amount"]:
            current = mapping.get(key, "")
            idx = headers_lower.index(current) if current in headers_lower else 0
            choice, ok = QtWidgets.QInputDialog.getItem(
                self,
                "Column Mapping",
                f"Select column for {key}",
                headers_display,
                idx,
                False,
            )
            if not ok:
                raise ValueError("Mapping cancelled")
            result[key] = headers_lower[headers_display.index(choice)]
        return result

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
                with open(path, newline="", encoding="utf-8-sig") as f:
                    reader = csv.reader(f)
                    headers = next(reader)
                    sample = next(reader, [])

                profiles = load_profiles()
                profile_name, mapping = match_profile(headers, profiles)
                if not mapping:
                    mapping = guess_column_mapping(headers, sample)

                mapping = self._confirm_mapping(headers, mapping)

                if profile_name:
                    if mapping != {v: k.lower() for k, v in profiles[profile_name].items()}:
                        reply = QtWidgets.QMessageBox.question(
                            self,
                            "Update Mapping",
                            f"Would you like to save this mapping for future {profile_name} imports?",
                        )
                        if reply == QtWidgets.QMessageBox.Yes:
                            add_profile(profile_name, headers, mapping)
                else:
                    reply = QtWidgets.QMessageBox.question(
                        self,
                        "Save Mapping",
                        "Would you like to save this mapping for future imports?",
                    )
                    if reply == QtWidgets.QMessageBox.Yes:
                        name, ok = QtWidgets.QInputDialog.getText(
                            self, "Profile Name", "Institution name:")
                        if ok and name:
                            add_profile(name, headers, mapping)

                transactions = parse_csv(path, mapping)
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

