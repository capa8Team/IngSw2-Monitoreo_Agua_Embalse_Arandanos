import { getApiAuthHeaders } from './apiContext.js'
import {
  IS_SIMULATED_MODE,
  buildSimulatedHistoricalReadings,
  buildSimulatedIncrementalReadings,
  getSimulatedHistoricalDevices,
} from './ArduinoConfig.js'
import {
  normalizeHistoryRecord,
  buildFallbackReadings,
  flattenMeasurements,
  expandReadingsForRegisteredDevices,
  readingsForCharts,
  parseTimestamp,
} from '../utils/sensorUtils.js'

const POLL_INTERVAL_MS = 10_000
const CHART_LOOKBACK_DAYS = 7
const CHART_FETCH_LIMIT = 500
const INCREMENTAL_LIMIT = 100
const TABLE_LIVE_PAGE_SIZE = 10

function resolveApiBase() {
  const raw = import.meta.env.VITE_API_URL
  if (raw == null || String(raw).trim() === '') return ''
  return String(raw).replace(/\/$/, '')
}

function normalizeRangeRecord(record) {
  return {
    device:       record.arduino_id || record.device || 'simulador-arandanos',
    timestamp:    parseTimestamp(record.timestamp),
    ph:           Number(record.ph),
    temperature:  Number(record.temperature),
    conductivity: Number(record.conductivity),
  }
}

function normalizeTableRow(row) {
  return {
    ...row,
    timestamp: parseTimestamp(row.timestamp),
  }
}

function filterFlattenedRows(rows, { sensor = 'all', dateFrom = null, dateTo = null } = {}) {
  return rows.filter((row) => {
    if (sensor !== 'all' && row.sensorKey !== sensor) return false
    if (dateFrom && row.dateKey < dateFrom) return false
    if (dateTo && row.dateKey > dateTo) return false
    return true
  })
}

function buildSimulatedTablePage({
  page = 1,
  pageSize = 10,
  sensor = 'all',
  dateFrom = null,
  dateTo = null,
  registeredDevices = [],
} = {}) {
  const records = buildSimulatedHistoricalReadings({
    days: CHART_LOOKBACK_DAYS,
    limit: CHART_FETCH_LIMIT,
  })
  const expanded = expandReadingsForRegisteredDevices(records, registeredDevices)
  const allRows = filterFlattenedRows(flattenMeasurements(expanded), {
    sensor,
    dateFrom,
    dateTo,
  })
  const total = allRows.length
  const start = (page - 1) * pageSize
  const end = start + pageSize

  return {
    rows: allRows.slice(start, end).map(normalizeTableRow),
    total,
    page,
    pageSize,
    hasMore: end < total,
  }
}

export async function fetchHistoricalReadings({
  since,
  until,
  days = CHART_LOOKBACK_DAYS,
  limit = CHART_FETCH_LIMIT,
} = {}) {
  if (IS_SIMULATED_MODE) {
    return buildSimulatedHistoricalReadings({ since, until, days, limit })
  }

  const api = resolveApiBase()
  const params = new URLSearchParams()
  params.set('limit', String(limit))
  if (since) params.set('since', since.toISOString())
  if (until) params.set('until', until.toISOString())
  if (!since && !until) params.set('days', String(days))

  try {
    const res = await fetch(`${api}/api/sensors/history/range?${params}`, {
      headers: getApiAuthHeaders(),
    })
    if (res.ok) {
      const payload = await res.json()
      if (Array.isArray(payload)) {
        return payload.map(normalizeRangeRecord)
      }
    }
  } catch { /* network error → fallback */ }

  return buildFallbackReadings()
}

export async function fetchHistoricalTable({
  page = 1,
  pageSize = 10,
  sensor = 'all',
  dateFrom = null,
  dateTo = null,
  registeredDevices = [],
  live = false,
  since = null,
} = {}) {
  if (IS_SIMULATED_MODE) {
    return buildSimulatedTablePage({
      page,
      pageSize,
      sensor,
      dateFrom,
      dateTo,
      registeredDevices,
    })
  }

  const api = resolveApiBase()
  const params = new URLSearchParams()
  params.set('page', String(page))
  params.set('page_size', String(pageSize))
  params.set('sensor', sensor)
  if (live) params.set('live', 'true')
  if (since) params.set('since', since.toISOString())
  if (dateFrom) params.set('date_from', dateFrom)
  if (dateTo) params.set('date_to', dateTo)

  try {
    const res = await fetch(`${api}/api/sensors/history/table?${params}`, {
      headers: getApiAuthHeaders(),
    })
    if (res.ok) {
      const payload = await res.json()
      return {
        rows:  Array.isArray(payload.rows) ? payload.rows.map(normalizeTableRow) : [],
        total: Number(payload.total) || 0,
        page:  Number(payload.page) || page,
        pageSize: Number(payload.page_size) || pageSize,
        hasMore: Boolean(payload.has_more),
      }
    }
  } catch { /* ignore */ }

  return { rows: [], total: 0, page, pageSize, hasMore: false }
}

