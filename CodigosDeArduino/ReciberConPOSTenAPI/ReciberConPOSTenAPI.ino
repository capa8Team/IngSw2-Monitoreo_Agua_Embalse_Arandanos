/*
  Receptor ESP-NOW + WebServer + POST a API (ESP8266)
  - Recibe datos de pH por ESP-NOW
  - Muestra dashboard local en servidor web
  - Publica cada lectura a una API REST via HTTP POST
*/

#include <ESP8266WiFi.h>
#include <espnow.h>
#include <ESP8266HTTPClient.h>
#include "ESPAsyncTCP.h"
#include "ESPAsyncWebServer.h"
#include <ArduinoJson.h>
#include <Arduino_JSON.h>

// Credenciales STA para acceso a internet/API
const char* ssid = "movistar2,4GHZ_0FDAC0";
const char* password = "jen82E99M6zcm2m8262v";

// Red AP local para abrir el dashboard aun sin internet
const char* apSsid = "ESP8266-pH";
const char* apPassword = "12345678";

// URL de tu API REST para registrar lecturas
// Importante: usa la IP LAN del PC donde corre FastAPI (no localhost).
const char* serverName = "http://192.168.1.97:8000/api/sensors/ph";

// Debe coincidir con el struct del sender
typedef struct struct_message {
  char Nombre[32];
  int id_env;
  float pH;
} struct_message;

struct_message incomingReadings;
struct_message pendingReadings;
volatile bool hasPendingReading = false;
char lastSenderMac[18] = "00:00:00:00:00:00";

AsyncWebServer server(80);
AsyncEventSource events("/events");
JSONVar board;

