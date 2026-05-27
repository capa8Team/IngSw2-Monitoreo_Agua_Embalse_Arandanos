import { normalizeMongoRecord, normalizeHistoryRecord, buildFallbackReadings } from '../utils/sensorUtils.js'

function resolveApiBase() {
  const raw = import.meta.env.VITE_API_URL
  if (raw == null || String(raw).trim() === '') return ''
  return String(raw).replace(/\/$/, '')
}

export async function fetchSensorReadings() {
  const api = resolveApiBase()
  try {
    const mongoRes = await fetch(`${api}/api/data/mongodb`)
    if (mongoRes.ok) {
      const payload = await mongoRes.json()
      if (!payload.error && Array.isArray(payload.data) && payload.data.length > 0)
        return payload.data.map(normalizeMongoRecord)
    }
    const histRes = await fetch(`${api}/api/sensors/history?limit=500`)
    if (histRes.ok) {
      const payload = await histRes.json()
      if (Array.isArray(payload) && payload.length > 0)
        return payload.map(normalizeHistoryRecord)
    }
  } catch { /* network error → fallback */ }
  return buildFallbackReadings()
}

export async function fetchDashboardSnapshot() {
  const api = resolveApiBase()
  const res = await fetch(`${api}/api/dashboard`)
  if (!res.ok) throw new Error(`Dashboard API error ${res.status}`)
  return res.json()
}

/** Dispositivos activos registrados (para filtros PDF / histórico). */
export async function fetchActiveDevices() {
  const api = resolveApiBase()
  try {
    const res = await fetch(`${api}/api/devices`)
    if (!res.ok) return []
    const data = await res.json()
    if (!Array.isArray(data)) return []
    return data.filter((d) => d.active !== false)
  } catch {
    return []
  }
}
