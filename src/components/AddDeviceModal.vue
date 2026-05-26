<template>
  <div v-if="showModal" class="modal-overlay" @click.self="closeModal">
    <div class="modal-content">
      <div class="modal-header">
        <h3>{{ title }}</h3>
        <button class="close-btn" @click="closeModal" aria-label="Cerrar">×</button>
      </div>

      <div class="modal-body">
        <form @submit.prevent="handleSubmit">
          <!-- Nombre -->
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

          <!-- Tipo de Dispositivo -->
          <div class="form-group">
            <label for="device-type">Tipo de Microcontrolador</label>
            <select v-model="formData.device_type" id="device-type" class="form-select">
              <option value="ESP8266">ESP8266 (WiFi)</option>
              <option value="Arduino">Arduino</option>
              <option value="STM32">STM32</option>
              <option value="other">Otro</option>
            </select>
          </div>

          <!-- Ubicación -->
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

          <!-- Arduino ID (si aplica) -->
          <div class="form-group">
            <label for="arduino-id">Arduino ID (opcional)</label>
            <input
              id="arduino-id"
              v-model.trim="formData.arduino_id"
              type="text"
              placeholder="Auto-detectado si se deja vacío"
              class="form-input"
            />
            <small class="help-text">
              Si tienes el ID del Arduino, colócalo aquí. De lo contrario, se detectará automáticamente.
            </small>
          </div>

          <!-- Botones -->
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

        <!-- Mensaje de Error -->
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
  arduino_id: ''
})

const isSubmitting = ref(false)
const errorMessage = ref('')

const showModal = computed({
  get: () => props.show,
  set: (value) => emit('update:show', value)
})

const isFormValid = computed(() => {
  return formData.value.name && formData.value.name.length > 0
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
    arduino_id: ''
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

// Reset cuando se cierra/abre la modal
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
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
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

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 6px;
  font-weight: 500;
  color: #374151;
  font-size: 0.95rem;
}

.form-input,
.form-select {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 1rem;
  font-family: inherit;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.form-input:focus,
.form-select:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.help-text {
  display: block;
  margin-top: 4px;
  color: #6b7280;
  font-size: 0.85rem;
}

.form-actions {
  display: flex;
  gap: 12px;
  margin-top: 24px;
  justify-content: flex-end;
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
</style>
