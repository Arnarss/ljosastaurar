"""
Video Display Widget for PySide6/PyQt6.
Renders real-time video frames with high FPS and aspect-ratio preservation.
"""

from typing import List, Optional
import numpy as np
from src.gui.qt_compat import QWidget, QLabel, QVBoxLayout, QImage, QPixmap, QPainter, QPen, QColor, QFont, Qt
from src.detection.detector import DetectedStreetlight


class VideoDisplayWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet("background-color: #121212; border-radius: 6px;")
        self.label.setText("Camera stream offline\nClick 'Start Inspection' to begin")
        self.label.setFont(QFont("Monospace", 12))
        self.layout.addWidget(self.label)

        self.latest_pixmap: Optional[QPixmap] = None

    def update_frame(self, frame_bgr: np.ndarray, detections: List[DetectedStreetlight]):
        if frame_bgr is None:
            return

        h, w, ch = frame_bgr.shape
        bytes_per_line = ch * w

        # Convert BGR (OpenCV) to RGB format for Qt QImage
        # In pure NumPy: BGR to RGB is frame_bgr[:, :, ::-1]
        frame_rgb = np.ascontiguousarray(frame_bgr[:, :, ::-1])

        qimg = QImage(frame_rgb.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(qimg)

        # Draw HUD overlays directly with QPainter
        painter = QPainter(pixmap)
        font = QFont("Sans-serif", 10, QFont.Weight.Bold)
        painter.setFont(font)

        for det in detections:
            x1, y1, x2, y2 = det.bbox
            is_off = (det.state == "OFF")

            box_color = QColor(230, 40, 40) if is_off else QColor(40, 200, 40)
            pen = QPen(box_color, 3)
            painter.setPen(pen)
            painter.drawRect(x1, y1, x2 - x1, y2 - y1)

            # Label banner
            label_text = f"#{det.track_id} {det.state} ({det.confidence:.2f})"
            painter.fillRect(x1, max(0, y1 - 22), 140, 22, box_color)
            painter.setPen(QColor(255, 255, 255))
            painter.drawText(x1 + 6, max(15, y1 - 6), label_text)

        painter.end()

        # Scale pixmap smoothly to fit current widget size
        scaled_pixmap = pixmap.scaled(
            self.label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.label.setPixmap(scaled_pixmap)
