import { createClient } from '@supabase/supabase-js'
import { supabase, authService } from './supabaseClient'

const SUPABASE_URL = import.meta.env.VITE_SUPABASE_URL
const SUPABASE_ANON_KEY = import.meta.env.VITE_SUPABASE_ANON_KEY
const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/

let isolatedAuthClient = null

function createIsolatedAuthClient() {
  if (isolatedAuthClient) return isolatedAuthClient

  isolatedAuthClient = createClient(SUPABASE_URL, SUPABASE_ANON_KEY, {
    auth: {
      persistSession: false,
      autoRefreshToken: false,
      detectSessionInUrl: false,
      storageKey: 'sb-isolated-admin-create',
    },
  })

  return isolatedAuthClient
}

/**
 * Crear un nuevo usuario en Supabase
 * @param {string} email 
 * @param {string} password 
 * @param {string} fullName 
 * @param {string} role - 'admin' o 'employee'
 * @returns {Promise<{success: boolean, error?: string, userId?: string}>}
 */
export async function createUserInSupabase(email, password, fullName, role) {
  try {
    if (!SUPABASE_URL || !SUPABASE_ANON_KEY) {
      return {
        success: false,
        error: 'Variables de entorno de Supabase no configuradas'
      }
    }

    const normalizedEmail = String(email || '').trim().toLowerCase()
    const normalizedFullName = String(fullName || '').trim()
    const normalizedRole = role === 'admin' ? 'admin' : 'employee'

    if (!EMAIL_REGEX.test(normalizedEmail)) {
      return {
        success: false,
        error: 'Correo invalido. Usa formato nombre@dominio.com sin espacios.'
      }
    }

    if (!password || String(password).length < 6) {
      return {
        success: false,
        error: 'La contrasena debe tener al menos 6 caracteres.'
      }
    }

    const isolatedClient = createIsolatedAuthClient()

    // 1. Crear usuario en Auth de Supabase sin cambiar la sesión del admin actual
    const { data: authData, error: authError } = await isolatedClient.auth.signUp({
      email: normalizedEmail,
      password,
      options: {
        data: {
          full_name: normalizedFullName,
          role: normalizedRole,
        },
      },
    })

    if (authError) {
      console.error('Error creating auth user:', authError)
      const rawMessage = authError.message || ''
      let friendlyMessage = rawMessage

      if (/Email address .* is invalid/i.test(rawMessage)) {
        friendlyMessage = 'Correo invalido. Prueba con un correo real, por ejemplo nombre@empresa.com.'
      } else if (/already registered/i.test(rawMessage)) {
        friendlyMessage = 'Ese correo ya esta registrado en Supabase.'
      } else if (/email rate limit exceeded/i.test(rawMessage)) {
        friendlyMessage = 'Supabase bloqueo temporalmente nuevos registros por limite de envios. Espera unos minutos e intenta otra vez.'
      } else if (/infinite recursion detected in policy for relation "users_roles"/i.test(rawMessage)) {
        friendlyMessage = 'Error de politica RLS en users_roles (recursion). Debes aplicar el script FIX_USERS_ROLES_RLS_RECURSION.sql en Supabase.'
      }

      return {
        success: false,
        error: friendlyMessage || 'Error al crear usuario en autenticacion'
      }
    }

    const userId = authData?.user?.id
    if (!userId) {
      return {
        success: false,
        error: 'No se pudo obtener el ID del usuario creado'
      }
    }

    return {
      success: true,
      userId
    }
  } catch (error) {
    console.error('Exception in createUserInSupabase:', error)
    return {
      success: false,
      error: error.message
    }
  }
}

/**
 * Obtener todos los usuarios
 * @returns {Promise<Array>}
 */
