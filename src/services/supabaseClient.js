import { createClient } from '@supabase/supabase-js'

const SUPABASE_URL = import.meta.env.VITE_SUPABASE_URL
const SUPABASE_ANON_KEY = import.meta.env.VITE_SUPABASE_ANON_KEY

if (!SUPABASE_URL || !SUPABASE_ANON_KEY) {
  console.error('Variables de Supabase no configuradas. Verifica VITE_SUPABASE_URL y VITE_SUPABASE_ANON_KEY en .env')
}

export const supabase = createClient(SUPABASE_URL || '', SUPABASE_ANON_KEY || '')

// Funciones auxiliares para autenticación
export const authService = {
  // Registrar nuevo usuario
  async signup(email, password, fullName) {
    try {
      const { data, error } = await supabase.auth.signUp({
        email,
        password,
        options: {
          data: {
            full_name: fullName,
          },
        },
      })

      if (error) throw error

      return { success: true, data }
    } catch (error) {
      return { success: false, error: error.message }
    }
  },

  // Iniciar sesión
  async login(email, password) {
    try {
      const { data, error } = await supabase.auth.signInWithPassword({
        email,
        password,
      })

      if (error) throw error

      return { success: true, data }
    } catch (error) {
      return { success: false, error: error.message }
    }
  },

  // Cerrar sesión
  async logout() {
    try {
      const { error } = await supabase.auth.signOut()
      if (error) throw error
      return { success: true }
    } catch (error) {
      return { success: false, error: error.message }
    }
  },

  // Obtener usuario actual
  async getCurrentUser() {
    try {
      const { data: { user }, error } = await supabase.auth.getUser()
      if (error) throw error
      return user
    } catch (error) {
      if (/auth session missing/i.test(String(error?.message || ''))) {
        return null
      }
      console.error('Error obteniendo usuario:', error)
      return null
    }
  },

  // Obtener rol del usuario desde la tabla users_roles
  async getUserRole(userId) {
    try {
      const { data, error } = await supabase
        .from('users_roles')
        .select('role')
        .eq('id', userId)
        .single()

      if (error) throw error
      return data?.role || 'user'
    } catch (error) {
      console.error('Error obteniendo rol:', error)
      return 'user'
    }
  },

  // Crear usuario como administrador (solo admin)
  async createUserAsAdmin(email, password, fullName, role = 'user') {
    try {
      // Crear usuario en auth
      const { data: authData, error: authError } = await supabase.auth.signUp({
        email,
        password,
        options: {
          data: {
            full_name: fullName,
          },
        },
      })

      if (authError) throw authError

      // Crear entrada en tabla users_roles
      const { error: roleError } = await supabase
        .from('users_roles')
        .insert([
          {
            id: authData.user.id,
            email: email,
            role: role,
            full_name: fullName,
            created_at: new Date().toISOString(),
          },
        ])

      if (roleError) throw roleError

      return { success: true, data: authData }
    } catch (error) {
      return { success: false, error: error.message }
    }
  },

  // Obtener todos los usuarios (solo admin)
  async getAllUsers() {
    try {
      const { data, error } = await supabase
        .from('users_roles')
        .select('*')
        .order('created_at', { ascending: false })

      if (error) throw error
      return { success: true, data }
    } catch (error) {
      return { success: false, error: error.message }
    }
  },

  // Actualizar rol de usuario
  async updateUserRole(userId, newRole) {
    try {
      const { error } = await supabase
        .from('users_roles')
        .update({ role: newRole })
        .eq('id', userId)

      if (error) throw error
      return { success: true }
    } catch (error) {
      return { success: false, error: error.message }
    }
  },

  // Eliminar usuario
  async deleteUser(userId) {
    try {
      const { error: deleteRoleError } = await supabase
        .from('users_roles')
        .delete()
        .eq('id', userId)

      if (deleteRoleError) throw deleteRoleError

      return { success: true }
    } catch (error) {
      return { success: false, error: error.message }
    }
  },

  // Obtener límites de alerta
  async getAlertLimits(userId) {
    try {
      const { data, error } = await supabase
        .from('alert_limits')
        .select('*')
        .eq('user_id', userId)

      if (error) throw error
      return { success: true, data }
    } catch (error) {
      return { success: false, error: error.message }
    }
  },

  // Actualizar límites de alerta
  async updateAlertLimits(userId, limits) {
    try {
      const { data, error } = await supabase
        .from('alert_limits')
        .upsert([
          {
            user_id: userId,
            ph_min: limits.ph_min,
            ph_max: limits.ph_max,
            temp_min: limits.temp_min,
            temp_max: limits.temp_max,
            turbidity_max: limits.turbidity_max,
            updated_at: new Date().toISOString(),
          },
        ])

      if (error) throw error
      return { success: true, data }
    } catch (error) {
      return { success: false, error: error.message }
    }
  },
}
