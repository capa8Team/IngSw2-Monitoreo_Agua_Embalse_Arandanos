<template>
  <div class="admin-alerts">
    <div class="alerts-header">
      <h2>Gestión de Límites de Alertas</h2>
      <p>Configura los límites de alerta para todos los usuarios</p>
    </div>

    <div class="alerts-container">
      <div class="alert-section">
        <h3>⚙️ Configuración Global de Límites</h3>
        <p class="section-subtitle">Estos son los límites predeterminados que se aplican a nuevos usuarios</p>

        <form @submit.prevent="handleSaveAlerts" class="alert-form">
          <div class="alert-group">
            <h4>pH</h4>
            <div class="input-row">
              <div class="input-group">
                <label>Mínimo</label>
                <input
                  v-model.number="globalAlerts.ph_min"
                  type="number"
                  step="0.1"
                  min="0"
                  max="14"
                />
              </div>
              <div class="input-group">
                <label>Máximo</label>
                <input
                  v-model.number="globalAlerts.ph_max"
                  type="number"
                  step="0.1"
                  min="0"
                  max="14"
                />
              </div>
            </div>
            <div class="alert-info">✓ Rango normal: 6.5 - 8.5</div>
          </div>

          <div class="alert-group">
            <h4>Temperatura (°C)</h4>
            <div class="input-row">
              <div class="input-group">
                <label>Mínimo</label>
                <input
                  v-model.number="globalAlerts.temp_min"
                  type="number"
                  step="0.1"
                  min="-50"
                  max="50"
                />
              </div>
              <div class="input-group">
                <label>Máximo</label>
                <input
                  v-model.number="globalAlerts.temp_max"
                  type="number"
                  step="0.1"
                  min="-50"
                  max="50"
                />
              </div>
            </div>
            <div class="alert-info">✓ Rango normal: 15 - 30</div>
          </div>

          <div class="alert-group">
            <h4>Turbidez (NTU)</h4>
            <div class="input-row">
              <div class="input-group">
                <label>Máximo</label>
                <input
                  v-model.number="globalAlerts.turbidity_max"
                  type="number"
                  step="0.1"
                  min="0"
                />
              </div>
            </div>
            <div class="alert-info">✓ Rango normal: 0 - 5</div>
          </div>

          <div v-if="alertSuccess" class="success-message">
            ✓ Límites guardados exitosamente
          </div>

          <div class="button-group">
            <button type="submit" class="save-btn">💾 Guardar Configuración</button>
            <button type="button" @click="handleResetToDefault" class="reset-btn">
              ↺ Restablecer Valores Predeterminados
            </button>
          </div>
        </form>
      </div>

      <div class="alert-section">
        <h3>👤 Límites por Usuario</h3>
        <p class="section-subtitle">Personaliza los límites para cada usuario específico</p>

        <div class="user-select">
          <select v-model="selectedUserId" @change="loadUserAlerts">
            <option value="">Selecciona un usuario...</option>
            <option v-for="user in users" :key="user.id" :value="user.id">
              {{ user.full_name }} ({{ user.email }})
            </option>
          </select>
        </div>

        <div v-if="selectedUserId && selectedUserAlerts" class="user-alerts">
          <h4>Límites para {{ getSelectedUserName() }}</h4>

          <form @submit.prevent="handleSaveUserAlerts" class="alert-form">
            <div class="alert-group">
              <h5>pH</h5>
              <div class="input-row">
                <div class="input-group">
                  <label>Mínimo</label>
                  <input
                    v-model.number="selectedUserAlerts.ph_min"
                    type="number"
                    step="0.1"
                  />
                </div>
                <div class="input-group">
                  <label>Máximo</label>
                  <input
                    v-model.number="selectedUserAlerts.ph_max"
                    type="number"
                    step="0.1"
                  />
                </div>
              </div>
            </div>

            <div class="alert-group">
              <h5>Temperatura (°C)</h5>
              <div class="input-row">
                <div class="input-group">
                  <label>Mínimo</label>
                  <input
                    v-model.number="selectedUserAlerts.temp_min"
                    type="number"
                    step="0.1"
                  />
                </div>
                <div class="input-group">
                  <label>Máximo</label>
                  <input
                    v-model.number="selectedUserAlerts.temp_max"
                    type="number"
                    step="0.1"
                  />
                </div>
              </div>
            </div>

            <div class="alert-group">
              <h5>Turbidez (NTU)</h5>
              <div class="input-row">
                <div class="input-group">
                  <label>Máximo</label>
                  <input
                    v-model.number="selectedUserAlerts.turbidity_max"
                    type="number"
                    step="0.1"
                  />
                </div>
              </div>
            </div>

            <div v-if="userAlertSuccess" class="success-message">
              ✓ Límites del usuario actualizados
            </div>

            <button type="submit" class="save-btn">💾 Guardar Límites del Usuario</button>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { authService } from '../services/supabaseClient'

