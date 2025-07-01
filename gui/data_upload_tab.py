from __future__ import annotations

from PyQt5 import QtWidgets, QtCore
import pandas as pd
import sqlite3
import os
import zipfile

from config import get_db_path


class UploadWidget(QtWidgets.QFrame):
    """Drag-and-drop area with button for importing files."""

    file_selected = QtCore.pyqtSignal(str)

    def __init__(self) -> None:
        super().__init__()
        layout = QtWidgets.QVBoxLayout(self)
        self.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.setAcceptDrops(True)

        self.label = QtWidgets.QLabel(
            "Drop CSV or .numbers files here or click to select"
        )
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(self.label)

        self.button = QtWidgets.QPushButton("Select Files")
        self.button.clicked.connect(self._open_dialog)
        layout.addWidget(self.button, alignment=QtCore.Qt.AlignCenter)

    # ------------------------------------------------------------------
    # File dialog helpers
    # ------------------------------------------------------------------
    def _open_dialog(self) -> None:
        paths, _ = QtWidgets.QFileDialog.getOpenFileNames(
            self,
            "Import Files",
            "",
            "CSV Files (*.csv *.numbers);;All Files (*)",
        )
        for path in paths:
            self.file_selected.emit(path)

    # ------------------------------------------------------------------
    # Drag and drop
    # ------------------------------------------------------------------
    def dragEnterEvent(self, event: QtCore.QDragEnterEvent) -> None:  # type: ignore[override]
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QtCore.QDropEvent) -> None:  # type: ignore[override]
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if path:
                self.file_selected.emit(path)
        event.acceptProposedAction()


class DataUploadTab(QtWidgets.QWidget):
    """Tab used for importing CSV or .numbers data into the database."""

    def __init__(self) -> None:
        super().__init__()
        layout = QtWidgets.QVBoxLayout(self)

        self.upload = UploadWidget()
        layout.addWidget(self.upload)

        btn = QtWidgets.QPushButton("Import Folder")
        btn.clicked.connect(self._choose_folder)
        layout.addWidget(btn, alignment=QtCore.Qt.AlignCenter)

        self.log = QtWidgets.QTextEdit(readOnly=True)
        layout.addWidget(self.log)

        self.watcher = QtCore.QFileSystemWatcher()
        self.watcher.directoryChanged.connect(self._process_folder)

        self.upload.file_selected.connect(self._import_file)

    # ------------------------------------------------------------------
    # Folder watching
    # ------------------------------------------------------------------
    def _choose_folder(self) -> None:
        path = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Folder")
        if path:
            if path not in self.watcher.directories():
                self.watcher.addPath(path)
            self._process_folder(path)

    def _process_folder(self, path: str) -> None:
        for name in os.listdir(path):
            full = os.path.join(path, name)
            if os.path.isfile(full) and name.lower().endswith((".csv", ".numbers")):
                self._import_file(full)

    # ------------------------------------------------------------------
    # Import logic
    # ------------------------------------------------------------------
    def _import_file(self, path: str) -> None:
        try:
            df = self._read_file(path)
            table = os.path.splitext(os.path.basename(path))[0]
            conn = sqlite3.connect(get_db_path())
            df.to_sql(table, conn, if_exists="replace", index=False)
            conn.close()
            self.log.append(f"Imported {path} into table '{table}'")
        except Exception as exc:
            self.log.append(f"Failed to import {path}: {exc}")

    def _read_file(self, path: str) -> pd.DataFrame:
        if path.lower().endswith(".numbers"):
            with zipfile.ZipFile(path) as zf:
                csv_name = next((n for n in zf.namelist() if n.endswith(".csv")), None)
                if not csv_name:
                    raise ValueError("No CSV found in .numbers file")
                with zf.open(csv_name) as fh:
                    return pd.read_csv(fh)
        return pd.read_csv(path)


__all__ = ["DataUploadTab"]
