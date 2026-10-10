"""
Inspection Worker Thread (QThread).
Decouples camera capture, AI detection, GPS polling, and database persistence from the UI.
"""

import os
import time
from typing import Optional
import numpy as np

from src.gui.qt_compat import QThread, Signal
from src.capture.video_stream import VideoStream
from src.capture.gps_receiver import GPSData, MockGPSReceiver, SerialNMEAGPSReceiver
from src.detection.detector import StreetlightDetector, DetectedStreetlight
from src.geo.spatial_filter import SpatialDeduplicator
from src.storage.database import InspectionDatabase, DefectIncident


class InspectionWorker(QThread):
    sig_frame_processed = Signal(object, list)   # (np.ndarray frame, List[DetectedStreetlight])
    sig_gps_updated = Signal(object)             # (GPSData)
    sig_defect_detected = Signal(object)         # (DefectIncident)
    sig_stats_updated = Signal(int, int, int)    # (total, working, defective)

    def __init__(
        self,
        video_source: str = "0",
        gps_mode: str = "mock",
        gps_port: str = "/dev/ttyUSB0",
        model_path: str = "yolov8n.pt",
        conf_thresh: float = 0.35,
        luminance_thresh: float = 180.0,
        dedup_radius: float = 15.0,
        db_path: str = "data/outputs/inspections.db",
        phone_url: str = "http://192.168.43.1:8080/sensors.json",
        parent=None
    ):
        super().__init__(parent)
        self.video_source = video_source
        self.gps_mode = gps_mode
        self.gps_port = gps_port
        self.phone_url = phone_url
        self.model_path = model_path
        self.conf_thresh = conf_thresh
        self.luminance_thresh = luminance_thresh
        self.dedup_radius = dedup_radius
        self.db_path = db_path
        self._running = False

        # Session counters
        self.total_count = 0
        self.working_count = 0
        self.defective_count = 0
        self.seen_track_ids = set()

    def run(self):
        self._running = True

        # Initialize Video Stream
        video = VideoStream(source=self.video_source)
        video.start()

        # Initialize GPS Receiver
        if self.gps_mode == "serial":
            gps_recv = SerialNMEAGPSReceiver(port=self.gps_port)
        elif self.gps_mode == "phone":
            from src.capture.gps_receiver import NetworkPhoneGPSReceiver
            gps_recv = NetworkPhoneGPSReceiver(phone_url=self.phone_url)
        else:
            gps_recv = MockGPSReceiver()
        gps_recv.start()


        # Initialize Detector, Deduplicator, and Database
        detector = StreetlightDetector(
            model_path=self.model_path,
            conf_thresh=self.conf_thresh,
            luminance_thresh=self.luminance_thresh
        )
        deduplicator = SpatialDeduplicator(radius_meters=self.dedup_radius)
        db = InspectionDatabase(db_path=self.db_path)

        while self._running:
            ret, frame = video.read()
            if not ret or frame is None:
                time.sleep(0.01)
                continue

            # Read current GPS fix
            gps_data: GPSData = gps_recv.get_latest_fix()
            self.sig_gps_updated.emit(gps_data)

            # Detect and evaluate streetlight states
            detections = detector.detect_and_classify(frame)

            for det in detections:
                if det.track_id not in self.seen_track_ids:
                    self.seen_track_ids.add(det.track_id)
                    self.total_count += 1
                    if det.state == "ON":
                        self.working_count += 1
                    else:
                        self.defective_count += 1

                # If detected OFF, check spatial deduplication
                if det.state == "OFF" and gps_data.is_valid():
                    if deduplicator.should_log(gps_data.latitude, gps_data.longitude):
                        # Save frame snapshot evidence
                        snapshot_dir = "data/snapshots"
                        os.makedirs(snapshot_dir, exist_ok=True)
                        snap_name = f"defect_{int(time.time())}_track{det.track_id}.jpg"
                        snap_path = os.path.join(snapshot_dir, snap_name)

                        try:
                            import cv2
                            cv2.imwrite(snap_path, frame)
                        except Exception:
                            snap_path = ""

                        incident = DefectIncident(
                            timestamp=time.time(),
                            latitude=gps_data.latitude,
                            longitude=gps_data.longitude,
                            speed_kmh=gps_data.speed_kmh,
                            confidence=det.confidence,
                            status="OFF",
                            snapshot_path=snap_path
                        )
                        inc_id = db.log_defect(incident)
                        incident.id = inc_id
                        self.sig_defect_detected.emit(incident)

            # Emit live frame and stats
            self.sig_frame_processed.emit(frame, detections)
            self.sig_stats_updated.emit(self.total_count, self.working_count, self.defective_count)

            # Cap loop rate to ~30 FPS to avoid overloading GUI event loop
            time.sleep(0.033)

        # Cleanup
        video.stop()
        gps_recv.stop()

    def stop(self):
        self._running = False
        self.wait(1000)
