// -------- Pins --------
const int tempPin  = A0;   // LM35
const int lightPin = A1;   // OPT101
const int pumpPin  = A3;   // Relay / MOSFET

// -------- Timing --------
const unsigned long SAMPLE_DELAY = 1000;  // 1 sec
const unsigned long PUMP_INTERVAL = 60000; // check every 1 min

// -------- Calibration --------
#define LIGHT_NIGHT     50
#define LIGHT_OVERCAST  200
#define LIGHT_CLOUDY   450
#define LIGHT_SUNNY    850

#define TEMP_HOT 30.0

// -------- State --------
unsigned long lastPumpTime = 0;

// -------- Read average ADC --------
int readAvg(int pin) {
  long sum = 0;
  for (int i = 0; i < 10; i++) {
    sum += analogRead(pin);
    delay(5);
  }
  return sum / 10;
}

// -------- Convert LM35 --------
float readTempC() {
  int raw = readAvg(tempPin);
  float voltage = raw * (5.0 / 1023.0);
  return voltage / 0.01;
}

// -------- Light classification --------
String classifyLight(int light) {
  if (light < LIGHT_NIGHT) return "Night";
  if (light < LIGHT_OVERCAST) return "Overcast";
  if (light < LIGHT_CLOUDY) return "Cloudy";
  if (light < LIGHT_SUNNY) return "Sunny";
  return "Direct Sun";
}

// -------- Pump control --------
void runPump(unsigned long durationMs) {
  digitalWrite(pumpPin, HIGH);
  delay(durationMs);
  digitalWrite(pumpPin, LOW);
}

// -------- Setup --------
void setup() {
  Serial.begin(9600);
  pinMode(pumpPin, OUTPUT);
  digitalWrite(pumpPin, LOW);
  Serial.println("🌱 Smart Irrigation Controller Started");
}

// -------- Loop --------
void loop() {
  float tempC = readTempC();
  int light   = readAvg(lightPin);
  String lightState = classifyLight(light);

  // --- CSV output for Python ---
  float vTemp = readAvg(tempPin) * (5.0 / 1023.0);
  float vLight = light * (5.0 / 1023.0);
  Serial.print(readAvg(tempPin)); Serial.print(",");   // rawTemp
  Serial.print(vTemp, 3); Serial.print(",");          // voltage
  Serial.print(tempC, 2); Serial.print(",");          // tempC
  Serial.print(light); Serial.print(",");             // rawLight
  Serial.println(vLight, 3);                           // vLight

  // --- Debug line (optional, can comment out if Python stuck) ---
  Serial.print("🌡 "); Serial.print(tempC, 2);
  Serial.print(" °C | 💡 "); Serial.print(light);
  Serial.print(" ("); Serial.print(lightState); Serial.println(")");

  unsigned long now = millis();

  if (now - lastPumpTime >= PUMP_INTERVAL) {
    lastPumpTime = now;

    if (lightState == "Night") {
      Serial.println("🚫 Pump OFF (night)");
    }
    else if (lightState == "Overcast") {
      Serial.println("💧 Pump SHORT");
      runPump(3000);  // 3 sec
    }
    else if (lightState == "Cloudy") {
      Serial.println("💧 Pump MEDIUM");
      runPump(6000);  // 6 sec
    }
    else {
      Serial.println("💧 Pump LONG");
      runPump(10000); // 10 sec
    }

    if (tempC > TEMP_HOT) {
      Serial.println("🔥 Extra watering (hot)");
      runPump(4000);
    }
  }

  delay(SAMPLE_DELAY);
}