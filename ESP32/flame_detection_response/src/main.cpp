#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>

// ====== EDIT THESE (Wi-Fi / MQTT) ======
const char* WIFI_SSID    = "PLM_WIFI";
const char* WIFI_PASS    = "PLMh@ribon";

const char* MQTT_HOST    = "172.20.63.240";   // broker (your laptop) LAN IP
const uint16_t MQTT_PORT = 1883;
const char* MQTT_USER    = "iotuser";
const char* MQTT_PASS    = "emtech_broker";

const char* SUB_TOPIC    = "site/lab1/devices/esp32-01/in";
const char* CLIENT_ID    = "esp32-01";
// =======================================

// ====== ACTION PINS (ESP32-WROOM-32D safe outputs) ======
const int PIN_TOP_LEFT_ACTION     = 23; // TL
const int PIN_TOP_RIGHT_ACTION    = 22; // TR
const int PIN_BOTTOM_LEFT_ACTION  = 21; // BL
const int PIN_BOTTOM_RIGHT_ACTION = 19; // BR
// If you want both bottom zones on one pin, set both BL & BR to the same GPIO.

// Sprinkler output mirrors any frame HIGH
const int SPRINKLER_PIN = 18; // choose another safe output if desired

// ====== SMOKE/GAS SENSOR + TIMERS ======
const int SMOKE_PIN = 34;         // ADC1_CH6 (input-only)
const int SMOKE_THRESHOLD = 400;

const unsigned long QUIET_MS     = 5000; // 5s with no fire (per frame) to allow clear
const unsigned long DEBOUNCE_MS  = 2000; // up to 2s gaps allowed between hits per frame
const unsigned long ARM_FRAME_MS = 3000; // need 3s debounced detection before first latch

// ---------- Types & Globals ----------
enum Zone : uint8_t { Z_TL=0, Z_TR=1, Z_BL=2, Z_BR=3, Z_NONE=4 };
constexpr int ZONE_COUNT = 4;
const int ZONE_PINS[ZONE_COUNT] = {
  PIN_TOP_LEFT_ACTION, PIN_TOP_RIGHT_ACTION, PIN_BOTTOM_LEFT_ACTION, PIN_BOTTOM_RIGHT_ACTION
};

unsigned long lastSeenMs[ZONE_COUNT] = {0,0,0,0}; // last time a detection for that frame was seen
unsigned long armStartMs[ZONE_COUNT] = {0,0,0,0}; // start of continuous (debounced) window for that frame
bool          latched[ZONE_COUNT]    = {false,false,false,false};

WiFiClient wifiClient;
PubSubClient mqtt(wifiClient);

// ---------- Small helpers ----------
static inline unsigned long nowMs() { return millis(); }
static inline int readSmoke()       { return analogRead(SMOKE_PIN); }

static inline String norm(String s) { s.trim(); s.toLowerCase(); return s; }

static inline bool anyLatched() {
  return latched[0] || latched[1] || latched[2] || latched[3];
}

static inline void updateSprinkler() {
  digitalWrite(SPRINKLER_PIN, anyLatched() ? HIGH : LOW);
}

// Unified write for frames + sprinkler mirror
static inline void applyFrameState(Zone z, bool on) {
  if (z == Z_NONE) return;
  digitalWrite(ZONE_PINS[z], on ? HIGH : LOW);
  latched[z] = on;
  updateSprinkler();
}

// --- robust parser: accept {fire}{top-left} OR any string that contains the zone token ---
String extractZone(const String& raw) {
  // Try the original brace-based format first
  String msg = raw;
  int firstOpen  = msg.indexOf('{');
  int firstClose = msg.indexOf('}', firstOpen + 1);
  int secondOpen = (firstClose < 0) ? -1 : msg.indexOf('{', firstClose + 1);
  int secondClose= (secondOpen < 0) ? -1 : msg.indexOf('}', secondOpen + 1);

  if (firstOpen >= 0 && firstClose > firstOpen && secondOpen >= 0 && secondClose > secondOpen) {
    return norm(msg.substring(secondOpen + 1, secondClose));
  }

  // Fallback: search tokens anywhere, ignore case/spacing
  String m = norm(raw);
  if (m.indexOf("top-left")     >= 0) return "top-left";
  if (m.indexOf("top-right")    >= 0) return "top-right";
  if (m.indexOf("bottom-left")  >= 0) return "bottom-left";
  if (m.indexOf("bottom-right") >= 0) return "bottom-right";
  return "";
}

static inline Zone toZone(const String& s) {
  if (s == "top-left")     return Z_TL;
  if (s == "top-right")    return Z_TR;
  if (s == "bottom-left")  return Z_BL;
  if (s == "bottom-right") return Z_BR;
  return Z_NONE;
}

