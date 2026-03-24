/*
  CÓDIGO ARDUINO - LECTURA DE SENSORES
  
  Código de ejemplo para Arduino Uno que lee sensores de:
  - pH (entrada analógica A0)
  - Temperatura (OneWire en pin 2)
  - Conductividad Eléctrica (entrada analógica A1)
  
  Los datos se envían en formato JSON a través del puerto serial.
  
  INSTALACIÓN DE LIBRERÍAS:
  1. Abre Arduino IDE
  2. Sketch > Include Library > Manage Libraries
  3. Busca e instala "OneWire" por Jim Studt
  4. Busca e instala "DallasTemperature" por Miles Burton
  
  CONEXIONES:
  - Sensor pH → A0 (entrada analógica)
  - Sensor Temperatura (DS18B20) → pin 2 (OneWire)
  - Sensor Conductividad → A1 (entrada analógica)
  - GND → GND
  - 5V → 5V
*/

#include <OneWire.h>
#include <DallasTemperature.h>

// ============================================================================
// CONFIGURACIÓN DE PINES
// ============================================================================

const int PH_SENSOR_PIN = A0;           // Pin analógico para pH
const int TEMP_SENSOR_PIN = 2;          // Pin digital para sensor temperatura
const int CONDUCTIVITY_SENSOR_PIN = A1; // Pin analógico para conductividad
const int LED_PIN = 13;                 // LED indicador de estado

// ============================================================================
// CONFIGURACIÓN DE SENSORES
// ============================================================================

OneWire oneWire(TEMP_SENSOR_PIN);
DallasTemperature temperatureSensors(&oneWire);

// Calibración pH (cambiar según tu sensor)
const float PH_OFFSET = 0.0;    // Offset de calibración
const float pH_AT_7 = 512.0;    // Valor ADC a pH 7

// ============================================================================
// VARIABLES GLOBALES
// ============================================================================

float phValue = 7.0;
float temperatureValue = 20.0;
float conductivityValue = 500.0;

unsigned long lastSensorReadTime = 0;
unsigned long lastSerialSendTime = 0;

const unsigned long SENSOR_READ_INTERVAL = 1000;  // Leer sensores cada 1s
const unsigned long SERIAL_SEND_INTERVAL = 3000;  // Enviar datos cada 3s

// ============================================================================
// SETUP
// ============================================================================

void setup() {
  Serial.begin(9600);        // Inicializar comunicación serial (9600 baud)
  pinMode(LED_PIN, OUTPUT);  // Configurar LED como salida
  
  // Inicializar sensor de temperatura
  temperatureSensors.begin();
  
  // Mensaje inicial
  Serial.println("{\"type\":\"system\",\"message\":\"Arduino iniciado\"}");
  delay(500);
}

// ============================================================================
// LOOP PRINCIPAL
// ============================================================================

void loop() {
  unsigned long currentTime = millis();
  
  // Leer sensores cada SENSOR_READ_INTERVAL ms
  if (currentTime - lastSensorReadTime >= SENSOR_READ_INTERVAL) {
    readAllSensors();
    lastSensorReadTime = currentTime;
    
    // Parpadear LED cuando se leen sensores
    digitalWrite(LED_PIN, HIGH);
    delayMicroseconds(100);
    digitalWrite(LED_PIN, LOW);
  }
  
  // Enviar datos por serial cada SERIAL_SEND_INTERVAL ms
  if (currentTime - lastSerialSendTime >= SERIAL_SEND_INTERVAL) {
    sendSensorDataJSON();
    lastSerialSendTime = currentTime;
  }
}

// ============================================================================
// FUNCIONES DE LECTURA DE SENSORES
// ============================================================================

void readAllSensors() {
  readpHSensor();
  readTemperatureSensor();
  readConductivitySensor();
}

/*
  LECTURA DE pH
  
  El sensor de pH produce una salida de voltaje:
  - pH 7 = ~2.5V (512 en ADC con 10 bits)
  - pH 6 = ~3.0V
  - pH 8 = ~2.0V
  
  Ajusta los valores según la calibración de tu sensor
*/

