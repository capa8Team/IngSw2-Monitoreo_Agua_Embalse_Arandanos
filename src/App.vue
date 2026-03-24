<template>
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
    </header>

    <main class="dashboard-content">
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
          sensor-name="Conductividad Eléctrica"
          :value="sensors.conductivity.value"
          :min="SENSOR_LIMITS.conductivity.min"
          :max="SENSOR_LIMITS.conductivity.max"
          :safe-max="SENSOR_LIMITS.conductivity.safeMax"
          unit="µS/cm"
          :last-updated="lastSync"
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
            <div class="info-card-value" :class="selectedDevice.status === 'connected' ? 'connected' : 'disconnected'">
              {{ selectedDevice.status === 'connected' ? 'Conectado' : 'Desconectado' }}
            </div>
          </div>
        </div>
      </section>

      <section class="alerts-section">
        <div class="alerts-header">
          <h2 class="section-title">Tabla de Alertas (día actual)</h2>
          <span class="alerts-count">Mostrando {{ visibleAlerts.length }} de {{ todayAlerts.length }}</span>
        </div>
        <div class="table-wrap">
          <table class="alerts-table">
            <thead>
              <tr>
                <th>Dispositivo</th>
                <th>pH</th>
                <th>Temperatura</th>
                <th>Conductividad</th>
                <th>Estado de carga</th>
                <th>Fecha</th>
                <th>Hora</th>
                <th>Telegram</th>
                <th>Email</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="alert in visibleAlerts" :key="alert.id">
                <td>{{ alert.deviceName }}</td>
                <td>{{ alert.ph }}</td>
                <td>{{ alert.temperature }}</td>
                <td>{{ alert.conductivity }}</td>
                <td>{{ alert.battery }}%</td>
                <td>{{ alert.date }}</td>
                <td>{{ alert.time }}</td>
                <td>{{ alert.telegramStatus }}</td>
                <td>{{ alert.emailStatus }}</td>
              </tr>
              <tr v-if="visibleAlerts.length === 0">
                <td colspan="9" class="empty-cell">Sin alertas registradas para hoy.</td>
              </tr>
            </tbody>
          </table>
        </div>
        <button
          v-if="todayAlerts.length > ALERT_TABLE_LIMIT"
          class="see-more-btn"
          @click="showAllTodayAlerts = !showAllTodayAlerts"
        >
          {{ showAllTodayAlerts ? 'Ver menos' : 'Ver más' }}
        </button>
      </section>
    </main>
  </div>

  <div v-else class="history-view">
    <header class="dashboard-header">
      <div class="header-content">
        <button class="back-btn" @click="goBack" title="Volver a dispositivos">
          <svg viewBox="0 0 24 24" width="24" height="24" fill="currentColor">
            <path d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z"/>
          </svg>
        </button>
        <div>
          <h1 class="header-title">Registro Histórico</h1>
          <p class="header-subtitle">Todas las mediciones guardadas por dispositivo y fecha</p>
        </div>
      </div>
      <button class="pdf-btn" @click="downloadHistoryPdf">Descargar PDF</button>
    </header>

    <main class="dashboard-content">
      <section class="filters-section">
        <h2 class="section-title">Opciones de filtrado</h2>
        <div class="filters-grid">
          <label class="filter-item">
            <span>Dispositivo</span>
            <select v-model="historyFilters.deviceId">
              <option value="all">Todos</option>
              <option v-for="device in devices" :key="device.id" :value="String(device.id)">
                {{ device.name }}
              </option>
            </select>
          </label>
          <label class="filter-item">
            <span>Fecha</span>
            <select v-model="historyFilters.date">
              <option value="all">Todas</option>
              <option v-for="dateValue in availableDates" :key="dateValue" :value="dateValue">
                {{ dateValue }}
              </option>
            </select>
          </label>
        </div>
      </section>

      <section class="charts-section">
        <h2 class="section-title">Gráficos de tendencias</h2>
        <div class="chart-grid">
          <div class="chart-card">
            <h3>pH</h3>
            <svg viewBox="0 0 320 120" class="line-chart">
              <polyline :points="buildLineChartPoints(historyFilteredRows, 'ph', 5, 9)" />
            </svg>
          </div>
          <div class="chart-card">
            <h3>Temperatura</h3>
            <svg viewBox="0 0 320 120" class="line-chart">
              <polyline :points="buildLineChartPoints(historyFilteredRows, 'temperature', 15, 35)" />
            </svg>
          </div>
          <div class="chart-card">
            <h3>Conductividad</h3>
            <svg viewBox="0 0 320 120" class="line-chart">
              <polyline :points="buildLineChartPoints(historyFilteredRows, 'conductivity', 200, 1800)" />
            </svg>
          </div>
        </div>
      </section>

      <section class="alerts-section">
        <div class="alerts-header">
          <h2 class="section-title">Mediciones filtradas</h2>
          <span class="alerts-count">{{ historyFilteredRows.length }} filas</span>
        </div>
        <div class="table-wrap">
          <table class="alerts-table">
            <thead>
              <tr>
                <th>Dispositivo</th>
                <th>pH</th>
                <th>Temperatura</th>
                <th>Conductividad</th>
                <th>Estado de carga</th>
                <th>Fecha</th>
                <th>Hora</th>
                <th>Telegram</th>
                <th>Email</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in historyFilteredRows" :key="row.id">
                <td>{{ row.deviceName }}</td>
                <td>{{ row.ph }}</td>
                <td>{{ row.temperature }}</td>
                <td>{{ row.conductivity }}</td>
                <td>{{ row.battery }}%</td>
                <td>{{ row.date }}</td>
                <td>{{ row.time }}</td>
                <td>{{ row.telegramStatus }}</td>
                <td>{{ row.emailStatus }}</td>
              </tr>
              <tr v-if="historyFilteredRows.length === 0">
                <td colspan="9" class="empty-cell">No hay datos para los filtros seleccionados.</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onUnmounted } from 'vue'
