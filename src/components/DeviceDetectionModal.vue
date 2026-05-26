<template>
  <div v-if="showModal" class="modal-overlay" @click.self="closeModal">
    <div class="modal-content">
      <div class="modal-header">
        <h3>🔍 Detectar Nuevos Microcontroladores</h3>
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
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
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
  background: white;
  border-radius: 8px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
  max-width: 500px;
  width: 90%;
  max-height: 90vh;
  overflow-y: auto;
  animation: slideUp 0.3s ease;
}

@keyframes slideUp {
  from {
    transform: translateY(20px);
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
  padding: 20px;
  border-bottom: 1px solid #e5e7eb;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.modal-header h3 {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
}

.close-btn {
  background: none;
  border: none;
  font-size: 28px;
  cursor: pointer;
  color: white;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: background-color 0.2s;
}

.close-btn:hover {
  background-color: rgba(255, 255, 255, 0.1);
}

.modal-body {
  padding: 20px;
}

/* Escaneando */
.scanning-container {
  text-align: center;
  padding: 40px 20px;
}

.spinner {
  width: 50px;
  height: 50px;
  border: 4px solid #e5e7eb;
  border-top-color: #667eea;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 20px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.scanning-text {
  color: #667eea;
  font-weight: 500;
  margin: 0;
}

/* Dispositivos Encontrados */
.devices-container {
  animation: fadeIn 0.3s ease;
}

.status-message {
  color: #065f46;
  background: #d1fae5;
  padding: 12px 16px;
  border-radius: 6px;
  margin-bottom: 20px;
  border-left: 4px solid #10b981;
}

.devices-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 20px;
}

.device-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  background: #f9fafb;
  transition: all 0.2s;
}

.device-item:hover {
  border-color: #667eea;
  background: #f3f4f6;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.1);
}

.device-info {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
}

.device-icon {
  font-size: 24px;
}

.device-details {
  min-width: 0;
}

.device-id {
  margin: 0;
  color: #1f2937;
  font-weight: 600;
  word-break: break-all;
  font-family: monospace;
  font-size: 0.9rem;
}

.device-status {
  margin: 4px 0 0 0;
  color: #6b7280;
  font-size: 0.85rem;
}

.btn-register {
  white-space: nowrap;
  flex-shrink: 0;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-register:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.btn-register:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Sin Dispositivos */
.no-devices {
  text-align: center;
  padding: 40px 20px;
  animation: fadeIn 0.3s ease;
}

.empty-icon {
  font-size: 48px;
  margin: 0 0 16px 0;
}

.empty-message {
  color: #6b7280;
  margin: 0 0 24px 0;
  font-size: 1.05rem;
}

.help-section {
  background: #fef3c7;
  border: 1px solid #fbbf24;
  border-radius: 6px;
  padding: 16px;
  margin-bottom: 20px;
  text-align: left;
}

.help-section h4 {
  margin: 0 0 12px 0;
  color: #92400e;
  font-size: 1rem;
}

.help-section ul {
  margin: 0;
  padding-left: 20px;
  color: #78350f;
  font-size: 0.95rem;
}

.help-section li {
  margin: 6px 0;
}

/* Acciones */
.actions {
  display: flex;
  gap: 12px;
  justify-content: center;
  flex-wrap: wrap;
}

.btn {
  padding: 10px 16px;
  border: none;
  border-radius: 6px;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.btn-primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-secondary {
  background: #e5e7eb;
  color: #374151;
}

.btn-secondary:hover:not(:disabled) {
  background: #d1d5db;
}

.btn-secondary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Alertas */
.alert {
  margin-top: 16px;
  padding: 12px 16px;
  border-radius: 6px;
  font-size: 0.95rem;
  animation: slideDown 0.3s ease;
}

@keyframes slideDown {
  from {
    transform: translateY(-10px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

.alert-error {
  background: #fee;
  color: #c33;
  border: 1px solid #f99;
}

.alert-success {
  background: #d1fae5;
  color: #065f46;
  border: 1px solid #10b981;
}
</style>
