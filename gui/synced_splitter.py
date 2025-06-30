from PyQt5 import QtWidgets, QtCore


class SyncedSplitter(QtWidgets.QWidget):
    """Demo widget showing two synced scroll areas in a splitter."""

    def __init__(self) -> None:
        super().__init__()
        layout = QtWidgets.QHBoxLayout(self)
        splitter = QtWidgets.QSplitter()
        layout.addWidget(splitter)

        self.left_area = QtWidgets.QScrollArea()
        self.left_area.setWidgetResizable(True)
        self.left_area.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)

        self.right_area = QtWidgets.QScrollArea()
        self.right_area.setWidgetResizable(True)
        self.right_area.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)

        splitter.addWidget(self.left_area)
        splitter.addWidget(self.right_area)

        # Populate left and right scroll areas with sample content
        left_widget = QtWidgets.QWidget()
        left_layout = QtWidgets.QVBoxLayout(left_widget)
        for i in range(30):
            left_layout.addWidget(QtWidgets.QLabel(f"Left item {i + 1}"))
        left_layout.addStretch()
        self.left_area.setWidget(left_widget)

        right_widget = QtWidgets.QWidget()
        right_layout = QtWidgets.QVBoxLayout(right_widget)
        for i in range(30):
            right_layout.addWidget(QtWidgets.QLabel(f"Right item {i + 1}"))
        right_layout.addStretch()
        self.right_area.setWidget(right_widget)

        # Sync the vertical scroll bars so both areas stay aligned
        self.left_area.verticalScrollBar().valueChanged.connect(
            self.right_area.verticalScrollBar().setValue
        )
        self.right_area.verticalScrollBar().valueChanged.connect(
            self.left_area.verticalScrollBar().setValue
        )


__all__ = ["SyncedSplitter"]
