from PyQt5 import QtWidgets
import sip

from .overview_section import OverviewSection

class ReorderableScrollArea(QtWidgets.QScrollArea):
    """Scroll area that exposes its container and layout."""
    def __init__(self, parent=None):
        super().__init__(parent)
        container = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setWidget(container)
        self.setWidgetResizable(True)

        # store references to prevent premature deletion
        self.container = container
        self._layout = layout

class MonthlyTab(QtWidgets.QWidget):
    """A tab containing reorderable sections for a month."""
    def __init__(self, parent=None):
        super().__init__(parent)
        # create scroll area before any sections are added
        self.area = ReorderableScrollArea(self)
        self.container = self.area.container
        self._layout = self.area._layout

        self.overview = OverviewSection()
        self._layout.addWidget(self.overview)

        outer_layout = QtWidgets.QVBoxLayout(self)
        outer_layout.addWidget(self.area)
        
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
    def __init__(self, parent=None):
        super().__init__(parent)
        central = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(central)
        self.monthly_tab = MonthlyTab()
        layout.addWidget(self.monthly_tab)
        self.setCentralWidget(central)

        # keep references so layout/container persist
        self._central_container = central
        self._central_layout = layout

    def refresh_overview(self) -> None:
        """Refresh charts for the current month."""
        self.monthly_tab.refresh_overview()
