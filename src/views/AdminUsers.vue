<template>
  <div class="admin-users">
    <div class="users-header">
      <h2>Gestión de Usuarios</h2>
      <button @click="showAddUserModal = true" class="add-user-btn">+ Nuevo Usuario</button>
    </div>

    <div v-if="supabaseSessionWarning" class="error-message session-warning">
      {{ supabaseSessionWarning }}
    </div>

    <!-- Modal para agregar usuario -->
    <div v-if="showAddUserModal" class="modal-overlay" @click.self="showAddUserModal = false">
      <div class="modal-content">
        <div class="modal-header">
          <h3>Crear Nuevo Usuario</h3>
          <button @click="showAddUserModal = false" class="close-btn">✕</button>
        </div>

        <form @submit.prevent="handleCreateUser" class="modal-form">
          <div class="form-group">
            <label>Nombre Completo</label>
            <input
              v-model="newUser.fullName"
              type="text"
              placeholder="Juan Pérez"
              required
            />
          </div>

          <div class="form-group">
            <label>Correo Electrónico</label>
            <input
              v-model="newUser.email"
              type="email"
              placeholder="juan@example.com"
              required
            />
          </div>

          <div class="form-group">
            <label>Contraseña Temporal</label>
            <input
              v-model="newUser.password"
              type="password"
              placeholder="••••••••"
              required
              minlength="6"
            />
          </div>

          <div class="form-group">
            <label>Rol</label>
            <select v-model="newUser.role" required>
              <option value="employee">Trabajador</option>
              <option value="admin">Administrador</option>
            </select>
          </div>

          <div v-if="newUserError" class="error-message">
            {{ newUserError }}
          </div>

          <div class="modal-actions">
            <button type="button" @click="showAddUserModal = false" class="cancel-btn">
              Cancelar
            </button>
            <button type="submit" class="submit-btn">Crear Usuario</button>
          </div>
        </form>
      </div>
    </div>

    <p v-if="!isLoading" class="users-count-summary">
      <strong>{{ supabaseUsersTotal }}</strong> en Auth —
      <strong style="color:#2e7d32">{{ supabaseUsersVerified }}</strong> verificados,
      <strong style="color:#b45309">{{ supabaseUsersPending }}</strong> pendientes
      <span v-if="usersListSource === 'supabase_auth'"> (sincronizado)</span>
    </p>
    <div v-if="usersLoadError" class="error-message session-warning">{{ usersLoadError }}</div>

    <!-- Tabla de usuarios -->
    <div class="users-table">
      <table>
        <thead>
          <tr>
            <th>Nombre</th>
            <th>Correo</th>
            <th>Estado</th>
            <th>Rol</th>
            <th>Creado</th>
            <th>Acciones</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="user in users" :key="user.id">
            <td>{{ user.full_name }}</td>
            <td>{{ user.email }}</td>
            <td>
              <span
                class="verification-pill"
                :class="user.is_verified ? 'verified' : 'pending'"
              >
                {{ user.verification_label || (user.is_verified ? 'Verificado' : 'Pendiente') }}
              </span>
            </td>
            <td>
              <select
                :value="user.role"
                @change="(e) => handleUpdateRole(user.id, e.target.value)"
                class="role-select"
              >
                <option value="employee">Trabajador</option>
                <option value="admin">Admin</option>
              </select>
            </td>
            <td>{{ formatDate(user.created_at) }}</td>
            <td>
              <button @click="handleDeleteUser(user.id)" class="delete-btn">🗑️</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import {
  createUserInSupabase,
  fetchSupabaseAuthUsersForAdmin,
  updateUserRole,
  deleteUserFromSupabase,
} from '../services/SupabaseAuthService'
import { ensureSupabaseAdminSession } from '../services/supabaseSessionBridge'

const users = ref([])
const supabaseUsersTotal = ref(0)
const supabaseUsersVerified = ref(0)
const supabaseUsersPending = ref(0)
const usersListSource = ref(null)
const usersLoadError = ref('')
const showAddUserModal = ref(false)
const newUserError = ref('')
const isLoading = ref(false)

const supabaseSessionWarning = ref('')

const newUser = ref({
  fullName: '',
  email: '',
  password: '',
  role: 'employee',
})

const refreshSupabaseSessionState = async () => {
  const check = await ensureSupabaseAdminSession()
  supabaseSessionWarning.value = check.ok ? '' : check.message
  return check.ok
}

// Cargar usuarios (lista unificada: normalizada + consulta cruda)
const loadUsers = async () => {
  isLoading.value = true
  try {
    await refreshSupabaseSessionState()
    const result = await fetchSupabaseAuthUsersForAdmin()
    users.value = result.users || []
    supabaseUsersTotal.value = result.total ?? users.value.length
    supabaseUsersVerified.value = result.verifiedCount ?? users.value.filter((u) => u.is_verified).length
    supabaseUsersPending.value = result.pendingCount ?? supabaseUsersTotal.value - supabaseUsersVerified.value
    usersListSource.value = result.source
    usersLoadError.value = result.error || ''
  } catch (error) {
    console.error('Error cargando usuarios en AdminUsers:', error)
  }
  isLoading.value = false
}

