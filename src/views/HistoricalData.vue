<template>
  <div class="historical-view">
    <div class="history-header">
      <div class="header-left">
        <ThemeToggleButton />
        <button class="back-btn" @click="goBack">←</button>
        <h1>Datos Históricos</h1>
      </div>
      <button class="pdf-btn" @click="openPdfModal">Descargar PDF</button>
    </div>

    <main class="history-content">
      <!-- pH Chart -->
      <div class="chart-wrapper">
        <div class="chart-title">
          <h3>pH</h3>
          <div class="period-buttons">
            <button 
              @click="phPeriod = 'day'" 
              :class="{ active: phPeriod === 'day' }"
              class="period-btn"
            >
              1 día
            </button>
            <button 
              @click="phPeriod = 'week'" 
              :class="{ active: phPeriod === 'week' }"
              class="period-btn"
            >
              1 semana
            </button>
          </div>
        </div>
        <div class="chart-container">
          <canvas ref="phChartRef"></canvas>
        </div>
        <div class="measurements">
          <span>Máx: {{ chartStats.ph.max.toFixed(2) }}</span>
          <span>Mín: {{ chartStats.ph.min.toFixed(2) }}</span>
          <span>Prom: {{ chartStats.ph.avg.toFixed(2) }}</span>
        </div>
      </div>

      <!-- Temperature Chart -->
      <div class="chart-wrapper">
        <div class="chart-title">
          <h3>Temperatura (°C)</h3>
          <div class="period-buttons">
            <button 
              @click="tempPeriod = 'day'" 
              :class="{ active: tempPeriod === 'day' }"
              class="period-btn"
            >
              1 día
            </button>
            <button 
              @click="tempPeriod = 'week'" 
              :class="{ active: tempPeriod === 'week' }"
              class="period-btn"
            >
              1 semana
            </button>
          </div>
        </div>
        <div class="chart-container">
          <canvas ref="tempChartRef"></canvas>
        </div>
        <div class="measurements">
          <span>Máx: {{ chartStats.temperature.max.toFixed(2) }}</span>
          <span>Mín: {{ chartStats.temperature.min.toFixed(2) }}</span>
          <span>Prom: {{ chartStats.temperature.avg.toFixed(2) }}</span>
        </div>
      </div>

      <!-- Conductivity Chart -->
      <div class="chart-wrapper">
        <div class="chart-title">
          <h3>Conductividad (µS/cm)</h3>
          <div class="period-buttons">
            <button 
              @click="condPeriod = 'day'" 
              :class="{ active: condPeriod === 'day' }"
              class="period-btn"
            >
              1 día
            </button>
            <button 
              @click="condPeriod = 'week'" 
              :class="{ active: condPeriod === 'week' }"
              class="period-btn"
            >
              1 semana
            </button>
          </div>
        </div>
        <div class="chart-container">
          <canvas ref="condChartRef"></canvas>
        </div>
        <div class="measurements">
          <span>Máx: {{ chartStats.conductivity.max.toFixed(2) }}</span>
          <span>Mín: {{ chartStats.conductivity.min.toFixed(2) }}</span>
          <span>Prom: {{ chartStats.conductivity.avg.toFixed(2) }}</span>
        </div>
      </div>

      <section class="table-wrapper">
        <div class="table-header">
          <h3>Mediciones En Tiempo Real</h3>
          <span class="table-meta">Actualiza cada 30 segundos</span>
        </div>

        <div class="table-filters" aria-label="Filtro de fechas de la tabla">
          <label class="table-filter-field">
            <span>Fecha</span>
            <select v-model="tableDateFilter.mode" class="table-filter-select">
              <option value="all">Todas las fechas</option>
              <option value="day">Día específico</option>
              <option value="range">Rango (desde / hasta)</option>
            </select>
          </label>
          <label v-if="tableDateFilter.mode === 'day'" class="table-filter-field">
            <span>Día</span>
            <input v-model="tableDateFilter.day" type="date" class="table-filter-input" />
          </label>
          <template v-else-if="tableDateFilter.mode === 'range'">
            <label class="table-filter-field">
              <span>Desde</span>
              <input v-model="tableDateFilter.startDate" type="date" class="table-filter-input" />
            </label>
            <label class="table-filter-field">
              <span>Hasta</span>
              <input v-model="tableDateFilter.endDate" type="date" class="table-filter-input" />
            </label>
          </template>
          <span v-if="tableDateFilter.mode !== 'all'" class="table-filter-count">
            {{ measurementRowsFiltered.length }} registro(s)
          </span>
        </div>

        <div class="table-scroll">
          <table class="measurements-table">
            <thead>
              <tr>
                <th>Dispositivo</th>
                <th>Sensor</th>
                <th>Medición</th>
                <th>Fecha</th>
                <th>Hora</th>
                <th>Alerta</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="visibleMeasurementRows.length === 0">
                <td colspan="6" class="no-data">
                  {{
                    measurementRows.length === 0
                      ? 'No hay datos disponibles.'
                      : 'No hay mediciones para el filtro de fechas seleccionado.'
                  }}
                </td>
              </tr>
              <tr v-for="row in visibleMeasurementRows" :key="row.key">
                <td>{{ row.device }}</td>
                <td>{{ row.sensorLabel }}</td>
                <td>{{ row.measurementText }}</td>
                <td>{{ row.dateText }}</td>
                <td>{{ row.timeText }}</td>
                <td>
                  <span class="alert-chip" :class="row.alertClass">{{ row.alertStatus }}</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="table-actions" v-if="totalTablePages > 1">
          <div class="pagination-controls">
            <button 
              class="pagination-btn" 
              :disabled="currentTablePage === 1"
              @click="prevTablePage"
            >
              ← Anterior
            </button>
            
            <div class="pagination-numbers">
              <button 
                v-for="page in totalTablePages" 
                :key="page"
                class="page-number-btn"
                :class="{ active: currentTablePage === page }"
                @click="goToTablePage(page)"
              >
                {{ page }}
              </button>
            </div>
            
            <button 
              class="pagination-btn" 
              :disabled="currentTablePage === totalTablePages"
              @click="nextTablePage"
            >
              Siguiente →
            </button>
          </div>
          <span class="pagination-info">
            Página {{ currentTablePage }} de {{ totalTablePages }} 
            ({{ measurementRowsFiltered.length }} registros totales)
          </span>
        </div>
      </section>
    </main>

    <div v-if="showPdfModal" class="pdf-modal-overlay" @click.self="closePdfModal">
      <div class="pdf-modal">
        <div class="pdf-modal-header">
          <h3>Descargar Reporte Alertas PDF</h3>
          <button class="modal-close-btn" @click="closePdfModal">✕</button>
        </div>

        <div class="pdf-modal-body">
          <div class="filter-grid">
            <label>
              <span>Dispositivo</span>
              <select v-model="pdfFilters.device">
                <option value="all">Todos</option>
                <option v-for="device in deviceOptions" :key="device" :value="device">{{ device }}</option>
              </select>
            </label>

            <label>
              <span>Sensor</span>
              <select v-model="pdfFilters.sensor">
                <option value="all">Todos los sensores</option>
                <option value="ph">pH</option>
                <option value="temperature">Temperatura</option>
                <option value="conductivity">Conductividad</option>
              </select>
            </label>

            <label>
              <span>Datos</span>
              <select v-model="pdfFilters.dataType">
                <option value="alerts">Alertas</option>
                <option value="normal">Normales</option>
                <option value="all">Todos</option>
              </select>
            </label>

            <label>
              <span>Filtro de fechas</span>
              <select v-model="pdfFilters.rangeType">
                <option value="day">Día específico</option>
                <option value="range">Rango de fechas</option>
              </select>
            </label>

            <label v-if="pdfFilters.rangeType === 'day'">
              <span>Día</span>
              <input v-model="pdfFilters.day" type="date" />
            </label>

            <label v-else>
              <span>Desde</span>
              <input v-model="pdfFilters.startDate" type="date" />
            </label>

            <label v-if="pdfFilters.rangeType === 'range'">
              <span>Hasta</span>
              <input v-model="pdfFilters.endDate" type="date" />
            </label>
          </div>

          <p class="pdf-preview-text">
            Registros a exportar ({{ selectedDataLabelForPdf }}): <strong>{{ selectedRowsForPdf.length }}</strong>
          </p>
          <p class="pdf-preview-text">
            Registros de alerta (referencia): <strong>{{ alertRowsForPdf.length }}</strong>
          </p>
          <p class="pdf-preview-text">
            Porcentaje de alertas sobre total filtrado: <strong>{{ alertPercentageForPdf.toFixed(2) }}%</strong>
          </p>
        </div>

        <div class="pdf-modal-actions">
          <button class="secondary-btn" @click="closePdfModal">Cancelar</button>
          <button class="primary-btn" :disabled="isGeneratingPdf" @click="downloadPDF">
            {{ isGeneratingPdf ? 'Generando...' : 'Generar PDF' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, reactive, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import Chart from 'chart.js/auto'
import { jsPDF } from 'jspdf'
import ThemeToggleButton from '../components/ThemeToggleButton.vue'

const router = useRouter()

const SENSOR_META = {
  ph: { label: 'pH', unit: '', min: 6, max: 8.5 },
  temperature: { label: 'Temperatura', unit: '°C', min: 15, max: 30 },
  conductivity: { label: 'Conductividad', unit: 'µS/cm', min: 700, max: 1600 },
}

const phPeriod = ref('day')
const tempPeriod = ref('day')
const condPeriod = ref('day')

const phChartRef = ref(null)
const tempChartRef = ref(null)
const condChartRef = ref(null)

let phChart = null
let tempChart = null
let condChart = null
let chartUpdateInterval = null
let tableUpdateInterval = null

const chartStats = reactive({
  ph: { max: 8.5, min: 6.0, avg: 7.2 },
  temperature: { max: 28, min: 18, avg: 22.5 },
  conductivity: { max: 1500, min: 800, avg: 1100 },
})

const normalizedReadings = ref([])
const measurementRows = ref([])
const currentTablePage = ref(1)
const itemsPerPage = 10
const showPdfModal = ref(false)
const isGeneratingPdf = ref(false)

const pdfFilters = reactive({
  device: 'all',
  sensor: 'all',
  dataType: 'alerts',
  rangeType: 'day',
  day: localDateKey(new Date()),
  startDate: localDateKey(new Date(Date.now() - 6 * 24 * 60 * 60 * 1000)),
  endDate: localDateKey(new Date()),
})

/** Filtro de fechas solo para la tabla «Mediciones en tiempo real» (misma vista admin/empleado). */
const tableDateFilter = reactive({
  mode: 'all',
  day: localDateKey(new Date()),
  startDate: localDateKey(new Date(Date.now() - 6 * 24 * 60 * 60 * 1000)),
  endDate: localDateKey(new Date()),
})

const deviceOptions = computed(() => {
  const devices = new Set(normalizedReadings.value.map((reading) => reading.device))
  return [...devices].sort((a, b) => a.localeCompare(b))
})

const measurementRowsFiltered = computed(() => {
  return measurementRows.value.filter((row) => {
    if (tableDateFilter.mode === 'all') return true
    if (tableDateFilter.mode === 'day') {
      return row.dateKey === tableDateFilter.day
    }
    const start = tableDateFilter.startDate || '0000-01-01'
    const end = tableDateFilter.endDate || '9999-12-31'
    return row.dateKey >= start && row.dateKey <= end
  })
})

const visibleMeasurementRows = computed(() => {
  const start = (currentTablePage.value - 1) * itemsPerPage
  const end = start + itemsPerPage
  return measurementRowsFiltered.value.slice(start, end)
})

const totalTablePages = computed(() => {
  return Math.ceil(measurementRowsFiltered.value.length / itemsPerPage) || 1
})

const filteredRowsForPdf = computed(() => {
  return measurementRows.value.filter((row) => {
    if (pdfFilters.device !== 'all' && row.device !== pdfFilters.device) return false
    if (pdfFilters.sensor !== 'all' && row.sensorKey !== pdfFilters.sensor) return false

    if (pdfFilters.rangeType === 'day') {
      return row.dateKey === pdfFilters.day
    }

    const start = pdfFilters.startDate || '0000-01-01'
    const end = pdfFilters.endDate || '9999-12-31'
    return row.dateKey >= start && row.dateKey <= end
  })
})

const alertRowsForPdf = computed(() => {
  return filteredRowsForPdf.value.filter((row) => row.alertStatus === 'Alerta')
})

const normalRowsForPdf = computed(() => {
  return filteredRowsForPdf.value.filter((row) => row.alertStatus === 'Normal')
})

const selectedRowsForPdf = computed(() => {
  if (pdfFilters.dataType === 'alerts') return alertRowsForPdf.value
  if (pdfFilters.dataType === 'normal') return normalRowsForPdf.value
  return filteredRowsForPdf.value
})

const selectedDataLabelForPdf = computed(() => {
  if (pdfFilters.dataType === 'alerts') return 'Alertas'
  if (pdfFilters.dataType === 'normal') return 'Normales'
  return 'Todos'
})

const alertPercentageForPdf = computed(() => {
  const totalFiltered = filteredRowsForPdf.value.length
  if (!totalFiltered) return 0
  return (alertRowsForPdf.value.length / totalFiltered) * 100
})

function localDateKey(date) {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

function getChartJsTheme() {
  const dark = document.documentElement.getAttribute('data-theme') === 'dark'
  if (dark) {
    return {
      tick: '#94a3b8',
      grid: 'rgba(148, 163, 184, 0.14)',
      axisTitle: '#86efac',
    }
  }
  return {
    tick: '#666',
    grid: 'rgba(0, 0, 0, 0.04)',
    axisTitle: '#66bb6a',
  }
}

function onChartsThemeChange() {
  void updateCharts()
}

function parseTimestamp(value) {
  if (typeof value === 'number') {
    const millis = value > 9999999999 ? value : value * 1000
    return new Date(millis)
  }

  if (typeof value === 'string' && /^\d+$/.test(value)) {
    const numericValue = Number(value)
    const millis = numericValue > 9999999999 ? numericValue : numericValue * 1000
    return new Date(millis)
  }

  const parsed = new Date(value)
  if (Number.isNaN(parsed.getTime())) {
    return new Date()
  }
  return parsed
}

function getAlertStatus(sensorKey, value) {
  const meta = SENSOR_META[sensorKey]
  if (!meta) return { status: 'Normal', cssClass: 'normal' }

  const isOutOfRange = value < meta.min || value > meta.max
  return {
    status: isOutOfRange ? 'Alerta' : 'Normal',
    cssClass: isOutOfRange ? 'warning' : 'normal',
  }
}

function measurementText(sensorKey, value) {
  const unit = SENSOR_META[sensorKey]?.unit || ''
  return unit ? `${value.toFixed(2)} ${unit}` : value.toFixed(2)
}

function normalizeMongoRecord(record) {
  const metrics = record.mediciones || {}
  return {
    device: record.arduino_id || record.embalse || 'simulador-arandanos',
    timestamp: parseTimestamp(record.timestamp),
    ph: Number(record.ph ?? metrics.ph),
    temperature: Number(record.temperature ?? metrics.temperatura),
    conductivity: Number(record.conductivity ?? metrics.conductividad),
  }
}

function normalizeHistoryRecord(record) {
  return {
    device: 'simulador-arandanos',
    timestamp: parseTimestamp(record.timestamp),
    ph: Number(record.ph),
    temperature: Number(record.temperature),
    conductivity: Number(record.conductivity),
  }
}

function buildFallbackReadings() {
  const now = Date.now()
  const fallback = []
  for (let i = 0; i < 40; i++) {
    const timestamp = new Date(now - i * 30 * 1000)
    fallback.push({
      device: 'simulador-arandanos',
      timestamp,
      ph: 7.0 + (Math.random() - 0.5) * 0.3,
      temperature: 22 + (Math.random() - 0.5) * 1.5,
      conductivity: 950 + (Math.random() - 0.5) * 80,
    })
  }
  return fallback
}

function flattenMeasurements(records) {
  const rows = []

  for (const record of records) {
    const timestamp = parseTimestamp(record.timestamp)
    const dateText = timestamp.toLocaleDateString('es-CL')
    const dateKey = localDateKey(timestamp)
    const timeText = timestamp.toLocaleTimeString('es-CL', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    })

    const sensors = [
      { key: 'ph', label: SENSOR_META.ph.label, value: Number(record.ph) },
      { key: 'temperature', label: SENSOR_META.temperature.label, value: Number(record.temperature) },
      { key: 'conductivity', label: SENSOR_META.conductivity.label, value: Number(record.conductivity) },
    ]

    for (const sensor of sensors) {
      if (!Number.isFinite(sensor.value)) continue

      const alertData = getAlertStatus(sensor.key, sensor.value)
      rows.push({
        key: `${record.device}-${sensor.key}-${timestamp.getTime()}`,
        device: record.device,
        sensorKey: sensor.key,
        sensorLabel: sensor.label,
        rawValue: sensor.value,
        measurementText: measurementText(sensor.key, sensor.value),
        dateText,
        dateKey,
        timeText,
        timestamp,
        alertStatus: alertData.status,
        alertClass: alertData.cssClass,
      })
    }
  }

  rows.sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime())
  return rows
}

function downsampleRows(rows, maxPoints) {
  if (rows.length <= maxPoints) return rows

  const sampled = []
  const step = Math.ceil(rows.length / maxPoints)
  for (let i = 0; i < rows.length; i += step) {
    sampled.push(rows[i])
  }
  return sampled.slice(-maxPoints)
}

/** Misma lógica que nginx/Docker: vacío → /api/... relativo al origen. */
function resolveApiBase() {
  const raw = import.meta.env.VITE_API_URL
  if (raw === undefined || raw === null || String(raw).trim() === '') return ''
  return String(raw).replace(/\/$/, '')
}

async function fetchRealtimeMeasurements() {
  const apiUrl = resolveApiBase()

  try {
    let records = []

    const mongoResponse = await fetch(`${apiUrl}/api/data/mongodb`)
    if (mongoResponse.ok) {
      const mongoPayload = await mongoResponse.json()
      if (!mongoPayload.error && Array.isArray(mongoPayload.data) && mongoPayload.data.length > 0) {
        records = mongoPayload.data.map(normalizeMongoRecord)
      }
    }

    if (!records.length) {
      const historyResponse = await fetch(`${apiUrl}/api/sensors/history?limit=200`)
      if (historyResponse.ok) {
        const historyPayload = await historyResponse.json()
        if (Array.isArray(historyPayload) && historyPayload.length > 0) {
          records = historyPayload.map(normalizeHistoryRecord)
        }
      }
    }

    if (!records.length) {
      records = buildFallbackReadings()
    }

    normalizedReadings.value = records.sort(
      (a, b) => parseTimestamp(b.timestamp).getTime() - parseTimestamp(a.timestamp).getTime()
    )
    measurementRows.value = flattenMeasurements(normalizedReadings.value)
  } catch (error) {
    console.error('Error obteniendo mediciones para la tabla:', error)
    normalizedReadings.value = buildFallbackReadings()
    measurementRows.value = flattenMeasurements(normalizedReadings.value)
  }
}

const generateMockData = async (type, period) => {
  try {
    const apiUrl = resolveApiBase()
    console.log(`[DEBUG] Fetching from ${apiUrl}/api/dashboard for type: ${type}`)
    const response = await fetch(`${apiUrl}/api/dashboard`)
    const data = await response.json()
    console.log(`[DEBUG] API response:`, data)
    
    const now = new Date()
    const dataPoints = period === 'day' ? 24 : 7
    const labels = []
    const values = []
    
    let baseValue = 0, maxVal = 0, minVal = 0

    // Extraer el valor base del sensor correspondiente
    if (type === 'ph') {
      baseValue = data.ph?.value || 7.2
      maxVal = data.ph?.max || 8.5
      minVal = data.ph?.min || 6.0
    } else if (type === 'temperature') {
      baseValue = data.temperature?.value || 22.5
      maxVal = data.temperature?.max || 28
      minVal = data.temperature?.min || 18
    } else if (type === 'conductivity') {
      baseValue = data.conductivity?.value || 1100
      maxVal = data.conductivity?.max || 1500
      minVal = data.conductivity?.min || 800
    }

    // Generar datos históricos simulados basados en el valor actual
    for (let i = 0; i < dataPoints; i++) {
      const date = new Date(now)
      if (period === 'day') {
        date.setHours(i, 0, 0, 0)
        labels.push(`${String(i).padStart(2, '0')}:00`)
      } else {
        date.setDate(date.getDate() - (6 - i))
        labels.push(date.toLocaleDateString('es-ES', { weekday: 'short' }))
      }
      
      // Agregar pequeña variación al valor real (±5% del rango)
      const variance = (maxVal - minVal) * 0.05
      const value = baseValue + (Math.random() - 0.5) * variance
      values.push(Math.max(minVal, Math.min(maxVal, value)))
    }

    const avg = values.reduce((a, b) => a + b, 0) / values.length
    const max = Math.max(...values)
    const min = Math.min(...values)
    
    console.log(`[DEBUG] Generated data for ${type}:`, { labels: labels.length, values: values.length, avg, max, min })

    return { labels, data: values, avg, max, min }
  } catch (error) {
    console.error('Error fetching data:', error)
    // Fallback a datos locales si hay error
    const dataPoints = period === 'day' ? 24 : 7
    const labels = []
    const data = []
    
    let baseValue = 0, maxVal = 0, minVal = 0
    
    if (type === 'ph') {
      baseValue = 7.2; maxVal = 8.5; minVal = 6.0
    } else if (type === 'temperature') {
      baseValue = 22.5; maxVal = 28; minVal = 18
    } else if (type === 'conductivity') {
      baseValue = 1100; maxVal = 1500; minVal = 800
    }

    for (let i = 0; i < dataPoints; i++) {
      const now = new Date()
      if (period === 'day') {
        now.setHours(i, 0, 0, 0)
        labels.push(`${String(i).padStart(2, '0')}:00`)
      } else {
        now.setDate(now.getDate() - (6 - i))
        labels.push(now.toLocaleDateString('es-ES', { weekday: 'short' }))
      }
      
      const variance = (maxVal - minVal) * 0.05
      const value = baseValue + (Math.random() - 0.5) * variance
      data.push(Math.max(minVal, Math.min(maxVal, value)))
    }
    
    const avg = data.reduce((a, b) => a + b, 0) / data.length
    return { labels, data, avg, max: Math.max(...data), min: Math.min(...data) }
  }
}

const updatePhChart = async () => {
  const phData = await generateMockData('ph', phPeriod.value)
  chartStats.ph = { max: phData.max, min: phData.min, avg: phData.avg }

  if (phChart) {
    phChart.data.labels = phData.labels
    phChart.data.datasets[0].data = phData.data
    phChart.update('none')
  } else if (phChartRef.value) {
    createChart(phChartRef, phData, 'pH', 6, 8.5, phChart, 'phChart')
  }
}

const updateTempChart = async () => {
  const tempData = await generateMockData('temperature', tempPeriod.value)
  chartStats.temperature = { max: tempData.max, min: tempData.min, avg: tempData.avg }

  if (tempChart) {
    tempChart.data.labels = tempData.labels
    tempChart.data.datasets[0].data = tempData.data
    tempChart.update('none')
  } else if (tempChartRef.value) {
    createChart(tempChartRef, tempData, 'Temperatura (°C)', 15, 30, tempChart, 'tempChart')
  }
}

const updateCondChart = async () => {
  const condData = await generateMockData('conductivity', condPeriod.value)
  chartStats.conductivity = { max: condData.max, min: condData.min, avg: condData.avg }

  if (condChart) {
    condChart.data.labels = condData.labels
    condChart.data.datasets[0].data = condData.data
    condChart.update('none')
  } else if (condChartRef.value) {
    createChart(condChartRef, condData, 'Conductividad (µS/cm)', 700, 1600, condChart, 'condChart')
  }
}

const updateCharts = async () => {
  await Promise.all([
    updatePhChart(),
    updateTempChart(),
    updateCondChart(),
  ])
}

const createChart = (chartRef, data, label, minVal, maxVal, chartInstance, varName) => {
  if (chartInstance) chartInstance.destroy()

  const theme = getChartJsTheme()
  const ctx = chartRef.value.getContext('2d')
  const newChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: data.labels,
      datasets: [{
        label: label,
        data: data.data,
        borderColor: '#66bb6a',
        backgroundColor: 'rgba(102, 187, 106, 0.08)',
        borderWidth: 2.5,
        fill: true,
        tension: 0.3,
        pointBackgroundColor: '#66bb6a',
        pointBorderColor: '#fff',
        pointBorderWidth: 2,
        pointRadius: 3,
        pointHoverRadius: 5,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: { duration: 0 },
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: 'rgba(0, 0, 0, 0.75)',
          padding: 8,
          titleFont: { size: 11 },
          bodyFont: { size: 11 },
        }
      },
      scales: {
        y: {
          min: minVal,
          max: maxVal,
          ticks: { color: theme.tick, font: { size: 10 } },
          grid: { color: theme.grid },
          beginAtZero: false,
          title: {
            display: true,
            text: label,
            font: { size: 11, weight: 'bold' },
            color: theme.axisTitle,
          },
        },
        x: {
          ticks: { color: theme.tick, font: { size: 10 } },
          grid: { display: false },
        },
      },
    }
  })
  
  // Actualizar la referencia global
  if (varName === 'phChart') phChart = newChart
  else if (varName === 'tempChart') tempChart = newChart
  else if (varName === 'condChart') condChart = newChart
}

