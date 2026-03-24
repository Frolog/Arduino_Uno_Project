# ---------- Project Info ----------
PROJECT_NAME = "Environment Monitor"
__version__ = "0.1"
print(f"{PROJECT_NAME} version {__version__}")

# Flask_console_web_graph_Arduino.py
# Version: 0.1
# Date: 2026-03-23
# Changes: Initial working version with LM35 + CJMCU + light sensor


import serial
import random
import time
import threading
import csv
import os
import shutil
from datetime import datetime
from flask import Flask, jsonify, render_template_string, send_file, abort
import logging

# ---------- Configuration ----------
COM_PORT = "COM11"
BAUD_RATE = 9600
TEMP_LOW = 10.0
TEMP_HIGH = 30.0
SKIP_READINGS = 5
BUFFER_SIZE = 300

# ---------- Light Calibration ----------
LIGHT_CALIB = {
    "Night": (0, 50),
    "Overcast": (51, 200),
    "Cloudy": (201, 450),
    "Sunny": (451, 850),
    "Direct Sun": (851, 1023)
}

def classify_light(value):
    for state, (low, high) in LIGHT_CALIB.items():
        if low <= value <= high:
            return state
    return "Unknown"

# ---------- Data storage ----------
temps = []
lights = []
light_states = []
times = []
start_time = time.time()
skip_counter = 0
ser = None

# ---------- Temp ----------
TEMP_JITTER = 0.3  # max ±0.3°C fluctuation

# ---------- CSV setup ----------
def get_csv_filename():
    date_str = datetime.now().strftime("%Y-%m-%d")
    filename = f"temperature_{date_str}.csv"
    if not os.path.isfile(filename):
        with open(filename, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Timestamp", "Temp (°C)", "Min", "Max", "Light"])
    return filename

csv_filename = get_csv_filename()

# ---------- Serial reading with auto-reconnect ----------
def read_serial():
    global ser, skip_counter
    while True:
        try:
            if ser is None or not ser.is_open:
                ser = serial.Serial(COM_PORT, BAUD_RATE, timeout=1)
                print("✅ Arduino connected")
                time.sleep(2)
                skip_counter = SKIP_READINGS

            line = ser.readline().decode(errors="ignore").strip()
            if not line:
                time.sleep(0.05)
                continue

            if skip_counter > 0:
                skip_counter -= 1
                continue
            
            # ⚡ Debug print — see exactly what Python receives
            #print("RAW:", line)

            # Parse CSV 
            try:
                # Expect CSV: rawTemp,voltage,tempC,rawLight,vLight
                raw_t, v_t, temp, raw_l, v_l = line.split(",")
                temp = float(temp)
                # Add small random fluctuation ±0.3°C
                temp += random.uniform(-TEMP_JITTER, TEMP_JITTER)
                light = int(raw_l)
                light_state = classify_light(light)

                if 0 <= temp <= 60:
                    temps.append(temp)
                    lights.append(light)
                    light_states.append(light_state)
                    times.append(time.time() - start_time)

                    # Keep buffer within size
                    if len(temps) > BUFFER_SIZE:
                        temps.pop(0)
                        lights.pop(0)
                        light_states.pop(0)
                        times.pop(0)

            except Exception as e:
                # Ignore parse errors
                # print("Parsing error:", e, "Line:", line)
                pass

        except serial.SerialException:
            print("❌ Arduino disconnected – reconnecting...")
            if ser:
                try:
                    ser.close()
                except:
                    pass
            ser = None
            temps.clear()
            lights.clear()
            light_states.clear()
            times.clear()
            skip_counter = 0
            time.sleep(2)

        except Exception:
            time.sleep(0.05)
            pass

threading.Thread(target=read_serial, daemon=True).start()

# ---------- Background stats and CSV logging ----------
def stats_and_logging():
    global csv_filename
    while True:
        if temps:
            cur = temps[-1]
            mn = min(temps)
            mx = max(temps)
            light_cur = lights[-1]

            print(f"🌡 Current: {cur:.2f} °C | Min: {mn:.2f} | Max: {mx:.2f} | 💡 Light: {light_cur}")

            # Log only unusual temperatures
            if cur < TEMP_LOW or cur > TEMP_HIGH:
                csv_filename = get_csv_filename()
                with open(csv_filename, "a", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        f"{cur:.2f}",
                        f"{mn:.2f}",
                        f"{mx:.2f}",
                        f"{light_cur}"
                    ])
        else:
            print("⏳ Waiting for Arduino data...")
        time.sleep(1)

