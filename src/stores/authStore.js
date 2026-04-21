import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { supabase, authService } from '../services/supabaseClient'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const userRole = ref(null)
  const isLoading = ref(false)
  const error = ref(null)

  // Computed properties
  const isAuthenticated = computed(() => user.value !== null)
  const isAdmin = computed(() => userRole.value === 'admin')
  const isUser = computed(() => userRole.value === 'user')

  // Inicializar autenticación
  async function initializeAuth() {
    isLoading.value = true
    try {
      const currentUser = await authService.getCurrentUser()
      if (currentUser) {
        user.value = currentUser
        userRole.value = await authService.getUserRole(currentUser.id)
      }
    } catch (err) {
      error.value = err.message
    } finally {
      isLoading.value = false
    }
  }

  // Login
  async function login(email, password) {
    isLoading.value = true
    error.value = null
    try {
      const result = await authService.login(email, password)
      if (result.success) {
        user.value = result.data.user
        userRole.value = await authService.getUserRole(result.data.user.id)
        return { success: true }
      } else {
        error.value = result.error
        return { success: false, error: result.error }
      }
    } finally {
      isLoading.value = false
    }
  }

  // Logout
  async function logout() {
    isLoading.value = true
    error.value = null
    try {
      const result = await authService.logout()
      if (result.success) {
        user.value = null
        userRole.value = null
        return { success: true }
      } else {
        error.value = result.error
        return { success: false, error: result.error }
      }
    } finally {
      isLoading.value = false
    }
  }

  // Listener de cambios de autenticación
  function subscribeToAuthChanges() {
    supabase.auth.onAuthStateChange(async (event, session) => {
      if (session?.user) {
        user.value = session.user
        userRole.value = await authService.getUserRole(session.user.id)
      } else {
        user.value = null
        userRole.value = null
      }
    })
  }

  return {
    // State
    user,
    userRole,
    isLoading,
    error,
    // Computed
    isAuthenticated,
    isAdmin,
    isUser,
    // Actions
    initializeAuth,
    login,
    logout,
    subscribeToAuthChanges,
  }
})