watch(phPeriod, async () => {
  await updatePhChart()
})

watch(tempPeriod, async () => {
  await updateTempChart()
})

watch(condPeriod, async () => {
  await updateCondChart()
})

watch(
  () => pdfFilters.rangeType,
  (newValue) => {
    if (newValue === 'day') {
      pdfFilters.day = pdfFilters.day || localDateKey(new Date())
      return
    }

    pdfFilters.startDate = pdfFilters.startDate || localDateKey(new Date(Date.now() - 6 * 24 * 60 * 60 * 1000))
    pdfFilters.endDate = pdfFilters.endDate || localDateKey(new Date())
  }
)

watch(deviceOptions, (options) => {
  if (pdfFilters.device !== 'all' && !options.includes(pdfFilters.device)) {
    pdfFilters.device = 'all'
  }
})

// Resetear la página cuando cambia el filtro de tabla
watch(
  () => [tableDateFilter.mode, tableDateFilter.day, tableDateFilter.startDate, tableDateFilter.endDate],
  () => {
    currentTablePage.value = 1
  }
)

onMounted(async () => {
  await nextTick()
  window.addEventListener('embalse-theme-change', onChartsThemeChange)
  await Promise.all([updateCharts(), fetchRealtimeMeasurements()])

  chartUpdateInterval = setInterval(async () => {
    try {
      await updateCharts()
    } catch (error) {
      console.error('Error actualizando gráficos:', error)
    }
  }, 5000)

  tableUpdateInterval = setInterval(async () => {
    try {
      await fetchRealtimeMeasurements()
    } catch (error) {
      console.error('Error actualizando tabla de mediciones:', error)
    }
  }, 30000)
})