export async function getAllUsers() {
  try {
    console.log('[getAllUsers] Iniciando carga de usuarios desde Supabase...')

    const normalizeUsers = (rows) => {
      if (!Array.isArray(rows)) return []

      return rows
        .map((row) => {
          const pk = row.id ?? row.user_id ?? row.uid ?? null
          const resolvedRole = String(row.role || 'user').toLowerCase()
          return {
            ...row,
            id: pk,
            email: row.email || row.user_email || 'sin-correo',
            full_name: row.full_name || row.name || row.nombre || 'N/A',
            role:
              resolvedRole === 'user'
                ? 'user'
                : resolvedRole === 'employee' || resolvedRole === 'empleado'
                  ? 'employee'
                  : resolvedRole === 'admin' || resolvedRole === 'administrador'
                    ? 'admin'
                    : 'user',
            created_at: row.created_at || row.inserted_at || row.updated_at || new Date().toISOString(),
          }
        })
        .filter((user) => !!user.id)
    }

    const attempts = [
      async () => {
        const { data, error } = await supabase
          .from('users_roles')
          .select('*')
          .order('created_at', { ascending: false, nullsFirst: false })
        return { data, error, source: 'users_roles:ordered' }
      },
      async () => {
        const { data, error } = await supabase
          .from('users_roles')
          .select('*')
        return { data, error, source: 'users_roles:raw' }
      },
      async () => {
        const { data, error } = await supabase
          .from('users_roles')
          .select('user_id, email, full_name, role, created_at')
        return { data, error, source: 'users_roles:user_id' }
      },
    ]

    for (const runAttempt of attempts) {
      const { data, error, source } = await runAttempt()

      if (error) {
        console.warn(`[getAllUsers] ${source} devolvió error:`, error.message)
        continue
      }

      const rawCount = Array.isArray(data) ? data.length : 0
      const normalized = normalizeUsers(data)
      if (rawCount > 0 && normalized.length < rawCount) {
        console.warn(
          `[getAllUsers] ${source}: ${rawCount - normalized.length} fila(s) sin id/user_id válido (revisa el registro en Supabase).`
        )
      }
      if (normalized.length > 0) {
        console.log(`[getAllUsers] ✅ Usuarios obtenidos desde ${source}. Total:`, normalized.length)
        return normalized
      }
    }

    // Fallback opcional si se está usando Service Role Key por configuración local.
    if (supabase?.auth?.admin?.listUsers) {
      try {
        const { data: authUsersData, error: authUsersError } = await supabase.auth.admin.listUsers()
        if (!authUsersError && Array.isArray(authUsersData?.users) && authUsersData.users.length > 0) {
          const normalizedAuthUsers = authUsersData.users.map((user) => ({
            id: user.id,
            email: user.email || 'sin-correo',
            full_name: user.user_metadata?.full_name || user.email || 'N/A',
            role: String(user.user_metadata?.role || 'employee').toLowerCase() === 'admin' ? 'admin' : 'employee',
            created_at: user.created_at || new Date().toISOString(),
          }))

          console.log('[getAllUsers] ✅ Usuarios obtenidos desde auth.admin.listUsers. Total:', normalizedAuthUsers.length)
          return normalizedAuthUsers
        }
      } catch (authAdminError) {
        console.warn('[getAllUsers] Fallback auth.admin.listUsers no disponible:', authAdminError.message)
      }
    }

    console.warn('[getAllUsers] ⚠️ No fue posible obtener usuarios con las consultas disponibles.')
    return []
  } catch (error) {
    console.error('[getAllUsers] ❌ Excepción:', error.message)
    console.error('[getAllUsers] Stack:', error.stack)
    return []
  }
}

function mergeUsersById(primary, secondary) {
  const byId = new Map()
  const add = (row) => {
    if (!row) return
    const id = row.id ?? row.user_id
    if (!id) return
    const prev = byId.get(id)
    byId.set(id, prev ? { ...prev, ...row, id } : { ...row, id })
  }
  ;(primary || []).forEach(add)
  ;(secondary || []).forEach(add)
  return Array.from(byId.values()).sort((a, b) => {
    const ta = new Date(a.created_at || 0).getTime()
    const tb = new Date(b.created_at || 0).getTime()
    return tb - ta
  })
}

