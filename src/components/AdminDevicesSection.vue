<template>
  <div>
    <!-- Sección completa (solo se muestra si showSection === true) -->
    <div v-if="isAdmin && showSection" class="admin-devices-section">
    <div class="section-header">
      <h2 class="section-title">📱 Gestión de Dispositivos</h2>
      <div class="header-actions">
        <button class="btn btn-detect" @click="openDetectionModal" :disabled="loading">
          <span>🔍 Detectar Nuevos</span>
        </button>
        <button class="btn btn-add" @click="openAddModal" :disabled="loading">
          <span>➕ Agregar Manual</span>
        </button>
      </div>
    </div>

    <!-- Estadísticas -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-icon">📊</div>
        <div class="stat-info">
          <p class="stat-label">Total Dispositivos</p>
          <p class="stat-value">{{ deviceCount }}</p>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">🟢</div>
        <div class="stat-info">
          <p class="stat-label">Activos</p>
          <p class="stat-value">{{ activeDeviceCount }}</p>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">🔴</div>
        <div class="stat-info">
          <p class="stat-label">Inactivos</p>
          <p class="stat-value">{{ offlineDevicesCount }}</p>
        </div>
      </div>
    </div>

    <!-- Búsqueda y Filtros -->
    <div class="filters-section">
      <input
        v-model="searchQuery"
        type="text"
        class="search-input"
        placeholder="Buscar por nombre o ID..."
      />
      <select v-model="statusFilter" class="status-filter">
        <option value="">Todos los estados</option>
        <option value="online">🟢 Conectados</option>
        <option value="offline">🔴 Desconectados</option>
      </select>
    </div>

    <!-- Tabla de Dispositivos -->
    <div class="devices-table-container">
      <div v-if="filteredDevices.length === 0" class="empty-state">
        <p class="empty-icon">📭</p>
        <p class="empty-text">No hay dispositivos para mostrar</p>
        <button class="btn btn-primary" @click="openDetectionModal">
          Detectar dispositivos
        </button>
      </div>

      <table v-else class="devices-table">
        <thead>
          <tr>
            <th>Estado</th>
            <th>Nombre</th>
            <th>Tipo</th>
            <th>Ubicación</th>
            <th>Batería</th>
            <th>Última Sincronización</th>
            <th>Acciones</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="device in filteredDevices" :key="device.id" class="device-row">
            <td class="status-cell">
              <span class="status-badge" :class="`status-${device.status}`">
                {{ getStatusIcon(device.status) }}
              </span>
            </td>
            <td class="name-cell">
              <strong>{{ device.name }}</strong>
              <span v-if="device.arduino_id" class="device-id">{{ device.arduino_id }}</span>
            </td>
            <td>{{ device.device_type }}</td>
            <td>{{ device.location || '-' }}</td>
            <td class="battery-cell">
              <div class="battery-bar">
                <div
                  class="battery-level"
                  :style="{ width: device.battery + '%', background: getBatteryColor(device.battery) }"
                ></div>
              </div>
              <span class="battery-text">{{ device.battery }}%</span>
            </td>
            <td class="sync-cell">
              <small>{{ formatDate(device.last_sync) }}</small>
            </td>
            <td class="actions-cell">
              <button
                class="btn-icon edit"
                @click="editDevice(device)"
                title="Editar"
              >
                ✏️
              </button>
              <button
                class="btn-icon delete"
                @click="deleteDevice(device.id)"
                title="Eliminar"
              >
                🗑️
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    </div>

    <!-- Modales (siempre disponibles, incluso si showSection === false) -->
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
import { ref, computed, onMounted, watch } from 'vue'
import { useDeviceStore } from '../stores/deviceStore'
import AddDeviceModal from './AddDeviceModal.vue'
import DeviceDetectionModal from './DeviceDetectionModal.vue'

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
const deviceCount = computed(() => deviceStore.deviceCount)
const activeDeviceCount = computed(() => deviceStore.activeDeviceCount)
const offlineDevicesCount = computed(() => deviceStore.deviceCount - deviceStore.activeDeviceCount)
const availableMicrocontrollers = computed(() => deviceStore.availableMicrocontrollers)
const devices = computed(() => deviceStore.devices)

// Estado local
const searchQuery = ref('')
const statusFilter = ref('')
const showAddModal = ref(false)
const showDetectionModal = ref(false)
const detectionInProgress = ref(false)
const detectionMessage = ref('')

// Dispositivos filtrados
const filteredDevices = computed(() => {
  let filtered = devices.value

  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    filtered = filtered.filter(d =>
      d.name.toLowerCase().includes(query) ||
      (d.arduino_id && d.arduino_id.toLowerCase().includes(query))
    )
  }

  if (statusFilter.value) {
    filtered = filtered.filter(d => d.status === statusFilter.value)
  }

  return filtered
})

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
    await deviceStore.createDevice(deviceData)
    closeAddModal()
  } catch (error) {
    console.error('Error creating device:', error)
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
  } catch (error) {
    console.error('Error registering device:', error)
    throw error
  }
}