onBeforeUnmount(() => {
  window.removeEventListener('embalse-theme-change', onChartsThemeChange)
  if (chartUpdateInterval) clearInterval(chartUpdateInterval)
  if (tableUpdateInterval) clearInterval(tableUpdateInterval)
  if (phChart) phChart.destroy()
  if (tempChart) tempChart.destroy()
  if (condChart) condChart.destroy()
})

const goBack = () => {
  router.back()
}

const goToTablePage = (page) => {
  const newPage = Math.max(1, Math.min(page, totalTablePages.value))
  currentTablePage.value = newPage
}

const nextTablePage = () => {
  if (currentTablePage.value < totalTablePages.value) {
    currentTablePage.value += 1
  }
}

const prevTablePage = () => {
  if (currentTablePage.value > 1) {
    currentTablePage.value -= 1
  }
}

const openPdfModal = () => {
  showPdfModal.value = true
}

const closePdfModal = () => {
  showPdfModal.value = false
}

const selectedSensorKeysForPdf = () => {
  if (pdfFilters.sensor === 'all') {
    return ['ph', 'temperature', 'conductivity']
  }
  return [pdfFilters.sensor]
}

const renderPdfChartImage = async (sensorKey, rows) => {
  const meta = SENSOR_META[sensorKey]
  const sensorRows = rows
    .filter((row) => row.sensorKey === sensorKey)
    .sort((a, b) => a.timestamp.getTime() - b.timestamp.getTime())

  if (!sensorRows.length) return null

  const sampledRows = downsampleRows(sensorRows, pdfFilters.rangeType === 'day' ? 24 : 45)
  const labels = sampledRows.map((row) => {
    if (pdfFilters.rangeType === 'day') return row.timeText
    return `${row.dateText} ${row.timeText.slice(0, 5)}`
  })

  const canvas = document.createElement('canvas')
  canvas.width = 1200
  canvas.height = 380
  const ctx = canvas.getContext('2d')

  const tempChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: [
        {
          label: meta.label,
          data: sampledRows.map((row) => row.rawValue),
          borderColor: '#66bb6a',
          backgroundColor: 'rgba(102, 187, 106, 0.08)',
          borderWidth: 2.5,
          fill: true,
          tension: 0.3,
          pointBackgroundColor: '#66bb6a',
          pointBorderColor: '#ffffff',
          pointBorderWidth: 2,
          pointRadius: 2.5,
          pointHoverRadius: 4,
        },
      ],
    },
    options: {
      responsive: false,
      maintainAspectRatio: false,
      animation: false,
      plugins: {
        legend: { display: false },
      },
      scales: {
        y: {
          min: meta.min,
          max: meta.max,
          beginAtZero: false,
          title: {
            display: true,
            text: `${meta.label}${meta.unit ? ` (${meta.unit})` : ''}`,
            color: '#66bb6a',
            font: { size: 12, weight: 'bold' },
          },
          ticks: {
            color: '#666',
            font: { size: 10 },
          },
          grid: {
            color: 'rgba(0, 0, 0, 0.05)',
          },
        },
        x: {
          ticks: {
            color: '#666',
            font: { size: 9 },
            maxRotation: 35,
            minRotation: 0,
          },
          grid: { display: false },
        },
      },
    },
  })

  await new Promise((resolve) => setTimeout(resolve, 60))
  const image = canvas.toDataURL('image/png')
  tempChart.destroy()

  return {
    title: meta.label,
    image,
  }
}

