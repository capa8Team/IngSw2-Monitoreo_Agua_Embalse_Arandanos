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

/** Claves con las que llegan lecturas MQTT para un dispositivo registrado. */
export function getDeviceTelemetryKeys(device) {
  const keys = []
  const telemetryKey = String(device?.telemetry_key ?? '').trim()
  const arduinoId = String(device?.arduino_id ?? '').trim()
  const name = String(device?.name ?? '').trim()

  if (telemetryKey) keys.push(telemetryKey)
  if (arduinoId && !keys.includes(arduinoId)) keys.push(arduinoId)
  if (!telemetryKey && !arduinoId && name) keys.push(name)

  return keys
}

export function readingMatchesDeviceTelemetry(readingKey, device) {
  const rk = String(readingKey ?? '').trim()
  if (!rk) return false
  return getDeviceTelemetryKeys(device).some(
    (k) => rk === k || rk.startsWith(`${k}-`),
  )
}

export function isReadingFromRegisteredDevice(readingKey, registeredDevices = []) {
  if (!registeredDevices.length) return true
  return registeredDevices.some((d) => readingMatchesDeviceTelemetry(readingKey, d))
}

/**
 * Réplicas con el mismo topic (p. ej. Norte + Dispositivo 1) comparten lecturas.
 * Cada fila usa el ``name`` del dispositivo para filtros PDF / tabla.
 */
export function expandReadingsForRegisteredDevices(records, registeredDevices = []) {
  if (!registeredDevices.length) return records

  const peersByTopic = new Map()
  for (const device of registeredDevices) {
    const topic = String(device.topic ?? '').trim()
    if (!topic) continue
    if (!peersByTopic.has(topic)) peersByTopic.set(topic, [])
    peersByTopic.get(topic).push(device)
  }

  const deviceId = (d) => String(d.id ?? d._id ?? d.name ?? '')

  const output = []
  for (const record of records) {
    let targets = registeredDevices.filter((d) =>
      readingMatchesDeviceTelemetry(record.device, d),
    )
    if (!targets.length) continue

    const topicSet = new Set(
      targets.map((d) => String(d.topic ?? '').trim()).filter(Boolean),
    )
    for (const topic of topicSet) {
      const peers = peersByTopic.get(topic) ?? []
      const merged = new Map(targets.map((d) => [deviceId(d), d]))
      for (const peer of peers) merged.set(deviceId(peer), peer)
      targets = [...merged.values()]
    }

    for (const device of targets) {
      const displayName = String(device.name ?? '').trim()
      if (!displayName) continue
      output.push({ ...record, device: displayName })
    }
  }

  return output.sort((a, b) => b.timestamp - a.timestamp)
}

/** Una lectura física por timestamp+origen (evita duplicar en gráficos). */
export function readingsForCharts(records, registeredDevices = []) {
  if (!registeredDevices.length) return records

  const seen = new Set()
  const out = []
  for (const record of records) {
    if (!isReadingFromRegisteredDevice(record.device, registeredDevices)) continue
    const ts = record.timestamp instanceof Date
      ? record.timestamp.getTime()
      : new Date(record.timestamp).getTime()
    const dedupeKey = `${ts}:${String(record.device).trim()}`
    if (seen.has(dedupeKey)) continue
    seen.add(dedupeKey)
    out.push(record)
  }
  return out.sort((a, b) => b.timestamp - a.timestamp)
}

export function downsampleRows(rows, maxPoints) {
  if (rows.length <= maxPoints) return rows
  const step = Math.ceil(rows.length / maxPoints)
  return Array.from({ length: Math.ceil(rows.length / step) }, (_, i) => rows[i * step]).slice(-maxPoints)
}

function formatChartLabel(timestampMs, period) {
  const d = new Date(timestampMs)
  if (period === 'hour' || period === 'day') {
    return d.toLocaleTimeString('es-CL', { hour: '2-digit', minute: '2-digit' })
  }
  return d.toLocaleDateString('es-CL', { weekday: 'short', day: '2-digit', month: '2-digit' })
}

function chartWindowStartMs(period, now = Date.now()) {
  if (period === 'hour') return now - 60 * 60 * 1000
  if (period === 'day') return now - 24 * 60 * 60 * 1000
  const start = new Date()
  start.setHours(0, 0, 0, 0)
  start.setDate(start.getDate() - 6)
  return start.getTime()
}

function maxSparsePointsForPeriod(period) {
  if (period === 'hour') return 120
  if (period === 'day') return 80
  return 40
}

