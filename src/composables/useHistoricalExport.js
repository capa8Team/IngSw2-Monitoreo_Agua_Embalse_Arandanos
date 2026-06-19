import { ref, computed } from 'vue'
import {
  fetchHistoricalExportRows,
  getHistoricalDataSourceLabel,
  IS_SIMULATED_MODE,
} from '../services/historicalDataService.js'
import { useDeviceStore } from '../stores/deviceStore.js'
import { getSimulatedExportDevice } from '../utils/simulatedDeviceStorage.js'

/** Exportación PDF global (todos los dispositivos de la organización). */
export function useHistoricalExport() {
  const deviceStore = useDeviceStore()

  const exportRows        = ref([])
  const registeredDevices = ref([])

  const deviceOptions = computed(() =>
    registeredDevices.value
      .map((d) => String(d.name || '').trim())
      .filter(Boolean)
      .sort((a, b) => a.localeCompare(b, 'es')),
  )

  async function loadRegisteredDevices() {
    if (IS_SIMULATED_MODE) {
      registeredDevices.value = [getSimulatedExportDevice()]
      return
    }

    if (!deviceStore.devices.length) {
      deviceStore.hydrateFromCache()
    }
    if (!deviceStore.devices.length) {
      await deviceStore.fetchDevices()
    }
    registeredDevices.value = deviceStore.devices
  }

  async function prepareExportRows() {
    await loadRegisteredDevices()
    exportRows.value = await fetchHistoricalExportRows(registeredDevices.value)
  }

  return {
    exportRows,
    deviceOptions,
    prepareExportRows,
    dataSourceLabel: getHistoricalDataSourceLabel(),
    isSimulatedMode: IS_SIMULATED_MODE,
  }
}
