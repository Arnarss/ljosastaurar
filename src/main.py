"""
Application Entry Point for Ljósastaurar (Streetlight Defect Detector).
Supports both GUI mode (PySide6 / PyQt6) and Headless CLI mode.
"""

import argparse
import sys
import os

# Ensure project root is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def run_gui():
    from src.gui.qt_compat import QApplication
    from src.gui.main_window import MainWindow

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


def run_cli(video_source: str, gps_mode: str):
    import time
    from src.capture.video_stream import VideoStream
    from src.capture.gps_receiver import MockGPSReceiver, SerialNMEAGPSReceiver
    from src.detection.detector import StreetlightDetector
    from src.geo.spatial_filter import SpatialDeduplicator
    from src.storage.database import InspectionDatabase, DefectIncident

    print("[CLI] Starting Ljósastaurar Headless Inspection Loop...")
    print(f"[CLI] Video Source: {video_source} | GPS Mode: {gps_mode}")

    video = VideoStream(source=video_source)
    video.start()

    gps_recv = SerialNMEAGPSReceiver() if gps_mode == "serial" else MockGPSReceiver()
    gps_recv.start()

    detector = StreetlightDetector()
    dedup = SpatialDeduplicator()
    db = InspectionDatabase()

    try:
        while True:
            ret, frame = video.read()
            if not ret or frame is None:
                time.sleep(0.01)
                continue

            gps_data = gps_recv.get_latest_fix()
            detections = detector.detect_and_classify(frame)

            for det in detections:
                if det.state == "OFF" and gps_data.is_valid():
                    if dedup.should_log(gps_data.latitude, gps_data.longitude):
                        inc = DefectIncident(
                            timestamp=time.time(),
                            latitude=gps_data.latitude,
                            longitude=gps_data.longitude,
                            speed_kmh=gps_data.speed_kmh,
                            confidence=det.confidence,
                            status="OFF"
                        )
                        inc_id = db.log_defect(inc)
                        print(f"🚨 [DEFECT LOGGED #{inc_id}] Lat: {gps_data.latitude:.5f}, Lon: {gps_data.longitude:.5f}, Speed: {gps_data.speed_kmh:.1f} km/h")

            time.sleep(0.033)
    except KeyboardInterrupt:
        print("\n[CLI] Stopping inspection...")
    finally:
        video.stop()
        gps_recv.stop()


def main():
    parser = argparse.ArgumentParser(description="Ljósastaurar - Night Streetlight Defect Detection System")
    parser.add_argument("--cli", action="store_true", help="Run in headless CLI mode instead of GUI")
    parser.add_argument("--source", type=str, default="synthetic", help="Video source (0 for webcam, file path, or synthetic)")
    parser.add_argument("--gps", type=str, default="mock", choices=["mock", "serial"], help="GPS source mode")

    args = parser.parse_args()

    if args.cli:
        run_cli(args.source, args.gps)
    else:
        run_gui()


if __name__ == "__main__":
    main()
