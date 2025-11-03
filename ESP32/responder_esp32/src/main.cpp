#include <Arduino.h>
#include <WiFi.h>
#include <WebServer.h>
#include <ArduinoJson.h>

#define WIFI_SSID     "Fake Extender"
#define WIFI_PASSWORD "Aa1231325213!"

int update = 5000;
int last_update = 0;

WebServer server(8080);  // same port as in Rails config

// =========================
// Action Function
// =========================
void respond_action() {
  Serial.println("[ESP32] 🚀 Action");
}

// =========================
// Handle Incoming Alert
// =========================
void handleAlert() {
  if (server.method() != HTTP_POST) {
    server.send(405, "application/json", "{\"error\":\"Method Not Allowed\"}");
    return;
  }

  // Read body
  String body = server.arg("plain");
  Serial.println("[ESP32] Received body:");
  Serial.println(body);

  // Parse JSON
  StaticJsonDocument<256> doc;
  DeserializationError err = deserializeJson(doc, body);
  if (err) {
    Serial.printf("[ESP32] JSON parse error: %s\n", err.c_str());
    server.send(400, "application/json", "{\"error\":\"Invalid JSON\"}");
    return;
  }

  const char* sender = doc["sender_tag"] | "unknown";
  const char* message = doc["message"] | "none";

  Serial.printf("[ESP32] 🔔 ALERT from %s: %s\n", sender, message);

  // === NEW: Trigger custom action ===
  respond_action();

  // Respond OK
  server.send(200, "application/json", "{\"ok\":true}");
}

// =========================
// Setup
// =========================
void setup() {
  Serial.begin(115200);

  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.print("[ESP32] Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\n[ESP32] Connected!");
  Serial.print("[ESP32] IP address: ");
  Serial.println(WiFi.localIP());

  // Define route
  server.on("/alert", HTTP_POST, handleAlert);
  server.begin();
  Serial.println("[ESP32] Server started at port 8080");
}

// =========================
// Main Loop
// =========================
void loop() {
  server.handleClient();
  
  if (update < (millis() - last_update)) {
    Serial.print("[ESP32] IP address: ");
    Serial.println(WiFi.localIP());
    last_update = millis();
  }
}
