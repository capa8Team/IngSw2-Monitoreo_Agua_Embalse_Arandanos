<template>
  <div class="weather-card">
    <div class="weather-header">
      <h3 class="weather-title">
        <span class="weather-emoji">{{ weatherEmoji }}</span>
        Clima
        <span v-if="weather?.city" class="weather-city">— {{ weather.city }}</span>
      </h3>
      <span v-if="weather?.country" class="country-badge">{{ weather.country }}</span>
    </div>

    <div v-if="showCitySetup" class="weather-setup">
      <p class="setup-text">
        Configura la ciudad del dispositivo para mostrar el clima actual.
      </p>
      <div class="setup-form">
        <input
          v-model.trim="cityInput"
          type="text"
          class="city-input"
          placeholder="Ej: Santiago, Chile"
          @keyup.enter="saveCity"
        />
        <button
          class="save-city-btn"
          :disabled="!cityInput || savingCity"
          @click="saveCity"
        >
          {{ savingCity ? 'Guardando...' : 'Guardar' }}
        </button>
      </div>
      <small class="setup-hint">Usa el formato ciudad y país, por ejemplo: Santiago, Chile</small>
    </div>

    <div v-else-if="loading" class="weather-loading">
      <p>Cargando datos de clima...</p>
    </div>

    <div v-else-if="error" class="weather-error">
      <p>{{ error }}</p>
      <button v-if="deviceId" class="retry-btn" @click="showCitySetup = true">
        Configurar ciudad
      </button>
    </div>

    <div v-else-if="weather" class="weather-display">
      <div class="weather-main">
        <div class="temperature-section">
          <div class="current-temp">
            <span class="temp-value">{{ weather.temperature.toFixed(1) }}°</span>
            <span class="temp-unit">C</span>
          </div>
          <p class="description">{{ weather.description }}</p>
        </div>

        <div class="weather-details">
          <div class="detail-item">
            <span class="detail-label">Sensación</span>
            <span class="detail-value">{{ weather.feels_like.toFixed(1) }}°C</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">Mín / Máx</span>
            <span class="detail-value">
              {{ weather.temp_min.toFixed(1) }}° / {{ weather.temp_max.toFixed(1) }}°
            </span>
          </div>
          <div class="detail-item">
            <span class="detail-label">Humedad</span>
            <span class="detail-value">{{ weather.humidity }}%</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">Presión</span>
            <span class="detail-value">{{ weather.pressure }} hPa</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">Viento</span>
            <span class="detail-value">{{ weather.wind_speed.toFixed(1) }} m/s</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">Nubosidad</span>
            <span class="detail-value">{{ weather.clouds }}%</span>
          </div>
        </div>
      </div>

      <div class="weather-sun">
        <div class="sun-item">
          <span class="sun-icon">🌅</span>
          <div>
            <p class="sun-label">Salida del Sol</p>
            <p class="sun-time">{{ formatTime(weather.sunrise) }}</p>
          </div>
        </div>
        <div class="sun-item">
          <span class="sun-icon">🌇</span>
          <div>
            <p class="sun-label">Puesta del Sol</p>
            <p class="sun-time">{{ formatTime(weather.sunset) }}</p>
          </div>
        </div>
      </div>

      <div class="weather-timestamp">
        <small>Datos actualizados: {{ formatTimestamp(weather.timestamp) }}</small>
        <button v-if="deviceId" class="edit-city-btn" @click="openCityEditor">Cambiar ciudad</button>
      </div>
    </div>

    <div v-else class="weather-empty">
      <p>No hay datos de clima disponibles</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'