const char index_html[] PROGMEM = R"rawliteral(
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Receptor pH + API</title>
  <style>
    :root {
      --bg: #eef4f6;
      --card: #ffffff;
      --line: #d6e3ea;
      --primary: #0f6f70;
      --text: #17313d;
      --muted: #607684;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      min-height: 100vh;
      font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
      color: var(--text);
      background: radial-gradient(circle at 10% 0%, #d9e9f2 0%, var(--bg) 45%);
      display: grid;
      place-items: center;
      padding: 18px;
    }
    .panel {
      width: min(760px, 100%);
      background: var(--card);
      border: 1px solid var(--line);
      border-radius: 18px;
      box-shadow: 0 20px 45px rgba(10, 35, 50, 0.12);
      overflow: hidden;
    }
    .header {
      background: linear-gradient(120deg, #0f6f70 0%, #349497 100%);
      color: #fff;
      padding: 18px 22px;
      font-size: 1.1rem;
      font-weight: 700;
    }
    .content {
      padding: 22px;
      display: grid;
      gap: 12px;
    }
    .row {
      display: flex;
      justify-content: space-between;
      gap: 12px;
      border-bottom: 1px solid var(--line);
      padding: 10px 0;
      align-items: center;
    }
    .row:last-child { border-bottom: none; }
    .label { color: var(--muted); font-weight: 600; }
    .value { font-weight: 700; text-align: right; word-break: break-word; }
    .ph { font-size: clamp(1.9rem, 5vw, 3rem); color: var(--primary); line-height: 1; }
    .api { padding: 0 22px 22px; color: var(--muted); font-size: 0.92rem; }
    code { background: #e9f2f7; padding: 2px 7px; border-radius: 7px; }
  </style>
</head>
<body>
  <section class="panel">
    <div class="header">Dashboard pH + Reenvio API</div>
    <div class="content">
      <div class="row"><span class="label">Dispositivo</span><span class="value" id="device">-</span></div>
      <div class="row"><span class="label">ID envio</span><span class="value" id="idEnv">-</span></div>
      <div class="row"><span class="label">pH</span><span class="value ph" id="ph">--.--</span></div>
      <div class="row"><span class="label">Ultimo evento</span><span class="value" id="time">-</span></div>
      <div class="row"><span class="label">POST API</span><span class="value" id="postStatus">-</span></div>
    </div>
    <div class="api">API local: <code>GET /api/ph</code></div>
  </section>

  <script>
    function now() {
      return new Date().toLocaleString();
    }

    function render(data) {
      document.getElementById('device').textContent = data.device || '-';
      document.getElementById('idEnv').textContent = data.id_env ?? '-';
      document.getElementById('ph').textContent = Number(data.ph || 0).toFixed(2);
      document.getElementById('time').textContent = data.timestamp || now();
      document.getElementById('postStatus').textContent = data.post_status || '-';
    }

    fetch('/api/ph')
      .then(r => r.json())
      .then(data => render(data))
      .catch(() => {});

    if (!!window.EventSource) {
      const source = new EventSource('/events');
      source.addEventListener('new_readings', function (e) {
        const data = JSON.parse(e.data);
        render(data);
      }, false);
    }
  </script>
</body>
</html>
)rawliteral";

String lastPostStatus = "Sin envio";

bool connectStaWiFi(unsigned long timeoutMs = 12000) {
  if (strlen(ssid) == 0) {
    Serial.println("SSID vacio: STA deshabilitado");
    return false;
  }

  Serial.print("Conectando STA a: ");
  Serial.println(ssid);

  WiFi.begin(ssid, password);
  unsigned long startMs = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - startMs < timeoutMs) {
    delay(400);
    Serial.println("Conectando STA...");
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.print("STA IP Address: ");
    Serial.println(WiFi.localIP());
    Serial.print("Wi-Fi Channel: ");
    Serial.println(WiFi.channel());
    return true;
  }

  Serial.print("Sin conexion STA (status=");
  Serial.print(WiFi.status());
  Serial.println(")");
  return false;
}

void ensureStaConnected() {
  static unsigned long lastRetryMs = 0;
  const unsigned long RETRY_INTERVAL_MS = 10000;

  if (WiFi.status() == WL_CONNECTED) {
    return;
  }

  if (millis() - lastRetryMs < RETRY_INTERVAL_MS) {
    return;
  }

  lastRetryMs = millis();
  Serial.println("STA desconectado, reintentando...");
  connectStaWiFi(8000);
}

String buildBoardJson() {
  board["device"] = incomingReadings.Nombre;
  board["id_env"] = incomingReadings.id_env;
  board["ph"] = incomingReadings.pH;
  board["timestamp"] = String(millis());
  board["post_status"] = lastPostStatus;
  return JSON.stringify(board);
}

void postToApi() {
  ensureStaConnected();

  if (WiFi.status() != WL_CONNECTED) {
    lastPostStatus = "Sin WiFi STA";
    return;
  }

  WiFiClient client;
  HTTPClient http;

  if (!http.begin(client, serverName)) {
    lastPostStatus = "http.begin fallo";
    return;
  }

  http.addHeader("Content-Type", "application/json");

  StaticJsonDocument<200> payload;
  payload["sensor_id"] = incomingReadings.Nombre;
  payload["id_env"] = incomingReadings.id_env;
  payload["ph"] = incomingReadings.pH;
  payload["timestamp"] = millis() / 1000;

  String requestBody;
  serializeJson(payload, requestBody);

  int httpCode = http.POST(requestBody);
  if (httpCode > 0) {
    String response = http.getString();
    lastPostStatus = String("OK ") + httpCode;
    Serial.print("POST API code: ");
    Serial.println(httpCode);
    Serial.print("POST API response: ");
    Serial.println(response);
  } else {
    String errorText = http.errorToString(httpCode);
    lastPostStatus = String("Error ") + httpCode + " " + errorText;
    Serial.print("POST API failed, code: ");
    Serial.println(httpCode);
    Serial.print("POST API error: ");
    Serial.println(errorText);
  }

  http.end();
}

void OnDataRecv(uint8_t* mac_addr, uint8_t* incomingData, uint8_t len) {
  if (len < sizeof(pendingReadings)) {
    return;
  }

  memcpy(&pendingReadings, incomingData, sizeof(pendingReadings));
  snprintf(lastSenderMac, sizeof(lastSenderMac), "%02X:%02X:%02X:%02X:%02X:%02X",
           mac_addr[0], mac_addr[1], mac_addr[2], mac_addr[3], mac_addr[4], mac_addr[5]);
  hasPendingReading = true;
}

void setupWebServer() {
  server.on("/", HTTP_GET, [](AsyncWebServerRequest* request) {
    request->send(200, "text/html", index_html);
  });

  server.on("/api/ph", HTTP_GET, [](AsyncWebServerRequest* request) {
    String json = buildBoardJson();
    request->send(200, "application/json", json);
  });

  events.onConnect([](AsyncEventSourceClient* client) {
    if (client->lastId()) {
      Serial.printf("Client reconnected, last ID: %u\n", client->lastId());
    }
    String json = buildBoardJson();
    client->send(json.c_str(), "new_readings", millis());
  });

  server.addHandler(&events);
  server.begin();
  Serial.println("WebServer iniciado");
}

void setupWiFi() {
  WiFi.mode(WIFI_AP_STA);
  WiFi.setAutoReconnect(true);
  WiFi.persistent(true);
  WiFi.softAP(apSsid, apPassword);

  Serial.print("AP SSID: ");
  Serial.println(apSsid);
  Serial.print("AP IP Address: ");
  Serial.println(WiFi.softAPIP());

  if (!connectStaWiFi()) {
    Serial.println("Sin conexion STA, POST a API deshabilitado temporalmente");
  }
}

void setupEspNow() {
  if (esp_now_init() != 0) {
    Serial.println("Error initializing ESP-NOW");
    return;
  }

  esp_now_set_self_role(ESP_NOW_ROLE_SLAVE);
  esp_now_register_recv_cb(OnDataRecv);
  Serial.println("ESP-NOW receptor listo");
}

void setup() {
  Serial.begin(115200);
  delay(200);

  if (String(serverName).indexOf("127.0.0.1") >= 0 || String(serverName).indexOf("localhost") >= 0) {
    Serial.println("AVISO: serverName usa localhost/127.0.0.1; desde ESP debes usar la IP de tu PC/API");
  }

  strncpy(incomingReadings.Nombre, "Sin dato", sizeof(incomingReadings.Nombre));
  incomingReadings.Nombre[sizeof(incomingReadings.Nombre) - 1] = '\0';
  incomingReadings.id_env = -1;
  incomingReadings.pH = 0.0;

  setupWiFi();
  setupEspNow();
  setupWebServer();
}

void loop() {
  ensureStaConnected();

  if (hasPendingReading) {
    noInterrupts();
    memcpy(&incomingReadings, &pendingReadings, sizeof(incomingReadings));
    hasPendingReading = false;
    interrupts();

    Serial.print("Packet received from: ");
    Serial.println(lastSenderMac);
    Serial.print("Nombre: ");
    Serial.println(incomingReadings.Nombre);
    Serial.print("ID envio: ");
    Serial.println(incomingReadings.id_env);
    Serial.print("Valor pH: ");
    Serial.println(incomingReadings.pH);

    postToApi();

    String jsonString = buildBoardJson();
    events.send(jsonString.c_str(), "new_readings", millis());
  }

  static unsigned long lastEventTime = millis();
  static const unsigned long EVENT_INTERVAL_MS = 5000;
  if ((millis() - lastEventTime) > EVENT_INTERVAL_MS) {
    events.send("ping", NULL, millis());
    lastEventTime = millis();
  }

  yield();
}
