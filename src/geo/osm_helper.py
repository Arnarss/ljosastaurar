"""
OpenStreetMap (OSM) Helper.
Loads or queries known streetlight coordinates (highway=street_lamp) to enable prior-verification inspections.
"""

from dataclasses import dataclass
import json
import os
import urllib.parse
import urllib.request
from typing import List, Optional
from src.geo.spatial_filter import haversine_distance_meters


@dataclass
class OSMLampNode:
    osm_id: int
    latitude: float
    longitude: float


class OSMStreetlightHelper:
    def __init__(self, cache_file: str = "data/mock_tracks/osm_lamps_cache.json"):
        self.cache_file = cache_file
        self.lamps: List[OSMLampNode] = []
        self._load_cache()

    def _load_cache(self):
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.lamps = [
                        OSMLampNode(osm_id=item["id"], latitude=item["lat"], longitude=item["lon"])
                        for item in data
                    ]
            except Exception as e:
                print(f"[OSMHelper] Cache load error: {e}")

    def save_cache(self):
        os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
        data = [{"id": l.osm_id, "lat": l.latitude, "lon": l.longitude} for l in self.lamps]
        with open(self.cache_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def fetch_from_overpass(self, south: float, west: float, north: float, east: float) -> int:
        """
        Fetches streetlights in a bounding box via OpenStreetMap Overpass API.
        Example: Reykjavik downtown [64.12, -21.96, 64.16, -21.90]
        """
        query = f"""
        [out:json][timeout:25];
        node["highway"="street_lamp"]({south},{west},{north},{east});
        out body;
        """
        url = "https://overpass-api.de/api/interpreter?data=" + urllib.parse.quote(query)
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Ljósastaurar/1.0"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                elements = result.get("elements", [])
                self.lamps = [
                    OSMLampNode(osm_id=el["id"], latitude=el["lat"], longitude=el["lon"])
                    for el in elements if "lat" in el and "lon" in el
                ]
                self.save_cache()
                return len(self.lamps)
        except Exception as e:
            print(f"[OSMHelper] Overpass API query failed: {e}")
            return 0

    def find_nearby_lamps(self, current_lat: float, current_lon: float, radius_meters: float = 25.0) -> List[OSMLampNode]:
        """
        Finds all known streetlights within radius_meters of current vehicle position.
        """
        nearby = []
        for lamp in self.lamps:
            dist = haversine_distance_meters(current_lat, current_lon, lamp.latitude, lamp.longitude)
            if dist <= radius_meters:
                nearby.append(lamp)
        return nearby