const PDF_TABLE_COLUMNS = [
  { title: 'Dispositivo', width: 45 },
  { title: 'Sensor', width: 24 },
  { title: 'Medición', width: 30 },
  { title: 'Fecha', width: 28 },
  { title: 'Hora', width: 20 },
  { title: 'Alerta', width: 35 },
]

const drawPdfTableRow = (doc, y, rowValues) => {
  const rowHeight = 6
  const startX = 14

  let currentX = startX
  doc.setDrawColor(170, 178, 186)
  doc.setLineWidth(0.15)

  PDF_TABLE_COLUMNS.forEach((column, index) => {
    doc.rect(currentX, y, column.width, rowHeight, 'S')
    const text = String(rowValues[index] ?? '')
    const textLimit = Math.max(8, Math.floor(column.width * 1.2))
    doc.setFontSize(8)
    doc.setTextColor(48, 55, 60)
    doc.text(text.slice(0, textLimit), currentX + 1.5, y + 4)
    currentX += column.width
  })

  return y + rowHeight
}

const addTableHeader = (doc, y) => {
  const rowHeight = 6
  const startX = 14
  const totalWidth = PDF_TABLE_COLUMNS.reduce((sum, column) => sum + column.width, 0)

  doc.setDrawColor(170, 178, 186)
  doc.setLineWidth(0.2)
  doc.setFillColor(232, 242, 232)
  doc.rect(startX, y, totalWidth, rowHeight, 'FD')

  let currentX = startX
  doc.setFont('helvetica', 'bold')
  doc.setFontSize(8)
  doc.setTextColor(38, 45, 52)

  PDF_TABLE_COLUMNS.forEach((column) => {
    doc.text(column.title, currentX + 1.5, y + 4)
    currentX += column.width
    if (currentX < startX + totalWidth) {
      doc.line(currentX, y, currentX, y + rowHeight)
    }
  })

  doc.setFont('helvetica', 'normal')
  return y + rowHeight
}

