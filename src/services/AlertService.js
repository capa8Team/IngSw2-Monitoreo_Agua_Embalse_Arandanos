/**
 * Servicio para enviar alertas al backend cuando sensores estén fuera de rango
 */

const API_BASE_URL = (import.meta.env.VITE_API_URL || '').replace(/\/$/, '')
const DATA_MODE = String(import.meta.env.VITE_DATA_MODE ?? 'real').trim().toLowerCase()
const IS_SIMULATED_MODE = DATA_MODE === 'simulated'
const API_URL = `${API_BASE_URL}/api/alerts`

export const sendAlertToBackend = async (deviceName, sensor, value, measurement, min, max) => {
  if (IS_SIMULATED_MODE) {
    return null
  }

  try {
    const payload = {
      embalse: deviceName,
      nombreDispositivo: deviceName,
      sensor: sensor,
      medicion: measurement,
      valor: value,
      minimo: min,
      maximo: max
    }

    const response = await fetch(API_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload)
    })

    if (!response.ok) {
      console.error(`Error enviando alerta: ${response.status}`)
      return null
    }

    const data = await response.json()
    console.log('Alerta enviada al backend:', data)
    return data
  } catch (error) {
    console.error('Error en sendAlertToBackend:', error)
    return null
  }
}

export const checkAndSendAlerts = async (device, sensorLimits) => {
  if (IS_SIMULATED_MODE) {
    return
  }

  const ph = device.sensors.ph
  const temperature = device.sensors.temperature
  const conductivity = device.sensors.conductivity

  // Función auxiliar para determinar el nivel de riesgo
  const getAlertLevel = (value, limits) => {
    const { danger_min, danger_max, warning_min, warning_max, safe_min, safe_max } = limits
    
    if (value >= safe_min && value <= safe_max) {
      return 'safe'
    } else if (value >= warning_min && value <= warning_max) {
      return 'warning'
    } else if (value >= danger_min && value <= danger_max) {
      return 'danger'
    } else {
      return 'danger' // Completamente fuera
    }
  }

  // Verificar pH
  const phLevel = getAlertLevel(ph, sensorLimits.ph)
  if (phLevel !== 'safe') {
    await sendAlertToBackend(
      device.name,
      'pH',
      ph,
      `${ph.toFixed(2)} pH (${phLevel})`,
      sensorLimits.ph.safe_min,
      sensorLimits.ph.safe_max
    )
  }

  // Verificar Temperatura
  const tempLevel = getAlertLevel(temperature, sensorLimits.temperature)
  if (tempLevel !== 'safe') {
    await sendAlertToBackend(
      device.name,
      'Temperatura',
      temperature,
      `${temperature.toFixed(2)} °C (${tempLevel})`,
      sensorLimits.temperature.safe_min,
      sensorLimits.temperature.safe_max
    )
  }

  // Verificar Conductividad
  const condLevel = getAlertLevel(conductivity, sensorLimits.conductivity)
  if (condLevel !== 'safe') {
    await sendAlertToBackend(
      device.name,
      'Conductividad Eléctrica',
      conductivity,
      `${conductivity.toFixed(0)} µS/cm (${condLevel})`,
      sensorLimits.conductivity.safe_min,
      sensorLimits.conductivity.safe_max
    )
  }
}

export default {
  sendAlertToBackend,
  checkAndSendAlerts
}
