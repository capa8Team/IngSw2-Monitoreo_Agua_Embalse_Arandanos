<template>
  <div class="dashboard-container">
    <!-- Header -->
    <header class="dashboard-header">
      <div class="header-left">
        <h1>🌊 Dashboard - Monitoreo Embalse</h1>
      </div>
      <div class="header-right">
        <button 
          v-if="isAdmin" 
          class="admin-btn"
          @click="goToAlerts"
        >
          ⚙️ Modificar Alertas
        </button>
        <button class="logout-btn" @click="handleLogout">
          Cerrar Sesión
        </button>
      </div>
    </header>

    <!-- Main Content -->
    <main class="dashboard-content">
      <!-- Welcome Message -->
      <div class="welcome-section">
        <h2>Bienvenido{{ isAdmin ? ' Administrador' : '' }}</h2>
        <p v-if="isAdmin">Tienes acceso a funciones de administración</p>
        <p v-else>Visualiza los datos de los sensores en tiempo real</p>
      </div>

      <!-- Sensores Grid -->
      <section class="sensors-section">
        <h3>Lecturas en Tiempo Real</h3>
        <div class="sensors-grid">
          <!-- pH Sensor -->
          <div class="sensor-card">
            <div class="sensor-header">
              <h4>pH</h4>
              <span class="sensor-unit">pH</span>
            </div>
            <div class="sensor-value">{{ sensorData.ph }}</div>
            <div class="sensor-status" :class="`status-${sensorStatus.ph}`">
              {{ sensorStatus.phText }}
            </div>
          </div>

          <!-- Temperature Sensor -->
          <div class="sensor-card">
            <div class="sensor-header">
              <h4>Temperatura</h4>
              <span class="sensor-unit">°C</span>
            </div>
            <div class="sensor-value">{{ sensorData.temperature }}</div>
            <div class="sensor-status" :class="`status-${sensorStatus.temp}`">
              {{ sensorStatus.tempText }}
            </div>
          </div>

          <!-- Conductivity Sensor -->
          <div class="sensor-card">
            <div class="sensor-header">
              <h4>Conductividad</h4>
              <span class="sensor-unit">µS/cm</span>
            </div>
            <div class="sensor-value">{{ sensorData.conductivity }}</div>
            <div class="sensor-status" :class="`status-${sensorStatus.cond}`">
              {{ sensorStatus.condText }}
            </div>
          </div>
        </div>
      </section>

      <!-- Admin Section -->
      <section v-if="isAdmin" class="admin-section">
        <h3>Panel Administrativo</h3>
        <div class="admin-grid">
          <div class="admin-card">
            <h4>Usuarios</h4>
            <p class="admin-stat">5 activos</p>
          </div>
          <div class="admin-card">
            <h4>Dispositivos</h4>
            <p class="admin-stat">3 conectados</p>
          </div>
          <div class="admin-card">
            <h4>Alertas Activas</h4>
            <p class="admin-stat">2 pendientes</p>
          </div>
        </div>
      </section>

      <!-- User Section -->
      <section v-else class="user-section">
        <h3>Información del Dispositivo</h3>
        <div class="device-info">
          <p><strong>Dispositivo:</strong> ESP8266 Embalse</p>
          <p><strong>Último sincronización:</strong> Hace 2 minutos</p>
          <p><strong>Estado:</strong> <span class="status-online">● Conectado</span></p>
        </div>
      </section>
    </main>

    <!-- Footer -->
    <footer class="dashboard-footer">
      <p>&copy; 2026 Sistema de Monitoreo Embalse Arándanos</p>
    </footer>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { clearSession, stopSessionIdleWatcher, isAdminRole } from '../services/sessionAuth.js'

const router = useRouter()

// Simular datos de sensores
const sensorData = ref({
  ph: 7.2,
  temperature: 18.5,
  conductivity: 450
})

// Determinar si es admin (por ahora hardcoded, luego desde authStore)
const isAdmin = ref(false)

const sensorStatus = computed(() => {
  return {
    ph: sensorData.value.ph >= 6.5 && sensorData.value.ph <= 8.5 ? 'normal' : 'warning',
    phText: sensorData.value.ph >= 6.5 && sensorData.value.ph <= 8.5 ? 'Normal' : 'Fuera de Rango',
    temp: sensorData.value.temperature >= 15 && sensorData.value.temperature <= 30 ? 'normal' : 'warning',
    tempText: sensorData.value.temperature >= 15 && sensorData.value.temperature <= 30 ? 'Normal' : 'Fuera de Rango',
    cond: sensorData.value.conductivity >= 200 && sensorData.value.conductivity <= 1500 ? 'normal' : 'warning',
    condText: sensorData.value.conductivity >= 200 && sensorData.value.conductivity <= 1500 ? 'Normal' : 'Fuera de Rango',
  }
})