const drawPdfChartBlock = (doc, y, chartTitle, imageData) => {
  const boxX = 14
  const boxY = y
  const boxWidth = 182
  const boxHeight = 68

  doc.setDrawColor(160, 168, 176)
  doc.setLineWidth(0.4)
  doc.roundedRect(boxX, boxY, boxWidth, boxHeight, 1.2, 1.2, 'S')

  doc.setFillColor(243, 247, 243)
  doc.rect(boxX + 0.2, boxY + 0.2, boxWidth - 0.4, 8, 'F')

  doc.setFontSize(11)
  doc.setTextColor(40, 44, 52)
  doc.text(`Gráfico ${chartTitle}`, boxX + 3, boxY + 5.6)

  doc.addImage(imageData, 'PNG', boxX + 3, boxY + 10.5, boxWidth - 6, 54)

  return boxY + boxHeight + 4
}

const ensurePdfPageSpace = (doc, y, requiredSpace) => {
  if (y + requiredSpace > 285) {
    doc.addPage()
    return 14
  }
  return y
}

/** Segmentos seguros para nombre de archivo (Windows/macOS/Linux). */
const sanitizePdfFilenameSegment = (value) =>
  String(value ?? '')
    .trim()
    .replace(/[/\\:*?"<>|]/g, '-')
    .replace(/\s+/g, '_')
    .replace(/_+/g, '_')

/**
 * reporte_<dispositivo>_<fecha_día> | reporte_<dispositivo>_<desde>_a_<hasta>
 * (No se usa "/" entre fechas: no es válido en rutas Windows.)
 */
const buildPdfFilename = () => {
  const deviceSegment = sanitizePdfFilenameSegment(
    pdfFilters.device === 'all' ? 'Todos_los_dispositivos' : pdfFilters.device
  )
  if (pdfFilters.rangeType === 'day') {
    const daySegment = sanitizePdfFilenameSegment(pdfFilters.day || '')
    return `reporte_${deviceSegment}_${daySegment}.pdf`
  }
  const fromSegment = sanitizePdfFilenameSegment(pdfFilters.startDate || 'inicio')
  const toSegment = sanitizePdfFilenameSegment(pdfFilters.endDate || 'fin')
  return `reporte_${deviceSegment}_${fromSegment}_a_${toSegment}.pdf`
}

function computePdfSensorStats(exportRows) {
  const groups = { ph: [], temperature: [], conductivity: [] }
  for (const row of exportRows) {
    if (!Number.isFinite(row.rawValue)) continue
    const k = row.sensorKey
    if (groups[k]) groups[k].push(row.rawValue)
  }
  const keys = selectedSensorKeysForPdf()
  const out = []
  for (const key of keys) {
    const values = groups[key]
    if (!values?.length) continue
    const min = Math.min(...values)
    const max = Math.max(...values)
    const avg = values.reduce((a, b) => a + b, 0) / values.length
    out.push({
      sensorKey: key,
      label: SENSOR_META[key].label,
      min,
      max,
      avg,
      count: values.length,
    })
  }
  return out
}

function drawPdfSensorStatsBlock(doc, y, exportRows) {
  const stats = computePdfSensorStats(exportRows)
  if (!stats.length) return y

  const cols = [
    { title: 'Sensor', width: 44 },
    { title: 'Mínimo', width: 38 },
    { title: 'Máximo', width: 38 },
    { title: 'Promedio', width: 38 },
    { title: 'N', width: 14 },
  ]
  const rowHeight = 6
  const startX = 14

  doc.setFontSize(11)
  doc.setFont('helvetica', 'bold')
  doc.setTextColor(38, 45, 52)
  doc.text('Resumen estadístico por sensor', startX, y)
  y += 6

  doc.setFontSize(8)
  doc.setFont('helvetica', 'italic')
  doc.setTextColor(90, 90, 90)
  doc.text('Valores calculados sobre los registros exportados en esta tabla.', startX, y)
  y += 5
  doc.setFont('helvetica', 'normal')

  const totalWidth = cols.reduce((sum, c) => sum + c.width, 0)
  doc.setDrawColor(170, 178, 186)
  doc.setLineWidth(0.2)
  doc.setFillColor(232, 242, 232)
  doc.rect(startX, y, totalWidth, rowHeight, 'FD')

  let cx = startX
  doc.setFont('helvetica', 'bold')
  doc.setFontSize(8)
  doc.setTextColor(38, 45, 52)
  cols.forEach((col, i) => {
    doc.text(col.title, cx + 1.5, y + 4)
    cx += col.width
    if (i < cols.length - 1) {
      doc.line(cx, y, cx, y + rowHeight)
    }
  })
  doc.setFont('helvetica', 'normal')
  y += rowHeight

  for (const s of stats) {
    const rowVals = [
      s.label,
      measurementText(s.sensorKey, s.min),
      measurementText(s.sensorKey, s.max),
      measurementText(s.sensorKey, s.avg),
      String(s.count),
    ]
    cx = startX
    doc.setDrawColor(170, 178, 186)
    doc.setLineWidth(0.15)
    cols.forEach((col, idx) => {
      doc.rect(cx, y, col.width, rowHeight, 'S')
      const text = String(rowVals[idx] ?? '')
      doc.setFontSize(8)
      doc.setTextColor(48, 55, 60)
      doc.text(text.slice(0, 32), cx + 1.5, y + 4)
      cx += col.width
    })
    y += rowHeight
  }

  return y + 6
}

const downloadPDF = async () => {
  const rows = filteredRowsForPdf.value
  const exportRows = selectedRowsForPdf.value
  const alertRows = alertRowsForPdf.value
  const alertPercent = alertPercentageForPdf.value

  if (!exportRows.length) {
    const typeMessage =
      pdfFilters.dataType === 'alerts'
        ? 'alertas'
        : pdfFilters.dataType === 'normal'
          ? 'mediciones normales'
          : 'datos'
    alert(`No hay ${typeMessage} para exportar con los filtros seleccionados.`)
    return
  }

  isGeneratingPdf.value = true

  try {
    const doc = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' })
    let y = 14

    doc.setFont('helvetica', 'bold')
    doc.setFontSize(11)
    doc.setTextColor(38, 45, 52)
    doc.text(`Reporte de Sensores (${selectedDataLabelForPdf.value})`, 14, y)
    y += 6

    doc.setFont('helvetica', 'normal')
    doc.setFontSize(10)
    doc.setTextColor(30, 30, 30)
    const deviceLabel = pdfFilters.device === 'all' ? 'Todos' : pdfFilters.device
    const sensorLabel = pdfFilters.sensor === 'all' ? 'Todos los sensores' : SENSOR_META[pdfFilters.sensor].label
    const rangeLabel =
      pdfFilters.rangeType === 'day'
        ? `Día: ${pdfFilters.day}`
        : `Rango: ${pdfFilters.startDate || 'inicio'} a ${pdfFilters.endDate || 'hoy'}`

    doc.text(`Dispositivo: ${deviceLabel}`, 14, y)
    y += 5
    doc.text(`Sensor: ${sensorLabel}`, 14, y)
    y += 5
    doc.text(`Filtro de fecha: ${rangeLabel}`, 14, y)
    y += 5
    doc.text(`Datos seleccionados: ${selectedDataLabelForPdf.value}`, 14, y)
    y += 5
    doc.text(`Registros exportados: ${exportRows.length}`, 14, y)
    y += 5
    doc.text(`Registros de alerta (referencia): ${alertRows.length}`, 14, y)
    y += 5
    doc.text(`Porcentaje de alertas sobre total filtrado: ${alertPercent.toFixed(2)}%`, 14, y)
    y += 8

    y = ensurePdfPageSpace(doc, y, 52)
    y = drawPdfSensorStatsBlock(doc, y, exportRows)

    y = addTableHeader(doc, y)

    const rowsForPdf = [...exportRows]
      .sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime())
      .slice(0, 120)

    for (const row of rowsForPdf) {
      y = ensurePdfPageSpace(doc, y, 6)
      if (y === 14) {
        y = addTableHeader(doc, y)
      }

      y = drawPdfTableRow(
        doc,
        y,
        [
          row.device,
          row.sensorLabel,
          row.measurementText,
          row.dateText,
          row.timeText.slice(0, 5),
          row.alertStatus,
        ],
        false
      )
    }

    const selectedSensors = selectedSensorKeysForPdf()
    for (const sensorKey of selectedSensors) {
      const chartData = await renderPdfChartImage(sensorKey, rows)
      if (!chartData) continue

      y = ensurePdfPageSpace(doc, y, 72)
      y = drawPdfChartBlock(doc, y, chartData.title, chartData.image)
    }

    doc.save(buildPdfFilename())
    showPdfModal.value = false
  } catch (error) {
    console.error('Error al generar PDF:', error)
    alert('No se pudo generar el PDF. Revisa la consola para más detalles.')
  } finally {
    isGeneratingPdf.value = false
  }
}
</script>

<style scoped>
.historical-view {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  min-height: 100dvh;
  height: 100vh;
  height: 100dvh;
  max-height: 100vh;
  max-height: 100dvh;
  background: #f5f7fa;
  min-width: 0;
}

.history-header {
  background: white;
  color: #333;
  padding: 14px 20px;
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  align-items: center;
  gap: 10px 12px;
  border-bottom: 2px solid #66bb6a;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  min-width: 0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.back-btn {
  width: 36px;
  height: 36px;
  border: 1px solid #e0e0e0;
  background: white;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  color: #333;
  transition: all 0.2s;
}

.back-btn:hover {
  background: #f0f0f0;
  border-color: #66bb6a;
}

.history-header h1 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #333;
}

