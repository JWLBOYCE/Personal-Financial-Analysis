from __future__ import annotations

from PyQt5 import QtWidgets
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import sqlite3
from datetime import datetime
import calendar

from logic.month_manager import _ensure_db
from config import get_db_path


class DashboardTab(QtWidgets.QWidget):
    """Dashboard showing charts for the selected month."""

    def __init__(self) -> None:
        super().__init__()
        layout = QtWidgets.QVBoxLayout(self)

        self.pie_fig = Figure(figsize=(4, 3))
        self.pie_canvas = FigureCanvas(self.pie_fig)
        policy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum
        )
        self.pie_canvas.setSizePolicy(policy)
        layout.addWidget(self.pie_canvas)

        self.bar_fig = Figure(figsize=(6, 3))
        self.bar_canvas = FigureCanvas(self.bar_fig)
        self.bar_canvas.setSizePolicy(policy)
        layout.addWidget(self.bar_canvas)

    # ------------------------------------------------------------------
    # Database helpers
    # ------------------------------------------------------------------
    def _get_conn(self) -> sqlite3.Connection:
        db_path = get_db_path()
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        _ensure_db(conn)
        return conn

    # ------------------------------------------------------------------
    # Data queries
    # ------------------------------------------------------------------
    def _month_range(self, month_name: str) -> tuple[str, str]:
        dt = datetime.strptime(month_name, "%B %Y")
        start = dt.replace(day=1)
        last_day = calendar.monthrange(dt.year, dt.month)[1]
        end = dt.replace(day=last_day)
        return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")

    def _expense_breakdown(self, month_name: str) -> tuple[list[str], list[float]]:
        start, end = self._month_range(month_name)
        conn = self._get_conn()
        cur = conn.execute(
            """
            SELECT COALESCE(c.name, 'Uncategorised') AS name,
                   SUM(ABS(t.amount)) AS total
            FROM transactions t
            LEFT JOIN categories c ON t.category = c.id
            WHERE t.type='expense' AND t.date BETWEEN ? AND ?
            GROUP BY name
            ORDER BY total DESC
            """,
            (start, end),
        )
        rows = cur.fetchall()
        conn.close()
        labels = [row["name"] for row in rows]
        totals = [row["total"] for row in rows]
        return labels, totals

    def _income_vs_expenses(self, month_name: str) -> tuple[list[str], list[float], list[float]]:
        dt = datetime.strptime(month_name, "%B %Y")
        conn = self._get_conn()
        labels: list[str] = []
        incomes: list[float] = []
        expenses: list[float] = []
        for i in range(5, -1, -1):
            year = dt.year
            month = dt.month - i
            while month <= 0:
                month += 12
                year -= 1
            label_dt = datetime(year, month, 1)
            labels.append(label_dt.strftime("%b %Y"))
            start = label_dt.replace(day=1).strftime("%Y-%m-%d")
            last_day = calendar.monthrange(year, month)[1]
            end = label_dt.replace(day=last_day).strftime("%Y-%m-%d")
            cur = conn.execute(
                "SELECT SUM(amount) FROM transactions WHERE type='income' AND date BETWEEN ? AND ?",
                (start, end),
            )
            income = cur.fetchone()[0] or 0.0
            cur = conn.execute(
                "SELECT SUM(ABS(amount)) FROM transactions WHERE type='expense' AND date BETWEEN ? AND ?",
                (start, end),
            )
            expense = cur.fetchone()[0] or 0.0
            incomes.append(income)
            expenses.append(expense)
        conn.close()
        return labels, incomes, expenses

    # ------------------------------------------------------------------
    # Chart rendering
    # ------------------------------------------------------------------
    def _draw_pie(self, labels: list[str], totals: list[float]) -> None:
        self.pie_fig.clear()
        ax = self.pie_fig.add_subplot(111)
        if totals:
            ax.pie(totals, labels=labels, autopct="%1.1f%%")
        ax.set_title("Expenses by Category")
        self.pie_fig.tight_layout()
        self.pie_canvas.draw()

    def _draw_bar(self, labels: list[str], incomes: list[float], expenses: list[float]) -> None:
        self.bar_fig.clear()
        ax = self.bar_fig.add_subplot(111)
        x = range(len(labels))
        ax.bar([i - 0.2 for i in x], incomes, width=0.4, label="Income")
        ax.bar([i + 0.2 for i in x], expenses, width=0.4, label="Expense")
        ax.set_xticks(list(x))
        ax.set_xticklabels(labels, rotation=45, ha="right")
        ax.set_ylabel("Amount")
        ax.legend()
        self.bar_fig.tight_layout()
        self.bar_canvas.draw()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def update_dashboard(self, month_name: str) -> None:
        labels, totals = self._expense_breakdown(month_name)
        self._draw_pie(labels, totals)

        months, incomes, expenses = self._income_vs_expenses(month_name)
        self._draw_bar(months, incomes, expenses)
