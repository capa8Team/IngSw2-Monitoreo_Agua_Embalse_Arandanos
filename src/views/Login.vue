<template>
  <div class="login-container">
    <div class="login-theme-corner">
      <ThemeToggleButton />
    </div>
    <div class="login-box">
      <div class="login-header">
        <h1> QAwa</h1>
        <p>Sistema de Monitoreo de Agua</p>
      </div>

      <form v-if="mode === 'login'" @submit.prevent="handleLogin" class="login-form">
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

        <div class="form-group remember-group">
          <label class="remember-label">
            <input
              v-model="rememberMe"
              type="checkbox"
              id="remember-me"
            />
            <span>Recordarme en este equipo</span>
          </label>
          <p class="remember-hint">Si no marcas esta opción, la sesión se cerrará al cerrar el navegador.</p>
        </div>

        <div v-if="error" class="error-message">
          {{ error }}
        </div>

        <button type="submit" class="login-btn" :disabled="isLoading">
          <span v-if="!isLoading">Iniciar Sesión</span>
          <span v-else>Cargando...</span>
        </button>
      </form>

      <form v-else @submit.prevent="handleSetPassword" class="login-form">
        <p class="setup-intro">
          Es la primera vez que inicias sesión con esta cuenta. Cambia tu contraseña para continuar.
        </p>

        <div class="form-group">
          <label for="new-password">Nueva contraseña</label>
          <input
            v-model="setupForm.password"
            type="password"
            id="new-password"
            placeholder="Mínimo 6 caracteres"
            required
            minlength="6"
          />
        </div>

        <div class="form-group">
          <label for="confirm-password">Confirmar contraseña</label>
          <input
            v-model="setupForm.confirmPassword"
            type="password"
            id="confirm-password"
            placeholder="Repite la contraseña"
            required
            minlength="6"
          />
        </div>

        <div v-if="error" class="error-message">
          {{ error }}
        </div>

        <button type="submit" class="login-btn" :disabled="isLoading">
          <span v-if="!isLoading">Guardar contraseña e ingresar</span>
          <span v-else>Guardando...</span>
        </button>

        <button type="button" class="link-btn" :disabled="isLoading" @click="backToLogin">
          Volver
        </button>
      </form>

    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import ThemeToggleButton from '../components/ThemeToggleButton.vue'
import {
  apiLogin,
  clearFirstAccessFlow,
  completeFirstAccessWithSession,
  persistSession,
  startSessionIdleWatcher,
} from '../services/sessionAuth.js'
import { useDeviceStore } from '../stores/deviceStore.js'

const router = useRouter()
const deviceStore = useDeviceStore()

const mode = ref('login')
const form = ref({
  email: '',
  password: '',
})
const setupForm = ref({
  password: '',
  confirmPassword: '',
})

const error = ref('')
const isLoading = ref(false)
const rememberMe = ref(false)
function resetSetupForm() {
  setupForm.value = { password: '', confirmPassword: '' }
}

function validatePasswordPair() {
  if (setupForm.value.password.length < 6) {
    error.value = 'La contraseña debe tener al menos 6 caracteres'
    return false
  }
  if (setupForm.value.password !== setupForm.value.confirmPassword) {
    error.value = 'Las contraseñas no coinciden'
    return false
  }
  return true
}

async function finishSession(data) {
  if (!data?.access_token) {
    throw new Error('No se recibió una sesión válida. Intenta iniciar sesión de nuevo.')
  }
  persistSession(data, rememberMe.value)
  startSessionIdleWatcher(router)
  mode.value = 'login'
  deviceStore.prefetchDevicesForActiveOrg()
  void router.push('/dashboard')
}

function backToLogin() {
  clearFirstAccessFlow()
  mode.value = 'login'
  error.value = ''
  resetSetupForm()
}

