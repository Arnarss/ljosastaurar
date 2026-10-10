"""
Photometric light state analyzer.
Evaluates whether a detected streetlight luminaire is functioning (ON) or defective (OFF).
"""

from dataclasses import dataclass
from typing import Tuple
import numpy as np


@dataclass
class LampStateResult:
    is_on: bool
    state_label: str       # "ON" or "OFF"
    confidence: float      # 0.0 to 1.0
    mean_luminance: float  # 0 to 255
    peak_luminance: float  # 0 to 255


class StreetlightStateAnalyzer:
    def __init__(self, luminance_threshold: float = 180.0, min_active_ratio: float = 0.05):
        """
        :param luminance_threshold: Pixel brightness threshold in the V (Value) channel (0-255).
        :param min_active_ratio: Minimum fraction of pixels in the fixture region above threshold to be ON.
        """
        self.luminance_threshold = luminance_threshold
        self.min_active_ratio = min_active_ratio

    def analyze_crop(self, crop_bgr: np.ndarray) -> LampStateResult:
        """
        Analyzes a cropped region containing the top portion (luminaire head) of a lamppost.
        """
        if crop_bgr is None or crop_bgr.size == 0:
            return LampStateResult(False, "OFF", 0.0, 0.0, 0.0)

        # Try to convert to HSV; if OpenCV is available use cv2.cvtColor, otherwise estimate via max(R,G,B)
        try:
            import cv2
            hsv = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2HSV)
            v_channel = hsv[:, :, 2]
        except (ImportError, Exception):
            # Fallback luminance estimation: V = max(R, G, B)
            v_channel = np.max(crop_bgr, axis=2)

        mean_v = float(np.mean(v_channel))
        # Top 5th percentile brightness
        peak_v = float(np.percentile(v_channel, 95))
        active_ratio = float(np.mean(v_channel >= self.luminance_threshold))

        is_on = (peak_v >= self.luminance_threshold) and (active_ratio >= self.min_active_ratio)

        if is_on:
            confidence = min(1.0, 0.5 + (peak_v - self.luminance_threshold) / (255.0 - self.luminance_threshold) * 0.5)
            return LampStateResult(
                is_on=True,
                state_label="ON",
                confidence=round(confidence, 2),
                mean_luminance=round(mean_v, 1),
                peak_luminance=round(peak_v, 1)
            )
        else:
            # Defective / unlit
            confidence = min(1.0, 0.5 + (self.luminance_threshold - peak_v) / self.luminance_threshold * 0.5)
            return LampStateResult(
                is_on=False,
                state_label="OFF",
                confidence=round(confidence, 2),
                mean_luminance=round(mean_v, 1),
                peak_luminance=round(peak_v, 1)
            )
