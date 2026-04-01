/**
 * Configuración de conexión con Arduino/ESP8266
 * Este archivo contiene funciones para conectar el dashboard con la API FastAPI/MongoDB
 * 
 * Flujo: ESP8266 → API FastAPI → MongoDB → Frontend Vue.js
 */

// ============================================================================
// CONFIGURACIÓN
// ============================================================================

const API_BASE_URL = (import.meta.env.VITE_API_URL || '').replace(/\/$/, '')
const POLL_INTERVAL = 2000 // Polling cada 2 segundos

// ============================================================================
// OPCIÓN 1: Fetch API (Polling) - Obtener datos del dashboard desde MongoDB
// ============================================================================

/**
 * Obtener datos del dashboard desde la API FastAPI
 * Estos datos son actualizados por el ESP8266 en tiempo real
 */
export const fetchDashboardData = async (apiUrl = `${API_BASE_URL}/api/dashboard`) => {
  try {
    console.log('[API] Obteniendo datos del dashboard desde:', apiUrl)
    const response = await fetch(apiUrl)
    if (!response.ok) throw new Error(`HTTP ${response.status}`)
    const data = await response.json()
    console.log('[API] Datos recibidos:', data)
    return data
  } catch (error) {
    console.error('[API] Error obteniendo datos del dashboard:', error)
    return null
  }
}

/**
 * Obtener la última lectura de sensores desde MongoDB
 */
export const fetchLatestSensorReading = async (apiUrl = `${API_BASE_URL}/api/sensors/latest`) => {
  try {
    const response = await fetch(apiUrl)
    if (!response.ok) throw new Error(`HTTP ${response.status}`)
    const data = await response.json()
    return data
  } catch (error) {
    console.error('[API] Error obteniendo última lectura:', error)
    return null
  }
}

/**
 * Obtener historial de lecturas de sensores desde MongoDB
 */
export const fetchSensorHistory = async (limit = 100) => {
  try {
    const apiUrl = `${API_BASE_URL}/api/sensors/history?limit=${limit}`
    const response = await fetch(apiUrl)
    if (!response.ok) throw new Error(`HTTP ${response.status}`)
    const data = await response.json()
    return data
  } catch (error) {
    console.error('[API] Error obteniendo historial:', error)
    return []
  }
}

/**
 * Iniciar polling automático de datos del dashboard
 * Usa callback para actualizar datos en tiempo real
 */
export const startDashboardPolling = (callback, interval = POLL_INTERVAL) => {
  console.log('[API] Iniciando polling cada', interval, 'ms')
  
  // Primera lectura inmediata
  fetchDashboardData().then(data => {
    if (data) callback(data)
  })
  
  // Polling periódico
  const intervalId = setInterval(() => {
    fetchDashboardData().then(data => {
      if (data) callback(data)
    })
  }, interval)
  
  // Retornar ID para detener el polling
  return intervalId
}

/**
 * Detener polling automático
 */
export const stopDashboardPolling = (intervalId) => {
  if (intervalId) {
    clearInterval(intervalId)
    console.log('[API] Polling detenido')
  }
}

// Uso en App.vue:
// import { startDashboardPolling, stopDashboardPolling, fetchDashboardData } from '@/services/ArduinoConfig'
//
// const updateSensorData = (dashboardData) => {
//   sensors.value = {
//     ph: dashboardData.ph,
//     temperature: dashboardData.temperature,
//     conductivity: dashboardData.conductivity
//   }
//   lastSync.value = dashboardData.metadata.lastSync
// }
//
// let pollingId
// 
// onMounted(() => {
//   pollingId = startDashboardPolling(updateSensorData)
// })
//
// onUnmounted(() => {
//   stopDashboardPolling(pollingId)
// })

export default {
  fetchDashboardData,
  fetchLatestSensorReading,
  fetchSensorHistory,
  startDashboardPolling,
  stopDashboardPolling
}

