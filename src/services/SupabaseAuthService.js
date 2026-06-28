import { createClient } from '@supabase/supabase-js'
import { supabase, authService } from './supabaseClient'
import { ensureSupabaseAdminSession } from './supabaseSessionBridge'
import {
  getActiveOrganizationId,
  getActiveOrganizationSlug,
} from './apiContext.js'
import {
  assignUserToOrganizationAdmin,
  markPasswordSetupRequired,
} from './sessionAuth.js'
import { getSessionRole } from './authStorage.js'

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

function normalizeDbRole(role) {
  return role === 'admin' ? 'admin' : 'employee'
}

function mapUiRoleToDb(role) {
  const r = String(role || '').toLowerCase()
  if (r === 'admin' || r === 'administrador') return 'admin'
  return 'employee'
}

function isUserVerified(row) {
  if (!row) return false
  if (row.is_verified === true || row.is_email_verified === true) return true
  if (row.email_confirmed_at) return true
  if (row.last_sign_in_at) return true
  return false
}

function normalizeUserRow(row) {
  if (!row) return null
  const pk = row.id ?? row.user_id ?? row.uid ?? null
  if (!pk) return null

  const resolvedRole = String(row.role || 'employee').toLowerCase()
  const verified = isUserVerified(row)
  return {
    ...row,
    id: pk,
    email: row.email || row.user_email || 'sin-correo',
    full_name: row.full_name || row.name || row.nombre || 'N/A',
    role:
      resolvedRole === 'admin' || resolvedRole === 'administrador'
        ? 'admin'
        : resolvedRole === 'employee' || resolvedRole === 'empleado' || resolvedRole === 'user'
          ? 'employee'
          : 'employee',
    created_at: row.created_at || row.inserted_at || row.updated_at || new Date().toISOString(),
    email_confirmed_at: row.email_confirmed_at || null,
    last_sign_in_at: row.last_sign_in_at || null,
    is_verified: verified,
    verification_label: verified ? 'Verificado' : 'Pendiente',
  }
}

function countVerificationStats(users) {
  const list = Array.isArray(users) ? users : []
  const verifiedCount = list.filter((u) => u.is_verified).length
  return {
    verifiedCount,
    pendingCount: list.length - verifiedCount,
  }
}

function normalizeUsers(rows) {
  if (!Array.isArray(rows)) return []
  return rows.map(normalizeUserRow).filter(Boolean)
}

/**
 * Lista usuarios autenticados en Supabase Auth (fuente: RPC admin_list_auth_users).
 * Requiere sesión admin en Supabase y el script ADMIN_LIST_AUTH_USERS.sql ejecutado.
 */
export async function fetchSupabaseAuthUsersForAdmin() {
  const adminSession = await ensureSupabaseAdminSession()
  if (!adminSession.ok) {
    return {
      success: false,
      users: [],
      total: 0,
      source: null,
      error: adminSession.message,
    }
  }

  if (!supabase) {
    return {
      success: false,
      users: [],
      total: 0,
      source: null,
      error: 'Supabase no configurado',
    }
  }

  try {
    const [{ data: rows, error: listError }, { data: countData, error: countError }] =
      await Promise.all([
        supabase.rpc('admin_list_auth_users'),
        supabase.rpc('admin_auth_users_count'),
      ])

    if (!listError && Array.isArray(rows)) {
      const users = normalizeUsers(rows)
      const totalFromRpc =
        countError || countData === null || countData === undefined
          ? users.length
          : Number(countData)
      const { verifiedCount, pendingCount } = countVerificationStats(users)

      return {
        success: true,
        users,
        total: Number.isFinite(totalFromRpc) ? totalFromRpc : users.length,
        verifiedCount,
        pendingCount,
        source: 'supabase_auth',
        error: null,
      }
    }

    const missingRpc =
      listError &&
      /function.*does not exist|cannot change return type|admin_list_auth_users/i.test(
        String(listError.message || '')
      )

    if (missingRpc) {
      console.warn(
        '[fetchSupabaseAuthUsersForAdmin] Falta o está desactualizada la RPC admin_list_auth_users. Vuelve a ejecutar ADMIN_LIST_AUTH_USERS.sql (incluye DROP FUNCTION).'
      )
    } else if (listError) {
      console.warn('[fetchSupabaseAuthUsersForAdmin] RPC error:', listError.message)
    }
  } catch (rpcException) {
    console.warn('[fetchSupabaseAuthUsersForAdmin] Excepción RPC:', rpcException.message)
  }

  const fallbackUsers = await getAllUsersFromRolesTable()
  const { verifiedCount, pendingCount } = countVerificationStats(fallbackUsers)
  return {
    success: fallbackUsers.length > 0,
    users: fallbackUsers,
    total: fallbackUsers.length,
    verifiedCount,
    pendingCount,
    source: 'users_roles',
    error:
      fallbackUsers.length === 0
        ? 'No se pudo leer auth.users. Ejecuta ADMIN_LIST_AUTH_USERS.sql en Supabase SQL Editor y recarga la pagina.'
        : `Solo se muestran ${fallbackUsers.length} fila(s) de users_roles. En Authentication hay mas usuarios: ejecuta ADMIN_LIST_AUTH_USERS.sql para ver los 10 y el estado verificado.`,
  }
}

