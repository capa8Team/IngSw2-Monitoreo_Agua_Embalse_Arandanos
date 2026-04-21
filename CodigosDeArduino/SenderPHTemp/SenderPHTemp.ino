//Inclusion de librerias para el uso de ESPNOW y ESP wifi
#include <ESP8266WiFi.h>
#include <espnow.h>
#include <OneWire.h>
#include <DallasTemperature.h>


#define BOARD_ID 1
const int oneWireBus = 4;  
// SSID de la red a la que se conecta el receptor (para sincronizar canal ESP-NOW).
// Debe coincidir con el ssid configurado en integracionESPNowWebserver.
constexpr char WIFI_SSID[] = "Doria phone";

// REPLACE WITH RECEIVER MAC Address
uint8_t broadcastAddress[] = {0xA8, 0x48, 0xFA, 0xFF, 0x2E, 0x0D}; 

// Structure example to send data
// Must match the receiver structure
typedef struct struct_message {
  char Nombre[32];
  int id_env;
  float pH;
  float Temp;
} struct_message;

// Create a struct_message called myData
struct_message myData;
OneWire oneWire(oneWireBus);
DallasTemperature sensors(&oneWire);

unsigned long lastTime = 0;  
unsigned long timerDelay = 1000;  // send readings timer
unsigned int idEnvCounter = 1;

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

// Callback when data is sent
void OnDataSent(uint8_t *mac_addr, uint8_t sendStatus) {
  Serial.print("Last Packet Send Status: ");
  if (sendStatus == 0){
    Serial.println("Delivery success");
  }
  else{
    Serial.println("Delivery fail");
  }
}

//Declaracion de variables
float calibration = 21.34+0.835; //change this value to calibrate
const int analogInPin = A0;
unsigned long int avgValue;
int buf[10],temp;


//Setup de los sensores y protocolo ESP NOW
void setup() {
  Serial.begin(115200);
//Set up ESP NOW sender
  WiFi.mode(WIFI_STA);

  int32_t channel = getWiFiChannel(WIFI_SSID);
  if (channel > 0) {
    wifi_promiscuous_enable(1);
    wifi_set_channel(channel);
    wifi_promiscuous_enable(0);
    Serial.print("Canal WiFi detectado para ESP-NOW: ");
    Serial.println(channel);
  } else {
    Serial.println("No se encontro SSID para sincronizar canal. Se usa canal actual.");
  }

  // Init ESP-NOW
  if (esp_now_init() != 0) {
    Serial.println("Error initializing ESP-NOW");
    return;
  }

  // Once ESPNow is successfully Init, we will register for Send CB to
  // get the status of Trasnmitted packet
  esp_now_set_self_role(ESP_NOW_ROLE_CONTROLLER);
  esp_now_register_send_cb(OnDataSent);
  
  // Register peer
  if (esp_now_add_peer(broadcastAddress, ESP_NOW_ROLE_SLAVE, 1, NULL, 0) != 0) {
    Serial.println("Error adding peer");
    return;
  }
  sensors.begin();
  Serial.println("Sender ESP-NOW listo");
}


//Codigo principal
void loop() {
  for(int i=0;i<10;i++){
    buf[i]=analogRead(analogInPin);
    delay(30);
  }

  for(int i=0;i<9;i++){
    for(int j=i+1;j<10;j++){
      if(buf[i]>buf[j]){
        temp=buf[i];
        buf[i]=buf[j];
        buf[j]=temp;
      }
    }
  }

  avgValue=0;
  for(int i=2;i<8;i++)
  avgValue+=buf[i];
  float pHVol=(float)avgValue*3.3/1024/6;
  float phValue = -5.70 * pHVol + calibration;
  Serial.print("sensor = ");
  Serial.println(phValue);

  //Sensor de temperatura 
  sensors.requestTemperatures(); 
  float temperatureC = sensors.getTempCByIndex(0);
  
  if ((millis() - lastTime) > timerDelay) {
    // Set values to send
    strncpy(myData.Nombre, "Dispositivo 1", sizeof(myData.Nombre));
    myData.Nombre[sizeof(myData.Nombre) - 1] = '\0';
    myData.id_env = idEnvCounter++;
    myData.pH = phValue;
    myData.Temp = temperatureC;
    // Send message via ESP-NOW
    esp_now_send(broadcastAddress, (uint8_t *) &myData, sizeof(myData));

    Serial.print("Enviado -> Nombre: ");
    Serial.print(myData.Nombre);
    Serial.print(" | id_env: ");
    Serial.print(myData.id_env);
    Serial.print(" | pH: ");
    Serial.println(myData.pH);
    Serial.print(" | Temperatura_C: ");
    Serial.println(myData.Temp);
    lastTime = millis();
  }
  delay(1000);
}
