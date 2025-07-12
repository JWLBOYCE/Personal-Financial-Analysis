"""Forecast display widget."""

from __future__ import annotations

import sqlite3
from datetime import datetime
from typing import Tuple, List

from PyQt5 import QtWidgets
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from logic.projection_engine import generate_projection
from logic.categoriser import DB_PATH, _ensure_db


class ForecastWidget(QtWidgets.QWidget):
    """Widget showing projected cashflow."""

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QtWidgets.QVBoxLayout(self)

        self.table = QtWidgets.QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Category", "Projected Amount"])
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)

        self.figure = Figure(figsize=(5, 3))
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)

        self.setLayout(layout)

    # ------------------------------------------------------------------
    # Data helpers
    # ------------------------------------------------------------------
    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        _ensure_db(conn)
        return conn

    def _load_history(self, month_id: str) -> Tuple[List[str], List[float]]:
        conn = self._get_conn()
        cur = conn.execute(
            "SELECT start_date FROM months WHERE id = ? OR name = ?",
            (month_id, month_id),
        )
        row = cur.fetchone()
        if not row:
            conn.close()
            return [], []
        start_date = row["start_date"]
        cur = conn.execute(
            "SELECT strftime('%Y-%m', date) as ym, SUM(amount) as total "
            "FROM transactions WHERE date < ? GROUP BY ym ORDER BY ym",
            (start_date,),
        )
        rows = cur.fetchall()
        conn.close()
        months = [datetime.strptime(r["ym"] + "-01", "%Y-%m-%d").strftime("%b %Y") for r in rows]
        totals = [r["total"] for r in rows]
        return months, totals

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def refresh(self, month_id: str) -> None:
        data = generate_projection(month_id)
        if not data:
            self.table.setRowCount(0)
            self.figure.clear()
            self.canvas.draw()
            return
        first = next(iter(data.values()))
        combined = {}
        for cat, amt in first["income"].items():
            combined[cat] = combined.get(cat, 0.0) + amt
        for cat, amt in first["expenses"].items():
            combined[cat] = combined.get(cat, 0.0) - amt
        self.table.setRowCount(len(combined))
        for i, (cat, amt) in enumerate(combined.items()):
            self.table.setItem(i, 0, QtWidgets.QTableWidgetItem(cat))
            self.table.setItem(i, 1, QtWidgets.QTableWidgetItem(f"{amt:.2f}"))
        self.table.resizeColumnsToContents()

        hist_months, hist_nets = self._load_history(month_id)
        proj_months = list(data.keys())
        proj_nets = [d["net"] for d in data.values()]

        months = hist_months + proj_months

        self.figure.clear()
        ax = self.figure.add_subplot(111)
        if hist_months:
            ax.plot(hist_months, hist_nets, marker="o", label="Historical")
            proj_plot_months = [hist_months[-1]] + proj_months
            proj_plot_vals = [hist_nets[-1]] + proj_nets
        else:
            proj_plot_months = proj_months
            proj_plot_vals = proj_nets
        ax.plot(proj_plot_months, proj_plot_vals, marker="o", label="Projected")
        ax.set_ylabel("Net Cashflow")
        ax.set_xticks(range(len(months)))
        ax.set_xticklabels(months, rotation=45, ha="right")
        ax.legend()
        self.figure.tight_layout()
        self.canvas.draw()


__all__ = ["ForecastWidget"]