async function getAllUsersFromRolesTable() {
  const attempts = [
    async () => supabase.from('users_roles').select('*').order('created_at', { ascending: false }),
    async () => supabase.from('users_roles').select('*'),
  ]

  for (const run of attempts) {
    const { data, error } = await run()
    if (!error && Array.isArray(data) && data.length > 0) {
      return normalizeUsers(data)
    }
  }
  return []
}

async function waitForUserRoleRow(userId, attempts = 8, delayMs = 400) {
  for (let i = 0; i < attempts; i += 1) {
    const { data, error } = await supabase
      .from('users_roles')
      .select('id, role')
      .eq('id', userId)
      .maybeSingle()

    if (!error && data?.id) return data
    await new Promise((resolve) => setTimeout(resolve, delayMs))
  }
  return null
}

async function syncCreatedUserRole(userId, desiredRole) {
  if (!supabase) return { success: false, error: 'Supabase no configurado' }

  const dbRole = normalizeDbRole(mapUiRoleToDb(desiredRole))
  await waitForUserRoleRow(userId)

  const { data: row, error: readError } = await supabase
    .from('users_roles')
    .select('id, role')
    .eq('id', userId)
    .maybeSingle()

  if (readError) {
    return { success: false, error: readError.message }
  }

  if (!row?.id) {
    return {
      success: false,
      error:
        'El usuario se creó en Auth pero no apareció en users_roles. Ejecuta FIX_USERS_ROLES_RLS_RECURSION.sql y verifica el trigger handle_new_user.',
    }
  }

  if (row.role === dbRole) return { success: true }

  return updateUserRole(userId, dbRole)
}

async function markUserMustSetPassword(userId) {
  if (supabase) {
    const { error } = await supabase
      .from('users_roles')
      .update({
        must_set_password: true,
        updated_at: new Date().toISOString(),
      })
      .eq('id', userId)

    if (!error) {
      return { success: true }
    }
    console.warn('[markUserMustSetPassword] Supabase update:', error.message)
  }

  try {
    await markPasswordSetupRequired(userId)
    return { success: true }
  } catch (markError) {
    return {
      success: false,
      error: markError?.message || 'No se pudo marcar el usuario para primer acceso',
    }
  }
}

