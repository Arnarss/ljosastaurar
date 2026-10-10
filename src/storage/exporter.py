"""
Exporter module to generate GeoJSON and HTML maps from detected defects.
"""

import json
import os
from typing import List
from src.storage.database import DefectIncident


def export_to_geojson(incidents: List[DefectIncident], output_path: str = "data/outputs/faulty_lamps.geojson"):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    features = []

    for inc in incidents:
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [inc.longitude, inc.latitude]
            },
            "properties": {
                "id": inc.id,
                "datetime": inc.datetime_str,
                "status": inc.status,
                "confidence": inc.confidence,
                "speed_kmh": inc.speed_kmh,
                "snapshot": os.path.basename(inc.snapshot_path) if inc.snapshot_path else None
            }
        })

    geojson_doc = {
        "type": "FeatureCollection",
        "features": features
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(geojson_doc, f, indent=2)

    return output_path


def export_to_html_map(incidents: List[DefectIncident], output_path: str = "data/outputs/map_view.html"):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    try:
        import folium
    except ImportError:
        return None

    if not incidents:
        # Default map center (Reykjavik)
        m = folium.Map(location=[64.1466, -21.9426], zoom_start=13)
    else:
        avg_lat = sum(inc.latitude for inc in incidents) / len(incidents)
        avg_lon = sum(inc.longitude for inc in incidents) / len(incidents)
        m = folium.Map(location=[avg_lat, avg_lon], zoom_start=14)

    for inc in incidents:
        popup_html = f"""
        <b>Defective Lamppost #{inc.id}</b><br>
        Status: <span style='color:red;'><b>{inc.status}</b></span><br>
        Time: {inc.datetime_str}<br>
        Coords: {inc.latitude:.5f}, {inc.longitude:.5f}<br>
        Confidence: {inc.confidence:.2f}
        """
        folium.CircleMarker(
            location=[inc.latitude, inc.longitude],
            radius=8,
            popup=popup_html,
            color="red",
            fill=True,
            fill_color="darkred",
            fill_opacity=0.8
        ).add_to(m)

    m.save(output_path)
    return output_path
