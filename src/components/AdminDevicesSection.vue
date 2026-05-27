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
      arduino_id: deviceData.arduino_id || null,
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
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 24px;
}

.btn {
  padding: 10px 16px;
  border: none;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  font-size: 14px;
}

.btn-detect {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.btn-detect:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 12px rgba(102, 126, 234, 0.4);
}

.btn-add {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  color: white;
}

.btn-add:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 12px rgba(245, 87, 108, 0.4);
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
