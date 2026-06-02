<template>
  <div v-if="showModal" class="modal-overlay" @click.self="closeModal">
    <div class="modal-content">
      <div class="modal-header">
        <h3>{{ title }}</h3>
        <button class="close-btn" @click="closeModal" aria-label="Cerrar">×</button>
      </div>

      <div class="modal-body">
        <form @submit.prevent="handleSubmit">
          <div class="form-group">
            <label for="device-name">Nombre del Dispositivo *</label>
            <input
              id="device-name"
              v-model.trim="formData.name"
              type="text"
              placeholder="Ej: Sensor Embalse Norte"
              required
              class="form-input"
            />
          </div>

          <div class="form-group">
            <label for="device-type">Tipo de Microcontrolador</label>
            <select v-model="formData.device_type" id="device-type" class="form-select">
              <option value="ESP8266">ESP8266 (WiFi)</option>
              <option value="Arduino">Arduino</option>
              <option value="STM32">STM32</option>
              <option value="other">Otro</option>
            </select>
          </div>

          <div class="form-group">
            <label for="device-location">Ubicación (opcional)</label>
            <input
              id="device-location"
              v-model.trim="formData.location"
              type="text"
              placeholder="Ej: Zona A - Profundidad 5m"
              class="form-input"
            />
          </div>

          <div class="form-group">
            <label for="arduino-id">Identificador del dispositivo (opcional)</label>
            <input
              id="arduino-id"
              v-model.trim="formData.arduino_id"
              type="text"
              placeholder="Ej: Norte (sobrenombre en el panel)"
              class="form-input"
            />
            <small class="help-text">
              Nombre interno o alias en el sistema. Puede ser distinto del nombre que envía el sensor por MQTT.
            </small>
          </div>

          <div class="form-group">
            <label for="telemetry-key">Clave de telemetría MQTT (opcional)</label>
            <input
              id="telemetry-key"
              v-model.trim="formData.telemetry_key"
              type="text"
              placeholder="Ej: Dispositivo 1 (nombre en el JSON del Arduino)"
              class="form-input"
            />
            <small class="help-text">
              Si comparte el mismo topic que otro dispositivo (réplica), indica aquí el campo
              <strong>nombre</strong> que envía el hardware (p. ej. Dispositivo 1).
            </small>
          </div>

          <div class="form-group">
            <label for="device-topic">Topic MQTT *</label>
            <input
              id="device-topic"
              v-model.trim="formData.topic"
              type="text"
              placeholder="Ej: boya/sensores o home/sala/temperatura"
              required
              class="form-input"
            />
            <small class="help-text">
              Topic MQTT para recibir datos del dispositivo (requerido)
            </small>
          </div>

          <div class="form-actions">
            <button
              type="button"
              class="btn btn-secondary"
              @click="closeModal"
              :disabled="isSubmitting"
            >
              Cancelar
            </button>
            <button
              type="submit"
              class="btn btn-primary"
              :disabled="!isFormValid || isSubmitting"
            >
              {{ isSubmitting ? 'Guardando...' : 'Agregar Dispositivo' }}
            </button>
          </div>
        </form>

        <div v-if="errorMessage" class="alert alert-error">
          {{ errorMessage }}
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
  title: {
    type: String,
    default: 'Agregar Nuevo Dispositivo'
  },
  onSubmit: {
    type: Function,
    default: null
  },
  onClose: {
    type: Function,
    default: null
  }
})

const emit = defineEmits(['update:show', 'submit', 'close'])

const formData = ref({
  name: '',
  device_type: 'ESP8266',
  location: '',
  arduino_id: '',
  telemetry_key: '',
  topic: ''
})

const isSubmitting = ref(false)
const errorMessage = ref('')

const showModal = computed({
  get: () => props.show,
  set: (value) => emit('update:show', value)
})

const isFormValid = computed(() => {
  return formData.value.name && formData.value.name.length > 0 &&
         formData.value.topic && formData.value.topic.length > 0
})

const closeModal = () => {
  resetForm()
  showModal.value = false
  if (props.onClose) props.onClose()
  emit('close')
}

const resetForm = () => {
  formData.value = {
    name: '',
    device_type: 'ESP8266',
    location: '',
    arduino_id: '',
    telemetry_key: '',
    topic: ''
  }
  errorMessage.value = ''
}

const handleSubmit = async () => {
  if (!isFormValid.value) return

  isSubmitting.value = true
  errorMessage.value = ''

  try {
    if (props.onSubmit) {
      await props.onSubmit(formData.value)
    }
    emit('submit', formData.value)
    closeModal()
  } catch (error) {
    errorMessage.value = `Error: ${error.message}`
    console.error('Error al agregar dispositivo:', error)
  } finally {
    isSubmitting.value = false
  }
}

watch(
  () => props.show,
  (newVal) => {
    if (newVal === false) {
      resetForm()
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

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  margin-bottom: 6px;
  font-weight: 600;
  color: #4b5563;
  font-size: 12px;
}

.form-input,
.form-select {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
  font-family: inherit;
  background-color: #ffffff;
  color: #1f2937;
  transition: border-color 0.2s, box-shadow 0.2s;
  box-sizing: border-box;
}

.form-input:focus,
.form-select:focus {
  outline: none;
  border-color: #66bb6a;
  box-shadow: 0 0 0 2px rgba(102, 187, 106, 0.2);
}

.help-text {
  display: block;
  margin-top: 4px;
  color: #6b7280;
  font-size: 12px;
  line-height: 1.4;
}

.form-actions {
  display: flex;
  gap: 8px;
  margin-top: 20px;
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
}

.alert-error {
  background: #ffebee;
  color: #c62828;
  border: 1px solid #ef9a9a;
}
</style>
