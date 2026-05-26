import { ref, computed, watch } from 'vue'
import { useDeviceStore } from '../stores/deviceStore'

/**
 * Composable para gestionar dispositivos y detección automática de microcontroladores
 */
export function useDeviceManagement() {
  const deviceStore = useDeviceStore()

  const newDeviceForm = ref({
    name: '',
    device_type: 'ESP8266',
    location: '',
    arduino_id: ''
  })

  const showAddModal = ref(false)
  const showDetectionModal = ref(false)
  const detectionInProgress = ref(false)
  const detectionMessage = ref('')

  // Validaciones
  const isFormValid = computed(() => {
    return newDeviceForm.value.name && newDeviceForm.value.name.trim().length > 0
  })

  const resetForm = () => {
    newDeviceForm.value = {
      name: '',
      device_type: 'ESP8266',
      location: '',
      arduino_id: ''
    }
  }

  const openAddModal = () => {
    resetForm()
    showAddModal.value = true
  }

  const closeAddModal = () => {
    showAddModal.value = false
    resetForm()
  }

  const openDetectionModal = () => {
    showDetectionModal.value = true
    detectionMessage.value = 'Buscando nuevos microcontroladores...'
    detectionInProgress.value = true
    scanForNewDevices()
  }

  const closeDetectionModal = () => {
    showDetectionModal.value = false
    detectionInProgress.value = false
    detectionMessage.value = ''
  }

  /**
   * Escanea y detecta nuevos microcontroladores disponibles
   */
  const scanForNewDevices = async () => {
    try {
      detectionInProgress.value = true
      detectionMessage.value = 'Escaneando dispositivos disponibles...'

      const result = await deviceStore.getAvailableMicrocontrollers()

      if (result.total > 0) {
        detectionMessage.value = `Se encontraron ${result.total} nuevo(s) dispositivo(s). Selecciona uno para registrar.`
      } else {
        detectionMessage.value = 'No hay nuevos microcontroladores disponibles. Asegúrate de que el dispositivo esté enviando datos.'
      }
    } catch (error) {
      detectionMessage.value = `Error escaneando: ${error.message}`
      console.error('Error en escaneo:', error)
    } finally {
      detectionInProgress.value = false
    }
  }

  /**
   * Registra un nuevo microcontrolador detectado
   */
  const registerDetectedDevice = async (arduinoId, customName = null) => {
    try {
      const detectionData = {
        arduino_id: arduinoId,
        device_name: customName || `Dispositivo ${arduinoId}`,
        device_type: 'ESP8266',
        location: ''
      }

      const detected = await deviceStore.detectMicrocontroller(detectionData)
      
      detectionMessage.value = `✓ Dispositivo registrado: ${detected.name}`
      
      // Limpiar la lista de disponibles
      deviceStore.availableMicrocontrollers = 
        deviceStore.availableMicrocontrollers.filter(id => id !== arduinoId)

      return detected
    } catch (error) {
      detectionMessage.value = `Error registrando dispositivo: ${error.message}`
      console.error('Error registrando:', error)
      throw error
    }
  }

  /**
   * Crea un nuevo dispositivo manualmente
   */
  const addNewDevice = async () => {
    if (!isFormValid.value) {
      console.warn('Formulario inválido')
      return
    }

    try {
      const device = await deviceStore.createDevice({
        name: newDeviceForm.value.name,
        device_type: newDeviceForm.value.device_type,
        location: newDeviceForm.value.location,
        arduino_id: newDeviceForm.value.arduino_id || null
      })

      closeAddModal()
      return device
    } catch (error) {
      console.error('Error creando dispositivo:', error)
      throw error
    }
  }

  /**
   * Actualiza un dispositivo existente
   */
  const updateExistingDevice = async (deviceId, updateData) => {
    try {
      return await deviceStore.updateDevice(deviceId, updateData)
    } catch (error) {
      console.error('Error actualizando dispositivo:', error)
      throw error
    }
  }

  /**
   * Elimina un dispositivo
   */
  const removeDevice = async (deviceId) => {
    if (!confirm('¿Estás seguro de que deseas eliminar este dispositivo?')) {
      return false
    }

    try {
      await deviceStore.deleteDevice(deviceId)
      return true
    } catch (error) {
      console.error('Error eliminando dispositivo:', error)
      throw error
    }
  }

  /**
   * Obtiene el estado del dispositivo con emojis/iconos
   */
  const getDeviceStatusIcon = (device) => {
    if (device.status === 'online') return '🟢'
    if (device.status === 'offline') return '🔴'
    return '⚫'
  }

  const getDeviceStatusText = (device) => {
    if (device.status === 'online') return 'Conectado'
    if (device.status === 'offline') return 'Desconectado'
    return 'Desconocido'
  }

  /**
   * Obtiene el tipo de dispositivo con nombre legible
   */
  const getDeviceTypeName = (type) => {
    const typeMap = {
      'ESP8266': 'ESP8266 (WiFi)',
      'Arduino': 'Arduino',
      'STM32': 'STM32',
      'other': 'Otro'
    }
    return typeMap[type] || type
  }

  return {
    // State
    newDeviceForm,
    showAddModal,
    showDetectionModal,
    detectionInProgress,
    detectionMessage,

    // Computed
    isFormValid,
    devices: computed(() => deviceStore.devices),
    activeDevices: computed(() => deviceStore.activeDevices),
    offlineDevices: computed(() => deviceStore.offlineDevices),
    deviceCount: computed(() => deviceStore.deviceCount),
    activeDeviceCount: computed(() => deviceStore.activeDeviceCount),
    loading: computed(() => deviceStore.loading),
    error: computed(() => deviceStore.error),
    availableMicrocontrollers: computed(() => deviceStore.availableMicrocontrollers),

    // Methods
    resetForm,
    openAddModal,
    closeAddModal,
    openDetectionModal,
    closeDetectionModal,
    scanForNewDevices,
    registerDetectedDevice,
    addNewDevice,
    updateExistingDevice,
    removeDevice,
    getDeviceStatusIcon,
    getDeviceStatusText,
    getDeviceTypeName
  }
}