.pdf-btn {
  padding: 8px 16px;
  background: #66bb6a;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s;
}

.pdf-btn:hover {
  background: #558a5a;
  transform: translateY(-1px);
}

.history-content {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 16px;
  display: grid;
  grid-template-columns: repeat(3, minmax(300px, 1fr));
  gap: 12px;
  align-items: start;
  justify-items: center;
  max-width: 100%;
  margin: 0 auto;
}

.chart-wrapper {
  background: white;
  border-radius: 8px;
  padding: 10px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.08);
  display: flex;
  flex-direction: column;
  gap: 6px;
  height: fit-content;
  width: 100%;
}

.chart-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
  margin-bottom: 4px;
}

.chart-title h3 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: #333;
}

.period-buttons {
  display: flex;
  gap: 6px;
}

.period-btn {
  padding: 6px 10px;
  min-height: 36px;
  background: #f0f0f0;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  color: #666;
  transition: all 0.2s;
  box-sizing: border-box;
}

.period-btn:hover {
  background: #e8e8e8;
}

.period-btn.active {
  background: #66bb6a;
  color: white;
  border-color: #66bb6a;
}

.chart-container {
  position: relative;
  height: 210px;
  width: 100%;
  flex-shrink: 0;
}

.chart-container canvas {
  display: block;
  width: 100%;
  height: 100%;
}

