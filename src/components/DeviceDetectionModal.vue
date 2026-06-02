<template>
  <div v-if="showModal" class="modal-overlay" @click.self="closeModal">
    <div class="modal-content">
      <div class="modal-header">
        <h3>Detectar Nuevos Microcontroladores</h3>
        <button class="close-btn" @click="closeModal" aria-label="Cerrar">×</button>
      </div>

      <div class="modal-body">
        <!-- Estado: Escaneando -->
        <div v-if="isDetecting" class="scanning-container">
          <div class="spinner"></div>
          <p class="scanning-text">{{ detectionMessage }}</p>
        </div>

        <!-- Estado: Completado - Dispositivos Encontrados -->
        <div v-else-if="availableDevices.length > 0" class="devices-container">
          <p class="status-message">
            ✓ Se encontraron <strong>{{ availableDevices.length }}</strong> nuevo(s) microcontrolador(es):
          </p>

          <div class="devices-list">
            <div
              v-for="(arduinoId, index) in availableDevices"
              :key="index"
              class="device-item"
            >
              <div class="device-info">
                <span class="device-icon">📱</span>
                <div class="device-details">
                  <p class="device-id"><strong>{{ arduinoId }}</strong></p>
                  <p class="device-status">Listo para registrar</p>
                </div>
              </div>

              <button
                class="btn btn-register"
                @click="registerDevice(arduinoId)"
                :disabled="isRegistering"
              >
                {{ isRegistering ? '⏳ Registrando...' : '✓ Registrar' }}
              </button>
            </div>
          </div>

          <div class="actions">
            <button class="btn btn-secondary" @click="rescan">
              🔄 Escanear de Nuevo
            </button>
            <button class="btn btn-primary" @click="closeModal">
              Cerrar
            </button>
          </div>
        </div>

        <!-- Estado: Sin Dispositivos Encontrados -->
        <div v-else class="no-devices">
          <p class="empty-icon">⚠️</p>
          <p class="empty-message">{{ detectionMessage }}</p>

          <div class="help-section">
            <h4>💡 Consejos:</h4>
            <ul>
              <li>Asegúrate de que el microcontrolador esté encendido y conectado a la red</li>
              <li>Verifica que el dispositivo esté enviando datos a la API</li>
              <li>Intenta escanear de nuevo después de unos segundos</li>
            </ul>
          </div>

          <div class="actions">
            <button class="btn btn-primary" @click="rescan" :disabled="isDetecting">
              🔄 Escanear de Nuevo
            </button>
            <button class="btn btn-secondary" @click="closeModal">
              Cerrar
            </button>
          </div>
        </div>

        <!-- Mensaje de Error -->
        <div v-if="errorMessage" class="alert alert-error">
          ❌ {{ errorMessage }}
        </div>

        <!-- Mensaje de Éxito -->
        <div v-if="successMessage" class="alert alert-success">
          ✓ {{ successMessage }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'

const props = defineProps({
  show: {
    type: Boolean,
    default: false
  },
  availableMicrocontrollers: {
    type: Array,
    default: () => []
  },
  isDetecting: {
    type: Boolean,
    default: false
  },
  detectionMessage: {
    type: String,
    default: 'Escaneando dispositivos...'
  },
  onDetect: {
    type: Function,
    default: null
  },
  onRegister: {
    type: Function,
    default: null
  },
  onClose: {
    type: Function,
    default: null
  }
})

const emit = defineEmits(['update:show', 'detect', 'register', 'close'])

const showModal = computed({
  get: () => props.show,
  set: (value) => emit('update:show', value)
})

const availableDevices = computed(() => props.availableMicrocontrollers)
const errorMessage = ref('')
const successMessage = ref('')
const isRegistering = ref(false)

const closeModal = () => {
  errorMessage.value = ''
  successMessage.value = ''
  showModal.value = false
  if (props.onClose) props.onClose()
  emit('close')
}

const rescan = () => {
  errorMessage.value = ''
  successMessage.value = ''
  if (props.onDetect) {
    props.onDetect()
  }
  emit('detect')
}

const registerDevice = async (arduinoId) => {
  isRegistering.value = true
  errorMessage.value = ''
  successMessage.value = ''

  try {
    const customName = `Dispositivo ${arduinoId.substring(0, 8)}`
    if (props.onRegister) {
      await props.onRegister(arduinoId, customName)
    }
    emit('register', { arduinoId, name: customName })

    successMessage.value = `Dispositivo ${arduinoId} registrado correctamente`
    
    // Remover de la lista visible
    availableDevices.value = availableDevices.value.filter(id => id !== arduinoId)
  } catch (error) {
    errorMessage.value = `Error registrando dispositivo: ${error.message}`
    console.error('Error:', error)
  } finally {
    isRegistering.value = false
  }
}

// Limpiar cuando se cierra
watch(
  () => props.show,
  (newVal) => {
    if (newVal === false) {
      errorMessage.value = ''
      successMessage.value = ''
    }
  }
)
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  animation: fadeIn 0.2s ease;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.modal-content {
  background: #ffffff;
  border-radius: 8px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.12);
  max-width: 520px;
  width: 90%;
  max-height: 90vh;
  overflow-y: auto;
  animation: slideUp 0.25s ease;
}