// Crear usuario
const handleCreateUser = async () => {
  newUserError.value = ''

  if (!newUser.value.fullName || !newUser.value.email || !newUser.value.password) {
    newUserError.value = 'Por favor completa todos los campos'
    return
  }

  const result = await createUserInSupabase(
    newUser.value.email,
    newUser.value.password,
    newUser.value.fullName,
    newUser.value.role
  )

  if (result.success) {
    showAddUserModal.value = false
    newUser.value = {
      fullName: '',
      email: '',
      password: '',
      role: 'employee',
    }
    await loadUsers()
  } else {
    newUserError.value = result.error
  }
}

// Actualizar rol
const handleUpdateRole = async (userId, newRole) => {
  const result = await updateUserRole(userId, newRole)
  if (result.success) {
    await loadUsers()
  }
}

// Eliminar usuario
const handleDeleteUser = async (userId) => {
  const target = users.value.find((u) => u.id === userId)
  const label = target?.email || userId
  if (!confirm(`¿Eliminar permanentemente ${label} en Supabase Auth?`)) {
    return
  }

  const result = await deleteUserFromSupabase(userId)
  if (result.success) {
    newUserError.value = ''
    await loadUsers()
  } else {
    newUserError.value = result.error || 'No se pudo eliminar el usuario'
  }
}

// Formatear fecha
const formatDate = (date) => {
  return new Date(date).toLocaleDateString('es-ES')
}

onMounted(() => {
  loadUsers()
})
</script>

<style scoped>
.admin-users {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  min-width: 0;
  max-width: 100%;
}

.users-header {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
}

.users-header h2 {
  margin: 0;
  color: #333;
}

.add-user-btn {
  padding: 10px 20px;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
  transition: background 0.3s;
}

.add-user-btn:hover {
  background: #5568d3;
}

.users-table {
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  overscroll-behavior-x: contain;
  max-width: 100%;
}

table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}

thead {
  background: #f5f5f5;
  border-bottom: 2px solid #e0e0e0;
}

th {
  padding: 12px;
  text-align: left;
  font-weight: 600;
  color: #333;
}

td {
  padding: 12px;
  border-bottom: 1px solid #e0e0e0;
  color: #666;
}

tr:hover {
  background: #f9f9f9;
}

.role-select {
  padding: 6px 10px;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
}

.delete-btn {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 18px;
  transition: transform 0.2s;
}

.delete-btn:hover {
  transform: scale(1.2);
}

/* Modal */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  padding: max(12px, env(safe-area-inset-top, 0px)) 12px max(12px, env(safe-area-inset-bottom, 0px));
  box-sizing: border-box;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 8px;
  width: 100%;
  max-width: 400px;
  max-height: min(90vh, 100dvh - 32px);
  overflow-y: auto;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  min-width: 0;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #e0e0e0;
}

.modal-header h3 {
  margin: 0;
  font-size: 18px;
  color: #333;
}

.close-btn {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 24px;
  color: #666;
}

.modal-form {
  padding: 20px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 16px;
}

.form-group label {
  font-weight: 600;
  color: #333;
  font-size: 14px;
}

.form-group input,
.form-group select {
  padding: 10px;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  font-size: 16px;
  width: 100%;
  max-width: 100%;
  box-sizing: border-box;
}

.form-group input:focus,
.form-group select:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.session-warning {
  margin-bottom: 16px;
}

.users-count-summary {
  margin: 0 0 16px 0;
  font-size: 15px;
  color: #444;
}

.verification-pill {
  display: inline-block;
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
}

.verification-pill.verified {
  background: #e8f5e9;
  color: #2e7d32;
}

.verification-pill.pending {
  background: #fff3e0;
  color: #e65100;
}

.error-message {
  background-color: #fee;
  color: #c33;
  padding: 12px;
  border-radius: 6px;
  font-size: 14px;
  margin-bottom: 16px;
  border-left: 4px solid #c33;
}

.modal-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
  margin-top: 20px;
}

.cancel-btn,
.submit-btn {
  padding: 10px 20px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
  transition: background 0.3s;
}

.cancel-btn {
  background: #e0e0e0;
  color: #333;
}

.cancel-btn:hover {
  background: #d0d0d0;
}

.submit-btn {
  background: #667eea;
  color: white;
}

.submit-btn:hover {
  background: #5568d3;
}

@media (max-width: 640px) {
  .admin-users {
    padding: 14px 12px;
  }

  .users-header h2 {
    font-size: 18px;
  }

  .add-user-btn {
    width: 100%;
    min-height: 44px;
  }

  th,
  td {
    padding: 10px 8px;
    font-size: 13px;
  }

  .modal-actions {
    flex-direction: column;
  }

  .cancel-btn,
  .submit-btn {
    width: 100%;
    min-height: 44px;
  }
}
</style>
