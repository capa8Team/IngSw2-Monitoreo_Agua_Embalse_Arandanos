<template>
  <div class="dashboard-view">
    <DeviceList
      v-if="currentView === 'devices'"
      :devices-data="devices"
      @select-device="selectDevice"
      @open-history="openHistory"
    />

    <div v-else-if="currentView === 'dashboard'" class="dashboard">
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
        <div class="data-source-badge" :class="`source-${selectedDevice.dataSource}`">
          <span v-if="selectedDevice.dataSource === 'real'">📊 Datos Reales</span>
          <span v-else-if="selectedDevice.dataSource === 'simulated'">⚙️ Datos Simulados</span>
          <span v-else>❓ Fuente Desconocida</span>
        </div>
      </header>

      <main class="dashboard-content">
        <!-- Sensores -->
        <div class="sensors-grid">
          <SensorCard
            sensor-name="pH"
            :value="sensors.ph.value"
            :min="SENSOR_LIMITS.ph.min"
            :max="SENSOR_LIMITS.ph.max"
            :safe-max="SENSOR_LIMITS.ph.safeMax"
            unit="pH"
            :last-updated="lastSync"
          />
          <SensorCard
            sensor-name="Temperatura"
            :value="sensors.temperature.value"
            :min="SENSOR_LIMITS.temperature.min"
            :max="SENSOR_LIMITS.temperature.max"
            :safe-max="SENSOR_LIMITS.temperature.safeMax"
            unit="°C"
            :last-updated="lastSync"
          />
          <SensorCard
            sensor-name="Turbidez"
            :value="sensors.turbidity.value"
            :min="SENSOR_LIMITS.turbidity.min"
            :max="SENSOR_LIMITS.turbidity.max"
            :safe-max="SENSOR_LIMITS.turbidity.safeMax"
            unit="NTU"
            :last-updated="lastSync"
          />
        </div>
      </main>
    </div>

    <div v-else-if="currentView === 'history'" class="history">
      <header class="history-header">
        <button class="back-btn" @click="goBack" title="Volver">
          <svg viewBox="0 0 24 24" width="24" height="24" fill="currentColor">
            <path d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z"/>
          </svg>
        </button>
        <h1>Registro Histórico</h1>
      </header>

      <main class="history-content">
        <p>Componente de historial - próximamente</p>
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import DeviceList from '../components/DeviceList.vue'
import SensorCard from '../components/SensorCard.vue'

const currentView = ref('devices')
const selectedDevice = ref(null)
const devices = ref([
  {
    id: 1,
    name: 'Sensor Estación 1',
    model: 'Arduino + Sensores Analógicos',
    dataSource: 'real',
    status: 'active',
  },
  {
    id: 2,
    name: 'Sensor Estación 2',
    model: 'ESP8266 WiFi',
    dataSource: 'simulated',
    status: 'active',
  },
])

const sensors = ref({
  ph: { value: 7.2 },
  temperature: { value: 22.5 },
  turbidity: { value: 1.2 },
})

const lastSync = ref(new Date())

const SENSOR_LIMITS = {
  ph: { min: 0, max: 14, safeMax: 8 },
  temperature: { min: 0, max: 50, safeMax: 35 },
  turbidity: { min: 0, max: 10, safeMax: 5 },
}

const overallStatus = ref('good')
const overallStatusText = ref('Normal')

const selectDevice = (device) => {
  selectedDevice.value = device
  currentView.value = 'dashboard'
}

const openHistory = () => {
  currentView.value = 'history'
}

const goBack = () => {
  currentView.value = 'devices'
}
</script>

<style scoped>
.dashboard-view {
  width: 100%;
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.dashboard-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 20px;
}

.header-content {
  display: flex;
  align-items: center;
  gap: 16px;
  flex: 1;
}

.back-btn {
  background: rgba(255, 255, 255, 0.2);
  border: none;
  color: white;
  padding: 8px;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.3s;
}

.back-btn:hover {
  background: rgba(255, 255, 255, 0.3);
}

.header-title {
  margin: 0;
  font-size: 24px;
}

.header-subtitle {
  margin: 4px 0 0 0;
  opacity: 0.9;
  font-size: 14px;
}

.header-status {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-indicator {
  width: 12px;
  height: 12px;
  border-radius: 50%;
}

.status-indicator.indicator-good {
  background: #4ade80;
}

.status-indicator.indicator-warning {
  background: #fbbf24;
}

.status-indicator.indicator-critical {
  background: #f87171;
}

.status-label {
  font-size: 14px;
  font-weight: 600;
}

.data-source-badge {
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
  background: rgba(255, 255, 255, 0.2);
}

.dashboard-content {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
}

.sensors-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
}

.history {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.history-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
}

.history-header h1 {
  margin: 0;
  flex: 1;
  font-size: 24px;
}

.history-content {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
}
</style>
