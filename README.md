# 🌙 Ljósastaurar (Streetlight Defect Detector)

An intelligent nighttime computer vision and GPS system to automatically detect defective (unlit/off) streetlights from a moving vehicle or camera feed and log their geospatial coordinates.

---

## 🚀 Quick Overview

1. **Live Camera Feed**: Ingests video from a USB camera, dashcam, RTSP stream, or test video file.
2. **Lamppost & State Detection**: Identifies streetlight fixtures and evaluates whether they are illuminated or unlit/defective.
3. **GPS Geotagging**: Pairs detection events with synchronized GPS coordinates (via USB NMEA dongle, phone stream, or mock GPX).
4. **Spatial Deduplication & Tracking**: Uses object tracking and distance thresholds to ensure each broken lamp is only logged once.
5. **Geospatial Reporting**: Stores incidents in SQLite and exports to GeoJSON / interactive map layers for maintenance crews.

---

## 📁 Repository Structure

```
ljosastaurar/
├── config/
│   └── settings.yaml         # Configuration (camera, GPS mode, thresholds)
├── data/
│   ├── mock_tracks/          # GPX/NMEA logs for offline testing
│   ├── outputs/              # Generated SQLite DB & GeoJSON files
│   ├── sample_videos/        # Recorded night test footage
│   └── snapshots/            # Saved photographic evidence of faulty lamps
├── models/                   # YOLO weights & model checkpoints
├── src/
│   ├── capture/              # Video & GPS ingestion
│   ├── detection/            # YOLO detection, tracking, & on/off analysis
│   ├── geo/                  # Coordinate interpolation & spatial deduplication
│   ├── gui/                  # PySide6 desktop dashboard & HUD components
│   └── storage/              # SQLite & GeoJSON export handlers
├── tests/                    # Unit & pipeline tests
├── PROJECT_SPECIFICATION.md  # Deep technical architecture & roadmap
├── SETUP_GUIDE.md            # Laptop OS setup & in-vehicle hardware checklist
└── requirements.txt          # Python dependencies
```

---

## 🖥️ Graphical User Interface (PySide6)

The application includes a desktop GUI designed for vehicle/in-cabin operation:
- **Live Video HUD**: Displays video feed with real-time detection boxes (Green = ON, Red = OFF) and tracking IDs.
- **GPS Telemetry Panel**: Live latitude, longitude, speed, heading, and satellite fix status.
- **Incident Inspector**: Table of detected defective streetlights with click-to-preview snapshots.
- **Controls**: Toggle live camera/file, select GPS mode (Serial / Mock), and export to GeoJSON/HTML map.


---

## 🛠️ Getting Started

### 1. Hardware & Laptop Setup
* **Recommended Zero-Cost Starter Setup**:
  * **Processing & UI**: Old laptop with NVIDIA GTX 960 running Ubuntu Linux.
  * **Camera & GPS**: Your smartphone mounted on the windshield, streaming video and GPS via local Wi-Fi / Hotspot using **IP Webcam** (Android) or **GPS 2 IP** (iOS).
* If you are setting up your laptop from scratch, follow the complete step-by-step instructions in **[SETUP_GUIDE.md](SETUP_GUIDE.md)**.

### 2. Setup Virtual Environment
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Run the Application
Launch the GUI:
```bash
python3 src/main.py
```
In the GUI toolbar:
* Select **Video Source** $\to$ `Smartphone Camera (IP Stream)...`
* Select **GPS Source** $\to$ `Smartphone GPS (IP Webcam / Wi-Fi)`
* Click **▶ Start Inspection**!


---

## 📖 Detailed Guides & Technical Roadmap

* **[SETUP_GUIDE.md](SETUP_GUIDE.md)**: Bootable USB creation, Ubuntu install, NVIDIA driver setup, and in-vehicle mounting checklist.
* **[PROJECT_SPECIFICATION.md](PROJECT_SPECIFICATION.md)**: Deep technical architecture, mathematical concepts, GIS integration, and implementation phases.
