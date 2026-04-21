<template>
  <div class="register-container">
    <div class="register-theme-corner">
      <ThemeToggleButton />
    </div>
    <div class="register-box">
      <div class="register-header">
        <h1>🌊 Crear Cuenta</h1>
        <p>Únete a Monitoreo Embalse</p>
      </div>

      <form @submit.prevent="handleRegister" class="register-form">
        <div class="form-group">
          <label for="fullname">Nombre Completo</label>
          <input
            v-model="form.fullName"
            type="text"
            id="fullname"
            placeholder="Juan Pérez"
            required
          />
        </div>

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
            minlength="6"
          />
          <small>Mínimo 6 caracteres</small>
        </div>

        <div class="form-group">
          <label for="confirm-password">Confirmar Contraseña</label>
          <input
            v-model="form.confirmPassword"
            type="password"
            id="confirm-password"
            placeholder="••••••••"
            required
          />
        </div>

        <div v-if="error" class="error-message">
          {{ error }}
        </div>

        <div v-if="success" class="success-message">
          ¡Cuenta creada exitosamente! Redirigiendo a inicio de sesión...
        </div>

        <button
          type="submit"
          class="register-btn"
          :disabled="authStore.isLoading"
        >
          <span v-if="!authStore.isLoading">Crear Cuenta</span>
          <span v-else>Creando...</span>
        </button>
      </form>

      <div class="register-footer">
        <p>¿Ya tienes cuenta? <router-link to="/login">Inicia sesión aquí</router-link></p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/authStore'
import ThemeToggleButton from '../components/ThemeToggleButton.vue'

const router = useRouter()
const authStore = useAuthStore()

const form = ref({
  fullName: '',
  email: '',
  password: '',
  confirmPassword: '',
})

const error = ref('')
const success = ref(false)

const handleRegister = async () => {
  error.value = ''
  success.value = false

  // Validaciones
  if (!form.value.fullName || !form.value.email || !form.value.password || !form.value.confirmPassword) {
    error.value = 'Por favor completa todos los campos'
    return
  }

  if (form.value.password !== form.value.confirmPassword) {
    error.value = 'Las contraseñas no coinciden'
    return
  }

  if (form.value.password.length < 6) {
    error.value = 'La contraseña debe tener al menos 6 caracteres'
    return
  }

  const result = await authStore.signup(
    form.value.email,
    form.value.password,
    form.value.fullName
  )

  if (result.success) {
    success.value = true
    setTimeout(() => {
      router.push('/login')
    }, 2000)
  } else {
    error.value = result.error || 'Error al crear la cuenta'
  }
}
</script>

<style scoped>
.register-container {
  position: relative;
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  min-height: 100dvh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
  padding: max(16px, env(safe-area-inset-top, 0px)) 16px max(16px, env(safe-area-inset-bottom, 0px));
  box-sizing: border-box;
}

.register-theme-corner {
  position: absolute;
  top: max(12px, env(safe-area-inset-top, 0px));
  left: max(12px, env(safe-area-inset-left, 0px));
  z-index: 2;
}

.register-box {
  background: white;
  border-radius: 12px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  padding: 40px;
  width: 100%;
  max-width: 450px;
}

.register-header {
  text-align: center;
  margin-bottom: 30px;
}

.register-header h1 {
  margin: 0;
  color: #333;
  font-size: 28px;
}

.register-header p {
  margin: 8px 0 0 0;
  color: #666;
  font-size: 14px;
}

.register-form {
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
  color: #333;
  font-size: 14px;
}

.form-group input {
  padding: 12px;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  font-size: 14px;
  transition: border-color 0.3s;
}

.form-group input:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.form-group small {
  color: #999;
  font-size: 12px;
  margin-top: -4px;
}

.error-message {
  background-color: #fee;
  color: #c33;
  padding: 12px;
  border-radius: 6px;
  font-size: 14px;
  border-left: 4px solid #c33;
}

.success-message {
  background-color: #efe;
  color: #3c3;
  padding: 12px;
  border-radius: 6px;
  font-size: 14px;
  border-left: 4px solid #3c3;
}

.register-btn {
  padding: 12px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 6px;
  font-weight: 600;
  font-size: 16px;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}

.register-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
}

.register-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.register-footer {
  text-align: center;
  margin-top: 20px;
  font-size: 14px;
  color: #666;
}

.register-footer a {
  color: #667eea;
  text-decoration: none;
  font-weight: 600;
}

.register-footer a:hover {
  text-decoration: underline;
}

@media (max-width: 480px) {
  .register-box {
    padding: 24px 18px;
    border-radius: 10px;
  }

  .register-header h1 {
    font-size: 22px;
  }

  .form-group input {
    font-size: 16px;
    width: 100%;
    box-sizing: border-box;
  }

  .register-btn {
    min-height: 48px;
    width: 100%;
  }
}
</style>