void readpHSensor() {
  int phRaw = analogRead(PH_SENSOR_PIN);
  
  // Convertir valor ADC (0-1023) a pH
  // Fórmula: pH = 7.0 + (512 - ADC) * (0.0048)
  float voltage = (phRaw / 1023.0) * 5.0;
  phValue = 7.0 + (2.5 - voltage) * 2.0;
  
  // Limitar valores al rango 0-14
  phValue = constrain(phValue, 0, 14);
}

/*
  LECTURA DE TEMPERATURA
  
  Usa sensor DS18B20 (OneWire)
  El sensor es muy preciso (±0.5°C)
*/

void readTemperatureSensor() {
  temperatureSensors.requestTemperatures();
  temperatureValue = temperatureSensors.getTempCByIndex(0);
  
  // Verificar si hay error en la lectura
  if (temperatureValue == DEVICE_DISCONNECTED_C) {
    temperatureValue = 0.0;
  }
}

/*
  LECTURA DE CONDUCTIVIDAD ELÉCTRICA
  
  El sensor produce una salida de voltaje proporcional a la conductividad
  Rango típico: 0-2000 µS/cm (microSiemens)
  
  Ajusta la escala según tu sensor específico
*/

void readConductivitySensor() {
  int conductivityRaw = analogRead(CONDUCTIVITY_SENSOR_PIN);
  
  // Convertir valor ADC a conductividad
  // Fórmula: Conductivity = (ADC / 1023) * 2000
  conductivityValue = (conductivityRaw / 1023.0) * 2000.0;
  
  // Limitar a 4 decimales
  conductivityValue = round(conductivityValue * 100.0) / 100.0;
}

// ============================================================================
// ENVÍO DE DATOS
// ============================================================================

/*
  Enviar datos en formato JSON al puerto serial
  Cada sensor se envía en una línea separada
*/

void sendSensorDataJSON() {
  // Enviar datos de pH
  Serial.print("{\"type\":\"pH\",\"value\":");
  Serial.print(phValue, 2); // 2 decimales
  Serial.println("}");
  
  // Enviar datos de temperatura
  Serial.print("{\"type\":\"temperature\",\"value\":");
  Serial.print(temperatureValue, 2);
  Serial.println("}");
  
  // Enviar datos de conductividad
  Serial.print("{\"type\":\"conductivity\",\"value\":");
  Serial.print(conductivityValue, 2);
  Serial.println("}");
  
  // Enviar estado del sistema
  Serial.print("{\"type\":\"status\",\"uptime\":");
  Serial.print(millis() / 1000);
  Serial.println("}");
}

// ============================================================================
// FUNCIONES AUXILIARES
// ============================================================================

/*
  Función para procesar comandos recibidos por serial (opcional)
  Permite cambiar configuraciones remotamente
*/

void processSerialCommand() {
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    
    if (command == "CALIBRATE_pH") {
      Serial.println("{\"type\":\"info\",\"message\":\"pH calibration started\"}");
      // Lógica de calibración...
    }
    else if (command == "STATUS") {
      Serial.println("{\"type\":\"status\",\"message\":\"System OK\"}");
    }
  }
}

/*
  NOTA SOBRE CALIBRACIÓN:
  
  1. CALIBRACIÓN DE pH:
     - Necesitas soluciones de calibración (pH 4, 7, 10)
     - Sumerge el sensor en solución pH 7
     - Anota el valor ADC
     - Sumerge en pH 4 y pH 10
     - Calcula la pendiente: (ADC_pH7 - ADC_pH4) / 3
  
  2. CALIBRACIÓN DE CONDUCTIVIDAD:
     - Usa soluciones de referencia conocidas
     - Ajusta el factor multiplicador en readConductivitySensor()
  
  3. CALIBRACIÓN DE TEMPERATURA:
     - El DS18B20 es muy preciso (no necesita calibración)
     - Solo verifica el offset si es necesario
*/

/*
  TROUBLESHOOTING:
  
  Problema: El sensor de pH no responde
  Solución: Verifica conexiones, asegúrate que A0 esté libre
  
  Problema: Temperatura siempre lee 85°C o -127°C
  Solución: Verifica conexión OneWire, instala librerías
  
  Problema: Valores de conductividad son constantes
  Solución: Verifica que A1 esté conectado, limpia el sensor
  
  Problema: No aparecen datos en el monitor serial
  Solución: Verifica baudrate (9600), revisa conexión USB
*/

// ============================================================================
// FIN DEL CÓDIGO
// ============================================================================
