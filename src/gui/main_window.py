"""
Main Window for the PySide6 / PyQt6 Streetlight Defect Inspection System.
"""

import os
import webbrowser
from src.gui.qt_compat import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QPushButton, QComboBox, QLabel, QFileDialog, QMessageBox, Qt
)
from src.gui.video_widget import VideoDisplayWidget
from src.gui.telemetry_panel import TelemetryPanel
from src.gui.incident_table import IncidentTableWidget
from src.gui.worker import InspectionWorker
from src.storage.database import InspectionDatabase
from src.storage.exporter import export_to_geojson, export_to_html_map


DARK_THEME_QSS = """
QMainWindow {
    background-color: #1e1e24;
}
QWidget {
    color: #e0e0e0;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    font-size: 13px;
}
QGroupBox {
    background-color: #25252d;
    border: 1px solid #383845;
    border-radius: 6px;
    margin-top: 14px;
    padding-top: 12px;
    font-weight: bold;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 6px;
    color: #90caf9;
}
QPushButton {
    background-color: #2e7d32;
    color: #ffffff;
    font-weight: bold;
    border: none;
    border-radius: 4px;
    padding: 8px 16px;
}
QPushButton:hover {
    background-color: #388e3c;
}
QPushButton#stopBtn {
    background-color: #c62828;
}
QPushButton#stopBtn:hover {
    background-color: #d32f2f;
}
QPushButton#secondaryBtn {
    background-color: #37474f;
}
QPushButton#secondaryBtn:hover {
    background-color: #455a64;
}
QComboBox {
    background-color: #2c2c36;
    border: 1px solid #48485a;
    border-radius: 4px;
    padding: 6px 12px;
    color: #ffffff;
}
QTableWidget {
    background-color: #1b1b22;
    alternate-background-color: #24242e;
    gridline-color: #323240;
    border: 1px solid #383845;
    border-radius: 4px;
}
QHeaderView::section {
    background-color: #282834;
    color: #90caf9;
    font-weight: bold;
    padding: 5px;
    border: 1px solid #323240;
}
"""


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🌙 Ljósastaurar - Night Streetlight Defect Inspector")
        self.resize(1280, 800)
        self.setStyleSheet(DARK_THEME_QSS)

        self.worker: Optional[InspectionWorker] = None
        self.db = InspectionDatabase()

        self._init_ui()
        self._load_previous_records()

    def _init_ui(self):
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # 1. Top Control Bar
        control_bar = QHBoxLayout()

        control_bar.addWidget(QLabel("Video Source:"))
        self.combo_source = QComboBox()
        self.combo_source.addItems([
            "Synthetic Night Simulation",
            "Webcam (Index 0)",
            "Smartphone Camera (IP Stream)...",
            "Select Video File (.mp4)..."
        ])
        self.combo_source.currentIndexChanged.connect(self._on_source_change)
        control_bar.addWidget(self.combo_source)

        control_bar.addWidget(QLabel("GPS Source:"))
        self.combo_gps = QComboBox()
        self.combo_gps.addItems([
            "Mock Simulation (Reykjavik)",
            "USB Serial NMEA (/dev/ttyUSB0)",
            "Smartphone GPS (IP Webcam / Wi-Fi)"
        ])
        self.combo_gps.currentIndexChanged.connect(self._on_gps_change)
        control_bar.addWidget(self.combo_gps)

        self.btn_toggle = QPushButton("▶ Start Inspection")
        self.btn_toggle.clicked.connect(self._toggle_inspection)
        control_bar.addWidget(self.btn_toggle)

        self.btn_export = QPushButton("🗺️ Export GeoJSON")
        self.btn_export.setObjectName("secondaryBtn")
        self.btn_export.clicked.connect(self._export_geojson)
        control_bar.addWidget(self.btn_export)

        self.btn_map = QPushButton("🌐 View Map")
        self.btn_map.setObjectName("secondaryBtn")
        self.btn_map.clicked.connect(self._open_map)
        control_bar.addWidget(self.btn_map)

        control_bar.addStretch()
        main_layout.addLayout(control_bar)

        # 2. Main Content Splitter (Vertical)
        v_splitter = QSplitter(Qt.Orientation.Vertical)

        # Upper section: Horizontal Splitter (Video Left, Telemetry Right)
        h_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.video_widget = VideoDisplayWidget(self)
        self.telemetry_panel = TelemetryPanel(self)

        h_splitter.addWidget(self.video_widget)
        h_splitter.addWidget(self.telemetry_panel)
        h_splitter.setStretchFactor(0, 4)
        h_splitter.setStretchFactor(1, 1)

        v_splitter.addWidget(h_splitter)

        # Lower section: Incident Table
        self.incident_table = IncidentTableWidget(self)
        v_splitter.addWidget(self.incident_table)
        v_splitter.setStretchFactor(0, 3)
        v_splitter.setStretchFactor(1, 2)

        main_layout.addWidget(v_splitter)

        self.custom_video_path = ""
        self.phone_stream_url = "http://192.168.43.1:8080/video"
        self.phone_sensors_url = "http://192.168.43.1:8080/sensors.json"

    def _on_source_change(self, index: int):
        from src.gui.qt_compat import QInputDialog
        if index == 2:  # Smartphone Camera
            url, ok = QInputDialog.getText(
                self, "Phone Camera Stream URL",
                "Enter IP Webcam or RTSP URL:\n(e.g., http://192.168.43.1:8080/video)",
                text=self.phone_stream_url
            )
            if ok and url:
                self.phone_stream_url = url
                # Update sensors url to match phone host
                host_base = url.rsplit("/", 1)[0]
                self.phone_sensors_url = f"{host_base}/sensors.json"
                self.combo_source.setItemText(2, f"Phone: {url}")
            else:
                self.combo_source.setCurrentIndex(0)
        elif index == 3:  # Select Video File
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Select Night Driving Video", "", "Video Files (*.mp4 *.avi *.mkv *.mov)"
            )
            if file_path:
                self.custom_video_path = file_path
                self.combo_source.setItemText(3, f"File: {os.path.basename(file_path)}")
            else:
                self.combo_source.setCurrentIndex(0)

    def _on_gps_change(self, index: int):
        from src.gui.qt_compat import QInputDialog
        if index == 2:  # Smartphone GPS
            url, ok = QInputDialog.getText(
                self, "Phone GPS Sensors URL",
                "Enter IP Webcam sensors endpoint:\n(e.g., http://192.168.43.1:8080/sensors.json)",
                text=self.phone_sensors_url
            )
            if ok and url:
                self.phone_sensors_url = url

    def _toggle_inspection(self):
        if self.worker is not None and self.worker.isRunning():
            # Stop inspection
            self.worker.stop()
            self.worker = None
            self.btn_toggle.setText("▶ Start Inspection")
            self.btn_toggle.setObjectName("")
            self.btn_toggle.setStyleSheet("background-color: #2e7d32;")
        else:
            # Determine video source
            source_idx = self.combo_source.currentIndex()
            if source_idx == 0:
                v_source = "synthetic"
            elif source_idx == 1:
                v_source = "0"
            elif source_idx == 2:
                v_source = self.phone_stream_url
            else:
                v_source = self.custom_video_path or "synthetic"

            # Determine GPS mode
            gps_idx = self.combo_gps.currentIndex()
            if gps_idx == 1:
                gps_mode = "serial"
            elif gps_idx == 2:
                gps_mode = "phone"
            else:
                gps_mode = "mock"

            self.worker = InspectionWorker(
                video_source=v_source,
                gps_mode=gps_mode,
                gps_port="/dev/ttyUSB0",
                phone_url=self.phone_sensors_url
            )

            # Connect signals
            self.worker.sig_frame_processed.connect(self.video_widget.update_frame)
            self.worker.sig_gps_updated.connect(self.telemetry_panel.update_gps)
            self.worker.sig_defect_detected.connect(self.incident_table.add_incident)

            self.worker.sig_stats_updated.connect(self.telemetry_panel.update_stats)

            self.worker.start()
            self.btn_toggle.setText("⏹ Stop Inspection")
            self.btn_toggle.setStyleSheet("background-color: #c62828;")

    def _load_previous_records(self):
        records = self.db.get_all_incidents()
        for rec in reversed(records):
            self.incident_table.add_incident(rec)

    def _export_geojson(self):
        incidents = self.db.get_all_incidents()
        if not incidents:
            QMessageBox.information(self, "Export", "No defect incidents recorded yet.")
            return

        out_path = export_to_geojson(incidents)
        QMessageBox.information(self, "Export Successful", f"GeoJSON exported to:\n{os.path.abspath(out_path)}")

    def _open_map(self):
        incidents = self.db.get_all_incidents()
        map_path = export_to_html_map(incidents)
        if map_path and os.path.exists(map_path):
            webbrowser.open(f"file://{os.path.abspath(map_path)}")
        else:
            QMessageBox.information(
                self, "Folium Not Available",
                "To generate interactive HTML maps, install folium:\npip install folium\n\nGeoJSON export is already available."
            )

    def closeEvent(self, event):
        if self.worker is not None:
            self.worker.stop()
        event.accept()
