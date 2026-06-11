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
  fetchIncrementalReadings,
  mergeHistoricalReadings,
  mergeTableRows,
  maxReadingTimestamp,
  getHistoricalDataSourceLabel,
  readHistoricalCache,
  writeHistoricalCache,
  IS_SIMULATED_MODE,
  POLL_INTERVAL_MS,
  TABLE_LIVE_PAGE_SIZE,
} from '../services/historicalDataService.js'
import { useDeviceStore } from '../stores/deviceStore.js'

export function useHistoricalData() {
  const deviceStore = useDeviceStore()

  const chartSourceReadings = ref([])
  const measurementRows       = ref([])
  const tableTotal            = ref(0)
  const tablePage             = ref(1)
  const tableLoading          = ref(false)
  const exportRows              = ref([])
  const registeredDevices       = ref([])
  const lastPollTimestamp       = ref(null)
  const lastTableDataTimestamp  = ref(null)
  const initialLoading          = ref(false)
  const chartsRefreshing        = ref(false)

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

  const hasChartData = computed(() =>
    chartData.ph.values.length > 0
    || chartData.temperature.values.length > 0
    || chartData.conductivity.values.length > 0,
  )

  function isDefaultTableContext() {
    return tablePage.value === 1
      && tableFilters.mode === 'all'
      && tableFilters.sensor === 'all'
  }

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

  function clearHistoricalState() {
    chartSourceReadings.value = []
    measurementRows.value = []
    tableTotal.value = 0
    tablePage.value = 1
    registeredDevices.value = []
    lastPollTimestamp.value = null
    lastTableDataTimestamp.value = null
    chartData.ph = { labels: [], values: [] }
    chartData.temperature = { labels: [], values: [] }
    chartData.conductivity = { labels: [], values: [] }
  }

  function hydrateFromCache() {
    const cached = readHistoricalCache()
    if (!cached) return false

    if (Array.isArray(cached.chartReadings) && cached.chartReadings.length) {
      chartSourceReadings.value = cached.chartReadings
      syncPollTimestampFromCharts()
    }

    if (isDefaultTableContext() && Array.isArray(cached.tableRows)) {
      measurementRows.value = cached.tableRows
      tableTotal.value = Number(cached.tableTotal) || cached.tableRows.length
      syncTableTimestampFromRows(cached.tableRows)
    }

    if (Array.isArray(cached.registeredDevices) && cached.registeredDevices.length) {
      registeredDevices.value = cached.registeredDevices
    }

    if (chartSourceReadings.value.length) {
      void loadAllChartData()
    }

    return Boolean(
      chartSourceReadings.value.length
      || measurementRows.value.length
      || registeredDevices.value.length,
    )
  }

  function saveToCache() {
    writeHistoricalCache({
      chartReadings: chartSourceReadings.value,
      tableRows: isDefaultTableContext() ? measurementRows.value : undefined,
      tableTotal: isDefaultTableContext() ? tableTotal.value : undefined,
      registeredDevices: registeredDevices.value,
    })
  }

  async function loadRegisteredDevices() {
    if (!deviceStore.devices.length) {
      deviceStore.hydrateFromCache()
    }
    if (!deviceStore.devices.length) {
      await deviceStore.fetchDevices()
    }
    registeredDevices.value = deviceStore.devices
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

  function isLiveTableContext() {
    return tablePage.value === 1
      && tableFilters.mode === 'all'
      && tableFilters.sensor === 'all'
  }

  function syncPollTimestampFromCharts() {
    const maxTs = maxReadingTimestamp(chartSourceReadings.value)
    if (maxTs) {
      lastPollTimestamp.value = new Date(maxTs)
    }
  }

  async function loadChartReadings(full = false) {
    if (full || !chartSourceReadings.value.length) {
      chartSourceReadings.value = await fetchHistoricalReadings()
      chartSourceReadings.value = mergeHistoricalReadings(
        [],
        chartSourceReadings.value,
        registeredDevices.value,
      )
      syncPollTimestampFromCharts()
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
        syncPollTimestampFromCharts()
      }
    }
    await loadAllChartData()
  }

  function syncTableTimestampFromRows(rows) {
    if (!rows?.length) return
    const maxTs = rows.reduce((max, row) => {
      const ts = new Date(row.timestamp).getTime()
      return ts > max ? ts : max
    }, 0)
    if (maxTs) {
      lastTableDataTimestamp.value = new Date(maxTs)
    }
  }

  async function loadTableData({ incremental = false, silent = false } = {}) {
    const useLive = incremental && isLiveTableContext()
    if (!useLive && !silent) {
      tableLoading.value = true
    }
    try {
      const result = await fetchHistoricalTable({
        ...tableQueryParams(),
        registeredDevices: registeredDevices.value,
        live: useLive || (tablePage.value === 1 && tableFilters.mode === 'all'),
        since: useLive ? lastTableDataTimestamp.value : null,
      })
      if (useLive && result.rows.length) {
        measurementRows.value = mergeTableRows(
          measurementRows.value,
          result.rows,
          TABLE_LIVE_PAGE_SIZE,
        )
        tableTotal.value = Math.max(tableTotal.value, measurementRows.value.length)
      } else {
        measurementRows.value = result.rows
        tableTotal.value = result.total
        tablePage.value = result.page
        syncTableTimestampFromRows(result.rows)
      }
    } finally {
      if (!useLive) {
        tableLoading.value = false
      }
    }
  }

  async function prepareExportRows() {
    exportRows.value = await fetchHistoricalExportRows(registeredDevices.value)
  }

  async function refreshHistorical({ full = false, reset = false } = {}) {
    if (reset) {
      clearHistoricalState()
    }
    const hadCachedData = hydrateFromCache()
    initialLoading.value = !hadCachedData
    chartsRefreshing.value = hadCachedData
    if (!hadCachedData) {
      tableLoading.value = true
    }

    try {
      await loadRegisteredDevices()
      await Promise.all([
        loadChartReadings(full),
        loadTableData({ silent: hadCachedData && isDefaultTableContext() }),
      ])
      saveToCache()
    } finally {
      initialLoading.value = false
      chartsRefreshing.value = false
    }
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
        await Promise.all([
          loadChartReadings(false),
          loadTableData({ incremental: true }),
        ])
        saveToCache()
      } catch (err) {
        console.error(err)
      }
    }, POLL_INTERVAL_MS)
  }

  function stopPolling() {
    clearInterval(refreshTimer)
  }

  return {
    measurementRows, exportRows, tableTotal, tablePage, tableLoading, initialLoading,
    chartsRefreshing, hasChartData,
    deviceOptions, registeredDevices,
    dataSourceLabel: getHistoricalDataSourceLabel(),
    pollIntervalMs: POLL_INTERVAL_MS,
    isSimulatedMode: IS_SIMULATED_MODE,
    phPeriod, tempPeriod, condPeriod,
    chartData, chartStats,
    loadTableData, loadAllChartData, loadChartData, refreshHistorical,
    onTablePageChange, onTableFiltersChange, prepareExportRows,
    startPolling, stopPolling,
  }
}
