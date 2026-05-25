/* 
   Basic pH Sensor Reading
   Connect Sensor Po to A0
*/
#include <OneWire.h>
#include <DallasTemperature.h>

#define ONE_WIRE_BUS 1

OneWire oneWire(ONE_WIRE_BUS);

DallasTemperature sensors(&oneWire);


float calibration = 21.50; //change this value to calibrate
const int analogInPin = A0;
int sensorValue = 0;
unsigned long int avgValue;
float b;
int buf[10],temp;


void setup() {
  Serial.begin(9600);
  sensors.begin();
}

void loop() {
  for(int i=0;i<10;i++)
    {
    buf[i]=analogRead(analogInPin);
    delay(30);
    }
  for(int i=0;i<9;i++)
  {
    for(int j=i+1;j<10;j++)
    {
      if(buf[i]>buf[j])
        {
        temp=buf[i];
        buf[i]=buf[j];
        buf[j]=temp;
        }
    }
  }
  avgValue=0;
  for(int i=2;i<8;i++)
  avgValue+=buf[i];
  float pHVol=(float)avgValue*5.0/1024/6;
  float phValue = -5.70 * pHVol + calibration;
  Serial.print("sensor = ");
  Serial.println(abs(phValue));
  sensors.requestTemperatures(); 
  Serial.print("  Celsius temperature: ");
  // Why "byIndex"? You can have more than one IC on the same bus. 0 refers to the first IC on the wire
  Serial.print(sensors.getTempCByIndex(1));
  Serial.print("\n");
  delay(1000); // Wait 1 second
}