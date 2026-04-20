<template>
  <div v-if="currentView === 'devices'" class="devices-view">
    <DeviceList
      :devices-data="devices"
      @select-device="selectDevice"
      @open-history="openHistory"
      @open-user-management="openUserManagementView"
    />
  </div>

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
      <div v-if="isAdmin" class="header-center admin-top-actions">
        <button class="admin-nav-btn" @click="openAlertConfigView">Configuracion rango alertas</button>
      </div>
      <div class="header-right">
        <div class="data-source-badge" :class="`source-${selectedDevice.dataSource}`">
          <span v-if="selectedDevice.dataSource === 'real'">📊 Datos Reales</span>
          <span v-else-if="selectedDevice.dataSource === 'simulated'">⚙️ Datos Simulados</span>
          <span v-else>❓ Fuente Desconocida</span>
        </div>
        <button class="history-btn" @click="openHistory" title="Ver datos históricos">📈 Históricos</button>
        <button class="logout-btn" @click="handleLogout">🚪 Logout</button>
      </div>
    </header>

    <main class="dashboard-content">
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
          <div class="info-card">
            <div class="info-card-label">Rol de Usuario</div>
            <div class="info-card-value" :class="isAdmin ? 'admin-role' : 'user-role'">
              {{ isAdmin ? '👨‍💼 Administrador' : '👤 Empleado' }}
            </div>
          </div>
        </div>
      </section>

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

      <section class="diagnostics-section">
        <div class="alerts-header">
          <h2 class="section-title">Diagnóstico de solicitudes (tiempo real)</h2>
          <span class="alerts-count">Actualiza cada 5s</span>
        </div>
        <div class="diagnostics-grid">
          <div class="diagnostic-card">
            <div class="diagnostic-title">Dashboard (/api/dashboard)</div>
            <div class="diagnostic-row"><span>Intentos</span><strong>{{ requestMonitor.dashboard.attempts }}</strong></div>
            <div class="diagnostic-row"><span>Exitosas</span><strong>{{ requestMonitor.dashboard.ok }}</strong></div>
            <div class="diagnostic-row"><span>Errores</span><strong>{{ requestMonitor.dashboard.error }}</strong></div>
            <div class="diagnostic-row"><span>Estado</span><strong>{{ requestMonitor.dashboard.lastStatus }}</strong></div>
            <div class="diagnostic-row"><span>Último dato</span><strong>{{ requestMonitor.dashboard.lastSuccessAt }}</strong></div>
          </div>
          <div class="diagnostic-card">
            <div class="diagnostic-title">Historial (/api/sensors/history)</div>
            <div class="diagnostic-row"><span>Intentos</span><strong>{{ requestMonitor.history.attempts }}</strong></div>
            <div class="diagnostic-row"><span>Exitosas</span><strong>{{ requestMonitor.history.ok }}</strong></div>
            <div class="diagnostic-row"><span>Errores</span><strong>{{ requestMonitor.history.error }}</strong></div>
            <div class="diagnostic-row"><span>Estado</span><strong>{{ requestMonitor.history.lastStatus }}</strong></div>
            <div class="diagnostic-row"><span>Último dato</span><strong>{{ requestMonitor.history.lastSuccessAt }}</strong></div>
          </div>
          <div class="diagnostic-card">
            <div class="diagnostic-title">Render del frontend</div>
            <div class="diagnostic-row"><span>Última pintura</span><strong>{{ requestMonitor.ui.lastRenderedAt }}</strong></div>
            <div class="diagnostic-row"><span>Último error</span><strong>{{ requestMonitor.ui.lastError }}</strong></div>
            <div class="diagnostic-row"><span>Dispositivo</span><strong>{{ selectedDevice.status === 'connected' ? 'Conectado' : 'Desconectado' }}</strong></div>
          </div>
        </div>
      </section>

      <section class="alerts-section">
        <div class="alerts-header">
          <h2 class="section-title">Tabla de Alertas (día actual)</h2>
          <span class="alerts-count">Mostrando {{ visibleAlerts.length }} de {{ todayAlerts.length }}</span>
        </div>
        <div class="table-wrapper" :class="{ expanded: showAllTodayAlerts }">
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
          <div v-if="todayAlerts.length > ALERT_TABLE_LIMIT" class="table-footer">
            <button
              class="see-more-btn"
              @click="showAllTodayAlerts = !showAllTodayAlerts"
            >
              {{ showAllTodayAlerts ? 'Ver menos' : 'Mostrar más' }}
            </button>
          </div>
        </div>
      </section>
    </main>
  </div>

  <div v-else-if="currentView === 'admin-alerts'" class="dashboard">
    <header class="dashboard-header">
      <div class="header-content">
        <button class="back-btn" @click="goToDashboardView" title="Volver al dashboard">
          <svg viewBox="0 0 24 24" width="24" height="24" fill="currentColor">
            <path d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z"/>
          </svg>
        </button>
        <div>
          <h1 class="header-title">Configuracion rango alertas</h1>
          <p class="header-subtitle">Define umbrales por sensor para dashboard y alertas</p>
        </div>
      </div>
      <div class="header-center admin-top-actions">
        <button class="admin-nav-btn active">Configuracion rango alertas</button>
      </div>
      <div class="header-right">
        <div class="data-source-badge" :class="`source-${selectedDevice.dataSource}`">
          <span v-if="selectedDevice.dataSource === 'real'">📊 Datos Reales</span>
          <span v-else-if="selectedDevice.dataSource === 'simulated'">⚙️ Datos Simulados</span>
          <span v-else>❓ Fuente Desconocida</span>
        </div>
        <button class="logout-btn" @click="handleLogout">🚪 Logout</button>
      </div>
    </header>

    <main class="dashboard-content">
      <section class="alerts-config-section">
        <div class="alerts-header">
          <h2 class="section-title">Configuracion de rangos por sensor</h2>
        </div>

        <div class="alerts-config-grid">
          <div class="alert-config-card">
            <h3>🔬 pH</h3>
            <div class="config-group">
              <label>Minimo:</label>
              <input v-model.number="SENSOR_LIMITS.ph.min" type="number" step="0.1" />
            </div>
            <div class="config-group">
              <label>Maximo:</label>
              <input v-model.number="SENSOR_LIMITS.ph.max" type="number" step="0.1" />
            </div>
            <div class="config-group">
              <label>Maximo seguro:</label>
              <input v-model.number="SENSOR_LIMITS.ph.safeMax" type="number" step="0.1" />
            </div>
            <button class="save-config-btn" @click="saveAlertConfig('ph')">Guardar pH</button>
          </div>

          <div class="alert-config-card">
            <h3>🌡️ Temperatura (°C)</h3>
            <div class="config-group">
              <label>Minimo:</label>
              <input v-model.number="SENSOR_LIMITS.temperature.min" type="number" step="1" />
            </div>
            <div class="config-group">
              <label>Maximo:</label>
              <input v-model.number="SENSOR_LIMITS.temperature.max" type="number" step="1" />
            </div>
            <div class="config-group">
              <label>Maximo seguro:</label>
              <input v-model.number="SENSOR_LIMITS.temperature.safeMax" type="number" step="1" />
            </div>
            <button class="save-config-btn" @click="saveAlertConfig('temperature')">Guardar temperatura</button>
          </div>

          <div class="alert-config-card">
            <h3>⚡ Conductividad (µS/cm)</h3>
            <div class="config-group">
              <label>Minimo:</label>
              <input v-model.number="SENSOR_LIMITS.conductivity.min" type="number" step="10" />
            </div>
            <div class="config-group">
              <label>Maximo:</label>
              <input v-model.number="SENSOR_LIMITS.conductivity.max" type="number" step="10" />
            </div>
            <div class="config-group">
              <label>Maximo seguro:</label>
              <input v-model.number="SENSOR_LIMITS.conductivity.safeMax" type="number" step="10" />
            </div>
            <button class="save-config-btn" @click="saveAlertConfig('conductivity')">Guardar conductividad</button>
          </div>
        </div>
      </section>
    </main>
  </div>

  <div v-else-if="currentView === 'admin-users'" class="dashboard">
    <header class="dashboard-header">
      <div class="header-content">
        <button class="back-btn" @click="goToDashboardView" title="Volver al dashboard">
          <svg viewBox="0 0 24 24" width="24" height="24" fill="currentColor">
            <path d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z"/>
          </svg>
        </button>
        <div>
          <h1 class="header-title">Gestion de usuarios</h1>
          <p class="header-subtitle">Crea cuentas y administra roles en Supabase</p>
        </div>
      </div>
      <div class="header-center admin-top-actions">
        <button class="admin-nav-btn active">Gestion de usuarios</button>
      </div>
      <div class="header-right">
        <div class="data-source-badge" :class="`source-${selectedDevice.dataSource}`">
          <span v-if="selectedDevice.dataSource === 'real'">📊 Datos Reales</span>
          <span v-else-if="selectedDevice.dataSource === 'simulated'">⚙️ Datos Simulados</span>
          <span v-else>❓ Fuente Desconocida</span>
        </div>
        <button class="logout-btn" @click="handleLogout">🚪 Logout</button>
      </div>
    </header>

    <main class="dashboard-content">
      <section class="user-management-section">
        <div class="alerts-header">
          <h2 class="section-title">Administracion de cuentas</h2>
        </div>

        <div class="user-management-content">
          <div class="user-creation-form">
            <h3>Crear nueva cuenta</h3>
            <div class="form-grid">
              <div class="form-group">
                <label>Email:</label>
                <input v-model="newUser.email" type="email" placeholder="usuario@empresa.com" />
              </div>
              <div class="form-group">
                <label>Contrasena:</label>
                <input v-model="newUser.password" type="password" placeholder="********" />
              </div>
              <div class="form-group">
                <label>Nombre completo:</label>
                <input v-model="newUser.fullName" type="text" placeholder="Juan Perez" />
              </div>
              <div class="form-group">
                <label>Rol:</label>
                <select v-model="newUser.role">
                  <option value="employee">Trabajador</option>
                  <option value="admin">Administrador</option>
                </select>
              </div>
            </div>

            <div v-if="userCreationError" class="error-message">
              {{ userCreationError }}
            </div>
            <div v-if="userCreationSuccess" class="success-message">
              {{ userCreationSuccess }}
            </div>

            <button
              class="create-user-btn"
              @click="createNewUser"
              :disabled="isCreatingUser"
            >
              {{ isCreatingUser ? 'Creando...' : 'Crear usuario' }}
            </button>
          </div>

          <div class="users-list">
            <div class="users-list-header">
              <h3>Usuarios existentes</h3>
              <button class="refresh-users-btn" @click="loadExistingUsers" :disabled="isLoadingUsers">
                {{ isLoadingUsers ? '⟳ Cargando...' : '↻ Actualizar' }}
              </button>
            </div>
            <div v-if="isLoadingUsers" class="loading-users">
              Cargando usuarios...
            </div>
            <div v-else-if="existingUsers.length > 0" class="users-table">
              <table>
                <thead>
                  <tr>
                    <th>Email</th>
                    <th>Nombre</th>
                    <th>Rol</th>
                    <th>Creado</th>
                    <th>Acciones</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="user in existingUsers" :key="user.id">
                    <td>{{ user.email }}</td>
                    <td>{{ user.full_name || 'N/A' }}</td>
                    <td>
                      <span class="role-badge" :class="`role-${user.role}`">
                        {{ user.role === 'admin' ? 'Admin' : 'Trabajador' }}
                      </span>
                    </td>
                    <td>{{ formatDate(user.created_at) }}</td>
                    <td>
                      <button class="delete-user-btn" @click="deleteUser(user.id)">Eliminar</button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
            <div v-else class="no-users">
              No hay usuarios registrados aun.
            </div>
          </div>
        </div>
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
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import DeviceList from './DeviceList.vue'
import SensorCard from './SensorCard.vue'
import { checkAndSendAlerts } from '../services/AlertService.js'
import { fetchDashboardData, fetchSensorHistory } from '../services/ArduinoConfig.js'
import { createUserInSupabase, getAllUsers, deleteUserFromSupabase, saveAlertLimits, getAlertLimitsByAdmin, getCurrentUser } from '../services/SupabaseAuthService.js'

