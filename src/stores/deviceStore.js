import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getApiAuthHeaders } from '../services/apiContext.js'

export const useDeviceStore = defineStore('device', () => {
  // State
  const devices = ref([])
  const loading = ref(false)
  const error = ref(null)
  const selectedDevice = ref(null)
  const availableMicrocontrollers = ref([])

  // Computed
  const activeDevices = computed(() => 
    devices.value.filter(d => d.active)
  )

  const offlineDevices = computed(() =>
    devices.value.filter(d => d.status === 'offline')
  )

  const deviceCount = computed(() => devices.value.length)

  const activeDeviceCount = computed(() => activeDevices.value.length)

  // Actions
  const fetchDevices = async (apiUrl = '') => {
    loading.value = true
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
      
      return devices.value
    } catch (err) {
      error.value = err.message
      console.error('[DeviceStore] Error fetching devices:', err)
      return []
    } finally {
      loading.value = false
    }
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
