from PyQt5 import QtWidgets, QtCore, QtGui
import sip
import sqlite3

from logic.categoriser import DB_PATH, _ensure_db

from .overview_section import OverviewSection

class ReorderableScrollArea(QtWidgets.QScrollArea):
    """Scroll area that exposes its container and layout and saves widget order."""

    def __init__(self, parent: QtWidgets.QWidget | None = None, month_id: int | None = None) -> None:
        super().__init__(parent)
        self.month_id = month_id or 1
        container = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setWidget(container)
        self.setWidgetResizable(True)

        # store references to prevent premature deletion
        self.container = container
        self._layout = layout

    # ------------------------------------------------------------------
    # Persistence helpers
    # ------------------------------------------------------------------
    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        _ensure_db(conn)
        return conn

    def save_order(self) -> None:
        """Persist the current widget order for this month."""
        if self.month_id is None:
            return
        conn = self._get_conn()
        conn.execute("DELETE FROM layout_order WHERE month_id = ?", (self.month_id,))
        for idx in range(self._layout.count()):
            item = self._layout.itemAt(idx)
            widget = item.widget()
            if widget is None:
                continue
            table_id = widget.objectName()
            if not table_id:
                continue
            conn.execute(
                "INSERT INTO layout_order (month_id, table_id, position) VALUES (?, ?, ?)",
                (self.month_id, table_id, idx),
            )
        conn.commit()
        conn.close()

    def load_order(self) -> None:
        """Reorder widgets based on saved layout."""
        if self.month_id is None:
            return
        conn = self._get_conn()
        cur = conn.execute(
            "SELECT table_id, position FROM layout_order WHERE month_id = ? ORDER BY position",
            (self.month_id,),
        )
        rows = cur.fetchall()
        conn.close()
        if not rows:
            return

        widgets: dict[str, QtWidgets.QWidget] = {}
        for i in range(self._layout.count()):
            w = self._layout.itemAt(i).widget()
            if w is not None:
                widgets[w.objectName()] = w

        for i in reversed(range(self._layout.count())):
            item = self._layout.takeAt(i)
            if item.widget() is not None:
                item.widget().setParent(None)

        for row in rows:
            w = widgets.get(row["table_id"])
            if w is not None:
                self._layout.addWidget(w)

        for name, w in widgets.items():
            if name not in {r["table_id"] for r in rows}:
                self._layout.addWidget(w)

    # ------------------------------------------------------------------
    # Drag-and-drop hook
    # ------------------------------------------------------------------
    def dropEvent(self, event: QtGui.QDropEvent) -> None:  # type: ignore
        super().dropEvent(event)
        self.save_order()

class MonthlyTab(QtWidgets.QWidget):
    """A tab containing reorderable sections for a month."""

    def __init__(self, parent: QtWidgets.QWidget | None = None, month_id: int | None = None) -> None:
        super().__init__(parent)
        self.month_id = month_id or 1
        # create scroll area before any sections are added
        self.area = ReorderableScrollArea(self, self.month_id)
        self.container = self.area.container
        self._layout = self.area._layout

        self.overview = OverviewSection()
        self._layout.addWidget(self.overview)

        outer_layout = QtWidgets.QVBoxLayout(self)
        outer_layout.addWidget(self.area)

        # restore layout order if saved
        QtCore.QTimer.singleShot(0, self.area.load_order)
        
    def add_section(self, widget: QtWidgets.QWidget) -> None:
        """Add a new section widget to the tab."""
        if sip.isdeleted(self._layout):
            print("Skipped add_section: layout has been deleted.")
            return
        self._layout.addWidget(widget)

    def refresh_overview(self) -> None:
        """Refresh charts in the overview section."""
        self.overview.refresh()

class MonthlyTabbedWindow(QtWidgets.QMainWindow):
    """Main window showing a tab of monthly sections."""

    def __init__(self, parent: QtWidgets.QWidget | None = None, month_id: int | None = None) -> None:
        super().__init__(parent)
        central = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(central)
        self.monthly_tab = MonthlyTab(month_id=month_id)
        layout.addWidget(self.monthly_tab)
        self.setCentralWidget(central)

        # keep references so layout/container persist
        self._central_container = central
        self._central_layout = layout

    def refresh_overview(self) -> None:
        """Refresh charts for the current month."""
        self.monthly_tab.refresh_overview()
