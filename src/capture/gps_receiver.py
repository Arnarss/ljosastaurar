"""
GPS Receiver Module supporting both real Serial NMEA hardware and offline Mock GPS simulation.
"""

from dataclasses import dataclass
from datetime import datetime
import math
import time
from typing import Optional


@dataclass
class GPSData:
    latitude: float
    longitude: float
    altitude: float = 0.0
    speed_kmh: float = 0.0
    heading: float = 0.0
    satellites: int = 8
    fix_quality: str = "3D Fix"
    timestamp: float = 0.0

    def is_valid(self) -> bool:
        return self.latitude != 0.0 and self.longitude != 0.0


class BaseGPSReceiver:
    def get_latest_fix(self) -> GPSData:
        raise NotImplementedError

    def start(self):
        pass

    def stop(self):
        pass


class MockGPSReceiver(BaseGPSReceiver):
    """
    Simulates a driving route (default centered in Reykjavik, Iceland).
    Calculates moving coordinates based on simulated speed and heading.
    """

    def __init__(self, start_lat: float = 64.1466, start_lon: float = -21.9426, speed_kmh: float = 40.0):
        self.current_lat = start_lat
        self.current_lon = start_lon
        self.speed_kmh = speed_kmh
        self.heading = 90.0  # Heading east initially
        self.last_update_time = time.time()
        self.running = False

    def start(self):
        self.running = True
        self.last_update_time = time.time()

    def stop(self):
        self.running = False

    def get_latest_fix(self) -> GPSData:
        now = time.time()
        dt = now - self.last_update_time
        self.last_update_time = now

        if self.running and dt > 0:
            # Advance coordinates along heading
            distance_meters = (self.speed_kmh * 1000.0 / 3600.0) * dt

            # Earth radius approx 6,371,000 meters
            rad_lat = math.radians(self.current_lat)
            d_lat = (distance_meters * math.cos(math.radians(self.heading))) / 111139.0
            d_lon = (distance_meters * math.sin(math.radians(self.heading))) / (111139.0 * math.cos(rad_lat))

            self.current_lat += d_lat
            self.current_lon += d_lon

            # Gently curve heading over time to simulate turns
            self.heading = (self.heading + 0.5 * dt) % 360.0

        return GPSData(
            latitude=self.current_lat,
            longitude=self.current_lon,
            altitude=15.0,
            speed_kmh=self.speed_kmh,
            heading=round(self.heading, 1),
            satellites=12,
            fix_quality="3D Fix (Mock)",
            timestamp=now
        )


class SerialNMEAGPSReceiver(BaseGPSReceiver):
    """
    Reads real NMEA-0183 sentences from a USB/Serial GPS dongle (e.g. u-blox NEO-M8N).
    """

    def __init__(self, port: str = "/dev/ttyUSB0", baudrate: int = 9600):
        self.port = port
        self.baudrate = baudrate
        self.latest_data = GPSData(latitude=0.0, longitude=0.0, timestamp=time.time())
        self.serial_conn = None
        self.running = False

    def start(self):
        try:
            import serial
            self.serial_conn = serial.Serial(self.port, self.baudrate, timeout=1.0)
            self.running = True
        except Exception as e:
            print(f"[GPS] Warning: Failed to open serial port {self.port}: {e}")
            self.running = False

    def stop(self):
        self.running = False
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()

    def get_latest_fix(self) -> GPSData:
        if not self.running or not self.serial_conn:
            return self.latest_data

        try:
            import pynmea2
            while self.serial_conn.in_waiting:
                line = self.serial_conn.readline().decode("ascii", errors="replace").strip()
                if line.startswith(("$GPRMC", "$GNRMC")):
                    msg = pynmea2.parse(line)
                    if getattr(msg, "status", None) == "A":
                        self.latest_data.latitude = msg.latitude
                        self.latest_data.longitude = msg.longitude
                        if msg.spd_over_grnd:
                            self.latest_data.speed_kmh = float(msg.spd_over_grnd) * 1.852  # Knots to km/h
                        if getattr(msg, "true_course", None):
                            self.latest_data.heading = float(msg.true_course)
                        self.latest_data.timestamp = time.time()
                elif line.startswith(("$GPGGA", "$GNGGA")):
                    msg = pynmea2.parse(line)
                    if msg.gps_qual > 0:
                        self.latest_data.latitude = msg.latitude
                        self.latest_data.longitude = msg.longitude
                        self.latest_data.satellites = int(msg.num_sats or 0)
                        self.latest_data.altitude = float(msg.altitude or 0.0)
                        self.latest_data.fix_quality = "3D Fix" if msg.gps_qual >= 1 else "No Fix"
                        self.latest_data.timestamp = time.time()
        except Exception as e:
            print(f"[GPS] Error reading serial: {e}")

        return self.latest_data


