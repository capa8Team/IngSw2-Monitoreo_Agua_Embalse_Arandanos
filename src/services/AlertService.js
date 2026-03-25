/**
 * Servicio para enviar alertas al backend cuando sensores estén fuera de rango
 */

const API_URL = 'http://localhost:8000/api/alerts'

export const sendAlertToBackend = async (deviceName, sensor, value, measurement, min, max) => {
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
  const ph = device.sensors.ph
  const temperature = device.sensors.temperature
  const conductivity = device.sensors.conductivity

  // Verificar pH
  if (ph < sensorLimits.ph.min || ph > sensorLimits.ph.max) {
    await sendAlertToBackend(
      device.name,
      'pH',
      ph,
      `${ph.toFixed(2)} pH`,
      sensorLimits.ph.min,
      sensorLimits.ph.max
    )
  }

  // Verificar Temperatura
  if (temperature < sensorLimits.temperature.min || temperature > sensorLimits.temperature.max) {
    await sendAlertToBackend(
      device.name,
      'Temperatura',
      temperature,
      `${temperature.toFixed(2)} °C`,
      sensorLimits.temperature.min,
      sensorLimits.temperature.max
    )
  }

  // Verificar Conductividad
  if (conductivity < sensorLimits.conductivity.min || conductivity > sensorLimits.conductivity.max) {
    await sendAlertToBackend(
      device.name,
      'Conductividad Eléctrica',
      conductivity,
      `${conductivity.toFixed(0)} µS/cm`,
      sensorLimits.conductivity.min,
      sensorLimits.conductivity.max
    )
  }
}

export default {
  sendAlertToBackend,
  checkAndSendAlerts
}