const handleLogin = async () => {
  error.value = ''
  const email = form.value.email.trim().toLowerCase()
  const password = String(form.value.password || '')

  if (!email || !password) {
    error.value = 'Por favor completa todos los campos'
    return
  }

  isLoading.value = true
  void import('../components/DeviceDashboard.vue')
  try {
    const data = await apiLogin(email, password)
    if (data?.requiresPasswordSetup) {
      mode.value = 'change-password'
      resetSetupForm()
      return
    }
    await finishSession(data)
  } catch (e) {
    error.value = e?.message || 'Error al iniciar sesión. Verifica que la API esté en ejecución.'
  } finally {
    isLoading.value = false
  }
}

const handleSetPassword = async () => {
  error.value = ''
  if (!validatePasswordPair()) return

  isLoading.value = true
  try {
    const data = await completeFirstAccessWithSession(
      form.value.email.trim().toLowerCase(),
      setupForm.value.password,
      form.value.password,
    )
    await finishSession(data)
  } catch (e) {
    error.value = e?.message || 'No se pudo guardar la contraseña'
  } finally {
    isLoading.value = false
  }
}
</script>

<style scoped>
.login-container {
  position: relative;
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  min-height: 100dvh;
  padding: max(16px, env(safe-area-inset-top, 0px)) 16px max(16px, env(safe-area-inset-bottom, 0px));
  box-sizing: border-box;
  background: linear-gradient(135deg, #f5f7fa 0%, #e8ecf1 100%);
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
  overflow-y: auto;
  scrollbar-gutter: stable;
}

.login-theme-corner {
  position: absolute;
  top: max(12px, env(safe-area-inset-top, 0px));
  left: max(12px, env(safe-area-inset-left, 0px));
  z-index: 2;
}

.login-box {
  background: white;
  border-radius: 12px;
  border: 2px solid #66bb6a;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  padding: 40px;
  width: 100%;
  max-width: 400px;
  flex-shrink: 0;
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

.form-group input:not([type='checkbox']) {
  padding: 12px;
  border: 2px solid #e8e8e8;
  border-radius: 6px;
  font-size: 16px;
  width: 100%;
  max-width: 100%;
  box-sizing: border-box;
  transition: border-color 0.2s ease, outline-color 0.2s ease;
  background-color: #ffffff;
  color: #333333;
}

.form-group input:not([type='checkbox']):focus {
  outline: 2px solid rgba(102, 187, 106, 0.45);
  outline-offset: 0;
  border-color: #66bb6a;
  box-shadow: none;
}

.setup-intro {
  margin: 0;
  font-size: 14px;
  color: #555555;
  line-height: 1.5;
  text-align: center;
}

.remember-group {
  gap: 6px;
}

.remember-label {
  display: flex;
  align-items: center;
  gap: 10px;
  font-weight: 500;
  color: #444444;
  font-size: 14px;
  cursor: pointer;
  user-select: none;
}

.remember-label input[type='checkbox'] {
  width: 16px;
  height: 16px;
  min-width: 16px;
  min-height: 16px;
  margin: 0;
  padding: 0;
  border: none;
  box-shadow: none;
  outline: none;
  flex-shrink: 0;
  accent-color: #66bb6a;
  cursor: pointer;
}

.remember-label input[type='checkbox']:focus {
  outline: 2px solid rgba(102, 187, 106, 0.45);
  outline-offset: 2px;
}

.remember-hint {
  margin: 0;
  font-size: 12px;
  color: #888888;
  line-height: 1.4;
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

.link-btn {
  background: none;
  border: none;
  color: #66bb6a;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  padding: 4px 0;
  text-align: center;
}

.link-btn:hover:not(:disabled) {
  text-decoration: underline;
}

.link-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

@media (max-width: 480px) {
  .login-box {
    padding: 24px 20px;
    border-radius: 10px;
  }

  .login-header h1 {
    font-size: 22px;
  }

  .login-btn {
    min-height: 48px;
    font-size: 15px;
  }
}
</style>
