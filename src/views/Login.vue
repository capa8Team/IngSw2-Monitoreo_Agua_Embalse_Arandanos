
<template>
  <div class="login-container">
    <div class="login-box">
      <div class="login-header">
        <h1>Monitoreo Embalse</h1>
        <p>Sistema de Monitoreo de Agua</p>
      </div>

      <form @submit.prevent="handleLogin" class="login-form">
        <div class="form-group">
          <label for="email">Correo Electrónico</label>
          <input
            v-model="form.email"
            type="email"
            id="email"
            placeholder="tu@email.com"
            required
          />
        </div>

        <div class="form-group">
          <label for="password">Contraseña</label>
          <input
            v-model="form.password"
            type="password"
            id="password"
            placeholder="••••••••"
            required
          />
        </div>

        <div v-if="error" class="error-message">
          {{ error }}
        </div>

        <button
          type="submit"
          class="login-btn"
          :disabled="isLoading"
        >
          <span v-if="!isLoading">Iniciar Sesión</span>
          <span v-else>Cargando...</span>
        </button>
      </form>

      <div class="login-footer">
        <p>¿No tienes cuenta? <router-link to="/register">Regístrate aquí</router-link></p>
      </div>

      <div class="demo-info">
        <p><strong>Demostración:</strong></p>
        <p>Admin: admin@test.com / 123456789</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const form = ref({
  email: '',
  password: '',
})

const error = ref('')
const isLoading = ref(false)

const handleLogin = async () => {
  error.value = ''

  if (!form.value.email || !form.value.password) {
    error.value = 'Por favor completa todos los campos'
    return
  }

  // Demostración: Determinar rol según el email
  let userRole = 'empleado'
  if (form.value.email.includes('admin')) {
    userRole = 'administrador'
  }

  // Guardar información de autenticación en localStorage
  localStorage.setItem('isAuthenticated', 'true')
  localStorage.setItem('userEmail', form.value.email)
  localStorage.setItem('userRole', userRole)

  // Redirigir al dashboard
  router.push('/dashboard')
}
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #f5f7fa 0%, #e8ecf1 100%);
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
}

.login-box {
  background: white;
  border-radius: 12px;
  border: 2px solid #66bb6a;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  padding: 40px;
  width: 100%;
  max-width: 400px;
}

.login-header {
  text-align: center;
  margin-bottom: 30px;
}

.login-header h1 {
  margin: 0;
  color: #333333;
  font-size: 28px;
  color: #66bb6a;
}

.login-header p {
  margin: 8px 0 0 0;
  color: #888888;
  font-size: 14px;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group label {
  font-weight: 600;
  color: #333333;
  font-size: 14px;
}

.form-group input {
  padding: 12px;
  border: 1px solid #e8e8e8;
  border-radius: 6px;
  font-size: 14px;
  transition: border-color 0.3s, box-shadow 0.3s;
  background-color: #ffffff;
  color: #333333;
}

.form-group input:focus {
  outline: none;
  border-color: #66bb6a;
  box-shadow: 0 0 0 3px rgba(102, 187, 106, 0.1);
}

.error-message {
  background-color: #fee;
  color: #c33;
  padding: 12px;
  border-radius: 6px;
  font-size: 14px;
  border-left: 4px solid #c33;
}

.login-btn {
  padding: 12px;
  background-color: #66bb6a;
  color: white;
  border: 2px solid #66bb6a;
  border-radius: 6px;
  font-weight: 600;
  font-size: 16px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.login-btn:hover:not(:disabled) {
  background-color: #5aa859;
  border-color: #5aa859;
  box-shadow: 0 4px 12px rgba(102, 187, 106, 0.3);
  transform: translateY(-2px);
}

.login-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  background-color: #99cc99;
  border-color: #99cc99;
}

.login-footer {
  text-align: center;
  margin-top: 20px;
  font-size: 14px;
  color: #888888;
}

.login-footer a {
  color: #66bb6a;
  text-decoration: none;
  font-weight: 600;
  transition: color 0.3s;
}

.login-footer a:hover {
  color: #5aa859;
  text-decoration: underline;
}

.demo-info {
  background: #f8f9fa;
  border: 1px solid #e8e8e8;
  padding: 12px;
  border-radius: 6px;
  margin-top: 20px;
  font-size: 12px;
  color: #888888;
}

.demo-info p {
  margin: 4px 0;
}

.demo-info strong {
  color: #333333;
}
</style>