@keyframes slideUp {
  from {
    transform: translateY(16px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 16px;
  border-bottom: 2px solid #66bb6a;
  background: #ffffff;
}

.modal-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #333333;
}

.close-btn {
  width: 32px;
  height: 32px;
  border: 1px solid #e0e0e0;
  background: #ffffff;
  border-radius: 6px;
  font-size: 18px;
  line-height: 1;
  cursor: pointer;
  color: #333333;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}

.close-btn:hover {
  background: #f0f0f0;
  border-color: #66bb6a;
}

.modal-body {
  padding: 16px;
}

.scanning-container {
  text-align: center;
  padding: 32px 16px;
}

.spinner {
  width: 44px;
  height: 44px;
  border: 3px solid #e5e7eb;
  border-top-color: #66bb6a;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 16px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.scanning-text {
  color: #2e7d32;
  font-weight: 600;
  font-size: 14px;
  margin: 0;
}

.devices-container {
  animation: fadeIn 0.3s ease;
}

.status-message {
  color: #2e7d32;
  background: #e8f5e9;
  padding: 10px 12px;
  border-radius: 6px;
  margin-bottom: 16px;
  border-left: 4px solid #66bb6a;
  font-size: 13px;
}

.devices-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 16px;
}

.device-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
  padding: 12px;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  background: #f8fafc;
  transition: all 0.2s ease;
}

.device-item:hover {
  border-color: #66bb6a;
  background: #f1f8f2;
}

.device-info {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
  min-width: 0;
}

.device-icon {
  font-size: 20px;
}

.device-details {
  min-width: 0;
}

.device-id {
  margin: 0;
  color: #333333;
  font-weight: 600;
  word-break: break-all;
  font-family: ui-monospace, monospace;
  font-size: 13px;
}

.device-status {
  margin: 4px 0 0 0;
  color: #6b7280;
  font-size: 12px;
}

.btn-register {
  white-space: nowrap;
  flex-shrink: 0;
  border: 1px solid #66bb6a;
  background: #66bb6a;
  color: #ffffff;
  padding: 8px 14px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  font-family: inherit;
}

.btn-register:hover:not(:disabled) {
  background: #558a5a;
  border-color: #558a5a;
}

.btn-register:disabled {
  opacity: 0.65;
  cursor: not-allowed;
}

.no-devices {
  text-align: center;
  padding: 24px 8px;
  animation: fadeIn 0.3s ease;
}

.empty-icon {
  font-size: 40px;
  margin: 0 0 12px 0;
}

.empty-message {
  color: #6b7280;
  margin: 0 0 20px 0;
  font-size: 14px;
}

.help-section {
  background: #f8fafc;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  padding: 14px;
  margin-bottom: 16px;
  text-align: left;
}

.help-section h4 {
  margin: 0 0 10px 0;
  color: #374151;
  font-size: 13px;
  font-weight: 600;
}

.help-section ul {
  margin: 0;
  padding-left: 18px;
  color: #6b7280;
  font-size: 13px;
}

.help-section li {
  margin: 6px 0;
}

.actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
  flex-wrap: wrap;
}

.btn {
  min-width: 120px;
  height: 36px;
  padding: 0 14px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  font-family: inherit;
}

.btn-primary {
  border: 1px solid #66bb6a;
  background: #66bb6a;
  color: #ffffff;
}

.btn-primary:hover:not(:disabled) {
  background: #558a5a;
  border-color: #558a5a;
}

.btn-primary:disabled {
  opacity: 0.65;
  cursor: not-allowed;
}

.btn-secondary {
  border: 1px solid #d1d5db;
  background: #ffffff;
  color: #374151;
}

.btn-secondary:hover:not(:disabled) {
  background: #f3f4f6;
  border-color: #9ca3af;
}

.btn-secondary:disabled {
  opacity: 0.65;
  cursor: not-allowed;
}

.alert {
  margin-top: 14px;
  padding: 10px 12px;
  border-radius: 6px;
  font-size: 13px;
  animation: slideDown 0.3s ease;
}

@keyframes slideDown {
  from {
    transform: translateY(-8px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

.alert-error {
  background: #ffebee;
  color: #c62828;
  border: 1px solid #ef9a9a;
}

.alert-success {
  background: #e8f5e9;
  color: #2e7d32;
  border: 1px solid #a5d6a7;
}
</style>
