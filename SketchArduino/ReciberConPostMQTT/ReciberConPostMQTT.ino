/*
  ReciberConPostMQTT - ESP8266
  - Recibe lecturas (pH, temperatura, EC, bateria) por ESP-NOW
  - Publica cada lectura en AWS IoT Core (MQTT), topic boya/sensores
*/

#include <ESP8266WiFi.h>
#include <WiFiClientSecure.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <time.h>
#include <espnow.h>
#include "secrets.h"

#define AWS_IOT_PUBLISH_TOPIC "boya/sensores"

// Debe coincidir con el struct del sender (Sender3Sensores / SensorPHEnvioDatos)
typedef struct struct_message {
  char Nombre[32];
  int id_env;
  float pH;
  float Temp;
  float EC;
  int CBat;
} struct_message;

struct_message incomingReadings;
struct_message pendingReadings;
volatile bool hasPendingReading = false;

void OnDataRecv(uint8_t* mac, uint8_t* incomingData, uint8_t len);

WiFiClientSecure net;

BearSSL::X509List cert(cacert);
BearSSL::X509List client_crt(client_cert);
BearSSL::PrivateKey key(privkey);

PubSubClient client(net);

time_t now;
time_t nowish = 1510592825;

void setupTimeZoneSantiago() {
  setenv("TZ", "<-03>3", 1);
  tzset();
  configTime(SANTIAGO_GMT_OFFSET_SEC, 0, "cl.pool.ntp.org", "pool.ntp.org");
}

void formatSantiagoTime(char* buf, size_t bufSize, time_t t) {
  struct tm timeinfo;
  localtime_r(&t, &timeinfo);
  strftime(buf, bufSize, "%Y-%m-%d %H:%M:%S", &timeinfo);
}

void NTPConnect(void) {
  setupTimeZoneSantiago();

  Serial.print("Sincronizando hora (Santiago de Chile, UTC-3)...");
  now = time(nullptr);
  while (now < nowish) {
    delay(500);
    Serial.print(".");
    now = time(nullptr);
  }
  Serial.println(" listo");

  char fechaHora[24];
  formatSantiagoTime(fechaHora, sizeof(fechaHora), now);
  Serial.print("Hora actual (Santiago): ");
  Serial.println(fechaHora);
}

void connectAWS() {
  WiFi.mode(WIFI_STA);
  WiFi.setAutoReconnect(true);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  Serial.println(String("Attempting to connect to SSID: ") + String(WIFI_SSID));

  unsigned long startMs = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - startMs < 20000) {
    Serial.print(".");
    delay(1000);
  }

  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi no conectado; MQTT pendiente");
    return;
  }

  Serial.print("STA IP: ");
  Serial.println(WiFi.localIP());

  NTPConnect();

  net.setTrustAnchors(&cert);
  net.setClientRSACert(&client_crt, &key);

  client.setServer(MQTT_HOST, 8883);

  Serial.println("Connecting to AWS IoT");

  while (!client.connect(THINGNAME)) {
    Serial.print(".");
    delay(1000);
  }

  if (!client.connected()) {
    Serial.println("AWS IoT Timeout!");
    return;
  }

  Serial.println("AWS IoT Connected!");
}

void publishSensorReading(const struct_message& data) {
  if (!client.connected()) {
    Serial.println("MQTT desconectado; lectura no publicada");
    return;
  }

  time_t lecturaTime = time(nullptr);
  char fechaHora[24];
  formatSantiagoTime(fechaHora, sizeof(fechaHora), lecturaTime);

  StaticJsonDocument<448> doc;
  doc["nombre"] = data.Nombre;
  doc["id_env"] = data.id_env;
  doc["pH"] = data.pH;
  doc["temperatura"] = data.Temp;
  doc["EC"] = data.EC;
  doc["bateria"] = data.CBat;
  doc["timestamp"] = lecturaTime;
  doc["fecha_hora"] = fechaHora;
  doc["zona_horaria"] = "America/Santiago";

  char jsonBuffer[512];
  serializeJson(doc, jsonBuffer);

  if (client.publish(AWS_IOT_PUBLISH_TOPIC, jsonBuffer)) {
    Serial.println("Publicado en AWS IoT:");
    Serial.println(jsonBuffer);
  } else {
    Serial.println("Error al publicar en AWS IoT");
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

void OnDataRecv(uint8_t* mac, uint8_t* incomingData, uint8_t len) {
  if (len < sizeof(pendingReadings)) {
    return;
  }

  memcpy(&pendingReadings, incomingData, sizeof(pendingReadings));
  hasPendingReading = true;
}

void setup() {
  Serial.begin(115200);
  delay(200);

  strncpy(incomingReadings.Nombre, "Sin dato", sizeof(incomingReadings.Nombre));
  incomingReadings.Nombre[sizeof(incomingReadings.Nombre) - 1] = '\0';
  incomingReadings.id_env = -1;
  incomingReadings.pH = 0.0;
  incomingReadings.Temp = 0.0;
  incomingReadings.EC = 0.0;
  incomingReadings.CBat = 0;

  connectAWS();
  setupEspNow();
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    static unsigned long lastWiFiRetryMs = 0;
    if (millis() - lastWiFiRetryMs > 10000) {
      lastWiFiRetryMs = millis();
      Serial.println("Reintentando WiFi...");
      WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    }
  }

  if (!client.connected()) {
    static unsigned long lastMqttRetryMs = 0;
    if (millis() - lastMqttRetryMs > 10000) {
      lastMqttRetryMs = millis();
      connectAWS();
    }
  } else {
    client.loop();
  }

  now = time(nullptr);

  if (hasPendingReading) {
    noInterrupts();
    memcpy(&incomingReadings, &pendingReadings, sizeof(incomingReadings));
    hasPendingReading = false;
    interrupts();

    Serial.println("--- Lectura ESP-NOW ---");
    Serial.print("Nombre: ");
    Serial.println(incomingReadings.Nombre);
    Serial.print("Id envio: ");
    Serial.println(incomingReadings.id_env);
    Serial.print("pH: ");
    Serial.println(incomingReadings.pH);
    Serial.print("Temperatura: ");
    Serial.println(incomingReadings.Temp);
    Serial.print("EC: ");
    Serial.println(incomingReadings.EC);
    Serial.print("Carga bateria: ");
    Serial.println(incomingReadings.CBat);

    publishSensorReading(incomingReadings);
  }

  yield();
}
