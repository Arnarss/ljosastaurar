"""
Telemetry & Statistics Panel for PySide6/PyQt6.
Displays live vehicle speed, GPS coordinates, fix status, and session counts.
"""

from src.gui.qt_compat import QWidget, QVBoxLayout, QGroupBox, QGridLayout, QLabel, QFont, Qt
from src.capture.gps_receiver import GPSData


class TelemetryPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # GPS Box
        gps_group = QGroupBox("📡 GPS Telemetry", self)
        gps_grid = QGridLayout(gps_group)

        self.lbl_fix = QLabel("Searching...")
        self.lbl_fix.setStyleSheet("color: #ff9800; font-weight: bold;")
        self.lbl_coords = QLabel("0.000000°, 0.000000°")
        self.lbl_speed = QLabel("0.0 km/h")
        self.lbl_heading = QLabel("0.0°")
        self.lbl_sats = QLabel("0 satellites")

        gps_grid.addWidget(QLabel("Status:"), 0, 0)
        gps_grid.addWidget(self.lbl_fix, 0, 1)
        gps_grid.addWidget(QLabel("Coords:"), 1, 0)
        gps_grid.addWidget(self.lbl_coords, 1, 1)
        gps_grid.addWidget(QLabel("Speed:"), 2, 0)
        gps_grid.addWidget(self.lbl_speed, 2, 1)
        gps_grid.addWidget(QLabel("Heading:"), 3, 0)
        gps_grid.addWidget(self.lbl_heading, 3, 1)
        gps_grid.addWidget(QLabel("Sats:"), 4, 0)
        gps_grid.addWidget(self.lbl_sats, 4, 1)

        layout.addWidget(gps_group)

        # Statistics Box
        stats_group = QGroupBox("📊 Inspection Statistics", self)
        stats_grid = QGridLayout(stats_group)

        self.lbl_total = QLabel("0")
        self.lbl_working = QLabel("0")
        self.lbl_defective = QLabel("0")

        self.lbl_total.setFont(QFont("Monospace", 14, QFont.Weight.Bold))
        self.lbl_working.setFont(QFont("Monospace", 14, QFont.Weight.Bold))
        self.lbl_defective.setFont(QFont("Monospace", 14, QFont.Weight.Bold))

        self.lbl_working.setStyleSheet("color: #4caf50;")
        self.lbl_defective.setStyleSheet("color: #f44336;")

        stats_grid.addWidget(QLabel("Total Inspected:"), 0, 0)
        stats_grid.addWidget(self.lbl_total, 0, 1)
        stats_grid.addWidget(QLabel("Working (ON):"), 1, 0)
        stats_grid.addWidget(self.lbl_working, 1, 1)
        stats_grid.addWidget(QLabel("Defective (OFF):"), 2, 0)
        stats_grid.addWidget(self.lbl_defective, 2, 1)

        layout.addWidget(stats_group)
        layout.addStretch()

    def update_gps(self, gps: GPSData):
        if gps.fix_quality and "No" not in gps.fix_quality:
            self.lbl_fix.setText(gps.fix_quality)
            self.lbl_fix.setStyleSheet("color: #4caf50; font-weight: bold;")
        else:
            self.lbl_fix.setText("No Fix")
            self.lbl_fix.setStyleSheet("color: #f44336; font-weight: bold;")

        self.lbl_coords.setText(f"{gps.latitude:.5f}°, {gps.longitude:.5f}°")
        self.lbl_speed.setText(f"{gps.speed_kmh:.1f} km/h")
        self.lbl_heading.setText(f"{gps.heading:.1f}°")
        self.lbl_sats.setText(f"{gps.satellites} satellites")

    def update_stats(self, total: int, working: int, defective: int):
        self.lbl_total.setText(str(total))
        self.lbl_working.setText(str(working))
        self.lbl_defective.setText(str(defective))