class NetworkPhoneGPSReceiver(BaseGPSReceiver):
    """
    Receives GPS data streamed from a smartphone over local Wi-Fi or Hotspot:
    1. HTTP Mode (IP Webcam app on Android): Polls http://<phone_ip>:8080/sensors.json
    2. UDP NMEA Mode (GPS 2 IP on iOS / GPS Logger on Android): Listens on UDP port (default 50000)
    """

    def __init__(self, mode: str = "http", phone_url: str = "http://192.168.43.1:8080/sensors.json", udp_port: int = 50000):
        self.mode = mode
        self.phone_url = phone_url
        self.udp_port = udp_port
        self.latest_data = GPSData(latitude=0.0, longitude=0.0, timestamp=time.time())
        self.running = False
        self._thread = None

    def start(self):
        import threading
        self.running = True
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self.running = False

    def _poll_loop(self):
        import urllib.request
        import json
        import socket

        if self.mode == "udp":
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.bind(("", self.udp_port))
            sock.settimeout(1.0)
            while self.running:
                try:
                    data, _ = sock.recvfrom(2048)
                    line = data.decode("ascii", errors="replace").strip()
                    self._parse_nmea_line(line)
                except socket.timeout:
                    continue
                except Exception as e:
                    time.sleep(0.1)
        else:
            # HTTP Polling mode (IP Webcam)
            while self.running:
                try:
                    req = urllib.request.Request(self.phone_url, headers={"User-Agent": "Ljósastaurar/1.0"})
                    with urllib.request.urlopen(req, timeout=1.0) as resp:
                        if resp.status == 200:
                            data = json.loads(resp.read().decode("utf-8"))
                            gps_info = data.get("gps", {})
                            gps_data_arr = gps_info.get("data", [])
                            if gps_data_arr:
                                # IP Webcam structure: [timestamp, [lat, lon, alt, acc, speed, bearing]]
                                latest_entry = gps_data_arr[-1][1]
                                self.latest_data.latitude = float(latest_entry[0])
                                self.latest_data.longitude = float(latest_entry[1])
                                self.latest_data.altitude = float(latest_entry[2]) if len(latest_entry) > 2 else 0.0
                                self.latest_data.speed_kmh = float(latest_entry[4]) * 3.6 if len(latest_entry) > 4 else 0.0
                                self.latest_data.heading = float(latest_entry[5]) if len(latest_entry) > 5 else 0.0
                                self.latest_data.fix_quality = "3D Fix (Phone)"
                                self.latest_data.timestamp = time.time()
                except Exception:
                    pass
                time.sleep(0.5)

    def _parse_nmea_line(self, line: str):
        try:
            import pynmea2
            if line.startswith(("$GPRMC", "$GNRMC")):
                msg = pynmea2.parse(line)
                if getattr(msg, "status", None) == "A":
                    self.latest_data.latitude = msg.latitude
                    self.latest_data.longitude = msg.longitude
                    if msg.spd_over_grnd:
                        self.latest_data.speed_kmh = float(msg.spd_over_grnd) * 1.852
                    if getattr(msg, "true_course", None):
                        self.latest_data.heading = float(msg.true_course)
                    self.latest_data.fix_quality = "3D Fix (Phone UDP)"
                    self.latest_data.timestamp = time.time()
        except Exception:
            pass

    def get_latest_fix(self) -> GPSData:
        return self.latest_data

