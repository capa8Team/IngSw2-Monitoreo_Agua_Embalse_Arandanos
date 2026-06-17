import { ref, reactive, computed, watch, unref } from 'vue'
import {
  buildChartSeriesFromReadings,
  computeChartStats,
  readingMatchesDeviceTelemetry,
} from '../utils/sensorUtils.js'
import {
  fetchHistoricalReadings,
  fetchIncrementalReadings,
  mergeHistoricalReadings,
  maxReadingTimestamp,
  readHistoricalCache,
  writeHistoricalCache,
  IS_SIMULATED_MODE,
  POLL_INTERVAL_MS,
} from '../services/historicalDataService.js'
import { useDeviceStore } from '../stores/deviceStore.js'

/**
 * Gráficos históricos (pH, temperatura, conductividad) acotados a un dispositivo.
 * @param {import('vue').MaybeRefOrGetter<string|null|undefined>} arduinoIdRef - Clave MQTT/arduino del dispositivo
 * @param {import('vue').MaybeRefOrGetter<object|null|undefined>} deviceRef - Objeto dispositivo registrado (para alias de telemetría)
 */
export function useDeviceHistoricalCharts(arduinoIdRef, deviceRef) {
  const deviceStore = useDeviceStore()

  const chartSourceReadings = ref([])
  const registeredDevice    = ref(null)
  const lastPollTimestamp   = ref(null)
  const initialLoading      = ref(false)
  const chartsRefreshing    = ref(false)

  const phPeriod   = ref('day')
  const tempPeriod = ref('day')
  const condPeriod = ref('day')

  const chartStats = reactive({
    ph:           { max: 0, min: 0, avg: 0 },
    temperature:  { max: 0, min: 0, avg: 0 },
    conductivity: { max: 0, min: 0, avg: 0 },
  })

  const chartData = reactive({
    ph:           { labels: [], values: [] },
    temperature:  { labels: [], values: [] },
    conductivity: { labels: [], values: [] },
  })

  const hasChartData = computed(() =>
    chartData.ph.values.length > 0
    || chartData.temperature.values.length > 0
    || chartData.conductivity.values.length > 0,
  )

  function resolveArduinoId() {
    return String(unref(arduinoIdRef) ?? '').trim() || null
  }

  function resolveDevice() {
    return unref(deviceRef) ?? null
  }

  function registeredDevicesList() {
    const device = resolveDevice()
    return device ? [device] : registeredDevice.value ? [registeredDevice.value] : []
  }

  function filterReadingsForDevice(readings) {
    const device = resolveDevice()
    if (!device) return readings
    return readings.filter((record) => readingMatchesDeviceTelemetry(record.device, device))
  }

  function clearChartState() {
    chartSourceReadings.value = []
    lastPollTimestamp.value = null
    chartData.ph = { labels: [], values: [] }
    chartData.temperature = { labels: [], values: [] }
    chartData.conductivity = { labels: [], values: [] }
  }

  function hydrateFromCache() {
    const arduinoId = resolveArduinoId()
    const cached = readHistoricalCache(undefined, arduinoId)
    if (!cached?.chartReadings?.length) return false

    chartSourceReadings.value = cached.chartReadings
    if (cached.registeredDevice) {
      registeredDevice.value = cached.registeredDevice
    }
    syncPollTimestampFromCharts()
    void loadAllChartData()
    return true
  }

  function saveToCache() {
    const arduinoId = resolveArduinoId()
    writeHistoricalCache({
      chartReadings: chartSourceReadings.value,
      registeredDevice: registeredDevice.value,
    }, undefined, arduinoId)
  }

  async function loadRegisteredDevice() {
    const device = resolveDevice()
    if (device) {
      registeredDevice.value = device
      return
    }
    if (!deviceStore.devices.length) {
      deviceStore.hydrateFromCache()
    }
    if (!deviceStore.devices.length) {
      await deviceStore.fetchDevices()
    }
    const arduinoId = resolveArduinoId()
    registeredDevice.value = deviceStore.devices.find((d) => {
      const keys = [d.telemetry_key, d.arduino_id, d.name].map((v) => String(v ?? '').trim()).filter(Boolean)
      return keys.includes(arduinoId)
    }) ?? null
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

  function syncPollTimestampFromCharts() {
    const maxTs = maxReadingTimestamp(chartSourceReadings.value)
    if (maxTs) {
      lastPollTimestamp.value = new Date(maxTs)
    }
  }

  async function loadChartReadings(full = false) {
    const arduinoId = resolveArduinoId()
    if (!arduinoId) {
      clearChartState()
      return
    }

    const devices = registeredDevicesList()

    if (full || !chartSourceReadings.value.length) {
      const raw = await fetchHistoricalReadings({ arduinoId })
      const scoped = filterReadingsForDevice(raw)
      chartSourceReadings.value = mergeHistoricalReadings([], scoped, devices)
      syncPollTimestampFromCharts()
    } else if (lastPollTimestamp.value) {
      const incoming = await fetchIncrementalReadings(
        lastPollTimestamp.value,
        devices,
        arduinoId,
      )
      if (incoming.length) {
        chartSourceReadings.value = mergeHistoricalReadings(
          chartSourceReadings.value,
          incoming,
          devices,
        )
        syncPollTimestampFromCharts()
      }
    }
    await loadAllChartData()
  }

  async function refreshCharts({ full = false, reset = false } = {}) {
    const arduinoId = resolveArduinoId()
    if (!arduinoId) {
      clearChartState()
      return
    }

    if (reset) {
      clearChartState()
    }

    const hadCachedData = !reset && hydrateFromCache()
    initialLoading.value = !hadCachedData
    chartsRefreshing.value = hadCachedData

    try {
      await loadRegisteredDevice()
      await loadChartReadings(full)
      saveToCache()
    } finally {
      initialLoading.value = false
      chartsRefreshing.value = false
    }
  }

  watch(phPeriod,   (p) => loadChartData('ph', p))
  watch(tempPeriod, (p) => loadChartData('temperature', p))
  watch(condPeriod, (p) => loadChartData('conductivity', p))

  let refreshTimer = null

  function startPolling() {
    stopPolling()
    refreshTimer = setInterval(async () => {
      try {
        await loadChartReadings(false)
        saveToCache()
      } catch (err) {
        console.error(err)
      }
    }, POLL_INTERVAL_MS)
  }

  function stopPolling() {
    if (refreshTimer) {
      clearInterval(refreshTimer)
      refreshTimer = null
    }
  }

  return {
    phPeriod, tempPeriod, condPeriod,
    chartData, chartStats,
    initialLoading, chartsRefreshing, hasChartData,
    isSimulatedMode: IS_SIMULATED_MODE,
    refreshCharts, startPolling, stopPolling,
  }
}