threading.Thread(target=stats_and_logging, daemon=True).start()

# ---------- Flask App ----------
app = Flask(__name__)

@app.route("/")
def index():
    return render_template_string(f"""
<!DOCTYPE html>
<html>
<head>
    <title>{PROJECT_NAME}</title> 
    <title>Environment Monitor</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
</head>
<body>
<h1>🌱 {PROJECT_NAME}</h1>
<p style="font-weight:bold; color:green;">Version: {__version__}</p>


<h2>🌡 Temperature</h2>
<div id="temp_alert" style="font-weight:bold; font-size:1.2em;"></div>
<div id="temp_graph" style="width:100%;height:400px;"></div>

<h2>💡 Light Level</h2>
<div id="light_graph" style="width:100%;height:400px;"></div>
<div id="light_state_text" style="font-size:20px;font-weight:bold;"></div>

<button onclick="window.location.href='/download_csv'">📥 Download CSV</button>

<script>
const LOW = {TEMP_LOW};
const HIGH = {TEMP_HIGH};

function updatePlots() {{
    fetch('/data')
        .then(res => res.json())
        .then(d => {{
            // Temperature
            let color = "blue";
            let alert = document.getElementById("temp_alert");
            if (d.temp.length > 0) {{
                let t = d.temp[d.temp.length - 1];
                if (t < LOW || t > HIGH) {{
                    color = "red";
                    alert.innerText = "⚠️ Temperature out of range!";
                }} else {{
                    alert.innerText = "Current Temp: " + t.toFixed(2) + " °C";
                }}
            }}
            Plotly.newPlot("temp_graph", [{{
                x: d.time,
                y: d.temp,
                mode: "lines+markers",
                line: {{color: color}},
                name: "Temperature"
            }}], {{
                yaxis: {{title: "°C", autorange: true}},
                xaxis: {{title: "Time (s)"}}
            }});

            // Light
            Plotly.newPlot("light_graph", [{{
                x: d.time,
                y: d.light,
                mode: "lines+markers",
                line: {{color: "orange"}},
                name: "Light Level"
            }}], {{
                yaxis: {{title: "Light Level", autorange: true}},
                xaxis: {{title: "Time (s)"}}
            }});

            // Light text
            if (d.light.length > 0) {{
                let latestLight = d.light[d.light.length - 1];
                let latestState = d.light_state[d.light_state.length - 1];
                document.getElementById("light_state_text").innerText =
                    "💡 Light: " + latestLight + " (" + latestState + ")";
            }}
        }});
}}

updatePlots();
setInterval(updatePlots, 1000);
</script>
</body>
</html>
""")

@app.route("/data")
def data():
    return jsonify({
        "time": times,
        "temp": temps,
        "light": lights,
        "light_state": light_states
    })

@app.route("/download_csv")
def download_csv():
    if not os.path.isfile(csv_filename):
        abort(404)
    safe_copy = csv_filename + "_copy.csv"
    shutil.copy(csv_filename, safe_copy)
    return send_file(
        os.path.abspath(safe_copy),
        as_attachment=True,
        download_name=os.path.basename(csv_filename)
    )

# ---------- Silence Flask logs ----------
logging.getLogger("werkzeug").setLevel(logging.ERROR)

# ---------- Run Flask ----------
app.run(host="0.0.0.0", port=5000, debug=False)