const props = defineProps({
  deviceId: {
    type: String,
    default: null
  },
  city: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['city-updated'])

const weather = ref(null)
const loading = ref(false)
const error = ref(null)
const showCitySetup = ref(false)
const cityInput = ref('')
const savingCity = ref(false)

const resolvedCity = computed(() => (props.city || '').trim())

const weatherEmoji = computed(() => {
  if (!weather.value?.icon) return '🌡️'
  const iconMap = {
    '01d': '☀️',
    '01n': '🌙',
    '02d': '⛅',
    '02n': '☁️',
    '03d': '☁️',
    '03n': '☁️',
    '04d': '☁️',
    '04n': '☁️',
    '09d': '🌧️',
    '09n': '🌧️',
    '10d': '🌦️',
    '10n': '🌧️',
    '11d': '⛈️',
    '11n': '⛈️',
    '13d': '❄️',
    '13n': '❄️',
    '50d': '🌫️',
    '50n': '🌫️'
  }
  return iconMap[weather.value.icon] || '🌡️'
})

const formatTime = (isoString) => {
  if (!isoString) return 'N/A'
  try {
    const date = new Date(isoString)
    return date.toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' })
  } catch {
    return isoString
  }
}

const formatTimestamp = (isoString) => {
  if (!isoString) return 'N/A'
  try {
    const date = new Date(isoString)
    return date.toLocaleString('es-ES', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch {
    return isoString
  }
}

const openCityEditor = () => {
  cityInput.value = resolvedCity.value
  showCitySetup.value = true
}

const saveCity = async () => {
  if (!cityInput.value.trim() || !props.deviceId) return

  savingCity.value = true
  error.value = null

  try {
    const apiUrl = import.meta.env.VITE_API_URL || ''
    const response = await fetch(`${apiUrl}/api/devices/${props.deviceId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ city: cityInput.value.trim() })
    })

    if (!response.ok) {
      const data = await response.json().catch(() => ({}))
      throw new Error(data.detail || `Error al guardar ciudad (${response.status})`)
    }

    showCitySetup.value = false
    emit('city-updated')
    await fetchWeatherData(cityInput.value.trim())
  } catch (err) {
    error.value = err.message || 'No se pudo guardar la ciudad'
    console.error('Error saving city:', err)
  } finally {
    savingCity.value = false
  }
}

const fetchWeatherData = async (cityOverride = null) => {
  const cityToQuery = (cityOverride || resolvedCity.value).trim()

  if (!cityToQuery && !props.deviceId) {
    showCitySetup.value = true
    return
  }

  loading.value = true
  error.value = null
  weather.value = null
  showCitySetup.value = false

  try {
    const apiUrl = import.meta.env.VITE_API_URL || ''
    const url = cityToQuery
      ? `${apiUrl}/api/devices/weather/${encodeURIComponent(cityToQuery)}`
      : `${apiUrl}/api/devices/${props.deviceId}/weather`

    const response = await fetch(url, {
      headers: { 'Content-Type': 'application/json' }
    })

    if (!response.ok) {
      const data = await response.json().catch(() => ({}))
      const detail = data.detail || `Error: ${response.status}`

      if (response.status === 400 && props.deviceId) {
        cityInput.value = cityToQuery
        showCitySetup.value = true
        error.value = null
        return
      }

      throw new Error(detail)
    }

    const data = await response.json()
    weather.value = data.weather
  } catch (err) {
    error.value = err.message || 'Error al obtener datos del clima'
    console.error('Error fetching weather:', err)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  if (!resolvedCity.value && props.deviceId) {
    showCitySetup.value = true
    return
  }

  if (resolvedCity.value || props.deviceId) {
    fetchWeatherData()
  }
})

watch(() => props.city, (newCity) => {
  if (newCity?.trim() && !showCitySetup.value) {
    fetchWeatherData()
  }
})

defineExpose({
  fetchWeatherData
})
</script>

<style scoped>
.weather-card {
  background: #ffffff;
  color: #333;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  border: 1px solid #e8e8e8;
  transition: all 0.3s ease;
}

.weather-card:hover {
  box-shadow: 0 4px 12px rgba(102, 187, 106, 0.15);
  border-color: #d0d0d0;
}

.weather-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  border-bottom: 1px solid #f0f0f0;
  padding-bottom: 16px;
}

.weather-title {
  font-size: 18px;
  font-weight: 600;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 8px;
  color: #333;
  letter-spacing: 0.3px;
}

.weather-city {
  font-weight: 500;
  color: #2e7d32;
}

.weather-emoji {
  font-size: 1.5rem;
}

.country-badge {
  background: #e8f5e9;
  color: #2e7d32;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 0.875rem;
  font-weight: 600;
}

.weather-setup {
  background: #f8f9fa;
  border: 1px solid #e8e8e8;
  border-left: 3px solid #66bb6a;
  border-radius: 8px;
  padding: 16px;
}

.setup-text {
  margin: 0 0 12px;
  color: #555;
  font-size: 14px;
}

.setup-form {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.city-input {
  flex: 1;
  min-width: 200px;
  padding: 10px 12px;
  border: 1px solid #d0d0d0;
  border-radius: 8px;
  font-size: 14px;
  color: #333;
  background: #fff;
}

.city-input:focus {
  outline: none;
  border-color: #66bb6a;
  box-shadow: 0 0 0 2px rgba(102, 187, 106, 0.2);
}

.save-city-btn,
.retry-btn,
.edit-city-btn {
  border: none;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s ease;
}

.save-city-btn {
  padding: 10px 16px;
  background: #66bb6a;
  color: #fff;
}

.save-city-btn:hover:not(:disabled) {
  background: #57a85c;
}

.save-city-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.setup-hint {
  display: block;
  margin-top: 8px;
  color: #888;
  font-size: 12px;
}

.weather-loading,
.weather-error,
.weather-empty {
  text-align: center;
  padding: 20px;
  color: #666;
}

.weather-error {
  background: #ffebee;
  border: 1px solid #ef9a9a;
  border-radius: 8px;
  color: #c62828;
}

.retry-btn {
  margin-top: 12px;
  padding: 8px 14px;
  background: #fff;
  color: #c62828;
  border: 1px solid #ef9a9a;
}

.retry-btn:hover {
  background: #ffcdd2;
}

.weather-display {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.weather-main {
  display: flex;
  gap: 24px;
  align-items: flex-start;
}

.temperature-section {
  flex: 0 0 auto;
  text-align: center;
  background: #f1f8f5;
  border: 1px solid #c8e6c9;
  border-radius: 8px;
  padding: 16px 20px;
  min-width: 140px;
}

.current-temp {
  display: flex;
  align-items: flex-start;
  justify-content: center;
  gap: 4px;
}

.temp-value {
  font-size: 3rem;
  font-weight: 700;
  line-height: 1;
  color: #2e7d32;
}

.temp-unit {
  font-size: 1.25rem;
  font-weight: 600;
  margin-top: 8px;
  color: #66bb6a;
}

.description {
  margin: 12px 0 0;
  font-size: 1rem;
  text-transform: capitalize;
  color: #555;
}

.weather-details {
  flex: 1;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.detail-item {
  background: #f8f9fa;
  padding: 12px;
  border-radius: 8px;
  border: 1px solid #f0f0f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.detail-label {
  font-size: 0.875rem;
  color: #888;
  font-weight: 600;
}

.detail-value {
  font-size: 1rem;
  font-weight: 600;
  color: #333;
}

.weather-sun {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  background: #f8f9fa;
  border: 1px solid #f0f0f0;
  padding: 16px;
  border-radius: 8px;
}

.sun-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.sun-icon {
  font-size: 1.75rem;
}

.sun-label {
  margin: 0;
  font-size: 0.875rem;
  color: #888;
  font-weight: 600;
}

.sun-time {
  margin: 4px 0 0;
  font-size: 1rem;
  font-weight: 600;
  color: #333;
}

.weather-timestamp {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  color: #888;
  font-size: 0.875rem;
  margin-top: 4px;
  padding-top: 12px;
  border-top: 1px solid #f0f0f0;
}

.edit-city-btn {
  padding: 6px 12px;
  background: #f8f9fa;
  color: #2e7d32;
  border: 1px solid #c8e6c9;
}

.edit-city-btn:hover {
  background: #e8f5e9;
}

@media (max-width: 768px) {
  .weather-card {
    padding: 16px;
  }

  .weather-title {
    font-size: 16px;
  }

  .weather-main {
    flex-direction: column;
    gap: 16px;
  }

  .weather-details {
    grid-template-columns: 1fr;
  }

  .weather-sun {
    grid-template-columns: 1fr;
  }

  .temp-value {
    font-size: 2.5rem;
  }

  .weather-timestamp {
    flex-direction: column;
    align-items: flex-start;
  }
}

html[data-theme='dark'] .weather-card {
  background: #262a36;
  border-color: #3d4254;
  color: #e2e8f0;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.35);
}

html[data-theme='dark'] .weather-card:hover {
  border-color: #4ade80;
  box-shadow: 0 4px 16px rgba(74, 222, 128, 0.15);
}

html[data-theme='dark'] .weather-header {
  border-bottom-color: #3d4254;
}

html[data-theme='dark'] .weather-title {
  color: #f1f5f9;
}

html[data-theme='dark'] .weather-city {
  color: #86efac;
}

html[data-theme='dark'] .country-badge {
  background: #14532d;
  color: #bbf7d0;
}

html[data-theme='dark'] .weather-setup {
  background: #1a1d26;
  border-color: #3d4254;
  border-left-color: #4ade80;
}

html[data-theme='dark'] .setup-text {
  color: #94a3b8;
}

html[data-theme='dark'] .city-input {
  background: #1a1d26;
  border-color: #3d4254;
  color: #e2e8f0;
}

html[data-theme='dark'] .temperature-section {
  background: #1a2e24;
  border-color: #166534;
}

html[data-theme='dark'] .temp-value {
  color: #86efac;
}

html[data-theme='dark'] .temp-unit {
  color: #4ade80;
}

html[data-theme='dark'] .description {
  color: #94a3b8;
}

html[data-theme='dark'] .detail-item,
html[data-theme='dark'] .weather-sun {
  background: #1a1d26;
  border-color: #3d4254;
}

html[data-theme='dark'] .detail-label,
html[data-theme='dark'] .sun-label,
html[data-theme='dark'] .weather-timestamp,
html[data-theme='dark'] .setup-hint {
  color: #94a3b8;
}

html[data-theme='dark'] .detail-value,
html[data-theme='dark'] .sun-time {
  color: #e2e8f0;
}

html[data-theme='dark'] .weather-error {
  background: #3f1d1d;
  border-color: #7f1d1d;
  color: #fecaca;
}

html[data-theme='dark'] .edit-city-btn {
  background: #1a2e24;
  border-color: #166534;
  color: #86efac;
}
</style>
