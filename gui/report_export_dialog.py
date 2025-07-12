from __future__ import annotations

import os
from PyQt5 import QtWidgets


class ReportExportDialog(QtWidgets.QDialog):
    """Dialog for choosing report export options."""

    def __init__(self, logo_path: str = "", footer: str = "", parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Export Report")
        self.resize(300, 150)
        self.logo_path = logo_path

        layout = QtWidgets.QFormLayout(self)

        self.theme_combo = QtWidgets.QComboBox()
        self.theme_combo.addItems(["Personal", "Executive", "Investor"])
        layout.addRow("Theme:", self.theme_combo)

        self.tone_combo = QtWidgets.QComboBox()
        self.tone_combo.addItems(["Formal", "Plain English"])
        layout.addRow("Tone:", self.tone_combo)

        self.logo_btn = QtWidgets.QPushButton("Upload Logo")
        self.logo_btn.clicked.connect(self._select_logo)
        layout.addRow("Logo:", self.logo_btn)

        self.footer_edit = QtWidgets.QLineEdit(footer)
        layout.addRow("Footer:", self.footer_edit)

        btn_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        layout.addRow(btn_box)

    def _select_logo(self) -> None:
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Select Logo", "", "Images (*.png *.jpg *.jpeg *.bmp)"
        )
        if path:
            self.logo_path = path

    def get_options(self) -> dict[str, str]:
        return {
            "theme": self.theme_combo.currentText(),
            "tone": "plain" if self.tone_combo.currentText().lower().startswith("plain") else "formal",
            "logo": self.logo_path,
            "footer": self.footer_edit.text(),
        }