async function assignUserToActiveOrganization(userId, role) {
  const organizationId = getActiveOrganizationId()
  if (!organizationId) {
    return {
      success: false,
      error:
        'No se detectó la organización activa del dashboard. Cierra sesión e ingresa de nuevo.',
    }
  }

  const orgRole = role === 'admin' ? 'admin' : 'employee'
  try {
    await assignUserToOrganizationAdmin({
      userId,
      organizationId,
      orgRole,
    })
    return { success: true }
  } catch (error) {
    const rawMessage = String(error?.message || '')
    if (/infinite recursion detected in policy for relation "user_organizations"/i.test(rawMessage)) {
      return {
        success: false,
        error:
          'Error de política RLS en user_organizations. Ejecuta FIX_USER_ORGANIZATIONS_RLS_RECURSION.sql en Supabase.',
      }
    }
    console.error('Error assigning organization to user:', error)
    return { success: false, error: rawMessage || 'No se pudo asignar la organización' }
  }
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

    const adminSession = await ensureSupabaseAdminSession()
    if (!adminSession.ok) {
      return { success: false, error: adminSession.message }
    }

    const normalizedEmail = String(email || '').trim().toLowerCase()
    const normalizedFullName = String(fullName || '').trim()
    const normalizedRole = normalizeDbRole(mapUiRoleToDb(role))

    if (!EMAIL_REGEX.test(normalizedEmail)) {
      return {
        success: false,
        error: 'Correo invalido. Usa formato nombre@dominio.com sin espacios.'
      }
    }

    if (!password || String(password).length < 6) {
      return {
        success: false,
        error: 'La contrasena debe tener al menos 6 caracteres.',
      }
    }

    const activeOrganizationId = getActiveOrganizationId()
    const activeOrganizationSlug = getActiveOrganizationSlug()
    if (!activeOrganizationId) {
      return {
        success: false,
        error:
          'No se detectó la organización activa. Cierra sesión e ingresa de nuevo desde el dashboard de tu empresa.',
      }
    }

    const isolatedClient = createIsolatedAuthClient()
    const { data: authData, error: authError } = await isolatedClient.auth.signUp({
      email: normalizedEmail,
      password,
      options: {
        data: {
          full_name: normalizedFullName,
          role: normalizedRole,
          must_set_password: true,
          organization_id: activeOrganizationId,
          organization_slug: activeOrganizationSlug || undefined,
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
        friendlyMessage =
          'Ese correo ya está registrado. No lo vuelvas a crear: confirma el correo anterior o elimínalo en Supabase.'
      } else if (/email rate limit exceeded/i.test(rawMessage)) {
        friendlyMessage =
          'Supabase bloqueó temporalmente nuevos registros por límite de envíos de correo. Espera entre 15 y 60 minutos e intenta de nuevo.'
      } else if (/infinite recursion detected in policy for relation "users_roles"/i.test(rawMessage)) {
        friendlyMessage = 'Error de politica RLS en users_roles (recursion). Debes aplicar el script FIX_USERS_ROLES_RLS_RECURSION.sql en Supabase.'
      }

      return {
        success: false,
        error: friendlyMessage || 'Error al crear usuario en autenticacion',
      }
    }

    const userId = authData?.user?.id
    if (!userId) {
      return {
        success: false,
        error: 'No se pudo obtener el ID del usuario creado',
      }
    }

    const roleSync = await syncCreatedUserRole(userId, normalizedRole)
    if (!roleSync.success) {
      return {
        success: false,
        error: roleSync.error || 'Usuario creado en Auth pero no se pudo sincronizar el rol en users_roles',
        userId,
      }
    }

    const orgAssign = await assignUserToActiveOrganization(userId, normalizedRole)
    if (!orgAssign.success) {
      return {
        success: false,
        error: orgAssign.error || 'Usuario creado pero no se pudo asignar a la organización activa',
        userId,
      }
    }

    const marked = await markUserMustSetPassword(userId)
    if (!marked.success) {
      return {
        success: false,
        error:
          marked.error ||
          'Usuario creado pero no se pudo registrar el cambio de contraseña obligatorio. Contacta al administrador.',
        userId,
      }
    }

    return {
      success: true,
      userId,
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
    const adminSession = await ensureSupabaseAdminSession()
    if (!adminSession.ok) {
      console.warn('[getAllUsers] Sin sesión admin Supabase:', adminSession.message)
      return []
    }

    console.log('[getAllUsers] Iniciando carga de usuarios desde Supabase...')

    const authResult = await fetchSupabaseAuthUsersForAdmin()
    if (authResult.success && authResult.users.length > 0) {
      console.log(
        `[getAllUsers] ✅ ${authResult.total} usuario(s) desde ${authResult.source}`
      )
      return authResult.users
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
 * Lista unificada para pantallas de administración (Auth + respaldo users_roles).
 */
export async function getAllUsersMerged() {
  const authResult = await fetchSupabaseAuthUsersForAdmin()
  if (authResult.success && authResult.users.length > 0) {
    return authResult.users
  }

  const [robust, legacyResult] = await Promise.all([
    getAllUsersFromRolesTable(),
    authService.getAllUsers(),
  ])
  const legacyList =
    legacyResult.success && Array.isArray(legacyResult.data)
      ? normalizeUsers(legacyResult.data)
      : []
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
    const adminSession = await ensureSupabaseAdminSession()
    if (!adminSession.ok) {
      return { success: false, error: adminSession.message }
    }

    const { error } = await supabase
      .from('users_roles')
      .update({
        role: normalizeDbRole(mapUiRoleToDb(newRole)),
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
 * Eliminar un usuario de Auth (auth.users) y tablas relacionadas (users_roles, etc.).
 * @param {string} userId
 * @returns {Promise<{success: boolean, error?: string}>}
 */
export async function deleteUserFromSupabase(userId) {
  try {
    const adminSession = await ensureSupabaseAdminSession()
    if (!adminSession.ok) {
      return { success: false, error: adminSession.message }
    }

    if (!userId) {
      return { success: false, error: 'ID de usuario invalido' }
    }

    const { data: deleted, error: rpcError } = await supabase.rpc('admin_delete_auth_user', {
      target_user_id: userId,
    })

    if (!rpcError && deleted === true) {
      return { success: true }
    }

    if (!rpcError && deleted === false) {
      return {
        success: false,
        error: 'No se encontró el usuario en Supabase Auth (puede que ya fue eliminado).',
      }
    }

    const missingRpc =
      rpcError &&
      /function.*does not exist|admin_delete_auth_user/i.test(String(rpcError.message || ''))

    if (missingRpc) {
      return {
        success: false,
        error:
          'Falta la función admin_delete_auth_user. Ejecuta ADMIN_DELETE_AUTH_USER.sql en el SQL Editor de Supabase.',
      }
    }

    if (rpcError) {
      const raw = rpcError.message || ''
      if (/does not exist|42P01/i.test(raw)) {
        return {
          success: false,
          error:
            'La función de borrado en Supabase está desactualizada. Vuelve a ejecutar ADMIN_DELETE_AUTH_USER.sql en el SQL Editor y recarga la página.',
        }
      }
      if (/No puedes eliminar tu propia cuenta/i.test(raw)) {
        return { success: false, error: 'No puedes eliminar la cuenta con la que iniciaste sesión.' }
      }
      if (/Solo administradores/i.test(raw)) {
        return { success: false, error: 'Tu sesión de Supabase no tiene permisos de administrador.' }
      }
      console.error('Error RPC admin_delete_auth_user:', rpcError)
      return { success: false, error: raw || 'Error al eliminar usuario en Supabase' }
    }

    // Respaldo: solo users_roles (cuenta Auth quedaría huérfana en el panel de Supabase)
    const { error: roleError } = await supabase.from('users_roles').delete().eq('id', userId)
    if (roleError) {
      return { success: false, error: roleError.message }
    }

    return {
      success: false,
      error:
        'Solo se eliminó users_roles. Ejecuta ADMIN_DELETE_AUTH_USER.sql para borrar también en Authentication.',
    }
  } catch (error) {
    console.error('Exception in deleteUserFromSupabase:', error)
    return {
      success: false,
      error: error.message,
    }
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
    let userRole = null
    try {
      userRole = await getUserById(data.user.id)
    } catch (roleError) {
      console.warn('No se pudo obtener el rol del usuario de Supabase, usando localStorage:', roleError)
      // Usar localStorage como fallback
      userRole = {
        id: data.user.id,
        role: getSessionRole() || 'employee',
        full_name: localStorage.getItem('userFullName') || data.user.email
      }
    }

    return {
      id: data.user.id,
      email: data.user.email,
      ...(userRole || {
        role: getSessionRole() || 'employee',
        full_name: localStorage.getItem('userFullName') || data.user.email
      })
    }
  } catch (error) {
    console.error('Exception in getCurrentUser:', error)
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

export default {
  createUserInSupabase,
  fetchSupabaseAuthUsersForAdmin,
  getAllUsers,
  getAllUsersMerged,
  getUserById,
  updateUserRole,
  deleteUserFromSupabase,
  getCurrentUser,
  getAlertLimitsByAdmin,
}
