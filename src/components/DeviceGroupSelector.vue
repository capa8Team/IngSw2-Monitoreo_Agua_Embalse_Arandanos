<template>
  <div class="group-selector">
    <div class="form-group">
      <label>Ubicación en mapa</label>
      <div class="mode-options">
        <label class="mode-option">
          <input v-model="mode" type="radio" value="none" />
          <span>Sin agrupar</span>
        </label>
        <label class="mode-option">
          <input v-model="mode" type="radio" value="existing" />
          <span>Agrupar en existente</span>
        </label>
        <label class="mode-option">
          <input v-model="mode" type="radio" value="new" />
          <span>Crear nuevo grupo</span>
        </label>
      </div>
    </div>

    <div v-if="mode === 'existing'" class="form-group">
      <label :for="`${fieldId}-group`">Grupo / embalse</label>
      <select :id="`${fieldId}-group`" v-model="selectedGroupId" class="form-select">
        <option value="">Selecciona un grupo…</option>
        <option v-for="group in groups" :key="group.id" :value="group.id">
          {{ group.name }} ({{ group.device_count }} disp.)
        </option>
      </select>
      <small v-if="groups.length === 0" class="help-text">
        No hay grupos creados. Usa "Crear nuevo grupo" para definir una ubicación en el mapa.
      </small>
    </div>

    <template v-if="mode === 'new'">
      <div class="form-group">
        <label :for="`${fieldId}-group-name`">Nombre del grupo *</label>
        <input
          :id="`${fieldId}-group-name`"
          v-model.trim="newGroup.name"
          type="text"
          class="form-input"
          placeholder="Ej: Embalse Arándanos"
        />
      </div>

      <div class="form-group">
        <label :for="`${fieldId}-group-location`">Descripción de ubicación</label>
        <input
          :id="`${fieldId}-group-location`"
          v-model.trim="newGroup.location_label"
          type="text"
          class="form-input"
          placeholder="Ej: Región Metropolitana, zona norte"
        />
      </div>

      <div class="form-group">
        <label :for="`${fieldId}-group-city`">Buscar en mapa por ciudad o dirección</label>
        <div class="geocode-row">
          <input
            :id="`${fieldId}-group-city`"
            v-model.trim="searchQuery"
            type="text"
            class="form-input"
            placeholder="Ej: Embalse El Yeso, Chile"
            @keyup.enter.prevent="searchLocation"
          />
          <button type="button" class="btn-geocode" :disabled="geocoding" @click="searchLocation">
            {{ geocoding ? '…' : 'Buscar' }}
          </button>
        </div>
        <small class="help-text">Usa OpenStreetMap (Nominatim) para ubicar el punto en el mapa.</small>
      </div>

      <div class="coords-row">
        <div class="form-group">
          <label :for="`${fieldId}-lat`">Latitud *</label>
          <input
            :id="`${fieldId}-lat`"
            v-model.number="newGroup.latitude"
            type="number"
            step="any"
            class="form-input"
            placeholder="-33.45"
          />
        </div>
        <div class="form-group">
          <label :for="`${fieldId}-lng`">Longitud *</label>
          <input
            :id="`${fieldId}-lng`"
            v-model.number="newGroup.longitude"
            type="number"
            step="any"
            class="form-input"
            placeholder="-70.66"
          />
        </div>
      </div>
    </template>

    <template v-if="mode === 'none' && allowIndividualCoords">
      <div class="form-group">
        <label class="checkbox-label">
          <input v-model="useIndividualCoords" type="checkbox" />
          <span>Ubicación individual en mapa (sin grupo)</span>
        </label>
      </div>

      <template v-if="useIndividualCoords">
        <div class="form-group">
          <label>Buscar coordenadas</label>
          <div class="geocode-row">
            <input
              v-model.trim="individualSearchQuery"
              type="text"
              class="form-input"
              placeholder="Ciudad o dirección"
              @keyup.enter.prevent="searchIndividualLocation"
            />
            <button type="button" class="btn-geocode" :disabled="geocoding" @click="searchIndividualLocation">
              {{ geocoding ? '…' : 'Buscar' }}
            </button>
          </div>
        </div>
        <div class="coords-row">
          <div class="form-group">
            <label>Latitud</label>
            <input v-model.number="individualCoords.latitude" type="number" step="any" class="form-input" />
          </div>
          <div class="form-group">
            <label>Longitud</label>
            <input v-model.number="individualCoords.longitude" type="number" step="any" class="form-input" />
          </div>
        </div>
      </template>
    </template>

    <p v-if="geocodeError" class="geocode-error">{{ geocodeError }}</p>
  </div>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import { geocodeLocation } from '../utils/mapUtils.js'