onMounted(() => {
  const userRole = localStorage.getItem('userRole') || ''
  isAdmin.value = isAdminRole(userRole)
})

const handleLogout = () => {
  stopSessionIdleWatcher()
  clearSession()
  router.push('/login')
}

const goToAlerts = () => {
  router.push('/alerts')
}
</script>

<style scoped>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

.dashboard-container {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background: linear-gradient(135deg, #f5f7fa 0%, #e8ecf1 100%);
}

.dashboard-header {
  background: white;
  border-bottom: 2px solid #e0e0e0;
  padding: 20px 40px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.header-left h1 {
  font-size: 28px;
  color: #1f2937;
  font-weight: 700;
}

.header-right {
  display: flex;
  gap: 16px;
}

.admin-btn {
  background: #66bb6a;
  color: white;
  border: none;
  padding: 10px 16px;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
  transition: background 0.3s;
}

.admin-btn:hover {
  background: #2e7d32;
}

.logout-btn {
  background: #f44336;
  color: white;
  border: none;
  padding: 10px 16px;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
  transition: background 0.3s;
}

.logout-btn:hover {
  background: #d32f2f;
}

.dashboard-content {
  flex: 1;
  padding: 40px;
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;
}

.welcome-section {
  margin-bottom: 40px;
}

.welcome-section h2 {
  font-size: 24px;
  color: #1f2937;
  margin-bottom: 8px;
}

.welcome-section p {
  color: #6b7280;
  font-size: 14px;
}

.sensors-section {
  margin-bottom: 40px;
}

.sensors-section h3 {
  font-size: 20px;
  color: #1f2937;
  margin-bottom: 20px;
  font-weight: 600;
}

.sensors-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
}

.sensor-card {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  border: 2px solid #e5e7eb;
  transition: transform 0.3s, box-shadow 0.3s;
}

.sensor-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
}

.sensor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.sensor-header h4 {
  font-size: 16px;
  color: #374151;
  font-weight: 600;
}

.sensor-unit {
  font-size: 12px;
  color: #9ca3af;
  background: #f3f4f6;
  padding: 4px 8px;
  border-radius: 4px;
}

.sensor-value {
  font-size: 36px;
  font-weight: 700;
  color: #2e7d32;
  margin-bottom: 12px;
}

.sensor-status {
  font-size: 13px;
  font-weight: 600;
  padding: 8px 12px;
  border-radius: 6px;
  text-align: center;
}

.status-normal {
  background: #d4edda;
  color: #155724;
  border: 1px solid #c3e6cb;
}

.status-warning {
  background: #fff3cd;
  color: #856404;
  border: 1px solid #ffeaa7;
}

.admin-section,
.user-section {
  margin-top: 40px;
}

.admin-section h3,
.user-section h3 {
  font-size: 20px;
  color: #1f2937;
  margin-bottom: 20px;
  font-weight: 600;
}

.admin-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}

.admin-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  border-left: 4px solid #66bb6a;
}

.admin-card h4 {
  font-size: 14px;
  color: #6b7280;
  font-weight: 600;
  text-transform: uppercase;
  margin-bottom: 8px;
}

.admin-stat {
  font-size: 24px;
  font-weight: 700;
  color: #2e7d32;
}

.device-info {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.device-info p {
  font-size: 14px;
  color: #374151;
  margin-bottom: 12px;
}

.device-info strong {
  font-weight: 600;
  color: #1f2937;
}

.status-online {
  color: #2e7d32;
  font-weight: 600;
}

.dashboard-footer {
  background: white;
  border-top: 1px solid #e5e7eb;
  padding: 20px 40px;
  text-align: center;
  color: #9ca3af;
  font-size: 13px;
  margin-top: auto;
}

@media (max-width: 768px) {
  .dashboard-header {
    flex-direction: column;
    gap: 16px;
    align-items: flex-start;
  }

  .header-right {
    width: 100%;
    justify-content: space-between;
  }

  .dashboard-content {
    padding: 20px;
  }

  .sensors-grid {
    grid-template-columns: 1fr;
  }
}
</style>
