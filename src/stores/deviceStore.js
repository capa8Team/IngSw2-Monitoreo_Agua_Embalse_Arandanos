import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getActiveOrganizationId, getApiAuthHeaders } from '../services/apiContext.js'

const DEVICES_CACHE_PREFIX = 'devicesCache:'

function devicesCacheKey(orgId) {
  return orgId ? `${DEVICES_CACHE_PREFIX}${orgId}` : ''
}

function readDevicesCache(orgId) {
  const key = devicesCacheKey(orgId)
  if (!key) return null
  try {
    let raw = localStorage.getItem(key)
    if (!raw) raw = sessionStorage.getItem(key)
    if (!raw) return null
    const parsed = JSON.parse(raw)
    return Array.isArray(parsed) ? parsed : null
  } catch {
    return null
  }
}

function writeDevicesCache(orgId, list) {
  const key = devicesCacheKey(orgId)
  if (!key || !Array.isArray(list)) return
  try {
    localStorage.setItem(key, JSON.stringify(list))
    sessionStorage.removeItem(key)
  } catch {
    // almacenamiento lleno o no disponible
  }
}

export const useDeviceStore = defineStore('device', () => {
  // State
  const devices = ref([])
  const loading = ref(false)
  const error = ref(null)
  const selectedDevice = ref(null)
  const availableMicrocontrollers = ref([])
  let fetchInFlight = null

  // Computed
  const activeDevices = computed(() => 
    devices.value.filter(d => d.active)
  )

  const offlineDevices = computed(() =>
    devices.value.filter(d => d.status === 'offline')
  )

  const deviceCount = computed(() => devices.value.length)

  const activeDeviceCount = computed(() => activeDevices.value.length)

  const hydrateFromCache = (orgId = getActiveOrganizationId()) => {
    const cached = readDevicesCache(orgId)
    if (cached?.length) {
      devices.value = cached
      return true
    }
    return false
  }

  const prefetchDevicesForActiveOrg = (apiUrl = '') => {
    const orgId = getActiveOrganizationId()
    if (!devices.value.length) {
      hydrateFromCache(orgId)
    }
    void fetchDevices(apiUrl)
  }

  // Actions
  const fetchDevices = async (apiUrl = '') => {
    if (fetchInFlight) return fetchInFlight

    const orgId = getActiveOrganizationId()
    if (!devices.value.length) {
      hydrateFromCache(orgId)
    }

    fetchInFlight = (async () => {
      const hadCachedDevices = devices.value.length > 0
      if (!hadCachedDevices) {
        loading.value = true
      }
      error.value = null

      try {
        const url = apiUrl || `${import.meta.env.VITE_API_URL || ''}/api/devices`
        const response = await fetch(url, { headers: getApiAuthHeaders() })

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`)
        }

        const data = await response.json()
        devices.value = Array.isArray(data)
          ? data.filter((d) => d.active !== false)
          : []

        writeDevicesCache(orgId, devices.value)
        return devices.value
      } catch (err) {
        error.value = err.message
        console.error('[DeviceStore] Error fetching devices:', err)
        return devices.value
      } finally {
        loading.value = false
        fetchInFlight = null
      }
    })()

    return fetchInFlight
  }

  const createDevice = async (deviceData) => {
    loading.value = true
    error.value = null
    
    try {
      const apiUrl = import.meta.env.VITE_API_URL || ''
      const response = await fetch(`${apiUrl}/api/devices`, {
        method: 'POST',
        headers: getApiAuthHeaders({ 'Content-Type': 'application/json' }),
        body: JSON.stringify(deviceData)
      })
      
      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || `HTTP ${response.status}`)
      }
      
      const newDevice = await response.json()
      devices.value.push(newDevice)
      writeDevicesCache(getActiveOrganizationId(), devices.value)

      return newDevice
    } catch (err) {
      error.value = err.message
      console.error('[DeviceStore] Error creating device:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  const updateDevice = async (deviceId, updateData) => {
    loading.value = true
    error.value = null
    
    try {
      const apiUrl = import.meta.env.VITE_API_URL || ''
      const response = await fetch(`${apiUrl}/api/devices/${deviceId}`, {
        method: 'PUT',
        headers: getApiAuthHeaders({ 'Content-Type': 'application/json' }),
        body: JSON.stringify(updateData)
      })
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }
      
      const updated = await response.json()
      const index = devices.value.findIndex(d => d.id === deviceId)
      if (index !== -1) {
        devices.value[index] = updated
      }
      writeDevicesCache(getActiveOrganizationId(), devices.value)

      return updated
    } catch (err) {
      error.value = err.message
      console.error('[DeviceStore] Error updating device:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  const deleteDevice = async (deviceId) => {
    loading.value = true
    error.value = null
    
    try {
      const apiUrl = import.meta.env.VITE_API_URL || ''
      const response = await fetch(`${apiUrl}/api/devices/${deviceId}`, {
        method: 'DELETE',
        headers: getApiAuthHeaders(),
      })
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }
      
      devices.value = devices.value.filter(d => d.id !== deviceId)
      writeDevicesCache(getActiveOrganizationId(), devices.value)

      if (selectedDevice.value?.id === deviceId) {
        selectedDevice.value = null
      }
      
      return true
    } catch (err) {
      error.value = err.message
      console.error('[DeviceStore] Error deleting device:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  const detectMicrocontroller = async (detectionData) => {
    loading.value = true
    error.value = null
    
    try {
      const apiUrl = import.meta.env.VITE_API_URL || ''
      const response = await fetch(`${apiUrl}/api/devices/detect`, {
        method: 'POST',
        headers: getApiAuthHeaders({ 'Content-Type': 'application/json' }),
        body: JSON.stringify(detectionData)
      })
      
      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || `HTTP ${response.status}`)
      }
      
      const detected = await response.json()
      
      // Agregar o actualizar en la lista
      const index = devices.value.findIndex(d => d.id === detected.id)
      if (index !== -1) {
        devices.value[index] = detected
      } else {
        devices.value.push(detected)
      }
      writeDevicesCache(getActiveOrganizationId(), devices.value)

      return detected
    } catch (err) {
      error.value = err.message
      console.error('[DeviceStore] Error detecting microcontroller:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  const getAvailableMicrocontrollers = async () => {
    loading.value = true
    error.value = null
    
    try {
      const apiUrl = import.meta.env.VITE_API_URL || ''
      const response = await fetch(`${apiUrl}/api/devices/detect-available`, {
        headers: getApiAuthHeaders(),
      })
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }
      
      const data = await response.json()
      availableMicrocontrollers.value = data.available || []
      
      return {
        available: data.available,
        total: data.total,
        message: data.message
      }
    } catch (err) {
      error.value = err.message
      console.error('[DeviceStore] Error getting available microcontrollers:', err)
      return { available: [], total: 0 }
    } finally {
      loading.value = false
    }
  }

  const selectDevice = (device) => {
    selectedDevice.value = device
  }

  const clearSelection = () => {
    selectedDevice.value = null
  }

  const reset = () => {
    devices.value = []
    loading.value = false
    error.value = null
    selectedDevice.value = null
    availableMicrocontrollers.value = []
  }

  return {
    // State
    devices,
    loading,
    error,
    selectedDevice,
    availableMicrocontrollers,

    // Computed
    activeDevices,
    offlineDevices,
    deviceCount,
    activeDeviceCount,

    // Actions
    hydrateFromCache,
    prefetchDevicesForActiveOrg,
    fetchDevices,
    createDevice,
    updateDevice,
    deleteDevice,
    detectMicrocontroller,
    getAvailableMicrocontrollers,
    selectDevice,
    clearSelection,
    reset
  }
})
