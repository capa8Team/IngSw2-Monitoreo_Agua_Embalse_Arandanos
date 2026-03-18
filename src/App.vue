<template>
  <!-- Vista de Dispositivos -->
  <DeviceList v-if="currentView === 'devices'" @select-device="selectDevice" />

  <!-- Vista de Dashboard -->
  <div v-else class="dashboard">
    <header class="dashboard-header">
      <div class="header-content">
        <button class="back-btn" @click="goBack" title="Volver a dispositivos">
          <svg viewBox="0 0 24 24" width="24" height="24" fill="currentColor">
            <path d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z"/>
          </svg>
        </button>
        <div>
          <h1 class="header-title">{{ selectedDevice.name }}</h1>
          <p class="header-subtitle">{{ selectedDevice.model }}</p>
        </div>
      </div>
      <div class="header-status">
        <div class="status-indicator" :class="`indicator-${overallStatus}`"></div>
        <span class="status-label">{{ overallStatusText }}</span>
      </div>
    </header>

    <main class="dashboard-content">
      <div class="sensors-grid">
        <SensorCard
          sensor-name="pH"
          :value="sensors.ph.value"
          :min="sensors.ph.min"
          :max="sensors.ph.max"
          :safe-max="sensors.ph.safeMax"
          unit="pH"
          :last-updated="sensors.ph.lastUpdated"
        />
        
        <SensorCard
          sensor-name="Temperatura"
          :value="sensors.temperature.value"
          :min="sensors.temperature.min"
          :max="sensors.temperature.max"
          :safe-max="sensors.temperature.safeMax"
          unit="°C"
          :last-updated="sensors.temperature.lastUpdated"
        />
        
        <SensorCard
          sensor-name="Conductividad Eléctrica"
          :value="sensors.conductivity.value"
          :min="sensors.conductivity.min"
          :max="sensors.conductivity.max"
          :safe-max="sensors.conductivity.safeMax"
          unit="µS/cm"
          :last-updated="sensors.conductivity.lastUpdated"
        />
      </div>

      <section class="info-section">
        <h2 class="section-title">Información del Sistema</h2>
        <div class="info-grid">
          <div class="info-card">
            <div class="info-card-label">Sensores Activos</div>
            <div class="info-card-value">3/3</div>
          </div>
          <div class="info-card">
            <div class="info-card-label">Última Sincronización</div>
            <div class="info-card-value">{{ lastSync }}</div>
          </div>
          <div class="info-card">
            <div class="info-card-label">Conexión Arduino</div>
            <div class="info-card-value" :class="arduinoConnected ? 'connected' : 'disconnected'">
              {{ arduinoConnected ? 'Conectado' : 'Desconectado' }}
            </div>
          </div>
        </div>
      </section>
    </main>

    <footer class="dashboard-footer">
      <p>&copy; 2026 Sistema de Monitoreo Embalse Arándanos. Todos los derechos reservados.</p>
    </footer>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import DeviceList from './components/DeviceList.vue'
import SensorCard from './components/SensorCard.vue'

// Estado de navegación
const currentView = ref('devices') // 'devices' o 'dashboard'

// Dispositivo seleccionado
const selectedDevice = ref({
  id: null,
  name: 'Sin dispositivo',
  model: 'Selecciona un dispositivo para comenzar'
})

const sensors = ref({
  ph: {
    value: 7.2,
    min: 6.0,
    max: 8.5,
    safeMax: 8.0,
    lastUpdated: 'hace 2s'
  },
  temperature: {
    value: 22.5,
    min: 5,
    max: 35,
    safeMax: 28,
    lastUpdated: 'hace 3s'
  },
  conductivity: {
    value: 650,
    min: 100,
    max: 2000,
    safeMax: 1500,
    lastUpdated: 'hace 1s'
  }
})

const lastSync = ref('hace 10 segundos')
const arduinoConnected = ref(true)

