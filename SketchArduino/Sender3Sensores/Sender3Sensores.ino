/*
 * Sender3Sensores - ESP32 Wroom DA
 * pH (GPIO 2), conductividad EC K=10 (GPIO 15), temperatura DS18B20 (GPIO 17)
 * Envio de lecturas por ESP-NOW (mismo peer/canal que SensorPHEnvioDatos)
 */

#include <WiFi.h>
#include <esp_now.h>
#include <esp_wifi.h>
#include "DFRobot_EC10.h"
#include <EEPROM.h>
#include <OneWire.h>
#include <DallasTemperature.h>

#define PH_PIN 33
#define EC_PIN 35
const int oneWireBus = 32;

constexpr char WIFI_SSID[] = "Jacke_D phone";

uint8_t broadcastAddress[] = {0xE0, 0x98, 0x06, 0x23, 0x99, 0xA2};

// Debe coincidir con el receptor (pH, Temp; EC al final para receptores antiguos)
typedef struct struct_message {
  char Nombre[32];
  int id_env;
  float pH;
  float Temp;
  float EC;
  int CBat;
} struct_message;

struct_message myData;

OneWire oneWire(oneWireBus);
DallasTemperature sensors(&oneWire);
DFRobot_EC10 ec;

float calibration = 31.6;
float voltage = 0;
float ecValue = 0;
float temperature = 25;
float phValue = 0;
int cargaBateria = 0;

unsigned long lastSendTime = 0;
const unsigned long timerDelay = 1000;
unsigned int idEnvCounter = 1;

int buf[10];
int sortTemp = 0;
unsigned long avgValue = 0;

int32_t getWiFiChannel(const char *ssid) {
  int32_t n = WiFi.scanNetworks();
  if (n > 0) {
    for (int32_t i = 0; i < n; i++) {
      if (!strcmp(ssid, WiFi.SSID(i).c_str())) {
        return WiFi.channel(i);
      }
    }
  }
  return 0;
}

void OnDataSent(const wifi_tx_info_t *tx_info, esp_now_send_status_t status) {
  (void)tx_info;
  Serial.print("Last Packet Send Status: ");
  Serial.println(status == ESP_NOW_SEND_SUCCESS ? "Delivery success" : "Delivery fail");
}

float readPh() {
  for (int i = 0; i < 10; i++) {
    buf[i] = analogRead(PH_PIN);
    delay(30);
  }

  for (int i = 0; i < 9; i++) {
    for (int j = i + 1; j < 10; j++) {
      if (buf[i] > buf[j]) {
        sortTemp = buf[i];
        buf[i] = buf[j];
        buf[j] = sortTemp;
      }
    }
  }

  avgValue = 0;
  for (int i = 2; i < 8; i++) {
    avgValue += buf[i];
  }

  float pHVol = (float)avgValue * 3.3 / 4095.0 / 6.0;
  return -5.70 * pHVol + calibration;
}

float readTemperature() {
  sensors.requestTemperatures();
  return sensors.getTempCByIndex(0);
}

void setup() {
  Serial.begin(115200);

  analogSetAttenuation(ADC_11db);

  EEPROM.begin(32);
  sensors.begin();
  ec.begin();

  WiFi.mode(WIFI_STA);

  int32_t channel = getWiFiChannel(WIFI_SSID);
  if (channel > 0) {
    esp_wifi_set_channel(channel, WIFI_SECOND_CHAN_NONE);
    Serial.print("Canal WiFi detectado para ESP-NOW: ");
    Serial.println(channel);
  } else {
    Serial.println("No se encontro SSID para sincronizar canal. Se usa canal actual.");
    channel = 1;
  }

  if (esp_now_init() != ESP_OK) {
    Serial.println("Error initializing ESP-NOW");
    return;
  }

  esp_now_register_send_cb(OnDataSent);

  esp_now_peer_info_t peerInfo = {};
  memcpy(peerInfo.peer_addr, broadcastAddress, 6);
  peerInfo.channel = channel;
  peerInfo.encrypt = false;

  if (esp_now_add_peer(&peerInfo) != ESP_OK) {
    Serial.println("Error adding peer");
    return;
  }

  Serial.println("Sender3Sensores ESP32 ESP-NOW listo");
}

void loop() {
  static unsigned long sampleTime = millis();

  if (millis() - sampleTime >= timerDelay) {
    sampleTime = millis();

//Obtencion de datos
    phValue = readPh();
    temperature = readTemperature();
    voltage = (analogRead(EC_PIN) / 1023 * 3300.0;)
    Serial.println(voltage);
    ecValue = ec.readEC(voltage, temperature);
    cargaBateria = random(50,100);
    strncpy(myData.Nombre, "Dispositivo 1", sizeof(myData.Nombre));
    myData.Nombre[sizeof(myData.Nombre) - 1] = '\0';
    myData.id_env = idEnvCounter++;
    myData.pH = phValue;
    myData.Temp = temperature;
    myData.EC = ecValue;
    myData.CBat = cargaBateria;
    esp_now_send(broadcastAddress, (uint8_t *)&myData, sizeof(myData));

    Serial.print("pH: ");
    Serial.print(phValue, 2);
    Serial.print("  Temp: ");
    Serial.print(temperature, 1);
    Serial.print(" C  EC: ");
    Serial.print(ecValue, 10);
    Serial.print(" ms/cm | Carga Bateria: ");
    Serial.print(cargaBateria);
    Serial.print(" %  | Enviado id_env: ");
    Serial.println(myData.id_env);

  }

  voltage = analogRead(EC_PIN) / 4095.0 * 3300.0;
  ec.calibration(voltage, temperature);
}