const router = useRouter()
const API_BASE_URL = (import.meta.env.VITE_API_URL || '').replace(/\/$/, '')

// Flags para modo simulado
const IS_SIMULATED_MODE = import.meta.env.VITE_DATA_MODE === 'simulated' || false
const DATA_MODE = import.meta.env.VITE_DATA_MODE || 'real'

const ALERT_TABLE_LIMIT = 5

let SENSOR_LIMITS = ref({
  ph: { min: 6.0, max: 8.5, safeMax: 8.0 },
  temperature: { min: 5, max: 35, safeMax: 28 },
  conductivity: { min: 100, max: 2000, safeMax: 1500 }
})

const currentView = ref('devices')
const selectedDeviceId = ref(null)
const lastSync = ref('Sin datos del Arduino')
const showAllTodayAlerts = ref(false)

// Detectar si es admin
const isAdmin = computed(() => {
  const userRole = localStorage.getItem('userRole')
  return userRole === 'admin'
})

// Estado de creación de usuario
const newUser = ref({
  email: '',
  password: '',
  fullName: '',
  role: 'employee'
})
const isCreatingUser = ref(false)
const userCreationError = ref('')
const userCreationSuccess = ref('')
const existingUsers = ref([])
const isLoadingUsers = ref(false)

const devices = ref([
  {
    id: 1,
    name: 'ESP8266 Embalse',
    model: 'ESP8266 - Lectura en tiempo real',
    status: 'disconnected',
    lastUpdate: 'Sin datos',
    battery: 100,
    sensors: { ph: 0, temperature: 0, conductivity: 0 },
    dataSource: IS_SIMULATED_MODE ? 'simulated' : 'real'
  }
])