const overallStatus = computed(() => {
  const statuses = [
    getStatus(sensors.value.ph.value, sensors.value.ph.min, sensors.value.ph.max, sensors.value.ph.safeMax),
    getStatus(sensors.value.temperature.value, sensors.value.temperature.min, sensors.value.temperature.max, sensors.value.temperature.safeMax),
    getStatus(sensors.value.conductivity.value, sensors.value.conductivity.min, sensors.value.conductivity.max, sensors.value.conductivity.safeMax)
  ]
  
  if (statuses.includes('danger')) return 'danger'
  if (statuses.includes('warning')) return 'warning'
  return 'safe'
})

const overallStatusText = computed(() => {
  if (overallStatus.value === 'danger') return 'Situación Peligrosa'
  if (overallStatus.value === 'warning') return 'Advertencia'
  return 'Sistema Normal'
})

const getStatus = (value, min, max, safeMax) => {
  const percentage = ((value - min) / (max - min)) * 100
  if (percentage < 15 || percentage > 85) return 'danger'
  if (percentage < 35 || percentage > 65) return 'warning'
  return 'safe'
}

// Métodos de navegación
const selectDevice = (device) => {
  selectedDevice.value = {
    id: device.id,
    name: device.name,
    model: device.model
  }
  currentView.value = 'dashboard'
  
  // Simular que los sensores se cargan del dispositivo seleccionado
  if (device.sensors) {
    const phSensor = device.sensors.find(s => s.id === 'ph')
    const tempSensor = device.sensors.find(s => s.id === 'temp')
    const condSensor = device.sensors.find(s => s.id === 'cond')
    
    if (phSensor) sensors.value.ph.value = phSensor.value
    if (tempSensor) sensors.value.temperature.value = tempSensor.value
    if (condSensor) sensors.value.conductivity.value = condSensor.value
  }
  
  startSensorUpdates()
}

const goBack = () => {
  currentView.value = 'devices'
  stopSensorUpdates()
}

// Simulación de actualización en tiempo real
let updateInterval = null

const updateSensorData = () => {
  // Simulación de datos (reemplazar con datos reales del Arduino)
  sensors.value.ph.value = 7.0 + Math.random() * 1.0
  sensors.value.temperature.value = 20 + Math.random() * 8
  sensors.value.conductivity.value = 600 + Math.random() * 200
  
  // Actualizar timestamps
  sensors.value.ph.lastUpdated = `hace ${Math.floor(Math.random() * 5) + 1}s`
  sensors.value.temperature.lastUpdated = `hace ${Math.floor(Math.random() * 5) + 1}s`
  sensors.value.conductivity.lastUpdated = `hace ${Math.floor(Math.random() * 5) + 1}s`
  lastSync.value = `hace ${Math.floor(Math.random() * 15) + 1}s`
}

const startSensorUpdates = () => {
  // Actualizar datos cada 3 segundos (simulación)
  if (updateInterval) clearInterval(updateInterval)
  updateInterval = setInterval(updateSensorData, 3000)
}

const stopSensorUpdates = () => {
  if (updateInterval) {
    clearInterval(updateInterval)
    updateInterval = null
  }
}

onMounted(() => {
  // No iniciar actualizaciones hasta que se seleccione un dispositivo
})

onUnmounted(() => {
  stopSensorUpdates()
})
</script>

<style scoped>
.dashboard {
  min-height: 100vh;
  background: linear-gradient(135deg, #f5f7fa 0%, #e8ecf1 100%);
  display: flex;
  flex-direction: column;
}

.dashboard-header {
  background: #ffffff;
  border-bottom: 1px solid #e8e8e8;
  padding: 32px 40px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.04);
}

.header-content {
  display: flex;
  align-items: center;
  gap: 16px;
  flex: 1;
}

.back-btn {
  width: 40px;
  height: 40px;
  background: #f0f2f5;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #333;
  transition: all 0.2s ease;
  flex-shrink: 0;
}

.back-btn:hover {
  background: #e0e2e5;
  color: #66bb6a;
}

