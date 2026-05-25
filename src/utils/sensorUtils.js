export const SENSOR_META = {
  ph:           { label: 'pH',                  unit: '',      min: 6,   max: 8.5  },
  temperature:  { label: 'Temperatura',         unit: '°C',    min: 15,  max: 30   },
  conductivity: { label: 'Conductividad',       unit: 'µS/cm', min: 700, max: 1600 },
}

export function localDateKey(date) {
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

export function parseTimestamp(value) {
  if (typeof value === 'number' || (typeof value === 'string' && /^\d+$/.test(value))) {
    const n = Number(value)
    return new Date(n > 9_999_999_999 ? n : n * 1000)
  }
  const parsed = new Date(value)
  return Number.isNaN(parsed.getTime()) ? new Date() : parsed
}

export function getAlertStatus(sensorKey, value) {
  const meta = SENSOR_META[sensorKey]
  if (!meta) return { status: 'Normal', cssClass: 'normal' }
  const out = value < meta.min || value > meta.max
  return { status: out ? 'Alerta' : 'Normal', cssClass: out ? 'warning' : 'normal' }
}

export function measurementText(sensorKey, value) {
  const unit = SENSOR_META[sensorKey]?.unit || ''
  return unit ? `${value.toFixed(2)} ${unit}` : value.toFixed(2)
}

export function normalizeMongoRecord(record) {
  const m = record.mediciones || {}
  return {
    device:       record.arduino_id || record.embalse || 'simulador-arandanos',
    timestamp:    parseTimestamp(record.timestamp),
    ph:           Number(record.ph          ?? m.ph),
    temperature:  Number(record.temperature ?? m.temperatura),
    conductivity: Number(record.conductivity ?? m.conductividad),
  }
}

export function normalizeHistoryRecord(record) {
  return {
    device:       'simulador-arandanos',
    timestamp:    parseTimestamp(record.timestamp),
    ph:           Number(record.ph),
    temperature:  Number(record.temperature),
    conductivity: Number(record.conductivity),
  }
}

export function buildFallbackReadings() {
  const now = Date.now()
  return Array.from({ length: 40 }, (_, i) => ({
    device:       'simulador-arandanos',
    timestamp:    new Date(now - i * 30_000),
    ph:           7.0 + (Math.random() - 0.5) * 0.3,
    temperature:  22  + (Math.random() - 0.5) * 1.5,
    conductivity: 950 + (Math.random() - 0.5) * 80,
  }))
}

export function flattenMeasurements(records) {
  const rows = []
  for (const record of records) {
    const ts       = parseTimestamp(record.timestamp)
    const dateText = ts.toLocaleDateString('es-CL')
    const dateKey  = localDateKey(ts)
    const timeText = ts.toLocaleTimeString('es-CL', { hour: '2-digit', minute: '2-digit', second: '2-digit' })

    for (const [key, meta] of Object.entries(SENSOR_META)) {
      const value = Number(record[key])
      if (!Number.isFinite(value)) continue
      const alert = getAlertStatus(key, value)
      rows.push({
        key:             `${record.device}-${key}-${ts.getTime()}`,
        device:          record.device,
        sensorKey:       key,
        sensorLabel:     meta.label,
        rawValue:        value,
        measurementText: measurementText(key, value),
        dateText, dateKey, timeText,
        timestamp:       ts,
        alertStatus:     alert.status,
        alertClass:      alert.cssClass,
      })
    }
  }
  return rows.sort((a, b) => b.timestamp - a.timestamp)
}

export function downsampleRows(rows, maxPoints) {
  if (rows.length <= maxPoints) return rows
  const step = Math.ceil(rows.length / maxPoints)
  return Array.from({ length: Math.ceil(rows.length / step) }, (_, i) => rows[i * step]).slice(-maxPoints)
}

export function getAlertLevel(value, limits) {
  const { danger_min, danger_max, warning_min, warning_max, safe_min, safe_max } = limits
  if (value >= safe_min && value <= safe_max) return 'safe'
  if (value >= warning_min && value <= warning_max) return 'warning'
  if (value >= danger_min && value <= danger_max) return 'danger'
  return 'danger'
}