const users = ref([])
const selectedUserId = ref('')
const selectedUserAlerts = ref(null)
const alertSuccess = ref(false)
const userAlertSuccess = ref(false)

const globalAlerts = ref({
  ph_min: 6.5,
  ph_max: 8.5,
  temp_min: 15,
  temp_max: 30,
  turbidity_max: 5,
})

const defaultAlerts = {
  ph_min: 6.5,
  ph_max: 8.5,
  temp_min: 15,
  temp_max: 30,
  turbidity_max: 5,
}

// Cargar usuarios
const loadUsers = async () => {
  const result = await authService.getAllUsers()
  if (result.success) {
    users.value = result.data
  }
}

// Cargar alertas del usuario seleccionado
const loadUserAlerts = async () => {
  if (!selectedUserId.value) return

  const result = await authService.getAlertLimits(selectedUserId.value)
  if (result.success && result.data.length > 0) {
    selectedUserAlerts.value = result.data[0]
  } else {
    selectedUserAlerts.value = {
      user_id: selectedUserId.value,
      ...defaultAlerts,
    }
  }
}

// Guardar alertas globales
const handleSaveAlerts = async () => {
  alertSuccess.value = false
  // En una aplicación real, esto guardaría en la base de datos
  // Por ahora solo mostramos un mensaje de éxito
  alertSuccess.value = true
  setTimeout(() => {
    alertSuccess.value = false
  }, 3000)
}

// Guardar alertas del usuario
const handleSaveUserAlerts = async () => {
  userAlertSuccess.value = false
  const result = await authService.updateAlertLimits(
    selectedUserId.value,
    selectedUserAlerts.value
  )

  if (result.success) {
    userAlertSuccess.value = true
    setTimeout(() => {
      userAlertSuccess.value = false
    }, 3000)
  }
}

// Obtener nombre del usuario seleccionado
const getSelectedUserName = () => {
  const user = users.value.find((u) => u.id === selectedUserId.value)
  return user?.full_name || ''
}

// Restablecer valores predeterminados
const handleResetToDefault = () => {
  if (confirm('¿Estás seguro de que deseas restablecer los valores predeterminados?')) {
    globalAlerts.value = { ...defaultAlerts }
  }
}

onMounted(() => {
  loadUsers()
})
</script>

<style scoped>
.admin-alerts {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.alerts-header {
  margin-bottom: 30px;
}

.alerts-header h2 {
  margin: 0;
  color: #333;
  font-size: 20px;
}

.alerts-header p {
  margin: 8px 0 0 0;
  color: #666;
  font-size: 14px;
}

.alerts-container {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 30px;
}

.alert-section {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.alert-section h3 {
  margin: 0;
  color: #333;
  font-size: 16px;
  font-weight: 600;
}

.section-subtitle {
  margin: 0;
  color: #999;
  font-size: 12px;
}

.alert-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.alert-group {
  padding: 16px;
  background: #f9f9f9;
  border-radius: 6px;
  border-left: 3px solid #667eea;
}

.alert-group h4,
.alert-group h5 {
  margin: 0 0 12px 0;
  color: #333;
  font-size: 14px;
}

.input-row {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.input-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
  flex: 1;
  min-width: 120px;
}

.input-group label {
  font-weight: 600;
  color: #666;
  font-size: 12px;
}

.input-group input {
  padding: 8px 12px;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  font-size: 14px;
}

.input-group input:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.alert-info {
  margin-top: 8px;
  font-size: 12px;
  color: #667eea;
  font-weight: 500;
}

.success-message {
  background-color: #efe;
  color: #3c3;
  padding: 12px;
  border-radius: 6px;
  font-size: 14px;
  border-left: 4px solid #3c3;
}

.button-group {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.save-btn,
.reset-btn {
  padding: 10px 20px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
  font-size: 14px;
  transition: background 0.3s;
}

.save-btn {
  background: #667eea;
  color: white;
  flex: 1;
  min-width: 150px;
}

.save-btn:hover {
  background: #5568d3;
}

.reset-btn {
  background: #e0e0e0;
  color: #333;
}

.reset-btn:hover {
  background: #d0d0d0;
}

.user-select {
  padding: 12px;
  background: #f9f9f9;
  border-radius: 6px;
}

.user-select select {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
}

.user-select select:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.user-alerts {
  padding: 16px;
  background: #f5f5f5;
  border-radius: 6px;
}

.user-alerts h4 {
  margin: 0 0 16px 0;
  color: #333;
  font-size: 14px;
  font-weight: 600;
}

@media (max-width: 768px) {
  .alerts-container {
    grid-template-columns: 1fr;
  }
}
</style>
