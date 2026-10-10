"""
Threaded Video Stream module supporting Webcams, RTSP, Video Files, and Synthetic Simulation.
"""

import math
import threading
import time
from typing import Optional, Tuple, Union
import numpy as np


class VideoStream:
    """
    Threaded video reader for low-latency frame acquisition.
    """

    def __init__(self, source: Union[int, str] = 0, width: int = 1280, height: int = 720, fps: int = 30):
        self.source = source
        self.target_width = width
        self.target_height = height
        self.target_fps = fps
        self.cap = None
        self.latest_frame: Optional[np.ndarray] = None
        self.running = False
        self.lock = threading.Lock()
        self.is_synthetic = False
        self._synthetic_step = 0

    def start(self):
        self.running = True
        try:
            import cv2
            if isinstance(self.source, str) and self.source.isdigit():
                source_val = int(self.source)
            else:
                source_val = self.source

            self.cap = cv2.VideoCapture(source_val)
            if not self.cap.isOpened():
                print(f"[VideoStream] Camera source {self.source} could not be opened. Using Synthetic Night Simulation.")
                self.is_synthetic = True
            else:
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.target_width)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.target_height)
        except Exception as e:
            print(f"[VideoStream] OpenCV error ({e}). Using Synthetic Night Simulation.")
            self.is_synthetic = True

        self.thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.thread.start()

    def _capture_loop(self):
        delay = 1.0 / self.target_fps
        while self.running:
            start_t = time.time()
            if self.is_synthetic:
                frame = self._generate_synthetic_night_frame()
                with self.lock:
                    self.latest_frame = frame
            else:
                if self.cap and self.cap.isOpened():
                    ret, frame = self.cap.read()
                    if ret and frame is not None:
                        with self.lock:
                            self.latest_frame = frame
                    else:
                        # Video file ended or frame drop
                        time.sleep(0.01)

            elapsed = time.time() - start_t
            sleep_t = max(0.001, delay - elapsed)
            time.sleep(sleep_t)

    def read(self) -> Tuple[bool, Optional[np.ndarray]]:
        with self.lock:
            if self.latest_frame is not None:
                return True, self.latest_frame.copy()
            return False, None

    def stop(self):
        self.running = False
        if hasattr(self, "thread") and self.thread.is_alive():
            self.thread.join(timeout=0.5)
        if self.cap and self.cap.isOpened():
            self.cap.release()

    def _generate_synthetic_night_frame(self) -> np.ndarray:
        """
        Generates a 1280x720 synthetic nighttime road scene with passing streetlights.
        Lamp states alternate between functioning (ON with yellow glow) and defective (OFF).
        """
        w, h = self.target_width, self.target_height
        frame = np.zeros((h, w, 3), dtype=np.uint8)

        # Dark night sky with slight horizon gradient
        horizon_y = int(h * 0.55)
        frame[horizon_y:, :] = (20, 20, 20)  # Dark asphalt

        # Road perspective lines (vehicle driving forward)
        left_bottom = (int(w * 0.15), h)
        right_bottom = (int(w * 0.85), h)
        vp = (int(w * 0.5), horizon_y)

        # Simple road markings
        self._synthetic_step = (self._synthetic_step + 1) % 1000
        phase = (self._synthetic_step % 60) / 60.0

        # Simulate streetlights on right roadside
        # Lamp moves from horizon towards bottom-right as vehicle advances
        for lamp_idx in range(3):
            p = (phase + lamp_idx * 0.33) % 1.0
            if p > 0.05:
                # 3D perspective projection
                curr_y = int(horizon_y + p * (h - horizon_y))
                curr_x = int(w * 0.5 + p * (w * 0.45))
                scale = p

                pole_h = int(180 * scale)
                pole_top_y = max(10, curr_y - pole_h)
                pole_w = max(2, int(6 * scale))

                # Draw pole (metallic grey)
                frame[pole_top_y:curr_y, curr_x:curr_x + pole_w] = (90, 90, 90)

                # Determine if this synthetic lamp is ON or OFF (lamp #2 is defective/OFF)
                is_faulty = (lamp_idx == 1)

                fixture_size = max(4, int(16 * scale))
                fx1 = curr_x - fixture_size
                fy1 = max(0, pole_top_y - fixture_size // 2)
                fx2 = curr_x + fixture_size
                fy2 = min(h, pole_top_y + fixture_size // 2)

                if is_faulty:
                    # Unlit fixture (dark grey)
                    frame[fy1:fy2, fx1:fx2] = (45, 45, 45)
                else:
                    # Functioning bright streetlight (bright warm glow)
                    frame[fy1:fy2, fx1:fx2] = (200, 245, 255)
                    # Ambient glow
                    glow_r = max(8, int(35 * scale))
                    gy1 = max(0, pole_top_y - glow_r)
                    gy2 = min(h, pole_top_y + glow_r)
                    gx1 = max(0, curr_x - glow_r)
                    gx2 = min(w, curr_x + glow_r)
                    frame[gy1:gy2, gx1:gx2] = np.clip(frame[gy1:gy2, gx1:gx2] + 40, 0, 255)

        return frame