.header-content h1 {
  margin: 0;
  font-size: 28px;
  font-weight: 700;
  color: #222;
  letter-spacing: -0.5px;
}

.header-subtitle {
  margin: 8px 0 0 0;
  color: #888;
  font-size: 14px;
  font-weight: 400;
}

.header-status {
  display: flex;
  align-items: center;
  gap: 12px;
  background: #f8f9fa;
  padding: 12px 20px;
  border-radius: 8px;
}

.status-indicator {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  animation: pulse 2s ease-in-out infinite;
}

.indicator-safe {
  background-color: #66bb6a;
}

.indicator-warning {
  background-color: #ffb84d;
}

.indicator-danger {
  background-color: #ff4444;
}

.status-label {
  font-size: 14px;
  font-weight: 600;
  color: #555;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.6;
  }
}

.dashboard-content {
  flex: 1;
  padding: 40px;
  max-width: 1400px;
  margin: 0 auto;
  width: 100%;
}

.sensors-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(380px, 1fr));
  gap: 24px;
  margin-bottom: 40px;
}

.info-section {
  background: #ffffff;
  border-radius: 12px;
  padding: 28px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  border: 1px solid #e8e8e8;
}

.section-title {
  margin: 0 0 20px 0;
  font-size: 18px;
  font-weight: 600;
  color: #333;
  letter-spacing: 0.3px;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}

.info-card {
  background: #f8f9fa;
  padding: 16px;
  border-radius: 8px;
  border-left: 3px solid #d0d0d0;
}

.info-card-label {
  font-size: 12px;
  color: #888;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 8px;
}

.info-card-value {
  font-size: 16px;
  color: #333;
  font-weight: 600;
}

.info-card-value.connected {
  color: #2e7d32;
}

.info-card-value.disconnected {
  color: #c62828;
}

.dashboard-footer {
  background: #ffffff;
  border-top: 1px solid #e8e8e8;
  padding: 20px 40px;
  text-align: center;
  color: #999;
  font-size: 13px;
  margin-top: auto;
}

.dashboard-footer p {
  margin: 0;
}

@media (max-width: 1024px) {
  .sensors-grid {
    grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  }

  .dashboard-header {
    flex-direction: column;
    gap: 20px;
    align-items: flex-start;
  }
}

@media (max-width: 768px) {
  .dashboard-header {
    padding: 20px 16px;
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
  }

  .header-content {
    gap: 12px;
  }

  .header-content h1 {
    font-size: 22px;
  }

  .header-subtitle {
    font-size: 13px;
  }

  .header-status {
    width: 100%;
    justify-content: center;
  }

  .dashboard-content {
    padding: 16px;
  }

  .sensors-grid {
    grid-template-columns: 1fr;
    gap: 16px;
    margin-bottom: 24px;
  }

  .info-section {
    padding: 20px;
  }

  .dashboard-footer {
    padding: 16px;
    font-size: 12px;
  }
}

@media (max-width: 480px) {
  .dashboard {
    min-height: 100vh;
  }

  .dashboard-header {
    padding: 16px 12px;
  }

  .back-btn {
    width: 36px;
    height: 36px;
  }

  .header-content {
    gap: 10px;
  }

  .header-content h1 {
    font-size: 18px;
  }

  .header-subtitle {
    font-size: 12px;
  }

  .status-label {
    font-size: 12px;
  }

  .dashboard-content {
    padding: 12px;
  }

  .sensors-grid {
    gap: 12px;
    margin-bottom: 20px;
  }

  .info-grid {
    grid-template-columns: 1fr;
  }

  .info-section {
    padding: 16px;
  }

  .section-title {
    font-size: 16px;
    margin-bottom: 16px;
  }

  .info-card {
    padding: 12px;
    border-left-width: 2px;
  }

  .info-card-label {
    font-size: 11px;
  }

  .info-card-value {
    font-size: 15px;
  }

  .dashboard-footer {
    padding: 12px;
    font-size: 11px;
  }
}
</style>
