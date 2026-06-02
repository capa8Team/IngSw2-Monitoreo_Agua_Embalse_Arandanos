import { ref, reactive, computed, watch } from 'vue'
import {
  buildChartSeriesFromReadings,
  computeChartStats,
  localDateKey,
} from '../utils/sensorUtils.js'
import {
  fetchHistoricalReadings,
  fetchHistoricalTable,
  fetchHistoricalExportRows,
  fetchActiveDevices,
  fetchIncrementalReadings,
  mergeHistoricalReadings,
  getHistoricalDataSourceLabel,
  IS_SIMULATED_MODE,
  POLL_INTERVAL_MS,
} from '../services/historicalDataService.js'

export function useHistoricalData() {
  const chartSourceReadings = ref([])
  const measurementRows       = ref([])
  const tableTotal            = ref(0)
  const tablePage             = ref(1)
  const tableLoading          = ref(false)
  const exportRows              = ref([])
  const registeredDevices       = ref([])
  const lastPollTimestamp       = ref(null)

  const tableFilters = reactive({
    sensor:    'all',
    mode:      'all',
    day:       localDateKey(new Date()),
    startDate: localDateKey(new Date(Date.now() - 6 * 24 * 60 * 60 * 1000)),
    endDate:   localDateKey(new Date()),
  })

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
    registeredDevices.value
      .map((d) => String(d.name || '').trim())
      .filter(Boolean)
      .sort((a, b) => a.localeCompare(b, 'es'))
  )

  function tableQueryParams() {
    const params = {
      page:     tablePage.value,
      pageSize: 10,
      sensor:   tableFilters.sensor,
    }
    if (tableFilters.mode === 'day') {
      params.dateFrom = tableFilters.day
      params.dateTo   = tableFilters.day
    } else if (tableFilters.mode === 'range') {
      params.dateFrom = tableFilters.startDate || null
      params.dateTo   = tableFilters.endDate || null
    }
    return params
  }

  async function loadRegisteredDevices() {
    registeredDevices.value = await fetchActiveDevices()
  }

  async function loadChartData(sensorKey, period) {
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

  async function loadChartReadings(full = false) {
    if (full || !chartSourceReadings.value.length) {
      chartSourceReadings.value = await fetchHistoricalReadings()
      chartSourceReadings.value = mergeHistoricalReadings(
        [],
        chartSourceReadings.value,
        registeredDevices.value,
      )
    } else if (lastPollTimestamp.value) {
      const incoming = await fetchIncrementalReadings(
        lastPollTimestamp.value,
        registeredDevices.value,
      )
      if (incoming.length) {
        chartSourceReadings.value = mergeHistoricalReadings(
          chartSourceReadings.value,
          incoming,
          registeredDevices.value,
        )
      }
    }
    lastPollTimestamp.value = new Date()
    await loadAllChartData()
  }

  async function loadTableData() {
    tableLoading.value = true
    try {
      const result = await fetchHistoricalTable({
        ...tableQueryParams(),
        registeredDevices: registeredDevices.value,
      })
      measurementRows.value = result.rows
      tableTotal.value = result.total
      tablePage.value = result.page
    } finally {
      tableLoading.value = false
    }
  }

  async function prepareExportRows() {
    exportRows.value = await fetchHistoricalExportRows(registeredDevices.value)
  }

  async function refreshHistorical({ full = false } = {}) {
    await loadRegisteredDevices()
    await loadChartReadings(full)
    await loadTableData()
  }

  async function onTablePageChange(page) {
    tablePage.value = page
    await loadTableData()
  }

  async function onTableFiltersChange(filters) {
    Object.assign(tableFilters, filters)
    tablePage.value = 1
    await loadTableData()
  }

  watch(phPeriod,   (p) => loadChartData('ph', p))
  watch(tempPeriod, (p) => loadChartData('temperature', p))
  watch(condPeriod, (p) => loadChartData('conductivity', p))

  let refreshTimer = null

  function startPolling() {
    refreshTimer = setInterval(async () => {
      try {
        await loadChartReadings(false)
        await loadTableData()
      } catch (err) {
        console.error(err)
      }
    }, POLL_INTERVAL_MS)
  }

  function stopPolling() {
    clearInterval(refreshTimer)
  }

  return {
    measurementRows, exportRows, tableTotal, tablePage, tableLoading, tableFilters,
    deviceOptions, registeredDevices,
    dataSourceLabel: getHistoricalDataSourceLabel(),
    isSimulatedMode: IS_SIMULATED_MODE,
    phPeriod, tempPeriod, condPeriod,
    chartData, chartStats,
    loadTableData, loadAllChartData, loadChartData, refreshHistorical,
    onTablePageChange, onTableFiltersChange, prepareExportRows,
    startPolling, stopPolling,
  }
}