function buildEmptyBucketSeries(period) {
  const now = Date.now()
  if (period === 'hour') {
    const startMs = now - 60 * 60 * 1000
    const bucketMs = 5 * 60 * 1000
    const labels = []
    for (let i = 0; i < 12; i++) {
      const t = new Date(startMs + i * bucketMs)
      labels.push(formatChartLabel(t.getTime(), 'hour'))
    }
    return { labels, values: Array(12).fill(null) }
  }
  if (period === 'day') {
    const startMs = now - 24 * 60 * 60 * 1000
    const labels = []
    for (let i = 0; i < 24; i++) {
      const t = new Date(startMs + i * 60 * 60 * 1000)
      labels.push(`${String(t.getHours()).padStart(2, '0')}:00`)
    }
    return { labels, values: Array(24).fill(null) }
  }
  const start = new Date()
  start.setHours(0, 0, 0, 0)
  start.setDate(start.getDate() - 6)
  const labels = []
  for (let i = 0; i < 7; i++) {
    const d = new Date(start)
    d.setDate(start.getDate() + i)
    labels.push(d.toLocaleDateString('es-ES', { weekday: 'short' }))
  }
  return { labels, values: Array(7).fill(null) }
}

function buildBucketedSeries(points, period, now) {
  const labels = []
  const buckets = []

  if (period === 'hour') {
    const startMs = now - 60 * 60 * 1000
    const bucketMs = 5 * 60 * 1000
    for (let i = 0; i < 12; i++) {
      const t = new Date(startMs + i * bucketMs)
      labels.push(formatChartLabel(t.getTime(), 'hour'))
      buckets.push([])
    }
    for (const p of points) {
      if (p.t < startMs || p.t > now) continue
      const idx = Math.min(11, Math.floor((p.t - startMs) / bucketMs))
      buckets[idx].push(p.v)
    }
  } else if (period === 'day') {
    const startMs = now - 24 * 60 * 60 * 1000
    const bucketMs = 60 * 60 * 1000
    for (let i = 0; i < 24; i++) {
      const t = new Date(startMs + i * bucketMs)
      labels.push(`${String(t.getHours()).padStart(2, '0')}:00`)
      buckets.push([])
    }
    for (const p of points) {
      if (p.t < startMs || p.t > now) continue
      const idx = Math.min(23, Math.floor((p.t - startMs) / bucketMs))
      buckets[idx].push(p.v)
    }
  } else {
    const start = new Date()
    start.setHours(0, 0, 0, 0)
    start.setDate(start.getDate() - 6)
    const startMs = start.getTime()

    for (let i = 0; i < 7; i++) {
      const d = new Date(start)
      d.setDate(start.getDate() + i)
      labels.push(d.toLocaleDateString('es-ES', { weekday: 'short' }))
      buckets.push([])
    }

    for (const p of points) {
      const dayStart = new Date(p.t)
      dayStart.setHours(0, 0, 0, 0)
      const t = dayStart.getTime()
      if (t < startMs) continue
      const dayIndex = Math.round((t - startMs) / (24 * 60 * 60 * 1000))
      if (dayIndex < 0 || dayIndex > 6) continue
      buckets[dayIndex].push(p.v)
    }
  }

  const values = buckets.map((arr) =>
    (arr.length ? arr.reduce((a, b) => a + b, 0) / arr.length : null),
  )
  return { labels, values }
}

/**
 * Series para gráficos históricos: puntos reales (pocas lecturas) o promedios por bucket.
 */
export function buildChartSeriesFromReadings(readings, sensorKey, period) {
  const now = Date.now()
  const windowStartMs = chartWindowStartMs(period, now)

  const points = readings
    .map((r) => ({
      t: parseTimestamp(r.timestamp).getTime(),
      v: Number(r[sensorKey]),
    }))
    .filter((p) => Number.isFinite(p.v) && Number.isFinite(p.t))
    .sort((a, b) => a.t - b.t)

  if (!points.length) {
    return buildEmptyBucketSeries(period)
  }

  let inWindow = points.filter((p) => p.t >= windowStartMs && p.t <= now)

  const maxSparsePoints = maxSparsePointsForPeriod(period)
  if (!inWindow.length) {
    inWindow = points.slice(-maxSparsePoints)
  }

  if (inWindow.length <= maxSparsePoints) {
    return {
      labels: inWindow.map((p) => formatChartLabel(p.t, period)),
      values: inWindow.map((p) => p.v),
    }
  }

  return buildBucketedSeries(inWindow, period, now)
}

export function computeChartStats(values, sensorKey) {
  const meta = SENSOR_META[sensorKey]
  const nums = values.filter((v) => Number.isFinite(v))
  if (!nums.length) {
    const mid = (meta.min + meta.max) / 2
    return { max: meta.max, min: meta.min, avg: mid }
  }
  return {
    max: Math.max(...nums),
    min: Math.min(...nums),
    avg: nums.reduce((a, b) => a + b, 0) / nums.length,
  }
}

export function getAlertLevel(value, limits) {
  const { danger_min, danger_max, warning_min, warning_max, safe_min, safe_max } = limits
  if (value >= safe_min && value <= safe_max) return 'safe'
  if (value >= warning_min && value <= warning_max) return 'warning'
  if (value >= danger_min && value <= danger_max) return 'danger'
  return 'danger'
}