const props = defineProps({
  groups: { type: Array, default: () => [] },
  allowIndividualCoords: { type: Boolean, default: true },
  fieldId: { type: String, default: 'group' },
  initialMode: { type: String, default: 'none' },
  initialGroupId: { type: String, default: '' },
  initialLatitude: { type: Number, default: null },
  initialLongitude: { type: Number, default: null },
})

const emit = defineEmits(['change'])

const mode = ref(props.initialGroupId ? 'existing' : props.initialMode)
const selectedGroupId = ref(props.initialGroupId || '')
const searchQuery = ref('')
const individualSearchQuery = ref('')
const geocoding = ref(false)
const geocodeError = ref('')
const useIndividualCoords = ref(
  props.initialLatitude != null && props.initialLongitude != null && !props.initialGroupId,
)

const newGroup = ref({
  name: '',
  location_label: '',
  city: '',
  latitude: null,
  longitude: null,
})

const individualCoords = ref({
  latitude: props.initialLatitude,
  longitude: props.initialLongitude,
})

const selectionPayload = computed(() => {
  if (mode.value === 'existing') {
    return {
      mode: 'existing',
      group_id: selectedGroupId.value || null,
      new_group: null,
      latitude: null,
      longitude: null,
    }
  }
  if (mode.value === 'new') {
    return {
      mode: 'new',
      group_id: null,
      new_group: { ...newGroup.value },
      latitude: null,
      longitude: null,
    }
  }
  return {
    mode: 'none',
    group_id: null,
    new_group: null,
    latitude: useIndividualCoords.value ? individualCoords.value.latitude : null,
    longitude: useIndividualCoords.value ? individualCoords.value.longitude : null,
  }
})

const searchLocation = async () => {
  geocodeError.value = ''
  geocoding.value = true
  try {
    const result = await geocodeLocation(searchQuery.value)
    if (!result) {
      geocodeError.value = 'No se encontró la ubicación. Prueba con otro nombre.'
      return
    }
    newGroup.value.latitude = result.latitude
    newGroup.value.longitude = result.longitude
    newGroup.value.city = searchQuery.value
    if (!newGroup.value.location_label) {
      newGroup.value.location_label = result.label
    }
  } catch {
    geocodeError.value = 'Error al buscar la ubicación.'
  } finally {
    geocoding.value = false
  }
}

const searchIndividualLocation = async () => {
  geocodeError.value = ''
  geocoding.value = true
  try {
    const result = await geocodeLocation(individualSearchQuery.value)
    if (!result) {
      geocodeError.value = 'No se encontró la ubicación.'
      return
    }
    individualCoords.value.latitude = result.latitude
    individualCoords.value.longitude = result.longitude
  } catch {
    geocodeError.value = 'Error al buscar la ubicación.'
  } finally {
    geocoding.value = false
  }
}

watch(selectionPayload, (val) => emit('change', val), { deep: true, immediate: true })

watch(
  () => props.initialGroupId,
  (val) => {
    if (val) {
      mode.value = 'existing'
      selectedGroupId.value = val
    }
  },
)
</script>

<style scoped>
.group-selector {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 12px;
  background: #f9fafb;
}

.mode-options {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.mode-option {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #374151;
  cursor: pointer;
}

.coords-row,
.geocode-row {
  display: flex;
  gap: 8px;
  align-items: flex-start;
}

.geocode-row .form-input {
  flex: 1;
}

.coords-row .form-group {
  flex: 1;
  margin-bottom: 0;
}

.btn-geocode {
  border: 1px solid #66bb6a;
  background: #fff;
  color: #2e7d32;
  border-radius: 6px;
  padding: 10px 14px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
}

.btn-geocode:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  cursor: pointer;
}

.geocode-error {
  color: #c62828;
  font-size: 12px;
  margin: 8px 0 0;
}

.form-group {
  margin-bottom: 12px;
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
  box-sizing: border-box;
}

.help-text {
  display: block;
  margin-top: 4px;
  color: #6b7280;
  font-size: 12px;
}

html[data-theme='dark'] .group-selector {
  background: #1a1d26;
  border-color: #3d4254;
}

html[data-theme='dark'] .mode-option {
  color: #e2e8f0;
}

html[data-theme='dark'] .form-input,
html[data-theme='dark'] .form-select {
  background: #262a36;
  border-color: #3d4254;
  color: #f1f5f9;
}
</style>