/**
 * Lista unificada para pantallas de administración: combina getAllUsers normalizado
 * con la consulta cruda por si alguna fila queda fuera tras normalizar.
 */
export async function getAllUsersMerged() {
  const [robust, legacyResult] = await Promise.all([getAllUsers(), authService.getAllUsers()])
  const legacyList =
    legacyResult.success && Array.isArray(legacyResult.data) ? legacyResult.data : []
  return mergeUsersById(robust, legacyList)
}

/**
 * Obtener un usuario por ID
 * @param {string} userId 
 * @returns {Promise<Object|null>}
 */
export async function getUserById(userId) {
  try {
    const { data, error } = await supabase
      .from('users_roles')
      .select('*')
      .eq('id', userId)
      .single()

    if (error) {
      console.error('Error fetching user:', error)
      return null
    }

    return data
  } catch (error) {
    console.error('Exception in getUserById:', error)
    return null
  }
}

/**
 * Actualizar rol de un usuario
 * @param {string} userId 
 * @param {string} newRole - 'admin' o 'employee'
 * @returns {Promise<{success: boolean, error?: string}>}
 */
export async function updateUserRole(userId, newRole) {
  try {
    const { error } = await supabase
      .from('users_roles')
      .update({
        role: newRole === 'admin' ? 'admin' : 'employee',
        updated_at: new Date().toISOString()
      })
      .eq('id', userId)

    if (error) {
      console.error('Error updating user role:', error)
      return {
        success: false,
        error: error.message
      }
    }

    return { success: true }
  } catch (error) {
    console.error('Exception in updateUserRole:', error)
    return {
      success: false,
      error: error.message
    }
  }
}

/**
 * Eliminar un usuario (de auth y de users_roles)
 * @param {string} userId 
 * @returns {Promise<{success: boolean, error?: string}>}
 */
export async function deleteUserFromSupabase(userId) {
  try {
    // 1. Eliminar de users_roles
    const { error: roleError } = await supabase
      .from('users_roles')
      .delete()
      .eq('id', userId)

    if (roleError) {
      console.error('Error deleting user role:', roleError)
      return {
        success: false,
        error: roleError.message
      }
    }

    // 2. Eliminar de Auth
    const { error: authError } = await supabase.auth.admin.deleteUser(userId)

    if (authError) {
      console.error('Error deleting auth user:', authError)
      // No retornamos error aquí porque ya eliminamos del DB
    }

    return { success: true }
  } catch (error) {
    console.error('Exception in deleteUserFromSupabase:', error)
    return {
      success: false,
      error: error.message
    }
  }
}

/**
 * Obtener usuarios con un rol específico
 * @param {string} role - 'admin' o 'employee'
 * @returns {Promise<Array>}
 */
export async function getUsersByRole(role) {
  try {
    const { data, error } = await supabase
      .from('users_roles')
      .select('*')
      .eq('role', role)
      .order('created_at', { ascending: false })

    if (error) {
      console.error('Error fetching users by role:', error)
      return []
    }

    return data || []
  } catch (error) {
    console.error('Exception in getUsersByRole:', error)
    return []
  }
}

/**
 * Obtener usuario actual desde auth
 * @returns {Promise<Object|null>}
 */
export async function getCurrentUser() {
  try {
    const { data, error } = await supabase.auth.getUser()

    if (error) {
      const rawMessage = String(error?.message || '')
      if (/auth session missing/i.test(rawMessage)) {
        return null
      }
      console.error('Error getting current user:', error)
      return null
    }

    if (!data.user) return null

    // Obtener detalles adicionales de users_roles
    const userRole = await getUserById(data.user.id)

    return {
      id: data.user.id,
      email: data.user.email,
      ...userRole
    }
  } catch (error) {
    console.error('Exception in getCurrentUser:', error)
    return null
  }
}

/**
 * Guardar o actualizar límites de alerta para un sensor
 * @param {string} adminId - ID del usuario admin
 * @param {string} sensorType - 'ph', 'temperature', 'conductivity'
 * @param {number} minValue 
 * @param {number} maxValue 
 * @param {number} safeMaxValue 
 * @returns {Promise<{success: boolean, error?: string, data?: Object}>}
 */
