import { ref } from 'vue'
import { buildDefaultSimulatedCard } from './deviceMapper.js'
import { resolveGroupAssignment } from './deviceGroupAssignment.js'
import { SIMULATED_HISTORICAL_DEVICE } from '../services/ArduinoConfig.js'

export const SIMULATED_DEVICE_ID = 'sim-default'
const STORAGE_KEY = 'simulatedDeviceOverrides'

/** Incrementa al guardar overrides para refrescar vistas reactivas. */
export const simulatedDeviceVersion = ref(0)

export function isSimulatedDeviceId(deviceId) {
  return String(deviceId || '').trim() === SIMULATED_DEVICE_ID
}

export function isSimulatedDevice(device) {
  if (!device) return false
  return isSimulatedDeviceId(device.id) || device.dataSource === 'simulated'
}

export function readSimulatedDeviceOverrides() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return {}
    const parsed = JSON.parse(raw)
    return parsed && typeof parsed === 'object' ? parsed : {}
  } catch {
    return {}
  }
}

export function writeSimulatedDeviceOverrides(updates) {
  const current = readSimulatedDeviceOverrides()
  const next = { ...current, ...updates }
  localStorage.setItem(STORAGE_KEY, JSON.stringify(next))
  simulatedDeviceVersion.value += 1
  return next
}

export function getSimulatedDeviceCard() {
  const overrides = readSimulatedDeviceOverrides()
  const base = buildDefaultSimulatedCard()
  const card = {
    ...base,
    ...overrides,
    id: SIMULATED_DEVICE_ID,
    dataSource: 'simulated',
    active: true,
  }
  const label = card.device_type === 'ESP8266' ? 'ESP8266 (WiFi)' : card.device_type
  const location = card.location ? ` — ${card.location}` : ''
  card.model = `${label}${location} — simulado`
  card.name = card.name || base.name
  return card
}

export async function saveSimulatedDeviceFromForm(formPayload, deviceGroupStore) {
  const assignment = await resolveGroupAssignment(formPayload.groupSelection, deviceGroupStore)
  writeSimulatedDeviceOverrides({
    name: formPayload.name,
    location: formPayload.location || '',
    city: formPayload.city || '',
    arduino_id: formPayload.arduino_id || null,
    telemetry_key: formPayload.telemetry_key || null,
    topic: formPayload.topic || null,
    group_id: assignment.group_id,
    latitude: assignment.latitude,
    longitude: assignment.longitude,
  })
}

/** Dispositivo registrado para exportación PDF / histórico en modo simulado. */
export function getSimulatedExportDevice() {
  const card = getSimulatedDeviceCard()
  return {
    id: card.id,
    name: card.name || 'ESP8266 Embalse (simulado)',
    arduino_id: SIMULATED_HISTORICAL_DEVICE,
    telemetry_key: SIMULATED_HISTORICAL_DEVICE,
    topic: card.topic || null,
    active: true,
  }
}
