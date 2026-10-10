# 💻 Laptop Setup & In-Vehicle Hardware Checklist

This guide covers setting up your older **NVIDIA GeForce GTX 960 / 960M** laptop from scratch (no OS) with **Ubuntu Linux**, along with the physical gear needed to run nighttime streetlight inspections from a vehicle.

---

## Part 1: Setting Up the GTX 960 Laptop (No OS $\to$ Ready)

### Step 1: Create a Bootable Ubuntu USB Drive
*(Perform this on your current Linux machine)*

1. Download the **[Ubuntu 24.04 LTS Desktop ISO](https://ubuntu.com/download/desktop)** (or **Ubuntu 22.04 LTS**).
2. Insert a USB flash drive ($\ge 8\text{ GB}$).
3. Open **Startup Disk Creator** (pre-installed on Ubuntu), select the downloaded ISO and your USB drive, and click **Make Startup Disk**.
   *(Alternatively, use [BalenaEtcher](https://etcher.balena.io/) or `dd`).*

### Step 2: Install Ubuntu on the Laptop
1. Insert the USB drive into the laptop.
2. Power on the laptop and immediately tap the **Boot Menu key** (typically **F12** on Dell/Lenovo, **F9** on HP, **F8/Esc** on Asus).
3. Select your USB drive from the boot list and select **Install Ubuntu**.
4. During installation, check the box: **"Install third-party software for graphics and Wi-Fi hardware"**.
5. Choose **Erase disk and install Ubuntu** (since there is no OS).

### Step 3: Install NVIDIA Drivers & Permissions
Once logged into your new Ubuntu desktop, open a terminal (`Ctrl + Alt + T`):

```bash
# 1. Update system packages
sudo apt update && sudo apt upgrade -y

# 2. Automatically detect and install recommended NVIDIA proprietary drivers (driver 535)
sudo ubuntu-drivers install

# 3. Add your user to the 'dialout' group (grants access to USB GPS dongles without root/sudo)
sudo usermod -a -G dialout $USER

# 4. Reboot to activate the NVIDIA drivers
sudo reboot
```

Verify GPU installation:
```bash
nvidia-smi
```
You should see your **GeForce GTX 960 / 960M** listed with driver version `535.xx`.

### Step 4: Clone & Run the Inspection System
```bash
# Install Python tools and git
sudo apt install -y python3-pip python3-venv git

# Clone repository
git clone <your-repo-url> ljosastaurar
cd ljosastaurar

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install project dependencies
pip install -r requirements.txt
pip install ultralytics opencv-python

# Test run the GUI
python3 src/main.py
```

---

## Part 2: Complete Hardware Checklist — What Else Do You Need?

Beyond the **laptop**, **camera**, and **GPS dongle**, here is the complete checklist of physical gear required for in-vehicle operation:

### 1. Essential Gear (Required to Test in a Car)

| Item | Why It Is Needed | Recommendation / Details |
| :--- | :--- | :--- |
| **1. Low-Light Camera** | Standard webcams suffer from severe night motion blur and noise. | **Arducam Sony IMX462 Ultra Low Light USB** (~$55) with $f/1.4$–$f/1.6$ lens. |
| **2. 10 Hz GPS Dongle** | 1 Hz GPS has a 14m position lag at 50 km/h. 10 Hz updates every 1.4m. | **u-blox NEO-M8N or NEO-M9N USB** (~$28–$40) with external magnetic antenna. |
| **3. Windshield Suction Mount** | Holding a camera by hand causes camera shake and incorrect pitch angles. | Heavy-duty twist-lock suction bracket with a standard 1/4" tripod screw or camera clamp (~$15). Place inside windshield wiper sweep zone. |
| **4. 12V In-Car Laptop Power** | Running AI + display will drain an older laptop battery in 30–60 minutes. | **Option A**: 12V car cigarette lighter to laptop charger matching your laptop's barrel plug (90W–130W) (~$25).<br>**Option B**: 150W pure-sine 12V-to-AC car inverter (~$30). |
| **5. USB Cable Slack (2m–3m)** | The GPS antenna must reach outside to the roof, and camera must reach the windshield. | 2m–3m USB-A extension cable or long antenna SMA extension cable. |

### 2. Physical Placement in the Vehicle

```
                         [ Car Metal Roof ]
                        ┌──────────────────┐
                        │ Magnetic GPS Ant │
                        └────────┬─────────┘
                                 │ (Wire runs through door weatherstrip)
 ┌───────────────────────────────┴───────────────────────────────┐
 │                        WINDSHIELD                             │
 │    ┌──────────────────┐                                       │
 │    │  Camera Mount    │ (Inside wiper sweep zone)             │
 │    └────────┬─────────┘                                       │
 │             │ USB                                             │
 │             ▼                                                 │
 │    ┌──────────────────────────────┐                           │
 │    │  Laptop on Passenger Seat    │ ◄── Powered by 12V Socket │
 │    │  Running PySide6 / YOLO      │                           │
 │    └──────────────────────────────┘                           │
 └───────────────────────────────────────────────────────────────┘
```

### 3. Option: Use Your Smartphone for Video & GPS ($0 Upfront Cost)

If you don't have a separate USB camera and GPS dongle yet, **you can use your smartphone for BOTH simultaneously!**

```
┌────────────────────────────────────────────────────────────────────────┐
│                      Smartphone (In Windshield Mount)                  │
│                      • Camera: Streams 1080p Video via Wi-Fi/Hotspot   │
│                      • GPS: Streams live Latitude & Longitude          │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Wi-Fi / Hotspot / USB Tethering
                                    ▼
                       ┌─────────────────────────┐
                       │    Laptop (PySide6 GUI) │
                       │    • Video: IP Stream   │
                       │    • GPS: Phone Sensors │
                       └─────────────────────────┘
```

#### Android Setup (Easiest — All in One App)
1. Install **[IP Webcam](https://play.google.com/store/apps/details?id=com.pas.webcam)** (by Pavel Khlebovich) from Google Play.
2. Open the app, scroll to **Data logging**, and check **Enable GPS data logging**.
3. Scroll to the bottom and tap **Start server**.
4. The app will display an IP address on screen (e.g. `http://192.168.43.1:8080`).
5. In the **Ljósastaurar GUI**:
   - Set **Video Source** $\to$ `Smartphone Camera (IP Stream)...` and enter `http://<phone_ip>:8080/video`.
   - Set **GPS Source** $\to$ `Smartphone GPS (IP Webcam / Wi-Fi)` and enter `http://<phone_ip>:8080/sensors.json`.
   - Click **▶ Start Inspection**!

#### iPhone / iOS Setup
1. **Video**: Install **IP Camera Lite** or **Camo** from the App Store and start the RTSP/HTTP broadcast.
2. **GPS**: Install **GPS 2 IP** (free), set connection type to UDP (port `50000`), and broadcast to your laptop's IP.

---

### 4. Pre-Drive Checklist
- [ ] Windshield cleaned inside and outside in front of camera lens.
- [ ] Phone / Camera mounted securely on windshield (facing forward, tilted slightly up $\sim 10^\circ$).
- [ ] Laptop plugged into 12V car power adapter on passenger seat.
- [ ] Connect laptop to phone's Wi-Fi Hotspot (or plug USB cable).
- [ ] Launch `python3 src/main.py`, select phone source, and press **▶ Start Inspection**.

