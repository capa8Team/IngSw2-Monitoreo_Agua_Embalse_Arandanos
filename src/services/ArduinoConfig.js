/**
 * Configuración de conexión con Arduino
 * Este archivo contiene ejemplos de cómo conectar el dashboard con datos reales del Arduino
 */

// ============================================================================
// OPCIÓN 1: Fetch API (Polling) - Recomendado para aplicaciones simples
// ============================================================================

export const fetchSensorData = async (apiUrl = 'http://localhost:3000/api/sensors') => {
  try {
    const response = await fetch(apiUrl)
    if (!response.ok) throw new Error('Error en la conexión')
    const data = await response.json()
    return data
  } catch (error) {
    console.error('Error fetching sensor data:', error)
    return null
  }
}

// Uso en App.vue:
// const updateSensorData = async () => {
//   const data = await fetchSensorData()
//   if (data) {
//     sensors.value = data
//   }
// }

// ============================================================================
// OPCIÓN 2: WebSocket - Recomendado para actualización en tiempo real
// ============================================================================

export class SensorWebSocketClient {
  constructor(wsUrl = 'ws://localhost:3000/sensors') {
    this.wsUrl = wsUrl
    this.ws = null
    this.listeners = []
  }

  connect() {
    return new Promise((resolve, reject) => {
      try {
        this.ws = new WebSocket(this.wsUrl)

        this.ws.onopen = () => {
          console.log('WebSocket conectado')
          resolve()
        }

        this.ws.onmessage = (event) => {
          const data = JSON.parse(event.data)
          this.notifyListeners(data)
        }

        this.ws.onerror = (error) => {
          console.error('Error WebSocket:', error)
          reject(error)
        }

        this.ws.onclose = () => {
          console.log('WebSocket desconectado')
          // Intentar reconectar después de 5 segundos
          setTimeout(() => this.connect(), 5000)
        }
      } catch (error) {
        reject(error)
      }
    })
  }

  subscribe(callback) {
    this.listeners.push(callback)
  }

  unsubscribe(callback) {
    this.listeners = this.listeners.filter(listener => listener !== callback)
  }

  notifyListeners(data) {
    this.listeners.forEach(listener => listener(data))
  }

  disconnect() {
    if (this.ws) {
      this.ws.close()
    }
  }
}

// Uso en App.vue:
// const wsClient = new SensorWebSocketClient()
// 
// onMounted(async () => {
//   await wsClient.connect()
//   wsClient.subscribe((data) => {
//     sensors.value = data
//   })
// })
//
// onUnmounted(() => {
//   wsClient.disconnect()
// })

// ============================================================================
// OPCIÓN 3: Socket.io - Más robusto y con fallbacks automáticos
// ============================================================================

import io from 'socket.io-client'

export class SensorSocketClient {
  constructor(serverUrl = 'http://localhost:3000') {
    this.socket = io(serverUrl, {
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
      reconnectionAttempts: 5
    })
  }

  connect() {
    return new Promise((resolve, reject) => {
      this.socket.on('connect', () => {
        console.log('Socket.io conectado')
        resolve()
      })

      this.socket.on('connect_error', (error) => {
        console.error('Error de conexión Socket.io:', error)
        reject(error)
      })
    })
  }

  onSensorUpdate(callback) {
    this.socket.on('sensor_data', callback)
  }

  disconnect() {
    this.socket.disconnect()
  }
}

// ============================================================================
// EJEMPLO DE BACKEND (Node.js + Express + Serial)
// ============================================================================

/*
// arduino-server.js
const express = require('express')
const SerialPort = require('serialport').SerialPort
const cors = require('cors')
const app = express()

app.use(cors())
app.use(express.json())

// Configurar puerto serial
const port = new SerialPort({
  path: '/dev/ttyACM0', // Cambiar según tu sistema (COM3 en Windows)
  baudRate: 9600
})

let sensorData = {
  ph: { value: 7.2, lastUpdated: new Date() },
  temperature: { value: 22.5, lastUpdated: new Date() },
  conductivity: { value: 650, lastUpdated: new Date() }
}

// Parser para datos del Arduino
port.on('data', (data) => {
  try {
    const line = data.toString().trim()
    const json = JSON.parse(line)
    
    // Actualizar datos del sensor
    if (json.type === 'pH') {
      sensorData.ph.value = json.value
      sensorData.ph.lastUpdated = new Date()
    } else if (json.type === 'temperature') {
      sensorData.temperature.value = json.value
      sensorData.temperature.lastUpdated = new Date()
    } else if (json.type === 'conductivity') {
      sensorData.conductivity.value = json.value
      sensorData.conductivity.lastUpdated = new Date()
    }
  } catch (error) {
    console.error('Error parsing Arduino data:', error)
  }
})

// Endpoint API
app.get('/api/sensors', (req, res) => {
  res.json(sensorData)
})

app.listen(3000, () => {
  console.log('Servidor ejecutándose en puerto 3000')
})
*/

// ============================================================================
// EJEMPLO DE CÓDIGO ARDUINO
// ============================================================================

/*
#include <DallasTemperature.h>
#include <OneWire.h>

// Pines
const int PH_PIN = A0;
const int TEMP_PIN = 2;
const int CONDUCTIVITY_PIN = A1;

// Variables
OneWire oneWire(TEMP_PIN);
DallasTemperature sensors(&oneWire);

void setup() {
  Serial.begin(9600);
  sensors.begin();
}

void loop() {
  // Leer pH
  int phRaw = analogRead(PH_PIN);
  float ph = 7.0 + (phRaw - 512) * 0.0049;
  
  // Leer temperatura
  sensors.requestTemperatures();
  float temperature = sensors.getTempCByIndex(0);
  
  // Leer conductividad
  int conductivityRaw = analogRead(CONDUCTIVITY_PIN);
  float conductivity = (conductivityRaw / 1023.0) * 2000;
  
  // Enviar datos en formato JSON
  Serial.print("{\"type\":\"pH\",\"value\":");
  Serial.print(ph);
  Serial.println("}");
  
  Serial.print("{\"type\":\"temperature\",\"value\":");
  Serial.print(temperature);
  Serial.println("}");
  
  Serial.print("{\"type\":\"conductivity\",\"value\":");
  Serial.print(conductivity);
  Serial.println("}");
  
  delay(3000); // Actualizar cada 3 segundos
}
*/

export default {
  fetchSensorData,
  SensorWebSocketClient,
  SensorSocketClient
}
