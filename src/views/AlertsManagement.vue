<template>
  <div class="alerts-management-container">
    <!-- Header -->
    <header class="management-header">
      <div class="header-left">
        <button class="back-btn" @click="goBack">← Volver</button>
        <h1>⚙️ Gestión de Alertas</h1>
      </div>
      <div class="header-right">
        <button class="logout-btn" @click="handleLogout">
          Cerrar Sesión
        </button>
      </div>
    </header>

    <!-- Main Content -->
    <main class="management-content">
      <!-- Alert Limits Configuration -->
      <section class="alert-section">
        <h2>Configurar Límites de Alerta</h2>
        
        <div class="alert-grid">
          <!-- pH Alert -->
          <div class="alert-card">
            <div class="alert-header">
              <h3>pH</h3>
              <span class="unit">pH</span>
            </div>
            <div class="form-group">
              <label>Mínimo Permitido</label>
              <input 
                v-model.number="alerts.ph.min" 
                type="number" 
                step="0.1"
                min="0"
                max="14"
              />
            </div>
            <div class="form-group">
              <label>Máximo Permitido</label>
              <input 
                v-model.number="alerts.ph.max" 
                type="number" 
                step="0.1"
                min="0"
                max="14"
              />
            </div>
            <button class="save-btn" @click="saveAlertConfig('ph')">Guardar</button>
          </div>

          <!-- Temperature Alert -->
          <div class="alert-card">
            <div class="alert-header">
              <h3>Temperatura</h3>
              <span class="unit">°C</span>
            </div>
            <div class="form-group">
              <label>Mínimo Permitido</label>
              <input 
                v-model.number="alerts.temperature.min" 
                type="number" 
                step="0.1"
              />
            </div>
            <div class="form-group">
              <label>Máximo Permitido</label>
              <input 
                v-model.number="alerts.temperature.max" 
                type="number" 
                step="0.1"
              />
            </div>
            <button class="save-btn" @click="saveAlertConfig('temperature')">Guardar</button>
          </div>

          <!-- Conductivity Alert -->
          <div class="alert-card">
            <div class="alert-header">
              <h3>Conductividad</h3>
              <span class="unit">µS/cm</span>
            </div>
            <div class="form-group">
              <label>Mínimo Permitido</label>
              <input 
                v-model.number="alerts.conductivity.min" 
                type="number" 
                step="1"
              />
            </div>
            <div class="form-group">
              <label>Máximo Permitido</label>
              <input 
                v-model.number="alerts.conductivity.max" 
                type="number" 
                step="1"
              />
            </div>
            <button class="save-btn" @click="saveAlertConfig('conductivity')">Guardar</button>
          </div>
        </div>
      </section>

      <!-- Recent Alerts -->
      <section class="recent-alerts-section">
        <h2>Alertas Recientes</h2>
        <div v-if="recentAlerts.length > 0" class="alerts-list">
          <div v-for="alert in recentAlerts" :key="alert.id" class="alert-item" :class="`severity-${alert.severity}`">
            <div class="alert-time">{{ formatTime(alert.timestamp) }}</div>
            <div class="alert-message">{{ alert.message }}</div>
            <div class="alert-severity">{{ alert.severity.toUpperCase() }}</div>
          </div>
        </div>
        <div v-else class="no-alerts">
          No hay alertas recientes
        </div>
      </section>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { clearSession, stopSessionIdleWatcher, isAdminRole } from '../services/sessionAuth.js'

const router = useRouter()

const alerts = ref({
  ph: { min: 6.5, max: 8.5 },
  temperature: { min: 5, max: 30 },
  conductivity: { min: 100, max: 1000 }
})

const recentAlerts = ref([
  {
    id: 1,
    timestamp: new Date(Date.now() - 3600000),
    message: 'pH fuera de rango: 5.2 (mínimo: 6.5)',
    severity: 'high'
  },
  {
    id: 2,
    timestamp: new Date(Date.now() - 7200000),
    message: 'Temperatura elevada: 32°C (máximo: 30°C)',
    severity: 'medium'
  },
  {
    id: 3,
    timestamp: new Date(Date.now() - 10800000),
    message: 'Conductividad dentro de rango normal',
    severity: 'low'
  }
])

