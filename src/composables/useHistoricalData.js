import { ref, reactive, computed, watch } from 'vue'
import {
  flattenMeasurements,
  buildChartSeriesFromReadings,
  computeChartStats,
  expandReadingsForRegisteredDevices,
  readingsForCharts,
} from '../utils/sensorUtils.js'
import { fetchSensorReadings, fetchActiveDevices } from '../services/historicalDataService.js'

export function useHistoricalData() {
  const normalizedReadings = ref([])
  const chartSourceReadings  = ref([])
  const measurementRows      = ref([])
  const registeredDevices    = ref([])

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

  /** Nombres en pantalla (Norte, Dispositivo 1, …) para el PDF. */
  const deviceOptions = computed(() =>
    registeredDevices.value
      .map((d) => String(d.name || '').trim())
      .filter(Boolean)
      .sort((a, b) => a.localeCompare(b, 'es'))
  )

  async function loadRegisteredDevices() {
    registeredDevices.value = await fetchActiveDevices()
  }

  async function loadTableData() {
    const records = await fetchSensorReadings()
    const sorted = records.sort((a, b) => b.timestamp - a.timestamp)
    const registered = registeredDevices.value

    chartSourceReadings.value = readingsForCharts(sorted, registered)
    normalizedReadings.value = expandReadingsForRegisteredDevices(sorted, registered)
    measurementRows.value = flattenMeasurements(normalizedReadings.value)
  }

  function loadChartData(sensorKey, period) {
    const series = buildChartSeriesFromReadings(chartSourceReadings.value, sensorKey, period)
    chartData[sensorKey] = series
    chartStats[sensorKey] = computeChartStats(series.values, sensorKey)
  }

  async function loadAllChartData() {
    await Promise.all([
      loadChartData('ph', phPeriod.value),
      loadChartData('temperature', tempPeriod.value),
      loadChartData('conductivity', condPeriod.value),
    ])
  }

  async function refreshHistorical() {
    await loadRegisteredDevices()
    await loadTableData()
    await loadAllChartData()
  }

  watch(phPeriod,   p => loadChartData('ph', p))
  watch(tempPeriod, p => loadChartData('temperature', p))
  watch(condPeriod, p => loadChartData('conductivity', p))

  let refreshTimer = null

  function startPolling() {
    refreshTimer = setInterval(() => refreshHistorical().catch(console.error), 5000)
  }

  function stopPolling() {
    clearInterval(refreshTimer)
  }

  return {
    normalizedReadings, chartSourceReadings, measurementRows,
    deviceOptions, registeredDevices,
    phPeriod, tempPeriod, condPeriod,
    chartData, chartStats,
    loadTableData, loadAllChartData, loadChartData, refreshHistorical,
    startPolling, stopPolling,
  }
}
