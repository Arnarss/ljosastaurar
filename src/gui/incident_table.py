"""
Incident Log Table Widget for PySide6/PyQt6.
Lists detected defective streetlights with live updates and snapshot preview support.
"""

from src.gui.qt_compat import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView,
    QGroupBox, QMessageBox, QColor, Qt
)
from src.storage.database import DefectIncident


class IncidentTableWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        group = QGroupBox("🚨 Defective Lamppost Alerts (State: OFF)", self)
        group_layout = QVBoxLayout(group)

        self.table = QTableWidget(0, 6, self)
        self.table.setHorizontalHeaderLabels([
            "ID", "Timestamp", "Latitude", "Longitude", "Speed (km/h)", "Confidence"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.cellDoubleClicked.connect(self._on_row_double_click)

        group_layout.addWidget(self.table)
        layout.addWidget(group)

        self.incidents = []

    def add_incident(self, inc: DefectIncident):
        self.incidents.append(inc)
        row = self.table.rowCount()
        self.table.insertRow(row)

        item_id = QTableWidgetItem(f"#{inc.id}")
        item_time = QTableWidgetItem(inc.datetime_str)
        item_lat = QTableWidgetItem(f"{inc.latitude:.5f}°")
        item_lon = QTableWidgetItem(f"{inc.longitude:.5f}°")
        item_spd = QTableWidgetItem(f"{inc.speed_kmh:.1f}")
        item_conf = QTableWidgetItem(f"{inc.confidence:.2f}")

        # Highlight defect row text in red/amber
        for it in (item_id, item_time, item_lat, item_lon, item_spd, item_conf):
            it.setForeground(QColor(230, 40, 40))

        self.table.setItem(row, 0, item_id)
        self.table.setItem(row, 1, item_time)
        self.table.setItem(row, 2, item_lat)
        self.table.setItem(row, 3, item_lon)
        self.table.setItem(row, 4, item_spd)
        self.table.setItem(row, 5, item_conf)

        # Auto scroll to newest incident
        self.table.scrollToBottom()

    def _on_row_double_click(self, row: int, col: int):
        if 0 <= row < len(self.incidents):
            inc = self.incidents[row]
            msg = (
                f"Incident #{inc.id}\n"
                f"Time: {inc.datetime_str}\n"
                f"Coordinates: {inc.latitude:.6f}, {inc.longitude:.6f}\n"
                f"Speed: {inc.speed_kmh:.1f} km/h\n"
                f"Confidence: {inc.confidence:.2f}\n"
                f"Snapshot: {inc.snapshot_path or 'No snapshot saved'}"
            )
            QMessageBox.information(self, f"Defect Details #{inc.id}", msg)