onMounted(() => {
  const isAuthenticated = localStorage.getItem('isAuthenticated')
  const userRole = localStorage.getItem('userRole')

  if (!isAuthenticated || !isAdminRole(userRole)) {
    router.push('/dashboard')
  }

  // Cargar configuración actual (simulado)
  const savedAlerts = localStorage.getItem('alertLimits')
  if (savedAlerts) {
    alerts.value = JSON.parse(savedAlerts)
  }
})

const saveAlertConfig = (sensorType) => {
  // Guardar en localStorage
  localStorage.setItem('alertLimits', JSON.stringify(alerts.value))
  
  // Mostrar confirmación
  alert(`Límites de ${sensorType} guardados exitosamente`)
}

const formatTime = (date) => {
  const now = new Date()
  const diff = now - date
  const hours = Math.floor(diff / 3600000)
  const minutes = Math.floor((diff % 3600000) / 60000)
  
  if (hours > 0) {
    return `Hace ${hours}h ${minutes}m`
  } else if (minutes > 0) {
    return `Hace ${minutes}m`
  } else {
    return 'Hace poco'
  }
}

const goBack = () => {
  router.push('/dashboard')
}

const handleLogout = () => {
  stopSessionIdleWatcher()
  clearSession()
  router.push('/login')
}
</script>

<style scoped>
.alerts-management-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  flex-direction: column;
}

.management-header {
  background: rgba(0, 0, 0, 0.1);
  padding: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: white;
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(10px);
}

.header-left,
.header-right {
  display: flex;
  align-items: center;
  gap: 20px;
}

.header-left h1 {
  margin: 0;
  font-size: 28px;
}

.back-btn,
.logout-btn {
  background: rgba(255, 255, 255, 0.2);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.3);
  padding: 10px 20px;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s;
}

.back-btn:hover,
.logout-btn:hover {
  background: rgba(255, 255, 255, 0.3);
  border-color: rgba(255, 255, 255, 0.5);
}

.management-content {
  flex: 1;
  padding: 30px;
  overflow-y: auto;
}

.alert-section,
.recent-alerts-section {
  background: white;
  border-radius: 12px;
  padding: 30px;
  margin-bottom: 30px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
}

.alert-section h2,
.recent-alerts-section h2 {
  margin-top: 0;
  color: #333;
  margin-bottom: 25px;
}

.alert-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
}

.alert-card {
  background: #f9f9f9;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 20px;
  transition: all 0.3s;
}

.alert-card:hover {
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
}

.alert-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 2px solid #667eea;
}

.alert-header h3 {
  margin: 0;
  color: #333;
}

.unit {
  background: #667eea;
  color: white;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
}

.form-group {
  margin-bottom: 15px;
}

.form-group label {
  display: block;
  font-weight: 600;
  color: #555;
  margin-bottom: 5px;
  font-size: 13px;
}

.form-group input {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  transition: border-color 0.3s;
  box-sizing: border-box;
}

.form-group input:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.save-btn {
  width: 100%;
  padding: 10px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 6px;
  font-weight: 600;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s;
  margin-top: 10px;
}

.save-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(102, 126, 234, 0.3);
}

.alerts-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.alert-item {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 15px;
  background: #f9f9f9;
  border-left: 4px solid #999;
  border-radius: 6px;
  transition: all 0.3s;
}

.alert-item:hover {
  box-shadow: 0 3px 10px rgba(0, 0, 0, 0.1);
}

.alert-item.severity-high {
  border-left-color: #ff6b6b;
  background: #ffe0e0;
}

.alert-item.severity-medium {
  border-left-color: #ffa500;
  background: #fff3e0;
}

.alert-item.severity-low {
  border-left-color: #4caf50;
  background: #e8f5e9;
}

.alert-time {
  font-size: 12px;
  color: #999;
  min-width: 80px;
  font-weight: 600;
}

.alert-message {
  flex: 1;
  color: #333;
  font-size: 14px;
}

.alert-severity {
  font-size: 11px;
  font-weight: 700;
  padding: 4px 8px;
  border-radius: 4px;
  background: rgba(0, 0, 0, 0.1);
  color: #333;
}

.no-alerts {
  text-align: center;
  padding: 40px 20px;
  color: #999;
  font-size: 14px;
}

@media (max-width: 768px) {
  .management-header {
    flex-direction: column;
    gap: 15px;
  }

  .header-left,
  .header-right {
    width: 100%;
    justify-content: space-between;
  }

  .management-content {
    padding: 15px;
  }

  .alert-grid {
    grid-template-columns: 1fr;
  }

  .alert-item {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
