<template>
  <div class="register-container">
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
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #f5f7fa 0%, #e8ecf1 100%);
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
  padding: 20px;
}

.register-box {
  background: white;
  border-radius: 12px;
  border: 2px solid #66bb6a;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
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
  color: #66bb6a;
  font-size: 28px;
}

.register-header p {
  margin: 8px 0 0 0;
  color: #888888;
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
  background-color: #66bb6a;
  color: white;
  border: 2px solid #66bb6a;
  border-radius: 6px;
  font-weight: 600;
  font-size: 16px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.register-btn:hover:not(:disabled) {
  background-color: #5aa859;
  border-color: #5aa859;
  box-shadow: 0 4px 12px rgba(102, 187, 106, 0.3);
  transform: translateY(-2px);
}

.register-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  background-color: #99cc99;
  border-color: #99cc99;
}

.register-footer {
  text-align: center;
  margin-top: 20px;
  font-size: 14px;
  color: #888888;
}

.register-footer a {
  color: #66bb6a;
  text-decoration: none;
  font-weight: 600;
  transition: color 0.3s;
}

.register-footer a:hover {
  color: #5aa859;
  text-decoration: underline;
}
</style>
