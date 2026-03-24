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
float minTemp = 1000.0;  // start very high
float maxTemp = -1000.0; // start very low

// -------- Read average ADC --------
int readAvg(int pin) {
  long sum = 0;
  for (int i = 0; i < 10; i++) {
    sum += analogRead(pin);
    delay(5);
  }
  return sum / 10;
}

// -------- Convert LM35 to °C --------
float readTempC() {
  int rawTemp = analogRead(tempPin);
  float voltage = rawTemp * (5.0 / 1023.0);
  float tempC = voltage / 0.01; // LM35: 10 mV per °C
  return tempC;
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
  // --- Read sensors ---
  float tempC = readTempC();
  int lightRaw = readAvg(lightPin);
  String lightState = classifyLight(lightRaw);

  // --- Update min/max ---
  if (tempC < minTemp) minTemp = tempC;
  if (tempC > maxTemp) maxTemp = tempC;

  // --- CSV output for Python ---
  float tempVolt = readAvg(tempPin) * (5.0 / 1023.0);
  float lightVolt = lightRaw * (5.0 / 1023.0);
  Serial.print(readAvg(tempPin)); Serial.print(",");   // rawTemp
  Serial.print(tempVolt, 3); Serial.print(",");       // voltage
  Serial.print(tempC, 2); Serial.print(",");          // tempC
  Serial.print(lightRaw); Serial.print(",");          // rawLight
  Serial.println(lightVolt, 3);                        // light voltage

  // --- Debug / human-readable line ---
  Serial.print("🌡 Current: "); Serial.print(tempC, 2);
  Serial.print(" °C | Min: "); Serial.print(minTemp, 2);
  Serial.print(" | Max: "); Serial.print(maxTemp, 2);
  Serial.print(" | 💡 Light: "); Serial.print(lightRaw);
  Serial.print(" ("); Serial.print(lightState); Serial.println(")");

  // --- Pump control every interval ---
  unsigned long now = millis();
  if (now - lastPumpTime >= PUMP_INTERVAL) {
    lastPumpTime = now;

    if (lightState == "Night") {
      Serial.println("🚫 Pump OFF (night)");
    } else if (lightState == "Overcast") {
      Serial.println("💧 Pump SHORT");
      runPump(3000);  // 3 sec
    } else if (lightState == "Cloudy") {
      Serial.println("💧 Pump MEDIUM");
      runPump(6000);  // 6 sec
    } else {
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