export async function saveAlertLimits(adminId, sensorType, minValue, maxValue, safeMaxValue) {
  try {
    const { data, error } = await supabase
      .from('alert_limits')
      .upsert({
        admin_id: adminId,
        sensor_type: sensorType,
        min_value: minValue,
        max_value: maxValue,
        safe_max: safeMaxValue,
        updated_at: new Date().toISOString()
      }, {
        onConflict: 'admin_id,sensor_type'
      })
      .select()

    if (error) {
      console.error('Error saving alert limits:', error)
      return {
        success: false,
        error: error.message
      }
    }

    return {
      success: true,
      data: data ? data[0] : null
    }
  } catch (error) {
    console.error('Exception in saveAlertLimits:', error)
    return {
      success: false,
      error: error.message
    }
  }
}

/**
 * Obtener límites de alerta para un sensor específico por admin
 * @param {string} adminId - ID del usuario admin
 * @param {string} sensorType - 'ph', 'temperature', 'conductivity'
 * @returns {Promise<Object|null>}
 */
export async function getAlertLimitsBySensorAndAdmin(adminId, sensorType) {
  try {
    const { data, error } = await supabase
      .from('alert_limits')
      .select('*')
      .eq('admin_id', adminId)
      .eq('sensor_type', sensorType)
      .single()

    if (error && error.code !== 'PGRST116') { // PGRST116 = no rows found
      console.error('Error fetching alert limits:', error)
      return null
    }

    return data || null
  } catch (error) {
    console.error('Exception in getAlertLimitsBySensorAndAdmin:', error)
    return null
  }
}

/**
 * Obtener todos los límites de alerta para un admin
 * @param {string} adminId - ID del usuario admin
 * @returns {Promise<Array>}
 */
export async function getAlertLimitsByAdmin(adminId) {
  try {
    const { data, error } = await supabase
      .from('alert_limits')
      .select('*')
      .eq('admin_id', adminId)
      .order('sensor_type', { ascending: true })

    if (error) {
      console.error('Error fetching alert limits for admin:', error)
      return []
    }

    return data || []
  } catch (error) {
    console.error('Exception in getAlertLimitsByAdmin:', error)
    return []
  }
}

/**
 * Obtener límites de alerta para un tipo de sensor (todos los admins)
 * @param {string} sensorType - 'ph', 'temperature', 'conductivity'
 * @returns {Promise<Array>}
 */
export async function getAlertLimitsBySensor(sensorType) {
  try {
    const { data, error } = await supabase
      .from('alert_limits')
      .select('*')
      .eq('sensor_type', sensorType)
      .order('updated_at', { ascending: false })

    if (error) {
      console.error('Error fetching alert limits for sensor:', error)
      return []
    }

    return data || []
  } catch (error) {
    console.error('Exception in getAlertLimitsBySensor:', error)
    return []
  }
}

/**
 * Eliminar límites de alerta
 * @param {string} id - ID del registro de alert_limits
 * @returns {Promise<{success: boolean, error?: string}>}
 */
export async function deleteAlertLimit(id) {
  try {
    const { error } = await supabase
      .from('alert_limits')
      .delete()
      .eq('id', id)

    if (error) {
      console.error('Error deleting alert limit:', error)
      return {
        success: false,
        error: error.message
      }
    }

    return { success: true }
  } catch (error) {
    console.error('Exception in deleteAlertLimit:', error)
    return {
      success: false,
      error: error.message
    }
  }
}

export default {
  createUserInSupabase,
  getAllUsers,
  getAllUsersMerged,
  getUserById,
  updateUserRole,
  deleteUserFromSupabase,
  getUsersByRole,
  getCurrentUser,
  saveAlertLimits,
  getAlertLimitsBySensorAndAdmin,
  getAlertLimitsByAdmin,
  getAlertLimitsBySensor,
  deleteAlertLimit
}
