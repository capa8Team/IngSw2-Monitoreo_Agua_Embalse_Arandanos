// Sensor de pH simple - lectura y calibración
// Modificar `calibration` para ajustar la calibración del sensor

const float CALIBRATION  = 31.6;
const int   ANALOG_PIN   = A0;
const int   SAMPLE_COUNT = 10;

int           buf[SAMPLE_COUNT];
int           temp;
unsigned long avgValue;

void setup() {
  Serial.begin(9600);
}

void loop() {
  // Tomar muestras
  for (int i = 0; i < SAMPLE_COUNT; i++) {
    buf[i] = analogRead(ANALOG_PIN);
    delay(30);
  }

  // Ordenar muestras (bubble sort)
  for (int i = 0; i < SAMPLE_COUNT - 1; i++) {
    for (int j = i + 1; j < SAMPLE_COUNT; j++) {
      if (buf[i] > buf[j]) {
        temp   = buf[i];
        buf[i] = buf[j];
        buf[j] = temp;
      }
    }
  }

  // Promediar las 6 muestras centrales (descartar extremos)
  avgValue = 0;
  for (int i = 2; i < 8; i++) {
    avgValue += buf[i];
  }

  float pHVol   = (float)avgValue * 5.0 / 1024.0 / 6.0;
  float phValue = -5.70 * pHVol + CALIBRATION;

  Serial.print("pH = ");
  Serial.println(phValue);

  delay(500);
}
