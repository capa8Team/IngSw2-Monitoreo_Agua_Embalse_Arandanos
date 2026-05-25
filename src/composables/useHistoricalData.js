import { ref, reactive, computed, watch } from 'vue'
import { SENSOR_META, flattenMeasurements } from '../utils/sensorUtils.js'
import { fetchSensorReadings, fetchDashboardSnapshot } from '../services/historicalDataService.js'

export function useHistoricalData() {
  const normalizedReadings = ref([])
  const measurementRows    = ref([])

  const phPeriod   = ref('day')
  const tempPeriod = ref('day')
  const condPeriod = ref('day')

  const chartStats = reactive({
    ph:           { max: 8.5,  min: 6.0, avg: 7.2   },
    temperature:  { max: 28,   min: 18,  avg: 22.5  },
    conductivity: { max: 1500, min: 800, avg: 1100  },
  })

  const chartData = reactive({
    ph:           { labels: [], values: [] },
    temperature:  { labels: [], values: [] },
    conductivity: { labels: [], values: [] },
  })

  const deviceOptions = computed(() =>
    [...new Set(normalizedReadings.value.map(r => r.device))].sort((a, b) => a.localeCompare(b))
  )

  async function loadTableData() {
    const records = await fetchSensorReadings()
    normalizedReadings.value = records.sort((a, b) => b.timestamp - a.timestamp)
    measurementRows.value = flattenMeasurements(normalizedReadings.value)
  }

  async function loadChartData(sensorKey, period) {
    const meta = SENSOR_META[sensorKey]
    let baseValue = (meta.min + meta.max) / 2

    try {
      const snap = await fetchDashboardSnapshot()
      baseValue = snap[sensorKey]?.value ?? baseValue
    } catch { /* use midpoint default */ }

    const count    = period === 'day' ? 24 : 7
    const variance = (meta.max - meta.min) * 0.05
    const now      = new Date()
    const labels   = []
    const values   = []

    for (let i = 0; i < count; i++) {
      const d = new Date(now)
      if (period === 'day') {
        d.setHours(i, 0, 0, 0)
        labels.push(`${String(i).padStart(2, '0')}:00`)
      } else {
        d.setDate(d.getDate() - (count - 1 - i))
        labels.push(d.toLocaleDateString('es-ES', { weekday: 'short' }))
      }
      const v = baseValue + (Math.random() - 0.5) * variance
      values.push(Math.max(meta.min, Math.min(meta.max, v)))
    }

    chartData[sensorKey] = { labels, values }
    chartStats[sensorKey] = {
      max: Math.max(...values),
      min: Math.min(...values),
      avg: values.reduce((a, b) => a + b, 0) / values.length,
    }
  }

  async function loadAllChartData() {
    await Promise.all([
      loadChartData('ph', phPeriod.value),
      loadChartData('temperature', tempPeriod.value),
      loadChartData('conductivity', condPeriod.value),
    ])
  }

  watch(phPeriod,   p => loadChartData('ph', p))
  watch(tempPeriod, p => loadChartData('temperature', p))
  watch(condPeriod, p => loadChartData('conductivity', p))

  let chartTimer = null
  let tableTimer = null

  function startPolling() {
    chartTimer = setInterval(() => loadAllChartData().catch(console.error), 5000)
    tableTimer = setInterval(() => loadTableData().catch(console.error), 30000)
  }

  function stopPolling() {
    clearInterval(chartTimer)
    clearInterval(tableTimer)
  }

  return {
    normalizedReadings, measurementRows, deviceOptions,
    phPeriod, tempPeriod, condPeriod,
    chartData, chartStats,
    loadTableData, loadAllChartData, loadChartData,
    startPolling, stopPolling,
  }
}
