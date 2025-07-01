from PyQt5 import QtWidgets, QtCore, QtGui

class ReorderableScrollArea(QtWidgets.QScrollArea):
    """Scroll area allowing drag-and-drop reordering of child widgets."""

    def __init__(self, name: str) -> None:
        super().__init__()
        self.setObjectName(name)
        self.setWidgetResizable(True)
        self.setAcceptDrops(True)

        self.container = QtWidgets.QWidget()
        self.layout = QtWidgets.QVBoxLayout(self.container)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(8)
        self.layout.addStretch()
        self.setWidget(self.container)

        self._drag_start = QtCore.QPoint()
        self._drag_widget: QtWidgets.QWidget | None = None

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _sections(self) -> list[QtWidgets.QWidget]:
        return [self.layout.itemAt(i).widget() for i in range(self.layout.count() - 1)]

    def add_section(self, widget: QtWidgets.QWidget) -> None:
        widget.installEventFilter(self)
        self.layout.insertWidget(self.layout.count() - 1, widget)

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
        self.layout.removeWidget(self._drag_widget)
        self.layout.insertWidget(index, self._drag_widget)
        self._drag_widget = None
        self.save_order()
        event.acceptProposedAction()

    def _index_at(self, pos: QtCore.QPoint) -> int:
        for i, widget in enumerate(self._sections()):
            rect = widget.geometry()
            if pos.y() < rect.center().y():
                return i
        return self.layout.count() - 1

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------
    def save_order(self) -> None:
        order = [w.objectName() for w in self._sections()]
        settings = QtCore.QSettings("PFA", "MonthlyLayout")
        settings.setValue(self.objectName(), order)

    def load_order(self) -> None:
        settings = QtCore.QSettings("PFA", "MonthlyLayout")
        order = settings.value(self.objectName())
        if not isinstance(order, list):
            return
        widgets = {w.objectName(): w for w in self._sections()}
        for name in order:
            w = widgets.get(name)
            if w is not None:
                self.layout.removeWidget(w)
                self.layout.insertWidget(self.layout.count() - 1, w)


__all__ = ['ReorderableScrollArea']
