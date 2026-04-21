<template>
  <div class="admin-dashboard">
    <header class="admin-header">
      <div class="header-content">
        <h1>👨‍💼 Panel de Administración</h1>
        <p>Bienvenido, {{ authStore.user?.email }}</p>
      </div>
      <button class="logout-btn" @click="handleLogout">Cerrar Sesión</button>
    </header>

    <nav class="admin-nav">
      <button
        @click="currentView = 'dashboard'"
        :class="{ active: currentView === 'dashboard' }"
        class="nav-btn"
      >
        📊 Dashboard
      </button>
      <button
        @click="currentView = 'users'"
        :class="{ active: currentView === 'users' }"
        class="nav-btn"
      >
        👥 Gestión de Usuarios
      </button>
      <button
        @click="currentView = 'alerts'"
        :class="{ active: currentView === 'alerts' }"
        class="nav-btn"
      >
        🚨 Límites de Alertas
      </button>
    </nav>

    <main class="admin-content">
      <!-- Vista Dashboard -->
      <div v-if="currentView === 'dashboard'" class="dashboard-view">
        <div class="stats-grid">
          <div class="stat-card">
            <h3>Total de Usuarios</h3>
            <p class="stat-number">{{ stats.totalUsers }}</p>
            <p class="stat-label">Usuarios activos en el sistema</p>
          </div>
          <div class="stat-card">
            <h3>Dispositivos Activos</h3>
            <p class="stat-number">{{ stats.activeDevices }}</p>
            <p class="stat-label">Sensores conectados</p>
          </div>
          <div class="stat-card">
            <h3>Alertas Pendientes</h3>
            <p class="stat-number">{{ stats.pendingAlerts }}</p>
            <p class="stat-label">Alertas sin revisar</p>
          </div>
          <div class="stat-card">
            <h3>Lecturas Hoy</h3>
            <p class="stat-number">{{ stats.readingsToday }}</p>
            <p class="stat-label">Mediciones registradas</p>
          </div>
        </div>

        <div class="recent-activity">
          <h2>Actividad Reciente</h2>
          <p>Sección de actividad - próximamente</p>
        </div>
      </div>

      <!-- Vista Usuarios -->
      <AdminUsers v-else-if="currentView === 'users'" />

      <!-- Vista Alertas -->
      <AdminAlerts v-else-if="currentView === 'alerts'" />
    </main>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/authStore'
import AdminUsers from './AdminUsers.vue'
import AdminAlerts from './AdminAlerts.vue'

const router = useRouter()
const authStore = useAuthStore()

const currentView = ref('dashboard')

const stats = ref({
  totalUsers: 24,
  activeDevices: 5,
  pendingAlerts: 3,
  readingsToday: 1240,
})

const handleLogout = async () => {
  await authStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.admin-dashboard {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #f5f7fa;
}

.admin-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-content h1 {
  margin: 0;
  font-size: 28px;
}

.header-content p {
  margin: 4px 0 0 0;
  opacity: 0.9;
}

.logout-btn {
  padding: 10px 20px;
  background: rgba(255, 255, 255, 0.2);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
  transition: background 0.3s;
}

.logout-btn:hover {
  background: rgba(255, 255, 255, 0.3);
}

.admin-nav {
  background: white;
  border-bottom: 1px solid #e0e0e0;
  padding: 0;
  display: flex;
  gap: 0;
}

.nav-btn {
  padding: 16px 20px;
  background: white;
  border: none;
  color: #666;
  font-weight: 600;
  cursor: pointer;
  font-size: 14px;
  border-bottom: 3px solid transparent;
  transition: all 0.3s;
}

.nav-btn:hover {
  color: #667eea;
}

.nav-btn.active {
  color: #667eea;
  border-bottom-color: #667eea;
}

.admin-content {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.stat-card {
  background: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  border-left: 4px solid #667eea;
}

.stat-card h3 {
  margin: 0 0 10px 0;
  font-size: 14px;
  color: #666;
  text-transform: uppercase;
}

.stat-number {
  margin: 0;
  font-size: 32px;
  font-weight: bold;
  color: #667eea;
}

.stat-label {
  margin: 8px 0 0 0;
  font-size: 12px;
  color: #999;
}

.recent-activity {
  background: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.recent-activity h2 {
  margin: 0 0 20px 0;
  font-size: 18px;
  color: #333;
}
</style>