.measurements {
  display: flex;
  justify-content: space-around;
  font-size: 12px;
  color: #666;
  padding-top: 6px;
  border-top: 1px solid #e8ecf1;
}

.measurements span {
  font-weight: 500;
}

.table-wrapper {
  grid-column: 1 / -1;
  background: white;
  border-radius: 8px;
  padding: 12px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.08);
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
}

.table-header h3 {
  margin: 0;
  font-size: 15px;
  color: #333;
}

.table-meta {
  font-size: 12px;
  color: #6b7280;
}

.table-filters {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  gap: 12px 16px;
  padding: 10px 12px;
  background: #f8fafc;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
}

.table-filter-field {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.table-filter-field > span {
  font-size: 11px;
  font-weight: 600;
  color: #4b5563;
}

.table-filter-select,
.table-filter-input {
  padding: 7px 10px;
  border-radius: 6px;
  border: 1px solid #d1d5db;
  font-size: 16px;
  color: #111827;
  background: #fff;
  width: 100%;
  max-width: 100%;
  min-width: 0;
  box-sizing: border-box;
}

.table-filter-select:focus,
.table-filter-input:focus {
  outline: none;
  border-color: #66bb6a;
  box-shadow: 0 0 0 2px rgba(102, 187, 106, 0.2);
}

.table-filter-count {
  font-size: 12px;
  color: #374151;
  font-weight: 600;
  margin-left: auto;
  align-self: center;
}

.table-scroll {
  overflow: auto;
  -webkit-overflow-scrolling: touch;
  overscroll-behavior-x: contain;
  max-height: 320px;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  min-width: 0;
}

.table-wrapper.expanded .table-scroll {
  max-height: 520px;
}

.measurements-table {
  width: 100%;
  border-collapse: collapse;
  min-width: 760px;
}

.measurements-table th,
.measurements-table td {
  text-align: left;
  padding: 9px 10px;
  font-size: 12px;
  border-bottom: 1px solid #eef0f3;
  color: #333;
}

.measurements-table thead th {
  position: sticky;
  top: 0;
  background: #f8fafc;
  z-index: 1;
  font-weight: 600;
}

.no-data {
  text-align: center !important;
  color: #6b7280 !important;
}

.alert-chip {
  padding: 3px 8px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 600;
}

.alert-chip.normal {
  background: #e8f5e9;
  color: #2e7d32;
}

.alert-chip.warning {
  background: #ffebee;
  color: #c62828;
}

.table-actions {
  display: flex;
  flex-direction: column;
  gap: 10px;
  align-items: center;
  justify-content: center;
  padding-top: 12px;
}

.pagination-controls {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  justify-content: center;
}

.pagination-btn {
  padding: 8px 12px;
  border-radius: 6px;
  border: 1px solid #66bb6a;
  background: #66bb6a;
  color: white;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}

.pagination-btn:hover:not(:disabled) {
  background: #558a5a;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.pagination-btn:disabled {
  background: #ccc;
  color: #888;
  cursor: not-allowed;
  opacity: 0.6;
}

.pagination-numbers {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
  justify-content: center;
}

.page-number-btn {
  min-width: 36px;
  height: 36px;
  padding: 0 8px;
  border-radius: 4px;
  border: 1px solid #ddd;
  background: #f5f5f5;
  color: #333;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.page-number-btn:hover {
  background: #e8e8e8;
  border-color: #66bb6a;
}

.page-number-btn.active {
  background: #66bb6a;
  color: white;
  border-color: #66bb6a;
  box-shadow: 0 2px 4px rgba(102, 187, 106, 0.3);
}

.pagination-info {
  font-size: 12px;
  color: #666;
  text-align: center;
  width: 100%;
}

.pdf-modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: max(12px, env(safe-area-inset-top, 0px)) max(14px, env(safe-area-inset-right, 0px))
    max(12px, env(safe-area-inset-bottom, 0px)) max(14px, env(safe-area-inset-left, 0px));
  z-index: 40;
  box-sizing: border-box;
}