/** Datos para exportación PDF (admin). */
export async function fetchHistoricalExportRows(registeredDevices = []) {
  const records = await fetchHistoricalReadings({ days: CHART_LOOKBACK_DAYS, limit: CHART_FETCH_LIMIT })
  const expanded = expandReadingsForRegisteredDevices(records, registeredDevices)
  return flattenMeasurements(expanded)
}

export async function fetchDashboardSnapshot() {
  const api = resolveApiBase()
  const res = await fetch(`${api}/api/dashboard`, { headers: getApiAuthHeaders() })
  if (!res.ok) throw new Error(`Dashboard API error ${res.status}`)
  return res.json()
}

/** Dispositivos activos registrados (para filtros PDF / histórico). */
export async function fetchActiveDevices() {
  if (IS_SIMULATED_MODE) {
    try {
      const api = resolveApiBase()
      const res = await fetch(`${api}/api/devices`, { headers: getApiAuthHeaders() })
      if (res.ok) {
        const data = await res.json()
        if (Array.isArray(data)) {
          const active = data.filter((d) => d.active !== false)
          if (active.length) return active
        }
      }
    } catch { /* usar dispositivo simulado por defecto */ }
    return getSimulatedHistoricalDevices()
  }

  const api = resolveApiBase()
  try {
    const res = await fetch(`${api}/api/devices`, { headers: getApiAuthHeaders() })
    if (!res.ok) return []
    const data = await res.json()
    if (!Array.isArray(data)) return []
    return data.filter((d) => d.active !== false)
  } catch {
    return []
  }
}

export function mergeHistoricalReadings(existing, incoming, registeredDevices = [], maxSize = CHART_FETCH_LIMIT) {
  const merged = new Map()
  for (const record of existing) {
    const ts = parseTimestamp(record.timestamp).getTime()
    merged.set(`${ts}:${String(record.device).trim()}`, record)
  }
  for (const record of incoming) {
    const ts = parseTimestamp(record.timestamp).getTime()
    merged.set(`${ts}:${String(record.device).trim()}`, record)
  }
  const sorted = [...merged.values()].sort((a, b) => parseTimestamp(b.timestamp) - parseTimestamp(a.timestamp))
  const trimmed = sorted.slice(0, maxSize)
  return readingsForCharts(trimmed, registeredDevices)
}

export async function fetchIncrementalReadings(since, registeredDevices = []) {
  if (!since) return []

  if (IS_SIMULATED_MODE) {
    const incoming = buildSimulatedIncrementalReadings(since, INCREMENTAL_LIMIT)
    return readingsForCharts(incoming, registeredDevices)
  }

  try {
    const incoming = await fetchHistoricalReadings({
      since,
      limit: INCREMENTAL_LIMIT,
    })
    return readingsForCharts(incoming, registeredDevices)
  } catch {
    return []
  }
}

export function getHistoricalDataSourceLabel() {
  return IS_SIMULATED_MODE ? 'Datos simulados' : 'Datos en vivo'
}

export function mergeTableRows(existing, incoming, maxSize = TABLE_LIVE_PAGE_SIZE) {
  const merged = new Map()
  for (const row of existing) {
    merged.set(row.key, row)
  }
  for (const row of incoming) {
    merged.set(row.key, row)
  }
  return [...merged.values()]
    .sort((a, b) => parseTimestamp(b.timestamp) - parseTimestamp(a.timestamp))
    .slice(0, maxSize)
}

export function maxReadingTimestamp(readings) {
  if (!readings?.length) return null
  return readings.reduce((max, record) => {
    const ts = parseTimestamp(record.timestamp).getTime()
    return ts > max ? ts : max
  }, 0)
}

export {
  IS_SIMULATED_MODE,
  POLL_INTERVAL_MS,
  CHART_LOOKBACK_DAYS,
  CHART_FETCH_LIMIT,
  TABLE_LIVE_PAGE_SIZE,
}

/** @deprecated Usar fetchHistoricalReadings */
export async function fetchSensorReadings() {
  const records = await fetchHistoricalReadings()
  return records.length ? records : buildFallbackReadings()
}

/** @deprecated Compatibilidad con código que esperaba normalizeHistoryRecord */
export { normalizeHistoryRecord }