const selectedDevice = computed(() => {
  return devices.value.find((device) => device.id === selectedDeviceId.value) || {
    id: null,
    name: 'Sin dispositivo',
    model: 'Selecciona un dispositivo para comenzar',
    status: 'disconnected',
    sensors: { ph: 0, temperature: 0, conductivity: 0 }
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
const lastProcessedAlertTimestamp = ref(0)

const requestMonitor = ref({
  dashboard: {
    attempts: 0,
    ok: 0,
    error: 0,
    lastStatus: 'sin solicitudes',
    lastSuccessAt: 'sin datos'
  },
  history: {
    attempts: 0,
    ok: 0,
    error: 0,
    lastStatus: 'sin solicitudes',
    lastSuccessAt: 'sin datos'
  },
  ui: {
    lastRenderedAt: 'sin render',
    lastError: 'sin errores'
  }
})

const getStatus = (value, min, max) => {
  const percentage = ((value - min) / (max - min)) * 100
  if (percentage < 15 || percentage > 85) return 'danger'
  if (percentage < 35 || percentage > 65) return 'warning'
  return 'safe'
}

const overallStatus = computed(() => {
  const statuses = [
    getStatus(sensors.value.ph.value, SENSOR_LIMITS.value.ph.min, SENSOR_LIMITS.value.ph.max),
    getStatus(sensors.value.temperature.value, SENSOR_LIMITS.value.temperature.min, SENSOR_LIMITS.value.temperature.max),
    getStatus(sensors.value.conductivity.value, SENSOR_LIMITS.value.conductivity.min, SENSOR_LIMITS.value.conductivity.max)
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
  if (!date) return 'N/A'
  const d = typeof date === 'string' ? new Date(date) : date
  const day = String(d.getDate()).padStart(2, '0')
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const year = d.getFullYear()
  return `${day}-${month}-${year}`
}

const formatTime = (date) => {
  const hour = String(date.getHours()).padStart(2, '0')
  const minute = String(date.getMinutes()).padStart(2, '0')
  const second = String(date.getSeconds()).padStart(2, '0')
  return `${hour}:${minute}:${second}`
}

const formatDateTime = (date) => {
  return `${formatDate(date)} ${formatTime(date)}`
}

const createRecord = ({ ph, temperature, conductivity, timestamp }) => {
  const now = timestamp ? new Date(timestamp) : new Date()
  const safePh = Number(Number(ph).toFixed(2))
  const safeTemperature = Number(Number(temperature).toFixed(2))
  const safeConductivity = Number(Number(conductivity).toFixed(2))
  const isAlert =
    safePh < SENSOR_LIMITS.value.ph.min || safePh > SENSOR_LIMITS.value.ph.max ||
    safeTemperature < SENSOR_LIMITS.value.temperature.min || safeTemperature > SENSOR_LIMITS.value.temperature.max ||
    safeConductivity < SENSOR_LIMITS.value.conductivity.min || safeConductivity > SENSOR_LIMITS.value.conductivity.max

  return {
    id: `real-${now.getTime()}-${Math.random().toString(16).slice(2, 8)}`,
    deviceId: 1,
    deviceName: devices.value[0].name,
    ph: safePh,
    temperature: safeTemperature,
    conductivity: safeConductivity,
    battery: devices.value[0].battery,
    date: formatDate(now),
    time: formatTime(now),
    timestamp: now.getTime(),
    telegramStatus: IS_SIMULATED_MODE ? 'deshabilitado (simulado)' : (isAlert ? 'pendiente' : 'sin alerta'),
    emailStatus: IS_SIMULATED_MODE ? 'deshabilitado (simulado)' : (isAlert ? 'pendiente' : 'sin alerta'),
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

const formatLastSync = (value) => {
  if (!value) return 'Sin datos del Arduino'
  const diff = Math.max(0, Math.floor((Date.now() - new Date(value).getTime()) / 1000))
  if (diff < 60) return `hace ${diff}s`
  return `hace ${Math.floor(diff / 60)}m`
}

const loadHistoryFromApi = async () => {
  requestMonitor.value.history.attempts += 1
  const rows = await fetchSensorHistory(300)
  if (!Array.isArray(rows)) {
    requestMonitor.value.history.error += 1
    requestMonitor.value.history.lastStatus = 'error'
    requestMonitor.value.ui.lastError = 'Fallo GET /api/sensors/history'
    return
  }

  requestMonitor.value.history.ok += 1
  requestMonitor.value.history.lastStatus = IS_SIMULATED_MODE ? `simulated (${rows.length} filas)` : `ok (${rows.length} filas)`
  requestMonitor.value.history.lastSuccessAt = formatDateTime(new Date())

  historyRecords.value = rows.map((item) =>
    createRecord({
      ph: item.ph,
      temperature: item.temperature,
      conductivity: item.conductivity,
      timestamp: item.timestamp
    })
  )
}

const loadDashboardFromApi = async () => {
  requestMonitor.value.dashboard.attempts += 1
  const dashboard = await fetchDashboardData()
  console.log('[DEBUG] Respuesta de /api/dashboard:', dashboard)
  if (!dashboard) {
    requestMonitor.value.dashboard.error += 1
    requestMonitor.value.dashboard.lastStatus = 'error'
    requestMonitor.value.ui.lastError = 'Fallo GET /api/dashboard'
    devices.value[0] = {
      ...devices.value[0],
      status: 'disconnected',
      lastUpdate: 'Sin datos',
      sensors: { ph: 0, temperature: 0, conductivity: 0 },
      dataSource: 'unknown'
    }
    lastSync.value = 'Sin datos del Arduino'
    return
  }

  requestMonitor.value.dashboard.ok += 1
  requestMonitor.value.dashboard.lastStatus = IS_SIMULATED_MODE ? 'simulated' : 'ok'
  requestMonitor.value.dashboard.lastSuccessAt = formatDateTime(new Date())

  let dataSource = IS_SIMULATED_MODE ? 'simulated' : 'real'
  if (!IS_SIMULATED_MODE) {
    try {
      const diagResponse = await fetch(`${API_BASE_URL}/api/diagnostics`)
      if (diagResponse.ok) {
        const diag = await diagResponse.json()
        dataSource = diag.data_source || 'real'
      }
    } catch (e) {
      console.log('No se pudo obtener datos de diagnóstico:', e)
    }
  }

  devices.value[0] = {
    ...devices.value[0],
    status: dashboard.metadata.arduinoConnected ? 'connected' : 'disconnected',
    lastUpdate: formatLastSync(dashboard.ph.lastUpdated),
    sensors: {
      ph: Number(dashboard.ph.value),
      temperature: Number(dashboard.temperature.value),
      conductivity: Number(dashboard.conductivity.value)
    },
    dataSource: dataSource
  }
  lastSync.value = formatLastSync(dashboard.metadata.lastSync)
}

const selectDevice = (device) => {
  selectedDeviceId.value = device.id
  currentView.value = 'dashboard'
  showAllTodayAlerts.value = false
}

const openHistory = () => {
  router.push('/historical')
}

const openAlertConfigView = () => {
  if (!isAdmin.value) return
  currentView.value = 'admin-alerts'
}

const openUserManagementView = async () => {
  if (!isAdmin.value) return
  currentView.value = 'admin-users'
  await loadExistingUsers()
}

const goToDashboardView = () => {
  currentView.value = 'dashboard'
}

const goBack = () => {
  currentView.value = 'devices'
}

const handleLogout = () => {
  localStorage.removeItem('isAuthenticated')
  localStorage.removeItem('userEmail')
  localStorage.removeItem('userRole')
  router.push('/login')
}

const saveAlertConfig = async (sensorType) => {
  try {
    isCreatingUser.value = true
    
    // Obtener usuario actual
    const currentUser = await getCurrentUser()
    if (!currentUser || currentUser.role !== 'admin') {
      alert('Debes ser administrador para guardar configuraciones de alertas')
      return
    }

    // Guardar en localStorage
    const config = { ...SENSOR_LIMITS.value }
    localStorage.setItem('sensorLimits', JSON.stringify(config))

    // Guardar en Supabase
    const sensorLimits = SENSOR_LIMITS.value[sensorType]
    const result = await saveAlertLimits(
      currentUser.id,
      sensorType,
      sensorLimits.min,
      sensorLimits.max,
      sensorLimits.safeMax
    )

    if (result.success) {
      alert(`✅ Límites de ${sensorType} guardados exitosamente en Supabase`)
    } else {
      alert(`⚠️ Error al guardar en Supabase: ${result.error}. Los datos se guardaron localmente.`)
    }
  } catch (error) {
    console.error('Error en saveAlertConfig:', error)
    alert(`Error: ${error.message}`)
  } finally {
    isCreatingUser.value = false
  }
}

const createNewUser = async () => {
  const sanitizedEmail = String(newUser.value.email || '').trim().toLowerCase()
  const sanitizedFullName = String(newUser.value.fullName || '').trim()

  // Validar campos
  if (!sanitizedEmail || !newUser.value.password || !sanitizedFullName) {
    userCreationError.value = 'Por favor completa todos los campos'
    userCreationSuccess.value = ''
    return
  }

  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/
  if (!emailRegex.test(sanitizedEmail)) {
    userCreationError.value = 'Correo invalido. Usa formato nombre@dominio.com sin espacios.'
    userCreationSuccess.value = ''
    return
  }

  newUser.value.email = sanitizedEmail
  newUser.value.fullName = sanitizedFullName

  isCreatingUser.value = true
  userCreationError.value = ''
  userCreationSuccess.value = ''

  try {
    const result = await createUserInSupabase(
      newUser.value.email,
      newUser.value.password,
      newUser.value.fullName,
      newUser.value.role
    )

    if (result.success) {
      userCreationSuccess.value = `Usuario ${sanitizedEmail} creado exitosamente`
      newUser.value = {
        email: '',
        password: '',
        fullName: '',
        role: 'employee'
      }
      
      // Esperar más tiempo para que el trigger sincronice el usuario a users_roles
      console.log('[createNewUser] ✅ Usuario creado, esperando sincronización (3 segundos)...')
      await new Promise(resolve => setTimeout(resolve, 3000))
      
      // Recargar lista de usuarios
      console.log('[createNewUser] Recargando lista de usuarios...')
      await loadExistingUsers()
      console.log('[createNewUser] ✅ Lista de usuarios refrescada')
    } else {
      userCreationError.value = result.error || 'Error al crear usuario'
      console.error('[createNewUser] ❌ Error:', result.error)
    }
  } catch (error) {
    userCreationError.value = `Error: ${error.message}`
  } finally {
    isCreatingUser.value = false
  }
}

const loadExistingUsers = async () => {
  isLoadingUsers.value = true
  console.log('[loadExistingUsers] Iniciando carga...')
  try {
    const users = await getAllUsers()
    console.log('[loadExistingUsers] Respuesta de getAllUsers:', users)
    console.log('[loadExistingUsers] Cantidad de usuarios:', users?.length || 0)
    
    // Solo actualizar si realmente hay datos
    if (users && Array.isArray(users)) {
      existingUsers.value = users
      console.log('[loadExistingUsers] ✅ Usuarios actualizados exitosamente')
    } else {
      console.warn('[loadExistingUsers] ⚠️ Respuesta inválida, manteniendo lista anterior')
    }
  } catch (error) {
    console.error('[loadExistingUsers] ❌ Error al cargar usuarios:', error)
    console.error('[loadExistingUsers] Stack:', error.stack)
    // NO limpiar la lista en caso de error, mantener lo que había
  } finally {
    isLoadingUsers.value = false
  }
}

const deleteUser = async (userId) => {
  if (!confirm('¿Estás seguro de que quieres eliminar este usuario?')) {
    return
  }

  try {
    const result = await deleteUserFromSupabase(userId)
    if (result.success) {
      await loadExistingUsers()
    }
  } catch (error) {
    console.error('Error al eliminar usuario:', error)
  }
}

let updateInterval = null

const updateSensorData = async () => {
  if (!selectedDeviceId.value) return

  await loadDashboardFromApi()

  if (currentView.value === 'dashboard' || currentView.value === 'history') {
    await loadHistoryFromApi()
  }

  requestMonitor.value.ui.lastRenderedAt = formatDateTime(new Date())

  if (currentView.value !== 'dashboard') return
  if (IS_SIMULATED_MODE) return

  const latestRecord = historyRecords.value[0]
  if (!latestRecord || !latestRecord.isAlert) return

  if (latestRecord.timestamp > lastProcessedAlertTimestamp.value) {
    await checkAndSendAlerts(devices.value[0], SENSOR_LIMITS.value)
    lastProcessedAlertTimestamp.value = latestRecord.timestamp
  }
}

const startSensorUpdates = () => {
  if (updateInterval) clearInterval(updateInterval)
  updateSensorData()
  updateInterval = setInterval(updateSensorData, 2000)
}

const stopSensorUpdates = () => {
  if (updateInterval) {
    clearInterval(updateInterval)
    updateInterval = null
  }
}

onMounted(async () => {
  // Verificar autenticación
  const isAuthenticated = localStorage.getItem('isAuthenticated')
  if (!isAuthenticated) {
    router.push('/login')
    return
  }

  selectedDeviceId.value = 1
  console.log('[FRONTEND] VITE_DATA_MODE:', DATA_MODE)
  startSensorUpdates()

  // Cargar lista de usuarios si es admin
  if (isAdmin.value) {
    await loadExistingUsers()
    
    // Cargar límites de alertas desde Supabase si es admin
    try {
      const currentUser = await getCurrentUser()
      if (currentUser) {
        const alertLimits = await getAlertLimitsByAdmin(currentUser.id)
        if (alertLimits && alertLimits.length > 0) {
          // Actualizar SENSOR_LIMITS con los valores de Supabase
          alertLimits.forEach(limit => {
            if (SENSOR_LIMITS.value[limit.sensor_type]) {
              SENSOR_LIMITS.value[limit.sensor_type].min = limit.min_value
              SENSOR_LIMITS.value[limit.sensor_type].max = limit.max_value
              SENSOR_LIMITS.value[limit.sensor_type].safeMax = limit.safe_max
            }
          })
          console.log('✅ Límites de alerta cargados desde Supabase:', SENSOR_LIMITS.value)
        } else {
          // Si no hay límites en Supabase, cargar del localStorage
          const savedLimits = localStorage.getItem('sensorLimits')
          if (savedLimits) {
            SENSOR_LIMITS.value = JSON.parse(savedLimits)
          }
        }
      }
    } catch (error) {
      console.error('Error al cargar límites de Supabase:', error)
      // Fallback a localStorage
      const savedLimits = localStorage.getItem('sensorLimits')
      if (savedLimits) {
        SENSOR_LIMITS.value = JSON.parse(savedLimits)
      }
    }
  } else {
    // Para usuarios normales, cargar del localStorage
    const savedLimits = localStorage.getItem('sensorLimits')
    if (savedLimits) {
      try {
        SENSOR_LIMITS.value = JSON.parse(savedLimits)
      } catch (e) {
        console.error('Error al cargar límites guardados:', e)
      }
    }
  }
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
  gap: 20px;
}

.header-content {
  display: flex;
  align-items: center;
  gap: 16px;
  flex: 1;
}

.header-center {
  display: flex;
  justify-content: center;
  flex: 1;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
  justify-content: flex-end;
}

.admin-top-actions {
  gap: 10px;
  flex-wrap: wrap;
}

.admin-nav-btn {
  border: 1px solid #ff9800;
  background: #ffffff;
  color: #a85c00;
  border-radius: 8px;
  padding: 10px 14px;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s ease;
}

.admin-nav-btn:hover {
  background: #fff3e0;
}

.admin-nav-btn.active {
  background: #ff9800;
  color: #ffffff;
  border-color: #ff9800;
}

.history-btn {
  background: #66bb6a;
  color: white;
  border: none;
  padding: 10px 16px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
  transition: all 0.3s;
}

.history-btn:hover {
  background: #5aa859;
  box-shadow: 0 2px 8px rgba(102, 187, 106, 0.3);
}

.logout-btn {
  background: #ff6b6b;
  color: white;
  border: none;
  padding: 10px 16px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
  transition: all 0.3s;
}

.logout-btn:hover {
  background: #ff5252;
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

.data-source-badge {
  padding: 8px 16px;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 6px;
  white-space: nowrap;
}

.source-real {
  background-color: #d4edda;
  color: #155724;
  border: 1px solid #c3e6cb;
}

.source-simulated {
  background-color: #fff3cd;
  color: #856404;
  border: 1px solid #ffeaa7;
}

.source-unknown {
  background-color: #e2e3e5;
  color: #383d41;
  border: 1px solid #d6d8db;
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
  margin-bottom: 60px;
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

.info-card-value.admin-role {
  color: #d32f2f;
  background: #ffebee;
  padding: 4px 8px;
  border-radius: 4px;
}

.info-card-value.user-role {
  color: #1976d2;
  background: #e3f2fd;
  padding: 4px 8px;
  border-radius: 4px;
}

/* Admin Sections */
.admin-section {
  background: #fff8f8;
  border: 2px solid #ffcdd2;
  margin-top: 28px;
}

.alerts-config-section,
.user-management-section {
  background: #ffffff;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  border: 2px solid #ff9800;
  margin-top: 28px;
}

.alerts-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14px;
}

.collapse-btn {
  background: #ff9800;
  color: white;
  border: none;
  padding: 8px 12px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
  transition: all 0.3s;
}

.collapse-btn:hover {
  background: #f57c00;
}

.alerts-count {
  font-size: 12px;
  color: #6b7280;
  font-weight: 600;
}

.alerts-config-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 20px;
  margin-top: 20px;
}

.alert-config-card {
  background: #f5f5f5;
  padding: 20px;
  border-radius: 8px;
  border-left: 4px solid #ff9800;
}

.alert-config-card h3 {
  margin-top: 0;
  color: #333;
  margin-bottom: 16px;
}

.config-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 12px;
}

.config-group label {
  font-size: 13px;
  font-weight: 600;
  color: #555;
}

.config-group input {
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 13px;
}

.config-group input:focus {
  outline: none;
  border-color: #ff9800;
  box-shadow: 0 0 0 3px rgba(255, 152, 0, 0.1);
}

.save-config-btn {
  background: #4caf50;
  color: white;
  border: none;
  padding: 10px;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
  font-size: 13px;
  margin-top: 12px;
  transition: all 0.3s;
}

.save-config-btn:hover {
  background: #45a049;
}

.user-management-content {
  margin-top: 20px;
}

.user-creation-form {
  background: #f5f5f5;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 30px;
}

.user-creation-form h3 {
  margin-top: 0;
  color: #333;
  margin-bottom: 16px;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 16px;
  margin-bottom: 16px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-group label {
  font-size: 13px;
  font-weight: 600;
  color: #555;
}

.form-group input,
.form-group select {
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 13px;
}

.form-group input:focus,
.form-group select:focus {
  outline: none;
  border-color: #ff9800;
  box-shadow: 0 0 0 3px rgba(255, 152, 0, 0.1);
}

.error-message {
  background: #ffebee;
  color: #c62828;
  padding: 12px;
  border-radius: 4px;
  margin-bottom: 12px;
  font-size: 13px;
  border-left: 4px solid #c62828;
}

.success-message {
  background: #e8f5e9;
  color: #2e7d32;
  padding: 12px;
  border-radius: 4px;
  margin-bottom: 12px;
  font-size: 13px;
  border-left: 4px solid #2e7d32;
}

.create-user-btn {
  background: #2196f3;
  color: white;
  border: none;
  padding: 12px 20px;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
  font-size: 14px;
  transition: all 0.3s;
}

.create-user-btn:hover:not(:disabled) {
  background: #1976d2;
}

.create-user-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.users-list {
  margin-top: 30px;
}

.users-list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.users-list-header h3 {
  color: #333;
  margin: 0;
}

.refresh-users-btn {
  padding: 6px 12px;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
  font-size: 12px;
  transition: background 0.3s;
}

.refresh-users-btn:hover:not(:disabled) {
  background: #5568d3;
}

.refresh-users-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.loading-users {
  text-align: center;
  padding: 20px;
  color: #666;
  font-style: italic;
}

.users-table {
  overflow-x: auto;
}

.users-table table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.users-table th,
.users-table td {
  border: 1px solid #e5e7eb;
  padding: 10px;
  text-align: left;
}

.users-table th {
  background: #f9fafb;
  color: #374151;
  font-weight: 600;
}

.role-badge {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
}

.role-admin {
  background: #ffebee;
  color: #c62828;
}

.role-employee {
  background: #e3f2fd;
  color: #1976d2;
}

.delete-user-btn {
  background: #ff9800;
  color: white;
  border: none;
  padding: 6px 12px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  font-weight: 600;
  transition: all 0.3s;
}

.delete-user-btn:hover {
  background: #f57c00;
}

.no-users {
  text-align: center;
  color: #999;
  padding: 20px;
  font-size: 13px;
}

.diagnostics-section,
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

.table-wrap {
  overflow: auto;
  transition: max-height 0.3s ease;
}

.alerts-section:has(.see-more-btn:disabled) .table-wrap,
.table-wrap:not(:has(~ .table-footer .see-more-btn:not(:disabled))) {
  max-height: none;
}

/* Cuando mostrar menos está activo (todas las alertas visibles) */
.table-wrapper.expanded .table-wrap {
  max-height: 400px;
  overflow-y: auto;
  overflow-x: auto;
}

.table-wrapper {
  position: relative;
}

.table-footer {
  display: flex;
  justify-content: flex-end;
  padding-top: 12px;
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
  margin-top: 0;
  border: 1px solid #66bb6a;
  background: #ffffff;
  color: #2e7d32;
  border-radius: 8px;
  padding: 8px 14px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.see-more-btn:hover,
.pdf-btn:hover {
  background: #e8f5e9;
  transform: translateY(-1px);
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
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

.diagnostics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 12px;
}

.diagnostic-card {
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  padding: 12px;
  background: #f9fafb;
}

.diagnostic-title {
  font-size: 13px;
  font-weight: 700;
  color: #1f2937;
  margin-bottom: 10px;
}

.diagnostic-row {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  font-size: 12px;
  color: #4b5563;
  margin-top: 6px;
}

.diagnostic-row strong {
  color: #111827;
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

  .pdf-btn {
    width: 100%;
  }

  .header-center {
    width: 100%;
    justify-content: flex-start;
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

  .admin-top-actions {
    width: 100%;
  }

  .admin-nav-btn {
    flex: 1;
    min-width: 0;
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
  .charts-section,
  .diagnostics-section,
  .alerts-config-section,
  .user-management-section {
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
