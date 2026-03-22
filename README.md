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

---

## 📁 Project Structure

```


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

Run:

```bash
chmod +x init-arduino-project.sh
./init-arduino-project.sh
```

---

## 🔌 Hardware Setup

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

## 🖥 Python Application Features

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

## ▶️ How to Run

### 1️⃣ Upload Arduino Code

* Connect Arduino via USB
* Select correct COM port
* Upload `.ino` file

---

### 2️⃣ Run Python Server

```bash
python main.py
```

---

### 3️⃣ Open Dashboard

Go to:

```
http://127.0.0.1:5000
```

---

## ⚠️ Common Issues

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

Lior A

---

## 📄 License

MIT License
