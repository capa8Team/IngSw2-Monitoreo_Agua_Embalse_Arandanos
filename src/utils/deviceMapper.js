import { getDeviceTelemetryKeys } from './sensorUtils.js'

/**
 * Convierte dispositivos del API (MongoDB) al formato usado por DeviceCard / DeviceDashboard.
 */

const DEVICE_TYPE_LABELS = {
  ESP8266: 'ESP8266 (WiFi)',
  Arduino: 'Arduino',
  STM32: 'STM32',
  other: 'Otro',
}

export function mapApiStatusToCard(status) {
  if (status === 'online') return 'connected'
  if (status === 'offline') return 'disconnected'
  return 'disconnected'
}

export function mapApiDeviceToCard(apiDevice, { dataSource = 'real', groups = [] } = {}) {
  const id = apiDevice.id ?? apiDevice._id
  const deviceType = apiDevice.device_type || 'ESP8266'
  const label = DEVICE_TYPE_LABELS[deviceType] || deviceType
  const location = apiDevice.location ? ` — ${apiDevice.location}` : ''
  const group = groups.find((g) => g.id === apiDevice.group_id)
  const groupLabel = group ? ` · ${group.name}` : ''

  return {
    id,
    name: apiDevice.name || 'Dispositivo sin nombre',
    model: `${label}${location}${groupLabel}`,
    device_type: deviceType,
    location: apiDevice.location || '',
    city: apiDevice.city || '',
    group_id: apiDevice.group_id || null,
    group_name: group?.name || null,
    latitude: apiDevice.latitude ?? null,
    longitude: apiDevice.longitude ?? null,
    arduino_id: apiDevice.arduino_id || null,
    telemetry_key: apiDevice.telemetry_key || null,
    telemetryQueryKey: getDeviceTelemetryKeys(apiDevice)[0] || null,
    topic: apiDevice.topic || null,
    status: mapApiStatusToCard(apiDevice.status),
    lastUpdate: apiDevice.last_sync ? formatRelativeSync(apiDevice.last_sync) : 'Sin datos',
    battery: typeof apiDevice.battery === 'number' ? apiDevice.battery : 100,
    sensors: { ph: 0, temperature: 0, conductivity: 0 },
    dataSource,
    active: apiDevice.active !== false,
  }
}

export function mergeCardWithTelemetry(card, telemetry) {
  if (!telemetry) return card
  return {
    ...card,
    ...telemetry,
    sensors: telemetry.sensors ?? card.sensors,
  }
}

export function buildDefaultSimulatedCard() {
  return {
    id: 'sim-default',
    name: 'ESP8266 Embalse (simulado)',
    model: 'ESP8266 (WiFi) — modo simulado',
    device_type: 'ESP8266',
    location: '',
    arduino_id: 'sim-1',
    topic: null,
    status: 'connected',
    lastUpdate: 'En vivo',
    battery: 100,
    sensors: { ph: 0, temperature: 0, conductivity: 0 },
    dataSource: 'simulated',
    active: true,
  }
}

function formatRelativeSync(isoOrDate) {
  const date = typeof isoOrDate === 'string' ? new Date(isoOrDate) : isoOrDate
  if (Number.isNaN(date?.getTime())) return 'Sin datos'
  const diffSec = Math.max(0, Math.floor((Date.now() - date.getTime()) / 1000))
  if (diffSec < 60) return `hace ${diffSec}s`
  return `hace ${Math.floor(diffSec / 60)}m`
}

export function applyDashboardToTelemetry(dashboard, dataSource = 'real') {
  if (!dashboard) return null
  return {
    status: dashboard.metadata?.arduinoConnected ? 'connected' : 'disconnected',
    lastUpdate: dashboard.metadata?.lastSync
      ? formatRelativeSync(dashboard.metadata.lastSync)
      : 'Sin datos',
    sensors: {
      ph: Number(dashboard.ph?.value ?? 0),
      temperature: Number(dashboard.temperature?.value ?? 0),
      conductivity: Number(dashboard.conductivity?.value ?? 0),
    },
    battery: dashboard.battery ?? 100,
    bateria: dashboard.battery ?? 100,
    dataSource,
  }
}
