<template>
  <div>
    <!-- Solo botones de acción -->
    <div v-if="isAdmin" class="admin-buttons-container">
      <button class="btn btn-detect" @click="openDetectionModal" :disabled="loading" title="Detectar nuevos dispositivos">
        <span>🔍 Detectar Nuevos</span>
      </button>
      <button class="btn btn-add" @click="openAddModal" :disabled="loading" title="Agregar dispositivo manualmente">
        <span>➕ Agregar Manual</span>
      </button>
    </div>

    <!-- Modales (siempre disponibles) -->
    <AddDeviceModal
      v-if="isAdmin"
      :show="showAddModal"
      title="Agregar Nuevo Dispositivo"
      @close="closeAddModal"
      @submit="handleAddDevice"
    />

    <!-- Modal Detección Automática -->
    <DeviceDetectionModal
      v-if="isAdmin"
      :show="showDetectionModal"
      :available-microcontrollers="availableMicrocontrollers"
      :is-detecting="detectionInProgress"
      :detection-message="detectionMessage"
      @close="closeDetectionModal"
      @detect="scanForNewDevices"
      @register="registerDetectedDevice"
    />
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useDeviceStore } from '../stores/deviceStore'
import AddDeviceModal from './AddDeviceModal.vue'
import DeviceDetectionModal from './DeviceDetectionModal.vue'

const emit = defineEmits(['devices-changed'])

const props = defineProps({
  showSection: {
    type: Boolean,
    default: true
  },
  triggerOpenModal: {
    type: Boolean,
    default: false
  },
  isAdmin: {
    type: Boolean,
    default: false
  }
})

const deviceStore = useDeviceStore()

// Propiedades computadas
const isAdmin = computed(() => props.isAdmin)
const loading = computed(() => deviceStore.loading)
const availableMicrocontrollers = computed(() => deviceStore.availableMicrocontrollers)

// Estado local
const showAddModal = ref(false)
const showDetectionModal = ref(false)
const detectionInProgress = ref(false)
const detectionMessage = ref('')

// Métodos
const openAddModal = () => {
  showAddModal.value = true
}

const closeAddModal = () => {
  showAddModal.value = false
}

const openDetectionModal = () => {
  showDetectionModal.value = true
  scanForNewDevices()
}

const closeDetectionModal = () => {
  showDetectionModal.value = false
  detectionInProgress.value = false
}

const handleAddDevice = async (deviceData) => {
  try {
    await deviceStore.createDevice({
      name: deviceData.name,
      device_type: deviceData.device_type,
      location: deviceData.location || '',
      city: deviceData.city || '',
      arduino_id: deviceData.arduino_id || null,
      telemetry_key: deviceData.telemetry_key || null,
      topic: deviceData.topic || null,
    })
    closeAddModal()
    emit('devices-changed')
  } catch (error) {
    console.error('Error creating device:', error)
    throw error
  }
}

const scanForNewDevices = async () => {
  try {
    detectionInProgress.value = true
    detectionMessage.value = 'Escaneando dispositivos disponibles...'
    await deviceStore.getAvailableMicrocontrollers()
    
    if (availableMicrocontrollers.value.length > 0) {
      detectionMessage.value = `Se encontraron ${availableMicrocontrollers.value.length} nuevo(s) dispositivo(s)`
    } else {
      detectionMessage.value = 'No hay nuevos microcontroladores disponibles'
    }
  } catch (error) {
    detectionMessage.value = `Error: ${error.message}`
  } finally {
    detectionInProgress.value = false
  }
}

const registerDetectedDevice = async (arduinoId, customName) => {
  try {
    const detectionData = {
      arduino_id: arduinoId,
      device_name: customName || `Dispositivo ${arduinoId}`,
      device_type: 'ESP8266',
      location: ''
    }
    await deviceStore.detectMicrocontroller(detectionData)
    emit('devices-changed')
  } catch (error) {
    console.error('Error registering device:', error)
    throw error
  }
}

// Monitorear cambios en triggerOpenModal para abrir el modal desde el padre
watch(() => props.triggerOpenModal, (newVal) => {
  if (newVal === true && isAdmin.value) {
    openAddModal()
  }
})

// Exponer métodos públicos para usar desde otros componentes
defineExpose({
  openAddModal,
  openDetectionModal,
  closeAddModal,
  closeDetectionModal
})
</script>

<style scoped>
.admin-buttons-container {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  margin-bottom: 24px;
}

.btn {
  padding: 10px 14px;
  border-radius: 8px;
  font-weight: 700;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s ease;
  font-family: inherit;
}

.btn-detect {
  border: 1px solid #66bb6a;
  background: #ffffff;
  color: #2e7d32;
}

.btn-detect:hover:not(:disabled) {
  background: #e8f5e9;
}

.btn-add {
  border: 1px solid #66bb6a;
  background: #66bb6a;
  color: #ffffff;
}

.btn-add:hover:not(:disabled) {
  background: #558a5a;
  border-color: #558a5a;
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(102, 187, 106, 0.25);
}

.btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}
</style>
