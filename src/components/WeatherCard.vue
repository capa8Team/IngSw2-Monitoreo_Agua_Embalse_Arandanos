<template>
  <div class="weather-card">
    <div class="weather-header">
      <h3 class="weather-title">
        <span class="weather-emoji">{{ weatherEmoji }}</span>
        Clima — {{ weather?.city }}
      </h3>
      <span v-if="weather?.country" class="country-badge">{{ weather.country }}</span>
    </div>

    <div v-if="loading" class="weather-loading">
      <p>Cargando datos de clima...</p>
    </div>

    <div v-else-if="error" class="weather-error">
      <p>⚠️ {{ error }}</p>
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
      </div>
    </div>

    <div v-else class="weather-empty">
      <p>No hay datos de clima disponibles</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'

const props = defineProps({
  deviceId: {
    type: String,
    default: null
  },
  city: {
    type: String,
    default: null
  }
})

const weather = ref(null)
const loading = ref(false)
const error = ref(null)

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

const fetchWeatherData = async () => {
  loading.value = true
  error.value = null
  weather.value = null

  try {
    const apiUrl = import.meta.env.VITE_API_URL || ''
    let url

    if (props.deviceId) {
      url = `${apiUrl}/api/devices/${props.deviceId}/weather`
    } else if (props.city) {
      url = `${apiUrl}/api/devices/weather/${encodeURIComponent(props.city)}`
    } else {
      error.value = 'No se especificó ni dispositivo ni ciudad'
      return
    }

    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json'
      }
    })

    if (!response.ok) {
      const data = await response.json()
      throw new Error(data.detail || `Error: ${response.status}`)
    }

    const data = await response.json()
    
    if (props.deviceId) {
      weather.value = data.weather
    } else {
      weather.value = data
    }
  } catch (err) {
    error.value = err.message || 'Error al obtener datos del clima'
    console.error('Error fetching weather:', err)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  if (props.deviceId || props.city) {
    fetchWeatherData()
  }
})

defineExpose({
  fetchWeatherData
})
</script>

<style scoped>
.weather-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.1);
  transition: all 0.3s ease;
  backdrop-filter: blur(10px);
}

.weather-card:hover {
  box-shadow: 0 8px 16px rgba(102, 126, 234, 0.4);
  transform: translateY(-2px);
}

.weather-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
  padding-bottom: 16px;
}

.weather-title {
  font-size: 1.4rem;
  font-weight: 600;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.weather-emoji {
  font-size: 1.8rem;
}

.country-badge {
  background: rgba(255, 255, 255, 0.2);
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 0.875rem;
  font-weight: 500;
}

.weather-loading,
.weather-error,
.weather-empty {
  text-align: center;
  padding: 20px;
  opacity: 0.9;
}

.weather-error {
  background: rgba(255, 0, 0, 0.1);
  border-radius: 8px;
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
}

.current-temp {
  display: flex;
  align-items: flex-start;
  justify-content: center;
  gap: 4px;
}

.temp-value {
  font-size: 3.5rem;
  font-weight: 700;
  line-height: 1;
}

.temp-unit {
  font-size: 1.5rem;
  font-weight: 500;
  margin-top: 8px;
}

.description {
  margin: 12px 0 0;
  font-size: 1.1rem;
  text-transform: capitalize;
  opacity: 0.95;
}

.weather-details {
  flex: 1;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.detail-item {
  background: rgba(255, 255, 255, 0.1);
  padding: 12px;
  border-radius: 8px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.detail-label {
  font-size: 0.875rem;
  opacity: 0.8;
  font-weight: 500;
}

.detail-value {
  font-size: 1rem;
  font-weight: 600;
}

.weather-sun {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  background: rgba(255, 255, 255, 0.1);
  padding: 16px;
  border-radius: 8px;
}

.sun-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.sun-icon {
  font-size: 2rem;
}

.sun-label {
  margin: 0;
  font-size: 0.875rem;
  opacity: 0.8;
}

.sun-time {
  margin: 4px 0 0;
  font-size: 1rem;
  font-weight: 600;
}

.weather-timestamp {
  text-align: center;
  opacity: 0.7;
  font-size: 0.875rem;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

@media (max-width: 768px) {
  .weather-card {
    padding: 16px;
  }

  .weather-title {
    font-size: 1.2rem;
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

  .current-temp {
    margin-bottom: 12px;
  }

  .temp-value {
    font-size: 2.5rem;
  }
}
</style>
