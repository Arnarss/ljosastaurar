"""
Spatial Cadence & Missing Lamp Gap Analyzer.
Detects burnt-out streetlights by measuring the physical distance interval between consecutive functioning (ON) streetlights.
This overcomes the 'black pole in black sky' problem without requiring prior map databases.
"""

from dataclasses import dataclass
import time
from typing import List, Optional, Tuple
from src.capture.gps_receiver import GPSData
from src.geo.spatial_filter import haversine_distance_meters


@dataclass
class CadenceGapAlert:
    latitude: float
    longitude: float
    timestamp: float
    gap_distance_meters: float
    expected_nominal_spacing: float
    confidence: float
    reason: str


class StreetlightCadenceAnalyzer:
    """
    Monitors the cadence (regular spacing) of functioning streetlights.
    Typical municipal streetlights are spaced 25m - 40m apart.
    When a gap significantly exceeds nominal spacing (e.g., > 50m - 70m),
    a burnt-out/missing streetlight is deduced at the midpoint.
    """

    def __init__(
        self,
        nominal_spacing_meters: float = 30.0,
        min_speed_kmh: float = 15.0,
        gap_multiplier_threshold: float = 1.7
    ):
        self.nominal_spacing = nominal_spacing_meters
        self.min_speed_kmh = min_speed_kmh
        self.threshold_gap = nominal_spacing_meters * gap_multiplier_threshold
        self.last_lit_lamp_gps: Optional[GPSData] = None
        self.last_lit_lamp_time: float = 0.0

    def register_lit_lamp(self, current_gps: GPSData) -> List[CadenceGapAlert]:
        """
        Called whenever a functioning (ON) streetlight is confirmed by the camera.
        Checks the distance traveled since the previous functioning lamp.
        If a gap was detected, returns one or more inferred defect locations.
        """
        alerts: List[CadenceGapAlert] = []

        if not current_gps or not current_gps.is_valid():
            return alerts

        # Only evaluate cadence if vehicle is actually moving at reasonable road speed
        if current_gps.speed_kmh < self.min_speed_kmh:
            self.last_lit_lamp_gps = current_gps
            self.last_lit_lamp_time = time.time()
            return alerts

        if self.last_lit_lamp_gps is not None:
            dist = haversine_distance_meters(
                self.last_lit_lamp_gps.latitude,
                self.last_lit_lamp_gps.longitude,
                current_gps.latitude,
                current_gps.longitude
            )

            # If the distance is between ~1.7x and ~3.5x nominal spacing,
            # exactly 1 lamp was likely missed in between
            if self.threshold_gap <= dist <= (self.nominal_spacing * 3.5):
                # Interpolate midpoint GPS coordinate where the dead lamp was passed
                mid_lat = (self.last_lit_lamp_gps.latitude + current_gps.latitude) / 2.0
                mid_lon = (self.last_lit_lamp_gps.longitude + current_gps.longitude) / 2.0
                conf = min(0.95, 0.70 + (dist / (self.nominal_spacing * 2.0)) * 0.2)

                alerts.append(CadenceGapAlert(
                    latitude=mid_lat,
                    longitude=mid_lon,
                    timestamp=time.time(),
                    gap_distance_meters=round(dist, 1),
                    expected_nominal_spacing=self.nominal_spacing,
                    confidence=round(conf, 2),
                    reason=f"Cadence gap detected: {dist:.1f}m between functioning lamps (expected ~{self.nominal_spacing:.0f}m)"
                ))

        self.last_lit_lamp_gps = current_gps
        self.last_lit_lamp_time = time.time()
        return alerts

    def reset(self):
        self.last_lit_lamp_gps = None
        self.last_lit_lamp_time = 0.0
