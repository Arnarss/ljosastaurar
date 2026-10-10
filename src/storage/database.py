"""
SQLite Database manager for logging detected defective streetlight incidents.
"""

from dataclasses import dataclass
from datetime import datetime
import os
import sqlite3
from typing import List, Optional


@dataclass
class DefectIncident:
    id: Optional[int] = None
    timestamp: float = 0.0
    datetime_str: str = ""
    latitude: float = 0.0
    longitude: float = 0.0
    speed_kmh: float = 0.0
    confidence: float = 0.0
    status: str = "OFF"
    snapshot_path: str = ""


class InspectionDatabase:
    def __init__(self, db_path: str = "data/outputs/inspections.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS incidents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL,
                    datetime_str TEXT,
                    latitude REAL,
                    longitude REAL,
                    speed_kmh REAL,
                    confidence REAL,
                    status TEXT,
                    snapshot_path TEXT
                )
            """)
            conn.commit()

    def log_defect(self, incident: DefectIncident) -> int:
        if not incident.datetime_str:
            incident.datetime_str = datetime.fromtimestamp(incident.timestamp).strftime("%Y-%m-%d %H:%M:%S")

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO incidents (
                    timestamp, datetime_str, latitude, longitude, speed_kmh, confidence, status, snapshot_path
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                incident.timestamp,
                incident.datetime_str,
                incident.latitude,
                incident.longitude,
                incident.speed_kmh,
                incident.confidence,
                incident.status,
                incident.snapshot_path
            ))
            conn.commit()
            return cursor.lastrowid

    def get_all_incidents(self) -> List[DefectIncident]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM incidents ORDER BY id DESC")
            rows = cursor.fetchall()
            return [
                DefectIncident(
                    id=row["id"],
                    timestamp=row["timestamp"],
                    datetime_str=row["datetime_str"],
                    latitude=row["latitude"],
                    longitude=row["longitude"],
                    speed_kmh=row["speed_kmh"],
                    confidence=row["confidence"],
                    status=row["status"],
                    snapshot_path=row["snapshot_path"]
                )
                for row in rows
            ]
