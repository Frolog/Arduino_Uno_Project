# 🌱 Smart Environment Monitoring & Irrigation System

## 📌 Overview

This project is a **real-time environmental monitoring and irrigation system** built with:

* Arduino (LM35 + OPT101 light sensor)
* Python (Flask dashboard + logging)
* Web UI (live graphs, alerts, CSV export)

The system:

* Monitors **temperature** and **light intensity**
* Displays live data in a **web dashboard**
* Logs **abnormal values** to CSV
* Can be extended to control a **water pump automatically**

Note: Open Only one Serial port vscode or arduino.
---

## 🧰 Pre-installed Tools & Applications

### 🔹 Development

* Python 3.x
* Arduino IDE
* VS Code
---
pyserial
flask
plotly
run for install:  python -m pip install -r requirements.txt

Install Flask for that Python,Use the same Python executable to install Flask and PySerial:
C:/Users/dev30/AppData/Local/Programs/Python/Python314/python.exe -m pip install flask pyserial

### 🔹 Python Libraries

* `pyserial` → Serial communication with Arduino
* `flask` → Web server + API
* `plotly` → Live graphs
* `csv`, `datetime`, `os`, `threading` → Data handling

Install manually if needed:

```bash
pip install pyserial flask plotly
```



## 📁 Project Structure
tmp_lm35_cjmcu_101_light_sens/
│
├── init-arduino-project.sh   # Project initializer script
├── Flask_console_web_graph_Arduino_auto_reconnect_with_cjmcu_v01.py   # Python Flask server
├── temperature_YYYY-MM-DD.csv
├── tmp_lm35_cjmcu_101_light_sens.ino     # Arduino code
└── README.md


---

## ⚙️ init-arduino-project.sh

This script:

* Creates project folders
* Initializes Git repository
* Sets up base structure for Arduino + Python
* Prepares environment for development


```

Python / Flask Setup

Install Python 3.14+ if not already installed.

Install required packages:

python -m pip install flask pyserial

Run the monitoring script:

python Flask_console_web_graph_Arduino_auto_reconnect_with_cjmcu_v01.py

Open browser at: http://127.0.0.1:5000/
```

---

## 🔌🛠 Hardware Setup
Component	Pin / Connection
LM35 Temp	A0
OPT101 Light	A1
Pump / Relay	A3
Power / Ground	5V / GND

OPT101 connection notes:

Pin 1 → 5V through 100Ω resistor

100µF and 0.1µF capacitors between pin 1 and GND

Pin 5 → pin 4

Pin 2 → leave unconnected

Arduino should send CSV lines:

rawTemp,voltage,tempC,rawLight,vLight

Optional human-readable lines for debugging:

🌡 23.46 °C | 💡 748 (Sunny)

## 🔌 Wiring

### 🧠 Arduino Uno Connections

#### 🌡 LM35 Temperature Sensor

| Pin | Connection |
| --- | ---------- |
| VCC | 5V         |
| GND | GND        |
| OUT | A0         |

---

#### 💡 OPT101 (CJMCU-101) Light Sensor

| Pin | Connection |
| --- | ---------- |
| V+  | 5V         |
| GND | GND        |
| OUT | A1         |

⚠️ Important:

* Ensure proper **bypass capacitors (0.1µF + 100µF)**
* Incorrect wiring → constant `1023` reading

---

#### 💧 Water Pump (via Relay / MOSFET)

| Arduino | Component |
| ------- | --------- |
| A3      | Relay IN  |

⚠️ Do NOT connect pump directly to Arduino

---

## 🔁 Arduino Code Behavior

Arduino sends serial data in this format:

```
rawTemp,voltage,tempC,rawLight,lightVoltage
```

Example:

```
45,0.220,21.99,850,4.15
```

---

## 📌 Features

🌡 Temperature monitoring via LM35

💡 Light monitoring via OPT101

📈 Live plots for temperature and light (Plotly.js in Flask)

📄 CSV logging with automatic daily files

💧 Pump control for irrigation:

Night → OFF

Overcast → short pulse

Cloudy → medium pulse

Sunny → long pulse

Extra watering if temperature is high

📝 Versioning displayed on the web page
Script version stored in __version__

Displayed on web interface (bold, colored text)

Manual updates until Git/Bitbucket workflow is implemented


🔧 Light calibration thresholds configurable

🔄 Auto-reconnect to Arduino if disconnected



### 📊 Live Dashboard

* Temperature graph
* Light graph
* Auto-updating every second
* Auto-scaling Y-axis

---

### 🚨 Alerts

* Triggered when:

  * Temp < LOW threshold
  * Temp > HIGH threshold
* Changes graph color + warning message

---

### 💾 CSV Logging

* Logs **only abnormal readings**
* File rotates **daily**
* Prevents disk overflow

---

### 📥 CSV Download

* Safe download via Flask endpoint:

```
/download_csv
```

---

### 🔄 Auto Reconnect

* Detects Arduino disconnect
* Reconnects automatically
* Skips unstable readings after reconnect

---
## 📷 Schematic
![Schematic](docs/screen.png)

## ▶️ How to Run

### 1️⃣ Upload Arduino Code
* Connect Arduino via USB
* Select correct COM port
* Upload `.ino` file

### 2️⃣ Run Python Server
tmp_lm35_cjmcu_101_light_sens main.py


### 3️⃣ Open Dashboard Environment Monitor:
http://127.0.0.1:5000/


## ⚠️  Problem Solving / Notes

Serial errors / Arduino disconnected

Close Arduino Serial Monitor before running Python

Python will auto-reconnect

Parsing errors in Python

Only parse CSV-formatted lines

Ignore human-readable emoji lines

Stable readings

Use readAvg() in Arduino for LM35 and OPT101

Skip first few readings after reconnect (SKIP_READINGS)

Light calibration thresholds:

LIGHT_CALIB = {
    "Night": (0, 50),
    "Overcast": (51, 200),
    "Cloudy": (201, 450),
    "Sunny": (451, 850),
    "Direct Sun": (851, 1023)
}

CSV download

Web page provides a download button

Files auto-named: temperature_YYYY-MM-DD.csv

Debugging plot issues

Ensure CSV lines are sent by Arduino

Print raw lines in Python:

print("RAW:", line)

### ❌ COM Port Busy

* Close Serial Monitor before running Python

---

### ❌ Constant Light = 1023

* Wiring issue
* Missing capacitor
* Wrong sensor pin

---

### ❌ Jumping Temperature

* ADC noise
* Fixed using:

  * Averaging
  * Capacitor (0.1µF on LM35)

---

## 🚀 Future Improvements

* Soil moisture sensor 🌱
* Rain detection 🌧
* ESP32 WiFi control 📡
* Mobile app 📱
* Smart irrigation scheduling ⏱

---

## 👨‍💻 Author

Lior A.

---

## 📄 License
none
