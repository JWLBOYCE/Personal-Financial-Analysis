from PyQt5 import QtWidgets
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import sqlite3
from logic.categoriser import DB_PATH, _ensure_db

class OverviewSection(QtWidgets.QWidget):
    """Widget showing passive income and asset allocation charts."""
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QtWidgets.QHBoxLayout(self)

        self.passive_fig = Figure(figsize=(4, 3))
        self.passive_canvas = FigureCanvas(self.passive_fig)
        layout.addWidget(self.passive_canvas)

        self.asset_fig = Figure(figsize=(4, 3))
        self.asset_canvas = FigureCanvas(self.asset_fig)
        layout.addWidget(self.asset_canvas)

        layout.addStretch()
        self.setLayout(layout)

        self.refresh()

    def _get_conn(self):
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        _ensure_db(conn)
        return conn

    def refresh(self):
        """Refresh charts using data from the database."""
        conn = self._get_conn()
        try:
            # Passive income
            cur = conn.execute(
                """
                SELECT description, SUM(amount) as total FROM transactions
                WHERE (category LIKE '%Interest%' OR category LIKE '%Dividend%')
                GROUP BY description
                ORDER BY total DESC
                """
            )
            rows = cur.fetchall()
            labels = [row['description'] for row in rows]
            values = [row['total'] for row in rows]

            self.passive_fig.clear()
            ax1 = self.passive_fig.add_subplot(111)
            ax1.bar(labels, values)
            ax1.set_ylabel('Amount')
            ax1.set_title('Passive Income')
            ax1.tick_params(axis='x', rotation=45)
            self.passive_fig.tight_layout()
            self.passive_canvas.draw()

            # Asset allocation
            cur = conn.execute(
                "SELECT name, amount FROM assets" if self._assets_exist(conn) else "SELECT '' as name, 1 as amount"
            )
            rows = cur.fetchall()
            names = [row['name'] for row in rows]
            amounts = [row['amount'] for row in rows]
            self.asset_fig.clear()
            ax2 = self.asset_fig.add_subplot(111)
            if amounts:
                ax2.pie(amounts, labels=names, autopct='%1.1f%%')
            ax2.set_title('Asset Allocation')
            self.asset_fig.tight_layout()
            self.asset_canvas.draw()
        finally:
            conn.close()

    def _assets_exist(self, conn):
        cur = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='assets'"
        )
        return cur.fetchone() is not None