const editDevice = (device) => {
  console.log('Edit device:', device)
  // Implementar edición si es necesario
}

const deleteDevice = async (deviceId) => {
  if (!confirm('¿Estás seguro de que deseas eliminar este dispositivo?')) {
    return
  }
  try {
    await deviceStore.deleteDevice(deviceId)
  } catch (error) {
    console.error('Error deleting device:', error)
  }
}

const getStatusIcon = (status) => {
  if (status === 'online') return '🟢'
  if (status === 'offline') return '🔴'
  return '⚫'
}

const getBatteryColor = (battery) => {
  if (battery > 60) return '#4ade80' // green
  if (battery > 30) return '#eab308' // yellow
  return '#ef4444' // red
}

const formatDate = (date) => {
  if (!date) return '-'
  return new Date(date).toLocaleDateString('es-ES', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// Monitorear cambios en triggerOpenModal para abrir el modal desde el padre
watch(() => props.triggerOpenModal, (newVal) => {
  if (newVal === true && isAdmin.value) {
    openAddModal()
  }
})

// Cargar dispositivos al montar
onMounted(async () => {
  const apiUrl = import.meta.env.VITE_API_URL || ''
  await deviceStore.fetchDevices(apiUrl)
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
.admin-devices-section {
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  border-radius: 12px;
  padding: 24px;
  margin: 24px 0;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  flex-wrap: wrap;
  gap: 16px;
}

.section-title {
  font-size: 22px;
  font-weight: 700;
  color: #1f2937;
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
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

/* Estadísticas */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.stat-card {
  background: white;
  border-radius: 8px;
  padding: 16px;
  display: flex;
  gap: 12px;
  align-items: center;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.stat-icon {
  font-size: 32px;
}

.stat-info {
  flex: 1;
}

.stat-label {
  font-size: 12px;
  color: #6b7280;
  margin: 0 0 4px 0;
  font-weight: 500;
}

.stat-value {
  font-size: 20px;
  font-weight: 700;
  color: #1f2937;
  margin: 0;
}

/* Filtros */
.filters-section {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
  flex-wrap: wrap;
}

.search-input,
.status-filter {
  padding: 10px 14px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
  font-family: inherit;
}

.search-input {
  flex: 1;
  min-width: 200px;
}

.search-input:focus,
.status-filter:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

/* Tabla */
.devices-table-container {
  background: white;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.empty-state {
  padding: 48px 24px;
  text-align: center;
}

.empty-icon {
  font-size: 48px;
  margin: 0 0 16px 0;
}

.empty-text {
  color: #6b7280;
  margin: 0 0 20px 0;
  font-size: 16px;
}

.devices-table {
  width: 100%;
  border-collapse: collapse;
}

.devices-table thead {
  background: #f3f4f6;
  border-bottom: 2px solid #e5e7eb;
}

.devices-table th {
  padding: 12px 16px;
  text-align: left;
  font-weight: 600;
  color: #374151;
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.devices-table tbody tr {
  border-bottom: 1px solid #e5e7eb;
  transition: background-color 0.2s ease;
}

.devices-table tbody tr:hover {
  background-color: #f9fafb;
}

.device-row td {
  padding: 14px 16px;
  font-size: 14px;
  color: #374151;
}

.status-cell {
  text-align: center;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: #f3f4f6;
  font-size: 16px;
}

.status-online {
  background: #d1fae5;
}

.status-offline {
  background: #fee2e2;
}

.name-cell {
  font-weight: 500;
}

.device-id {
  display: block;
  font-size: 12px;
  color: #9ca3af;
  margin-top: 4px;
  font-weight: normal;
}

.battery-cell {
  min-width: 120px;
}

.battery-bar {
  width: 100%;
  height: 6px;
  background: #e5e7eb;
  border-radius: 3px;
  overflow: hidden;
  margin-bottom: 4px;
}

.battery-level {
  height: 100%;
  border-radius: 3px;
  transition: width 0.3s ease;
}

.battery-text {
  font-size: 12px;
  color: #6b7280;
}

.sync-cell {
  color: #9ca3af;
}

.actions-cell {
  display: flex;
  gap: 8px;
}

.btn-icon {
  padding: 6px 10px;
  border: none;
  background: none;
  cursor: pointer;
  font-size: 16px;
  border-radius: 4px;
  transition: background-color 0.2s ease;
}

.btn-icon:hover {
  background-color: #e5e7eb;
}

.btn-icon.delete:hover {
  background-color: #fee2e2;
}

.btn-primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 10px 20px;
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 12px rgba(102, 126, 234, 0.4);
}

/* Responsive */
@media (max-width: 768px) {
  .admin-devices-section {
    padding: 16px;
  }

  .section-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .header-actions {
    width: 100%;
  }

  .btn {
    flex: 1;
    min-width: 0;
  }

  .devices-table {
    font-size: 12px;
  }

  .devices-table th,
  .device-row td {
    padding: 8px 12px;
  }

  .actions-cell {
    flex-direction: column;
  }

  .btn-icon {
    width: 100%;
    padding: 4px 8px;
  }
}
</style>
