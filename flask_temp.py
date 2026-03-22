import serial
import time
import threading
from flask import Flask, jsonify, render_template_string

# ---------- Configuration ----------
COM_PORT = "COM11"
BAUD_RATE = 9600

# ---------- Data storage ----------
temps = []
times = []
start_time = time.time()
skip_readings = 5  # number of readings to ignore after Arduino reconnect
skip_counter = 0
ser = None  # Will be initialized in thread

# ---------- Function to read Arduino with auto-reconnect ----------
def read_serial():
    global ser, skip_counter
    while True:
        try:
            # Try to open port if not open
            if ser is None or not ser.is_open:
                ser = serial.Serial(COM_PORT, BAUD_RATE, timeout=1)
                print("Arduino connected!")
                time.sleep(2)  # wait for Arduino reset
                skip_counter = skip_readings  # start skipping first readings

            # Read line
            line = ser.readline().decode(errors='ignore').strip()
            if line:
                # Skip first N readings after reconnect
                if skip_counter > 0:
                    skip_counter -= 1
                    continue

                try:
                    # Arduino sends: RAW,Voltage,Temp_C
                    _, _, temp = line.split(',')
                    temp = float(temp)

                    # Optional: only accept reasonable temps
                    if 0 <= temp <= 60:
                        temps.append(temp)
                        times.append(time.time() - start_time)

                        if len(temps) > 200:
                            temps.pop(0)
                            times.pop(0)
                except:
                    pass

        except serial.SerialException:
            # Serial disconnected
            print("Arduino disconnected! Trying to reconnect...")
            if ser:
                try:
                    ser.close()
                except:
                    pass
            ser = None
            temps.clear()
            times.clear()
            skip_counter = 0
            time.sleep(2)  # wait before retrying

        except Exception:
            pass

        time.sleep(0.05)

# Start serial reading thread
threading.Thread(target=read_serial, daemon=True).start()

# ---------- Flask App ----------
app = Flask(__name__)

@app.route("/")
def index():
    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
    <title>LM35 Temperature Monitor</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
</head>
<body>
    <h2>🌡️ LM35 Live Temperature</h2>
    <div id="graph"></div>

    <script>
        function updatePlot() {
            fetch('/data')
                .then(res => res.json())
                .then(data => {
                    let trace = {
                        x: data.time,
                        y: data.temp,
                        mode: 'lines+markers'
                    };
                    Plotly.newPlot('graph', [trace], {
                        yaxis: {title: 'Temperature (°C)', range: [0, 60]},
                        xaxis: {title: 'Time (s)'}
                    });
                });
        }
        setInterval(updatePlot, 1000);
        updatePlot();
    </script>
</body>
</html>
""")

@app.route("/data")
def data():
    return jsonify({
        "time": times,
        "temp": temps
    })

# ---------- Background thread to print stats ----------
def print_stats():
    while True:
        if temps:
            current = temps[-1]
            minimum = min(temps)
            maximum = max(temps)
            print(f"Current: {current:.2f} °C | Min: {minimum:.2f} °C | Max: {maximum:.2f} °C")
        else:
            print("No data - Arduino not connected")
        time.sleep(1)

threading.Thread(target=print_stats, daemon=True).start()

# ---------- Run Flask server ----------
app.run(host="0.0.0.0", port=5000, debug=False)
