import serial
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

# Number of initial readings to skip at Arduino startup
SKIP_STARTUP = 5
STARTUP_AVG = 3  # number of readings to average for first valid value

# ---------- Data storage ----------
temps = []
lights = []
times = []
start_time = time.time()

skip_counter = SKIP_STARTUP
startup_buffer_temp = []
startup_buffer_light = []

ser = None

# ---------- CSV ----------
def get_csv_filename():
    date_str = datetime.now().strftime("%Y-%m-%d")
    filename = f"temperature_{date_str}.csv"
    if not os.path.isfile(filename):
        with open(filename, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Timestamp", "Temp (°C)", "Min", "Max"])
    return filename

csv_filename = get_csv_filename()

# ---------- Serial Reader ----------
def read_serial():
    global ser, skip_counter, startup_buffer_temp, startup_buffer_light

    while True:
        try:
            if ser is None or not ser.is_open:
                ser = serial.Serial(COM_PORT, BAUD_RATE, timeout=1)
                print("✅ Arduino connected")
                time.sleep(2)
                skip_counter = SKIP_STARTUP
                startup_buffer_temp.clear()
                startup_buffer_light.clear()

            line = ser.readline().decode(errors="ignore").strip()
            if not line:
                continue

            # parse line: Arduino sends rawTemp,voltage,tempC,rawLight,vLight
            try:
                raw_t, v_t, temp, raw_l, v_l = line.split(",")
                temp = float(temp)
                light = int(raw_l)

                # Skip first few readings to avoid startup spikes
                if skip_counter > 0:
                    skip_counter -= 1
                    startup_buffer_temp.append(temp)
                    startup_buffer_light.append(light)
                    continue

                # For first stable readings, average a few to smooth spikes
                if len(startup_buffer_temp) < STARTUP_AVG:
                    startup_buffer_temp.append(temp)
                    startup_buffer_light.append(light)
                    if len(startup_buffer_temp) == STARTUP_AVG:
                        temp = sum(startup_buffer_temp) / STARTUP_AVG
                        light = int(sum(startup_buffer_light) / STARTUP_AVG)
                    else:
                        continue  # wait until buffer fills

                # Add to main lists
                if 0 <= temp <= 60:
                    temps.append(temp)
                    lights.append(light)
                    times.append(time.time() - start_time)

                    # Keep only last 300 readings
                    if len(temps) > 300:
                        temps.pop(0)
                        lights.pop(0)
                        times.pop(0)

            except Exception as e:
                # uncomment for debug:
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
            times.clear()
            skip_counter = SKIP_STARTUP
            startup_buffer_temp.clear()
            startup_buffer_light.clear()
            time.sleep(2)

        time.sleep(0.05)

threading.Thread(target=read_serial, daemon=True).start()

# ---------- Stats + CSV logging ----------
def stats_and_logging():
    global csv_filename
    while True:
        if temps and lights:
            cur = temps[-1]
            mn = min(temps)
            mx = max(temps)
            light_cur = lights[-1]

            print(f"🌡 Current: {cur:.2f} °C | Min: {mn:.2f} | Max: {mx:.2f} | 💡 Light: {light_cur}")

            # Console alert
            if cur < TEMP_LOW or cur > TEMP_HIGH:
                print("⚠️ TEMPERATURE ALERT")

                # Log unusual temperatures
                csv_filename = get_csv_filename()
                with open(csv_filename, "a", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        f"{cur:.2f}",
                        f"{mn:.2f}",
                        f"{mx:.2f}"
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
    <title>Arduino Environment Monitor</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
</head>
<body>

<h1>🌱 Environment Monitor</h1>

<h2>🌡 Temperature (LM35)</h2>
<div id="temp_alert" style="font-weight:bold; font-size:1.2em;"></div>
<div id="temp_graph" style="width:100%;height:400px;"></div>

<h2>💡 Light Level (CJMCU-101)</h2>
<div id="light_graph" style="width:100%;height:400px;"></div>

<button onclick="window.location.href='/download_csv'">📥 Download CSV</button>

<script>
const LOW = {TEMP_LOW};
const HIGH = {TEMP_HIGH};

function updatePlots() {{
    fetch('/data')
        .then(res => res.json())
        .then(d => {{
            // --- Temperature ---
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

            // --- Light ---
            Plotly.newPlot("light_graph", [{{
                x: d.time,
                y: d.light,
                mode: "lines+markers",
                line: {{color: "orange"}},
                name: "Light Level"
            }}], {{
                yaxis: {{title: "ADC (0–1023)", autorange: true}},
                xaxis: {{title: "Time (s)"}}
            }});
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
        "light": lights
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

# ---------- Run Flask server ----------
app.run(host="0.0.0.0", port=5000, debug=False)