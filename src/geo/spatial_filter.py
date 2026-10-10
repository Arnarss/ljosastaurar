"""
Spatial Filter & Deduplication module.
Prevents duplicate defect logs for the same physical streetlight.
"""

from dataclasses import dataclass
import math
import time
from typing import List, Optional


def haversine_distance_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Computes great-circle distance between two GPS coordinates in meters.
    """
    R = 6371000.0  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0)**2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c


@dataclass
class LoggedIncidentReference:
    latitude: float
    longitude: float
    timestamp: float


class SpatialDeduplicator:
    def __init__(self, radius_meters: float = 15.0, cooldown_seconds: float = 60.0):
        self.radius_meters = radius_meters
        self.cooldown_seconds = cooldown_seconds
        self.history: List[LoggedIncidentReference] = []

    def should_log(self, lat: float, lon: float, current_time: Optional[float] = None) -> bool:
        """
        Returns True if this coordinate represents a new defect not yet logged within the radius and cooldown window.
        """
        now = current_time or time.time()

        # Prune records older than cooldown window
        self.history = [ref for ref in self.history if (now - ref.timestamp) < self.cooldown_seconds]

        # Check proximity to any recent records
        for ref in self.history:
            dist = haversine_distance_meters(lat, lon, ref.latitude, ref.longitude)
            if dist < self.radius_meters:
                return False  # Duplicate within radius

        # New unique incident
        self.history.append(LoggedIncidentReference(lat, lon, now))
        return True
