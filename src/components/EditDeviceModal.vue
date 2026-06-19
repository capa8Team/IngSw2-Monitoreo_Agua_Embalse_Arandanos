<template>
  <div v-if="showModal" class="modal-overlay" @click.self="closeModal">
    <div class="modal-content">
      <div class="modal-header">
        <h3>Configurar dispositivo</h3>
        <button class="close-btn" @click="closeModal" aria-label="Cerrar">×</button>
      </div>

      <div class="modal-body">
        <form @submit.prevent="handleSubmit">
          <div class="form-group">
            <label for="edit-device-name">Nombre *</label>
            <input
              id="edit-device-name"
              v-model.trim="formData.name"
              type="text"
              required
              class="form-input"
            />
          </div>

          <div class="form-group">
            <label for="edit-device-type">Tipo</label>
            <select id="edit-device-type" v-model="formData.device_type" class="form-select">
              <option value="ESP8266">ESP8266 (WiFi)</option>
              <option value="Arduino">Arduino</option>
              <option value="STM32">STM32</option>
              <option value="other">Otro</option>
            </select>
          </div>

          <div class="form-group">
            <label for="edit-device-location">Ubicación (zona / profundidad)</label>
            <input
              id="edit-device-location"
              v-model.trim="formData.location"
              type="text"
              class="form-input"
              placeholder="Ej: Zona A - Profundidad 5m"
            />
          </div>

          <div class="form-group">
            <label for="edit-device-city">Ciudad (clima)</label>
            <input
              id="edit-device-city"
              v-model.trim="formData.city"
              type="text"
              class="form-input"
              placeholder="Ej: Santiago"
            />
          </div>

          <div class="form-group">
            <label for="edit-arduino-id">Identificador del dispositivo</label>
            <input
              id="edit-arduino-id"
              v-model.trim="formData.arduino_id"
              type="text"
              class="form-input"
            />
          </div>

          <div class="form-group">
            <label for="edit-telemetry-key">Clave de telemetría MQTT</label>
            <input
              id="edit-telemetry-key"
              v-model.trim="formData.telemetry_key"
              type="text"
              class="form-input"
            />
          </div>

          <div class="form-group">
            <label for="edit-device-topic">Topic MQTT</label>
            <input
              id="edit-device-topic"
              v-model.trim="formData.topic"
              type="text"
              class="form-input"
            />
          </div>

          <DeviceGroupSelector
            :groups="groups"
            field-id="edit"
            :initial-group-id="formData.group_id || ''"
            :initial-latitude="formData.latitude"
            :initial-longitude="formData.longitude"
            @change="onGroupSelectionChange"
          />

          <div class="form-actions">
            <button type="button" class="btn btn-secondary" :disabled="isSubmitting" @click="closeModal">
              Cancelar
            </button>
            <button type="submit" class="btn btn-primary" :disabled="!isFormValid || isSubmitting">
              {{ isSubmitting ? 'Guardando…' : 'Guardar cambios' }}
            </button>
          </div>
        </form>

        <div v-if="errorMessage" class="alert alert-error">{{ errorMessage }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import DeviceGroupSelector from './DeviceGroupSelector.vue'

const props = defineProps({
  show: { type: Boolean, default: false },
  device: { type: Object, default: null },
  groups: { type: Array, default: () => [] },
  onSubmit: { type: Function, default: null },
})

const emit = defineEmits(['update:show', 'submit', 'close'])

const formData = ref(emptyForm())
const groupSelection = ref(null)
const isSubmitting = ref(false)
const errorMessage = ref('')

function emptyForm() {
  return {
    name: '',
    device_type: 'ESP8266',
    location: '',
    city: '',
    arduino_id: '',
    telemetry_key: '',
    topic: '',
    group_id: '',
    latitude: null,
    longitude: null,
  }
}

const showModal = computed({
  get: () => props.show,
  set: (value) => emit('update:show', value),
})

const isFormValid = computed(() => Boolean(formData.value.name?.trim()))

const onGroupSelectionChange = (selection) => {
  groupSelection.value = selection
}

const loadDevice = () => {
  if (!props.device) return
  formData.value = {
    name: props.device.name || '',
    device_type: props.device.device_type || 'ESP8266',
    location: props.device.location || '',
    city: props.device.city || '',
    arduino_id: props.device.arduino_id || '',
    telemetry_key: props.device.telemetry_key || '',
    topic: props.device.topic || '',
    group_id: props.device.group_id || '',
    latitude: props.device.latitude ?? null,
    longitude: props.device.longitude ?? null,
  }
}

const closeModal = () => {
  showModal.value = false
  errorMessage.value = ''
  emit('close')
}

const handleSubmit = async () => {
  if (!isFormValid.value || !props.device?.id) return

  isSubmitting.value = true
  errorMessage.value = ''

  try {
    const payload = {
      name: formData.value.name,
      location: formData.value.location,
      city: formData.value.city,
      arduino_id: formData.value.arduino_id || null,
      telemetry_key: formData.value.telemetry_key || null,
      topic: formData.value.topic || null,
      groupSelection: groupSelection.value,
    }

    if (props.onSubmit) {
      await props.onSubmit(props.device.id, payload)
    }
    emit('submit', { deviceId: props.device.id, payload })
    closeModal()
  } catch (error) {
    errorMessage.value = error?.message || 'No se pudo guardar'
  } finally {
    isSubmitting.value = false
  }
}

watch(() => props.show, (visible) => {
  if (visible) loadDevice()
})

watch(() => props.device, () => {
  if (props.show) loadDevice()
})
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
}

.modal-content {
  background: #ffffff;
  border-radius: 8px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.12);
  max-width: 560px;
  width: 90%;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 16px;
  border-bottom: 2px solid #66bb6a;
}

.modal-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.close-btn {
  width: 32px;
  height: 32px;
  border: 1px solid #e0e0e0;
  background: #fff;
  border-radius: 6px;
  font-size: 18px;
  cursor: pointer;
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
  font-size: 12px;
  color: #4b5563;
}

.form-input,
.form-select {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
  box-sizing: border-box;
}

.form-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
  margin-top: 20px;
}

.btn {
  min-width: 120px;
  height: 36px;
  padding: 0 14px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
}

.btn-primary {
  border: 1px solid #66bb6a;
  background: #66bb6a;
  color: #fff;
}

.btn-secondary {
  border: 1px solid #d1d5db;
  background: #fff;
  color: #374151;
}

.alert-error {
  margin-top: 14px;
  padding: 10px 12px;
  border-radius: 6px;
  background: #ffebee;
  color: #c62828;
  font-size: 13px;
}
</style>