// ---------- Frame auto-clear based on your rules ----------
void maybeClearFrames(int smoke) {
  const unsigned long now = nowMs();

  for (int i = 0; i < ZONE_COUNT; ++i) {
    if (!latched[i]) continue;

    const unsigned long gap = now - lastSeenMs[i];
    const bool quietEnough  = (gap >= QUIET_MS);

    Serial.printf("[CHK] i=%d latched=%d gap=%lu smoke=%d (need gap>=%lu & smoke<=%d)\n",
                  i, latched[i], gap, smoke, QUIET_MS, SMOKE_THRESHOLD);

    if (quietEnough && smoke <= SMOKE_THRESHOLD) {
      applyFrameState(static_cast<Zone>(i), false); // will also update sprinkler
      // armStartMs[i] left as-is; next detection will restart via debounce logic
    }
  }
}

// ---------- MQTT callback ----------
void onMqttMessage(char* topic, byte* payload, unsigned int length) {
  String msg; msg.reserve(length);
  for (unsigned int i = 0; i < length; i++) msg += (char)payload[i];

  Serial.printf("[MQTT] %s -> %s\n", topic, msg.c_str());

  const String zoneStr = extractZone(msg);
  const Zone   z       = toZone(zoneStr);

  if (z == Z_NONE) {
    Serial.println("[WARN] Message format not recognized");
    return;
  }

  const unsigned long now = nowMs();

  // Debounced continuity tracking per frame:
  if (now - lastSeenMs[z] > DEBOUNCE_MS) {
    // gap too large: (re)start window for THIS frame
    armStartMs[z] = now;
  } else if (armStartMs[z] == 0) {
    // first ever sighting
    armStartMs[z] = now;
  }
  lastSeenMs[z] = now;

  // First-time latch for THIS frame only after 3 s of (debounced) continuous detection
  if (!latched[z]) {
    const unsigned long armedFor = now - armStartMs[z];
    if (armedFor >= ARM_FRAME_MS) {
      applyFrameState(z, true);
      Serial.printf("[INFO] LATCH (per-frame %lu ms) -> %s\n", ARM_FRAME_MS, zoneStr.c_str());
    } else {
      Serial.printf("[INFO] %s seen; arming... %lu ms/%lu ms\n", zoneStr.c_str(), armedFor, ARM_FRAME_MS);
    }
  } else {
    // already latched; no need to re-assert pin each message
  }
}

// ---------- Connectivity ----------
void connectWifi() {
  if (WiFi.status() == WL_CONNECTED) return;
  Serial.printf("Connecting WiFi to %s", WIFI_SSID);
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  while (WiFi.status() != WL_CONNECTED) { delay(300); Serial.print("."); }
  Serial.printf("\nWiFi OK, IP: %s\n", WiFi.localIP().toString().c_str());
}

void connectMqtt() {
  while (!mqtt.connected()) {
    Serial.print("Connecting MQTT… ");
    const char* willTopic = "site/lab1/devices/esp32-01/status";
    const char* willMsg   = "offline";
    const bool ok = mqtt.connect(
      CLIENT_ID,
      MQTT_USER, MQTT_PASS,
      willTopic, 0, true, willMsg,   // LWT retained
      true                           // clean session
    );
    if (ok) {
      Serial.println("connected");
      mqtt.publish(willTopic, "online", true);
      mqtt.subscribe(SUB_TOPIC);   // QoS 0 (PubSubClient)
      Serial.printf("Subscribed: %s\n", SUB_TOPIC);
    } else {
      Serial.printf("failed (rc=%d). Retrying in 2s\n", mqtt.state());
      delay(2000);
    }
  }
}

// ---------- Setup / Loop ----------
void setup() {
  Serial.begin(115200);

  // frame pins
  for (int i = 0; i < ZONE_COUNT; ++i) {
    pinMode(ZONE_PINS[i], OUTPUT);
    digitalWrite(ZONE_PINS[i], LOW);
  }

  // sprinkler pin
  pinMode(SPRINKLER_PIN, OUTPUT);
  digitalWrite(SPRINKLER_PIN, LOW);

  // smoke pin
  pinMode(SMOKE_PIN, INPUT);

  connectWifi();

  mqtt.setServer(MQTT_HOST, MQTT_PORT);
  mqtt.setCallback(onMqttMessage);
  mqtt.setBufferSize(512);   // payload is tiny; 512 is safe

  connectMqtt();
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) connectWifi();
  if (!mqtt.connected()) connectMqtt();
  mqtt.loop();

  // Single ADC read per loop, shared by all frames
  const int smoke = readSmoke();
  maybeClearFrames(smoke);
}