import DeviceList from './components/DeviceList.vue'
import SensorCard from './components/SensorCard.vue'

const ALERT_TABLE_LIMIT = 20
const SENSOR_LIMITS = {
  ph: { min: 6.0, max: 8.5, safeMax: 8.0 },
  temperature: { min: 5, max: 35, safeMax: 28 },
  conductivity: { min: 100, max: 2000, safeMax: 1500 }
}

const currentView = ref('devices')
const selectedDeviceId = ref(null)
const lastSync = ref('hace 10 segundos')
const showAllTodayAlerts = ref(false)

const devices = ref([
  {
    id: 1,
    name: 'Arduino Embalse A',
    model: 'Arduino Uno - Zona Norte',
    status: 'connected',
    lastUpdate: 'hace 2 segundos',
    battery: 89,
    sensors: { ph: 7.2, temperature: 22.5, conductivity: 650 }
  },
  {
    id: 2,
    name: 'Arduino Embalse B',
    model: 'Arduino Uno - Zona Sur',
    status: 'connected',
    lastUpdate: 'hace 1 segundo',
    battery: 74,
    sensors: { ph: 7.1, temperature: 21.8, conductivity: 620 }
  },
  {
    id: 3,
    name: 'Arduino Embalse C',
    model: 'Arduino Uno - Zona Este',
    status: 'connected',
    lastUpdate: 'hace 3 segundos',
    battery: 81,
    sensors: { ph: 7.4, temperature: 23.2, conductivity: 680 }
  },
  {
    id: 4,
    name: 'Arduino Embalse D',
    model: 'Arduino Uno - Zona Oeste',
    status: 'disconnected',
    lastUpdate: 'hace 5 minutos',
    battery: 52,
    sensors: { ph: 6.8, temperature: 20.6, conductivity: 590 }
  }
])

