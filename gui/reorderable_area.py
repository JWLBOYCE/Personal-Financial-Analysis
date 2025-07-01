from PyQt5 import QtWidgets, QtCore, QtGui
import sqlite3
import sip

from logic.month_manager import _ensure_db
from config import get_db_path

class ReorderableScrollArea(QtWidgets.QScrollArea):
    """Scroll area allowing drag-and-drop reordering of child widgets."""

    def __init__(self, name: str, month_id: str) -> None:
        super().__init__()
        self.setObjectName(name)
        self.month_id = month_id
        self.setWidgetResizable(True)
        self.setAcceptDrops(True)

        # Keep this container alive for the lifetime of the scroll area so the
        # layout is not destroyed when changing widgets.
        self.container = QtWidgets.QWidget()
        self._layout = QtWidgets.QVBoxLayout(self.container)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(8)
        self._layout.addStretch()
        # Set the container as the scroll area's widget after the layout is ready.
        self.setWidget(self.container)

        self._drag_start = QtCore.QPoint()
        self._drag_widget: QtWidgets.QWidget | None = None

    # ------------------------------------------------------------------
    # Database helpers
    # ------------------------------------------------------------------
    def _get_conn(self) -> sqlite3.Connection:
        db_path = get_db_path()
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        _ensure_db(conn)
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS layout_order (
                month_id TEXT NOT NULL,
                table_id TEXT NOT NULL,
                position INTEGER NOT NULL,
                PRIMARY KEY (month_id, table_id)
            )
            """
        )
        return conn

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _sections(self) -> list[QtWidgets.QWidget]:
        layout = getattr(self, "_layout", None)
        if layout is None:
            return []
        try:
            if sip.isdeleted(layout):
                return []
        except Exception:
            return []
        try:
            count = layout.count()
        except RuntimeError:
            return []
        return [layout.itemAt(i).widget() for i in range(count - 1)]

    def add_section(self, widget: QtWidgets.QWidget) -> None:
        """Insert a new widget section if the layout is valid."""
        if sip.isdeleted(self._layout):
            print("Layout deleted; skipping add_section.")
            return
        widget.installEventFilter(self)
        self._layout.insertWidget(self._layout.count() - 1, widget)

    def eventFilter(self, obj: QtCore.QObject, event: QtCore.QEvent) -> bool:
        if obj in self._sections():
            if event.type() == QtCore.QEvent.MouseButtonPress and isinstance(event, QtGui.QMouseEvent):
                if event.button() == QtCore.Qt.LeftButton:
                    self._drag_start = event.pos()
            elif event.type() == QtCore.QEvent.MouseMove and isinstance(event, QtGui.QMouseEvent):
                if event.buttons() & QtCore.Qt.LeftButton:
                    if (event.pos() - self._drag_start).manhattanLength() > QtWidgets.QApplication.startDragDistance():
                        drag = QtGui.QDrag(obj)
                        mime = QtCore.QMimeData()
                        mime.setData(b"application/x-section", obj.objectName().encode())
                        drag.setMimeData(mime)
                        pix = obj.grab()
                        drag.setPixmap(pix)
                        self._drag_widget = obj
                        drag.exec_(QtCore.Qt.MoveAction)
                        return True
        return super().eventFilter(obj, event)

    # ------------------------------------------------------------------
    # Drag/drop events with auto-scroll
    # ------------------------------------------------------------------
    def dragEnterEvent(self, event: QtGui.QDragEnterEvent) -> None:
        if event.mimeData().hasFormat("application/x-section"):
            event.acceptProposedAction()

    def dragMoveEvent(self, event: QtGui.QDragMoveEvent) -> None:
        if not event.mimeData().hasFormat("application/x-section"):
            return
        margin = 20
        pos = event.pos()
        bar = self.verticalScrollBar()
        if pos.y() < margin:
            bar.setValue(bar.value() - margin)
        elif pos.y() > self.viewport().height() - margin:
            bar.setValue(bar.value() + margin)
        event.acceptProposedAction()

    def dropEvent(self, event: QtGui.QDropEvent) -> None:
        if not event.mimeData().hasFormat("application/x-section") or self._drag_widget is None:
            return
        index = self._index_at(event.pos())
        self._layout.removeWidget(self._drag_widget)
        self._layout.insertWidget(index, self._drag_widget)
        self._drag_widget = None
        self.save_order()
        event.acceptProposedAction()

    def _index_at(self, pos: QtCore.QPoint) -> int:
        for i, widget in enumerate(self._sections()):
            rect = widget.geometry()
            if pos.y() < rect.center().y():
                return i
        return self._layout.count() - 1

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------
    def save_order(self) -> None:
        order = [w.objectName() for w in self._sections()]
        conn = self._get_conn()
        conn.execute(
            "DELETE FROM layout_order WHERE month_id = ?",
            (self.month_id,),
        )
        for pos, tid in enumerate(order):
            conn.execute(
                "INSERT INTO layout_order (month_id, table_id, position) VALUES (?, ?, ?)",
                (self.month_id, tid, pos),
            )
        conn.commit()
        conn.close()

    def load_order(self) -> None:
        conn = self._get_conn()
        cur = conn.execute(
            "SELECT table_id FROM layout_order WHERE month_id = ? ORDER BY position",
            (self.month_id,),
        )
        rows = cur.fetchall()
        conn.close()
        order = [row["table_id"] for row in rows]
        if not order:
            return
        widgets = {w.objectName(): w for w in self._sections()}
        for name in order:
            w = widgets.get(name)
            if w is not None:
                self._layout.removeWidget(w)
                self._layout.insertWidget(self._layout.count() - 1, w)


__all__ = ['ReorderableScrollArea']
