/**
 * Configuración de conexión con Arduino/ESP8266
 * Funciones para conectar el dashboard con la API FastAPI/MongoDB
 *
 * Flujo: ESP8266 → API FastAPI → MongoDB → Frontend Vue.js
 */

// ============================================================================
// CONFIGURACIÓN
// ============================================================================

const API_BASE_URL = (import.meta.env.VITE_API_URL || '').replace(/\/$/, '')
const RAW_DATA_MODE = String(import.meta.env.VITE_DATA_MODE ?? 'real').trim().toLowerCase()
export const DATA_MODE = RAW_DATA_MODE === 'simulated' ? 'simulated' : 'real'
export const IS_SIMULATED_MODE = DATA_MODE === 'simulated'

const SIM_LIMITS = {
  ph:           { min: 6.0, max: 8.5,  safeMax: 8.0  },
  temperature:  { min: 5,   max: 35,   safeMax: 28   },
  conductivity: { min: 100, max: 2000, safeMax: 1500 },
}

const SIMULATION_START_TIME = Date.now()

// ============================================================================
// HELPERS DE SIMULACIÓN (solo activos cuando VITE_DATA_MODE=simulated)
// ============================================================================

const clamp     = (value, min, max) => Math.max(min, Math.min(max, value))
const withNoise = (value, amount)   => value + (Math.random() - 0.5) * 2 * amount

const getWave = (timestampMs, periodSeconds, phase = 0) =>
  Math.sin((timestampMs / 1000) * (2 * Math.PI / periodSeconds) + phase)

const getSensorStatus = (value, min, max) => {
  if (value < min || value > max) return 'critical'
  const margin = (max - min) * 0.15
  if (value < min + margin || value > max - margin) return 'warning'
  return 'stable'
}

const generateSyntheticReading = (timestampMs = Date.now()) => {
  const phBase           = 7.1 + getWave(timestampMs, 180, 0.3) * 0.45 + getWave(timestampMs, 47,  1.1) * 0.08
  const tempBase         = 22  + getWave(timestampMs, 240, 1.6) * 3.2  + getWave(timestampMs, 31,  0.4) * 0.25
  const conductivityBase = 900 + getWave(timestampMs, 210, 2.2) * 230  + getWave(timestampMs, 29,  0.9) * 22
  return {
    ph:           Number(clamp(withNoise(phBase,           0.03), 5.8,  8.7 ).toFixed(2)),
    temperature:  Number(clamp(withNoise(tempBase,         0.12), 4,    36  ).toFixed(2)),
    conductivity: Number(clamp(withNoise(conductivityBase, 8),    100,  2000).toFixed(2)),
    timestamp: timestampMs,
  }
}

const buildSimulatedDashboard = () => {
  const reading = generateSyntheticReading(Date.now())
  const nowIso  = new Date(reading.timestamp).toISOString()
  const uptime  = Math.floor((Date.now() - SIMULATION_START_TIME) / 1000)

  const sensor = (key) => ({
    value:       reading[key],
    min:         SIM_LIMITS[key].min,
    max:         SIM_LIMITS[key].max,
    safeMax:     SIM_LIMITS[key].safeMax,
    lastUpdated: nowIso,
    status:      getSensorStatus(reading[key], SIM_LIMITS[key].min, SIM_LIMITS[key].max),
  })

  return {
    ph:           sensor('ph'),
    temperature:  sensor('temperature'),
    conductivity: sensor('conductivity'),
    metadata: {
      systemStatus:     'operational',
      arduinoConnected: true,
      lastSync:         nowIso,
      uptime,
      activeSensors:    3,
    },
    battery: Math.min(100, Math.max(20, 75 + Math.random() * 20)),
  }
}

// ============================================================================
// API CALLS
// ============================================================================

export const fetchDashboardData = async (apiUrl = `${API_BASE_URL}/api/dashboard`) => {
  if (IS_SIMULATED_MODE) return buildSimulatedDashboard()

  try {
    const response = await fetch(apiUrl)
    if (!response.ok) throw new Error(`HTTP ${response.status}`)
    return await response.json()
  } catch (error) {
    console.error('[API] Error obteniendo datos del dashboard:', error)
    return null
  }
}

export const fetchSensorHistory = async (limit = 100) => {
  if (IS_SIMULATED_MODE) {
    const maxRows = Math.max(1, Number(limit) || 100)
    const now     = Date.now()
    return Array.from({ length: maxRows }, (_, i) => generateSyntheticReading(now - i * 60_000))
  }

  try {
    const response = await fetch(`${API_BASE_URL}/api/sensors/history?limit=${limit}`)
    if (!response.ok) throw new Error(`HTTP ${response.status}`)
    return await response.json()
  } catch (error) {
    console.error('[API] Error obteniendo historial:', error)
    return []
  }
}

export default {
  DATA_MODE,
  IS_SIMULATED_MODE,
  fetchDashboardData,
  fetchSensorHistory,
}
