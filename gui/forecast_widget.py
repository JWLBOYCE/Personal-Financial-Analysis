"""Forecast display widget."""

from __future__ import annotations

import sqlite3
from datetime import datetime
from typing import Tuple, List

from PyQt5 import QtWidgets, QtCore
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from logic.projection_engine import generate_projection
from logic.categoriser import DB_PATH, _ensure_db


class ForecastWidget(QtWidgets.QWidget):
    """Widget showing projected cashflow."""

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)

        self._baseline_data: dict[str, dict] = {}
        self._hist_months: list[str] = []
        self._hist_nets: list[float] = []
        self._proj_months: list[str] = []
        self._baseline_nets: list[float] = []

        outer = QtWidgets.QHBoxLayout(self)

        # left side - table and chart
        left_widget = QtWidgets.QWidget()
        left_layout = QtWidgets.QVBoxLayout(left_widget)

        self.table = QtWidgets.QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Category", "Projected Amount"])
        self.table.horizontalHeader().setStretchLastSection(True)
        left_layout.addWidget(self.table)

        self.figure = Figure(figsize=(5, 3))
        self.canvas = FigureCanvas(self.figure)
        left_layout.addWidget(self.canvas)

        outer.addWidget(left_widget, 3)

        # right side - controls
        control_widget = QtWidgets.QWidget()
        form = QtWidgets.QFormLayout(control_widget)

        self.salary_spin = QtWidgets.QDoubleSpinBox()
        self.salary_spin.setRange(0, 10_000_000)
        self.salary_spin.setPrefix("$")
        self.salary_spin.valueChanged.connect(self._recompute)

        self.rent_spin = QtWidgets.QDoubleSpinBox()
        self.rent_spin.setRange(0, 10_000_000)
        self.rent_spin.setPrefix("$")
        self.rent_spin.valueChanged.connect(self._recompute)

        self.inv_spin = QtWidgets.QDoubleSpinBox()
        self.inv_spin.setRange(0, 100)
        self.inv_spin.setSuffix("%")
        self.inv_spin.setDecimals(2)
        self.inv_spin.valueChanged.connect(self._recompute)

        self.inflation_spin = QtWidgets.QDoubleSpinBox()
        self.inflation_spin.setRange(0, 100)
        self.inflation_spin.setSuffix("%")
        self.inflation_spin.setDecimals(2)
        self.inflation_spin.valueChanged.connect(self._recompute)

        self.savings_spin = QtWidgets.QDoubleSpinBox()
        self.savings_spin.setRange(0, 10_000_000)
        self.savings_spin.setPrefix("$")
        self.savings_spin.valueChanged.connect(self._recompute)

        form.addRow("Monthly Salary", self.salary_spin)
        form.addRow("Rent/Mortgage", self.rent_spin)
        form.addRow("Investment Return %", self.inv_spin)
        form.addRow("Inflation %", self.inflation_spin)
        form.addRow("Target Savings", self.savings_spin)

        self.reset_btn = QtWidgets.QPushButton("Reset to Baseline")
        self.reset_btn.clicked.connect(self._reset_baseline)
        form.addRow(self.reset_btn)

        outer.addWidget(control_widget, 1)

        self.setLayout(outer)

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
        self._baseline_data = generate_projection(month_id)
        if not self._baseline_data:
            self.table.setRowCount(0)
            self.figure.clear()
            self.canvas.draw()
            return

        first = next(iter(self._baseline_data.values()))
        combined: dict[str, float] = {}
        for cat, amt in first["income"].items():
            combined[cat] = combined.get(cat, 0.0) + amt
        for cat, amt in first["expenses"].items():
            combined[cat] = combined.get(cat, 0.0) - amt
        self.table.setRowCount(len(combined))
        for i, (cat, amt) in enumerate(combined.items()):
            self.table.setItem(i, 0, QtWidgets.QTableWidgetItem(cat))
            self.table.setItem(i, 1, QtWidgets.QTableWidgetItem(f"{amt:.2f}"))
        self.table.resizeColumnsToContents()

        self._hist_months, self._hist_nets = self._load_history(month_id)
        self._proj_months = list(self._baseline_data.keys())
        self._baseline_nets = [d["net"] for d in self._baseline_data.values()]

        self._init_baseline_values(first)
        self._reset_baseline()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _init_baseline_values(self, first: dict) -> None:
        """Set baseline values based on projection data."""
        self._base_salary = float(first.get("income", {}).get("Salary", 0.0))
        rent = first.get("expenses", {}).get("Rent")
        if rent is None:
            rent = first.get("expenses", {}).get("Mortgage", 0.0)
        self._base_rent = float(rent or 0.0)
        self._base_inv = 0.0
        self._base_inflation = 0.0
        self._base_target = 0.0

    def _reset_baseline(self) -> None:
        """Reset all controls to baseline values."""
        self.salary_spin.blockSignals(True)
        self.rent_spin.blockSignals(True)
        self.inv_spin.blockSignals(True)
        self.inflation_spin.blockSignals(True)
        self.savings_spin.blockSignals(True)

        self.salary_spin.setValue(self._base_salary)
        self.rent_spin.setValue(self._base_rent)
        self.inv_spin.setValue(self._base_inv)
        self.inflation_spin.setValue(self._base_inflation)
        self.savings_spin.setValue(self._base_target)

        for spin in (
            self.salary_spin,
            self.rent_spin,
            self.inv_spin,
            self.inflation_spin,
            self.savings_spin,
        ):
            spin.blockSignals(False)

        self._recompute()

    def _recompute(self) -> None:
        """Recompute projection using current control values."""
        if not self._baseline_data:
            return
        adjusted, negatives = self._compute_adjusted_projection()

        months = self._hist_months + self._proj_months

        self.figure.clear()
        ax = self.figure.add_subplot(111)
        if self._hist_months:
            ax.plot(self._hist_months, self._hist_nets, marker="o", label="Historical")
            base_months = [self._hist_months[-1]] + self._proj_months
            base_vals = [self._hist_nets[-1]] + self._baseline_nets
            adj_months = base_months
            adj_vals = [self._hist_nets[-1]] + adjusted
        else:
            base_months = self._proj_months
            base_vals = self._baseline_nets
            adj_months = self._proj_months
            adj_vals = adjusted

        ax.plot(base_months, base_vals, marker="o", label="Baseline")
        ax.plot(adj_months, adj_vals, marker="o", label="Adjusted")

        # highlight negative months
        offset = 1 if self._hist_months else 0
        for i, neg in enumerate(negatives):
            if neg:
                x = adj_months[i + offset]
                y = adj_vals[i + offset]
                ax.plot(x, y, "ro")

        ax.set_ylabel("Net Cashflow")
        ax.set_xticks(range(len(months)))
        ax.set_xticklabels(months, rotation=45, ha="right")
        ax.legend()
        self.figure.tight_layout()
        self.canvas.draw()

    def _compute_adjusted_projection(self) -> Tuple[list[float], list[bool]]:
        adjusted_nets: list[float] = []
        negatives: list[bool] = []

        invest_rate = self.inv_spin.value() / 100.0
        inflation = self.inflation_spin.value() / 100.0
        target = self.savings_spin.value()

        cumulative = 0.0
        for idx, (label, row) in enumerate(self._baseline_data.items()):
            incomes = row.get("income", {}).copy()
            expenses = row.get("expenses", {}).copy()

            if "Salary" in incomes:
                incomes["Salary"] = self.salary_spin.value()

            if "Rent" in expenses:
                expenses["Rent"] = self.rent_spin.value()
            elif "Mortgage" in expenses:
                expenses["Mortgage"] = self.rent_spin.value()
            else:
                expenses["Rent"] = self.rent_spin.value()

            for cat in expenses:
                if cat not in {"Rent", "Mortgage"}:
                    expenses[cat] *= (1 + inflation) ** idx

            investment_return = cumulative * invest_rate
            total_income = sum(incomes.values()) + investment_return
            total_expense = sum(expenses.values())
            net = total_income - total_expense
            cumulative += net
            adjusted_nets.append(net)
            negatives.append(net - target < 0)

        return adjusted_nets, negatives


__all__ = ["ForecastWidget"]