.pdf-modal {
  width: min(760px, 100%);
  max-height: min(92vh, 100dvh - 24px);
  background: white;
  border-radius: 10px;
  overflow: hidden;
  box-shadow: 0 16px 40px rgba(0, 0, 0, 0.2);
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.pdf-modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 16px;
  border-bottom: 1px solid #e5e7eb;
  flex-shrink: 0;
  gap: 8px;
  min-width: 0;
}

.pdf-modal-header h3 {
  margin: 0;
  font-size: 16px;
}

.modal-close-btn {
  border: none;
  background: transparent;
  font-size: 16px;
  cursor: pointer;
  color: #374151;
}

.pdf-modal-body {
  padding: 14px 16px;
  overflow-y: auto;
  flex: 1;
  min-height: 0;
}

.filter-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 12px;
}

.filter-grid label {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.filter-grid span {
  font-size: 12px;
  color: #4b5563;
  font-weight: 600;
}

.filter-grid select,
.filter-grid input {
  height: 40px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  padding: 0 10px;
  font-size: 16px;
  color: #1f2937;
  width: 100%;
  max-width: 100%;
  min-width: 0;
  box-sizing: border-box;
}

.pdf-preview-text {
  margin: 12px 0 0;
  font-size: 13px;
  color: #374151;
}

.pdf-modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding: 12px 16px max(16px, env(safe-area-inset-bottom, 0px));
  border-top: 1px solid #e5e7eb;
  flex-shrink: 0;
  flex-wrap: wrap;
}

.secondary-btn,
.primary-btn {
  min-width: 120px;
  height: 36px;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
}

.secondary-btn {
  border: 1px solid #d1d5db;
  background: white;
  color: #374151;
}

.primary-btn {
  border: 1px solid #66bb6a;
  background: #66bb6a;
  color: white;
}

.primary-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

@media (max-width: 980px) {
  .history-content {
    grid-template-columns: 1fr;
  }

  .chart-container {
    height: 200px;
  }
}

@media (max-width: 768px) {
  .historical-view {
    height: auto;
    min-height: 100vh;
    min-height: 100dvh;
    max-height: none;
  }

  .history-header {
    padding: 12px 14px;
    flex-direction: column;
    align-items: stretch;
    gap: 10px;
  }

  .header-left {
    justify-content: flex-start;
  }

  .history-header h1 {
    font-size: 18px;
  }

  .pdf-btn {
    width: 100%;
  }

  .history-content {
    padding: 12px;
    gap: 10px;
  }

  .chart-title {
    align-items: flex-start;
    flex-direction: column;
  }

  .chart-title h3 {
    font-size: 13px;
  }

  .period-buttons {
    width: 100%;
  }

  .period-btn {
    flex: 1;
    text-align: center;
  }

  .chart-container {
    height: 185px;
  }

  .measurements {
    flex-wrap: wrap;
    gap: 6px 10px;
    justify-content: space-between;
  }

  .table-wrapper {
    padding: 10px;
  }

  .table-filters {
    flex-direction: column;
    align-items: stretch;
  }

  .table-filter-count {
    margin-left: 0;
  }

  .table-scroll {
    max-height: 280px;
  }

  .table-wrapper.expanded .table-scroll {
    max-height: 420px;
  }

  .pdf-modal {
    width: 100%;
    max-height: min(92vh, 100dvh - 24px);
    overflow: hidden;
  }

  .filter-grid {
    grid-template-columns: 1fr;
  }

  .pdf-modal-actions {
    flex-direction: column;
  }

  .secondary-btn,
  .primary-btn {
    width: 100%;
  }
}

@media (max-width: 480px) {
  .history-header {
    padding: 10px 12px;
  }

  .history-header h1 {
    font-size: 16px;
    line-height: 1.25;
  }

  .back-btn {
    min-width: 40px;
    min-height: 40px;
  }

  .pdf-btn {
    min-height: 44px;
    font-size: 13px;
  }

  .history-content {
    padding: 10px;
    gap: 8px;
  }

  .chart-wrapper {
    padding: 8px;
  }

  .chart-container {
    height: 170px;
  }

  .measurements-table th,
  .measurements-table td {
    padding: 8px 6px;
    font-size: 11px;
  }

  .pdf-modal-header h3 {
    font-size: 14px;
    line-height: 1.3;
  }

  .pdf-modal-body {
    padding: 12px;
  }

  .pdf-preview-text {
    font-size: 12px;
  }
}
</style>