const selectedDevice = computed(() => {
  return devices.value.find((device) => device.id === selectedDeviceId.value) || {
    id: null,
    name: 'Sin dispositivo',
    model: 'Selecciona un dispositivo para comenzar',
    status: 'disconnected',
    sensors: { ph: 7.2, temperature: 22.5, conductivity: 650 }
  }
})

const sensors = computed(() => ({
  ph: { value: selectedDevice.value.sensors.ph },
  temperature: { value: selectedDevice.value.sensors.temperature },
  conductivity: { value: selectedDevice.value.sensors.conductivity }
}))

const historyRecords = ref([])
const historyFilters = ref({
  deviceId: 'all',
  date: 'all'
})

const getStatus = (value, min, max) => {
  const percentage = ((value - min) / (max - min)) * 100
  if (percentage < 15 || percentage > 85) return 'danger'
  if (percentage < 35 || percentage > 65) return 'warning'
  return 'safe'
}

const overallStatus = computed(() => {
  const statuses = [
    getStatus(sensors.value.ph.value, SENSOR_LIMITS.ph.min, SENSOR_LIMITS.ph.max),
    getStatus(sensors.value.temperature.value, SENSOR_LIMITS.temperature.min, SENSOR_LIMITS.temperature.max),
    getStatus(sensors.value.conductivity.value, SENSOR_LIMITS.conductivity.min, SENSOR_LIMITS.conductivity.max)
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

const formatDate = (date) => {
  const day = String(date.getDate()).padStart(2, '0')
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const year = date.getFullYear()
  return `${day}-${month}-${year}`
}

const formatTime = (date) => {
  const hour = String(date.getHours()).padStart(2, '0')
  const minute = String(date.getMinutes()).padStart(2, '0')
  const second = String(date.getSeconds()).padStart(2, '0')
  return `${hour}:${minute}:${second}`
}

const createRecord = (device) => {
  const now = new Date()
  const ph = Number(device.sensors.ph.toFixed(2))
  const temperature = Number(device.sensors.temperature.toFixed(2))
  const conductivity = Number(device.sensors.conductivity.toFixed(2))
  const isAlert =
    ph < SENSOR_LIMITS.ph.min || ph > SENSOR_LIMITS.ph.max ||
    temperature < SENSOR_LIMITS.temperature.min || temperature > SENSOR_LIMITS.temperature.max ||
    conductivity < SENSOR_LIMITS.conductivity.min || conductivity > SENSOR_LIMITS.conductivity.max

  const statuses = ['enviado', 'recibido', 'fallo']
  return {
    id: `${device.id}-${now.getTime()}-${Math.random().toString(16).slice(2, 8)}`,
    deviceId: device.id,
    deviceName: device.name,
    ph,
    temperature,
    conductivity,
    battery: device.battery,
    date: formatDate(now),
    time: formatTime(now),
    timestamp: now.getTime(),
    telegramStatus: statuses[Math.floor(Math.random() * statuses.length)],
    emailStatus: statuses[Math.floor(Math.random() * statuses.length)],
    isAlert
  }
}

const availableDates = computed(() => {
  const uniqueDates = [...new Set(historyRecords.value.map((record) => record.date))]
  return uniqueDates.sort((a, b) => {
    const [da, ma, ya] = a.split('-').map(Number)
    const [db, mb, yb] = b.split('-').map(Number)
    return new Date(yb, mb - 1, db) - new Date(ya, ma - 1, da)
  })
})

const historyFilteredRows = computed(() => {
  return historyRecords.value
    .filter((record) => {
      const matchesDevice = historyFilters.value.deviceId === 'all' || record.deviceId === Number(historyFilters.value.deviceId)
      const matchesDate = historyFilters.value.date === 'all' || record.date === historyFilters.value.date
      return matchesDevice && matchesDate
    })
    .sort((a, b) => b.timestamp - a.timestamp)
})

const todayString = computed(() => formatDate(new Date()))
const todayAlerts = computed(() => {
  return historyRecords.value
    .filter((record) => record.isAlert && record.deviceId === selectedDeviceId.value && record.date === todayString.value)
    .sort((a, b) => b.timestamp - a.timestamp)
})

const visibleAlerts = computed(() => {
  return showAllTodayAlerts.value ? todayAlerts.value : todayAlerts.value.slice(0, ALERT_TABLE_LIMIT)
})

const buildLineChartPoints = (rows, key, min, max) => {
  const chartRows = rows.slice(0, 20).reverse()
  if (chartRows.length < 2) return '0,100 320,100'
  return chartRows.map((row, index) => {
    const x = (index / (chartRows.length - 1)) * 320
    const value = Number(row[key])
    const normalized = (value - min) / (max - min)
    const y = 110 - Math.max(0, Math.min(1, normalized)) * 100
    return `${x.toFixed(2)},${y.toFixed(2)}`
  }).join(' ')
}

const escapeHtml = (value) => {
  return String(value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;')
}

const downloadHistoryPdf = () => {
  const groupedByDevice = historyFilteredRows.value.reduce((acc, row) => {
    if (!acc[row.deviceName]) acc[row.deviceName] = []
    acc[row.deviceName].push(row)
    return acc
  }, {})

  const rowsHtml = Object.entries(groupedByDevice).map(([deviceName, rows]) => {
    const tableRows = rows.map((row) => {
      return `<tr>
        <td>${escapeHtml(row.ph)}</td>
        <td>${escapeHtml(row.temperature)}</td>
        <td>${escapeHtml(row.conductivity)}</td>
        <td>${escapeHtml(row.battery)}%</td>
        <td>${escapeHtml(row.date)}</td>
        <td>${escapeHtml(row.time)}</td>
        <td>${escapeHtml(row.telegramStatus)}</td>
        <td>${escapeHtml(row.emailStatus)}</td>
      </tr>`
    }).join('')
    return `
      <h2>${escapeHtml(deviceName)}</h2>
      <table>
        <thead>
          <tr>
            <th>pH</th>
            <th>Temperatura</th>
            <th>Conductividad</th>
            <th>Estado de carga</th>
            <th>Fecha</th>
            <th>Hora</th>
            <th>Telegram</th>
            <th>Email</th>
          </tr>
        </thead>
        <tbody>${tableRows}</tbody>
      </table>
    `
  }).join('')

  const win = window.open('', '_blank')
  if (!win) return
  win.document.write(`
    <html>
      <head>
        <title>Registro Historico</title>
        <style>
          body { font-family: Arial, sans-serif; margin: 20px; color: #1f2937; }
          h1 { margin-bottom: 8px; }
          h2 { margin-top: 28px; margin-bottom: 8px; color: #2e7d32; }
          p { margin-top: 0; color: #4b5563; }
          table { width: 100%; border-collapse: collapse; margin-bottom: 16px; }
          th, td { border: 1px solid #d1d5db; padding: 6px 8px; font-size: 12px; text-align: left; }
          th { background: #f3f4f6; }
        </style>
      </head>
      <body>
        <h1>Registro Historico de Mediciones</h1>
        <p>Filtro dispositivo: ${escapeHtml(historyFilters.value.deviceId === 'all' ? 'Todos' : selectedDevice.value.name)} | Filtro fecha: ${escapeHtml(historyFilters.value.date === 'all' ? 'Todas' : historyFilters.value.date)}</p>
        ${rowsHtml || '<p>No hay datos para exportar.</p>'}
      </body>
    </html>
  `)
  win.document.close()
  win.focus()
  win.print()
}

const seedHistoricalData = () => {
  const dates = [0, 1, 2]
  dates.forEach((daysAgo) => {
    devices.value.forEach((device) => {
      for (let i = 0; i < 18; i += 1) {
        const sampleDate = new Date()
        sampleDate.setDate(sampleDate.getDate() - daysAgo)
        sampleDate.setHours(6 + i, Math.floor(Math.random() * 60), Math.floor(Math.random() * 60), 0)
        const clone = {
          ...device,
          sensors: {
            ph: 6.4 + Math.random() * 2.3,
            temperature: 18 + Math.random() * 12,
            conductivity: 450 + Math.random() * 900
          },
          battery: Math.max(35, device.battery - Math.floor(Math.random() * 15))
        }
        const record = createRecord(clone)
        record.timestamp = sampleDate.getTime()
        record.date = formatDate(sampleDate)
        record.time = formatTime(sampleDate)
        historyRecords.value.push(record)
      }
    })
  })
}

const selectDevice = (device) => {
  selectedDeviceId.value = device.id
  currentView.value = 'dashboard'
  showAllTodayAlerts.value = false
  startSensorUpdates()
}

const openHistory = () => {
  currentView.value = 'history'
  stopSensorUpdates()
}

const goBack = () => {
  currentView.value = 'devices'
  stopSensorUpdates()
}

let updateInterval = null
const updateSensorData = () => {
  if (!selectedDeviceId.value) return
  const index = devices.value.findIndex((device) => device.id === selectedDeviceId.value)
  if (index === -1) return
  const device = devices.value[index]
  const statusConnected = device.status === 'connected'
  if (!statusConnected) return

  device.sensors.ph = 6.0 + Math.random() * 3.0
  device.sensors.temperature = 17 + Math.random() * 20
  device.sensors.conductivity = 350 + Math.random() * 1800
  device.battery = Math.max(15, device.battery - (Math.random() > 0.8 ? 1 : 0))
  device.lastUpdate = 'hace unos segundos'
  devices.value[index] = { ...device }

  const newRecord = createRecord(device)
  historyRecords.value.push(newRecord)
  lastSync.value = `hace ${Math.floor(Math.random() * 12) + 1}s`
}

const startSensorUpdates = () => {
  if (updateInterval) clearInterval(updateInterval)
  updateSensorData()
  updateInterval = setInterval(updateSensorData, 3000)
}

const stopSensorUpdates = () => {
  if (updateInterval) {
    clearInterval(updateInterval)
    updateInterval = null
  }
}

seedHistoricalData()

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

.alerts-section,
.filters-section,
.charts-section {
  margin-top: 28px;
  background: #ffffff;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  border: 1px solid #e8e8e8;
}

.alerts-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14px;
}

.alerts-count {
  font-size: 12px;
  color: #6b7280;
  font-weight: 600;
}

.table-wrap {
  overflow-x: auto;
}

.alerts-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.alerts-table th,
.alerts-table td {
  border: 1px solid #e5e7eb;
  padding: 8px 10px;
  text-align: left;
  white-space: nowrap;
}

.alerts-table th {
  background: #f9fafb;
  color: #374151;
}

.empty-cell {
  text-align: center;
  color: #6b7280;
}

.see-more-btn,
.pdf-btn {
  margin-top: 14px;
  border: 1px solid #66bb6a;
  background: #ffffff;
  color: #2e7d32;
  border-radius: 8px;
  padding: 8px 14px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
}

.see-more-btn:hover,
.pdf-btn:hover {
  background: #e8f5e9;
}

.pdf-btn {
  margin-top: 0;
}

.filters-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 14px;
}

.filter-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 13px;
  color: #374151;
  font-weight: 600;
}

.filter-item select {
  border: 1px solid #d1d5db;
  border-radius: 8px;
  padding: 8px 10px;
  font-size: 13px;
  background: #ffffff;
}

.chart-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 16px;
}

.chart-card {
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  padding: 12px;
  background: #f9fafb;
}

.chart-card h3 {
  margin-bottom: 8px;
  font-size: 14px;
}

.line-chart {
  width: 100%;
  height: 120px;
}

.line-chart polyline {
  fill: none;
  stroke: #2e7d32;
  stroke-width: 2.5;
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

  .pdf-btn {
    width: 100%;
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

  .alerts-section,
  .filters-section,
  .charts-section {
    margin-top: 20px;
    padding: 16px;
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

  .alerts-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 6px;
  }

  .dashboard-footer {
    padding: 12px;
    font-size: 11px;
  }
}
</style>
