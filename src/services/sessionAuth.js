import { createCorrelationId, appLogger } from '../utils/logger.js'
import { getApiAuthHeaders, notifyOrganizationChanged } from './apiContext.js'
import { clearSupabaseSession } from './supabaseSessionBridge.js'
import { supabase } from './supabaseClient.js'

/**
 * Access JWT: 30 min solo administrador; empleado con validez mayor (config en API).
 * Refresh JWT: administrador y empleado; se usa en POST /api/auth/refresh.
 * Inactividad 30 min: solo aplica cierre de sesión al rol administrador.
 */

/**
 * Vacío = rutas relativas (/api/...), p. ej. detrás de nginx en Docker.
 * Si defines VITE_API_URL, debe ser alcanzable desde el navegador (p. ej. http://localhost:8000).
 */
function resolvePublicApiBase() {
  const raw = import.meta.env.VITE_API_URL
  if (raw === undefined || raw === null || String(raw).trim() === '') return ''
  return String(raw).replace(/\/$/, '')
}

const API_URL = resolvePublicApiBase()

export const IDLE_TIMEOUT_MS = 30 * 60 * 1000
const ACTIVITY_THROTTLE_MS = 400
const TICK_MS = 25 * 1000
const ACCESS_RENEW_MARGIN_MS = 2 * 60 * 1000

let lastActivityAt = Date.now()
let lastThrottleMark = 0
let routerRef = null
let tickIntervalId = null
const activityHandler = () => {
  const now = Date.now()
  if (now - lastThrottleMark < ACTIVITY_THROTTLE_MS) return
  lastThrottleMark = now
  lastActivityAt = now
}

const activityEvents = ['pointerdown', 'keydown', 'click', 'scroll', 'touchstart', 'wheel']

export function getJwtExpMs(token) {
  if (!token || typeof token !== 'string') return 0
  try {
    const part = token.split('.')[1]
    if (!part) return 0
    const b64 = part.replace(/-/g, '+').replace(/_/g, '/')
    const padded = b64 + '='.repeat((4 - (b64.length % 4)) % 4)
    const payload = JSON.parse(atob(padded))
    return typeof payload.exp === 'number' ? payload.exp * 1000 : 0
  } catch {
    return 0
  }
}

function isAccessTokenValid() {
  const at = localStorage.getItem('access_token')
  return !!(at && getJwtExpMs(at) > Date.now() + 2000)
}

function isRefreshTokenValid() {
  const rt = localStorage.getItem('refresh_token')
  return !!(rt && getJwtExpMs(rt) > Date.now() + 2000)
}

/** Sesión iniciada y al menos un token (access o refresh) vigente. */
export function hasValidSessionToken() {
  if (localStorage.getItem('isAuthenticated') !== 'true') return false
  return isAccessTokenValid() || isRefreshTokenValid()
}

function persistOrganizationContext(data) {
  const orgs = Array.isArray(data.organizations) ? data.organizations : []
  localStorage.setItem('userOrganizations', JSON.stringify(orgs))

  let activeId = data.organization_id || null
  if (activeId && !orgs.some((o) => o.id === activeId)) {
    activeId = null
  }
  if (!activeId && orgs[0]?.id) {
    activeId = orgs[0].id
  }
  if (activeId) {
    localStorage.setItem('activeOrganizationId', activeId)
  } else {
    localStorage.removeItem('activeOrganizationId')
  }
}

export function persistSession(data) {
  localStorage.setItem('access_token', data.access_token)
  if (data.refresh_token) {
    localStorage.setItem('refresh_token', data.refresh_token)
  }
  localStorage.setItem('isAuthenticated', 'true')
  localStorage.setItem('userRole', data.role)
  localStorage.setItem('userEmail', data.email || '')
  persistOrganizationContext(data)
  lastActivityAt = Date.now()
  lastThrottleMark = Date.now()
}

const FIRST_ACCESS_AT_KEY = 'first_access_supabase_at'
const FIRST_ACCESS_RT_KEY = 'first_access_supabase_rt'

function storeFirstAccessSupabaseSession(accessToken, refreshToken) {
  if (accessToken) sessionStorage.setItem(FIRST_ACCESS_AT_KEY, accessToken)
  if (refreshToken) sessionStorage.setItem(FIRST_ACCESS_RT_KEY, refreshToken)
}

function clearFirstAccessSupabaseSession() {
  sessionStorage.removeItem(FIRST_ACCESS_AT_KEY)
  sessionStorage.removeItem(FIRST_ACCESS_RT_KEY)
}

export function clearFirstAccessFlow() {
  clearFirstAccessSupabaseSession()
  return clearSupabaseSession()
}

async function ensureSupabaseSessionForPasswordChange(email, currentPassword) {
  const { data: existing } = await supabase.auth.getSession()
  if (existing?.session?.access_token) {
    return existing.session
  }

  const storedAt = sessionStorage.getItem(FIRST_ACCESS_AT_KEY)
  const storedRt = sessionStorage.getItem(FIRST_ACCESS_RT_KEY)
  if (storedAt && storedRt) {
    const { data, error } = await supabase.auth.setSession({
      access_token: storedAt,
      refresh_token: storedRt,
    })
    if (!error && data?.session?.access_token) {
      return data.session
    }
  }

  if (currentPassword) {
    const { data, error } = await supabase.auth.signInWithPassword({
      email,
      password: currentPassword,
    })
    if (error) {
      throw new Error(mapSupabaseLoginError(error.message))
    }
    if (data?.session?.access_token) {
      storeFirstAccessSupabaseSession(data.session.access_token, data.session.refresh_token)
      return data.session
    }
  }

  throw new Error('Sesión de Supabase no disponible. Vuelve a iniciar sesión con tu contraseña actual.')
}

export function clearSession() {
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
  localStorage.removeItem('isAuthenticated')
  localStorage.removeItem('userEmail')
  localStorage.removeItem('userRole')
  localStorage.removeItem('userOrganizations')
  localStorage.removeItem('activeOrganizationId')
  clearFirstAccessSupabaseSession()
  clearSupabaseSession()
}

const EMPLOYEE_ROLES = new Set(['empleado', 'employee', 'trabajador', 'user'])

export function isEmployeeRole(role) {
  const r = String(role || '').toLowerCase().trim()
  return EMPLOYEE_ROLES.has(r)
}

export function isAdminRole(role) {
  const r = String(role || '').toLowerCase().trim()
  if (!r || isEmployeeRole(r)) return false
  return r === 'administrador' || r === 'admin'
}

/** Vistas internas del dashboard reservadas a administradores. */
export const ADMIN_ONLY_VIEWS = new Set(['admin-users', 'admin-activity', 'admin-alerts'])

function mapSupabaseLoginError(message) {
  const m = String(message || '').toLowerCase()
  if (m.includes('invalid login credentials')) return 'Correo o contraseña incorrectos'
  if (m.includes('email not confirmed')) return 'Debes confirmar tu correo antes de iniciar sesión'
  return message || 'No se pudo iniciar sesión'
}

async function exchangeSupabaseSession(email, accessToken) {
  const res = await fetch(`${API_URL}/api/auth/session`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
      'X-Correlation-Id': createCorrelationId(),
    },
    body: JSON.stringify({ email, access_token: accessToken }),
  })
  const body = await res.json().catch(() => ({}))
  if (body.requires_password_setup) {
    return body
  }
  if (!res.ok) {
    const msg = body.message || body.detail || 'No se pudo obtener sesión de la API'
    throw new Error(typeof msg === 'string' ? msg : 'Error al iniciar sesión')
  }
  return body
}

async function completePasswordSetupOnBackend(email, accessToken) {
  const res = await fetch(`${API_URL}/api/auth/first-access/complete`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
      'X-Correlation-Id': createCorrelationId(),
    },
    body: JSON.stringify({ email, access_token: accessToken }),
  })
  const body = await res.json().catch(() => ({}))
  if (!res.ok) {
    const msg = body.message || body.detail || 'No se pudo completar la configuración de contraseña'
    throw new Error(typeof msg === 'string' ? msg : 'Error al guardar la contraseña')
  }
  if (body.requires_password_setup || !body.access_token) {
    throw new Error(
      'La contraseña se guardó pero no se pudo abrir la sesión. Cierra sesión e ingresa con la nueva contraseña.',
    )
  }
  return body
}

/** Indica si el correo debe definir contraseña en su primer acceso. */
export async function checkFirstAccess(email) {
  const normalizedEmail = String(email || '').trim().toLowerCase()
  const res = await fetch(`${API_URL}/api/auth/first-access/check`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
      'X-Correlation-Id': createCorrelationId(),
    },
    body: JSON.stringify({ email: normalizedEmail }),
  })
  const body = await res.json().catch(() => ({}))
  if (!res.ok) {
    const msg = body.message || body.detail || 'No se pudo verificar el estado de la cuenta'
    throw new Error(typeof msg === 'string' ? msg : 'Error de verificación')
  }
  return !!body.requires_password_setup
}

/** Lista usuarios de la organización activa (solo admin de esa org). */
export async function fetchOrganizationUsersForAdmin() {
  await tryRenewAccessToken()
  const res = await fetch(`${API_URL}/api/auth/admin/organization-users`, {
    headers: getApiAuthHeaders({ Accept: 'application/json' }),
  })
  const body = await res.json().catch(() => ({}))
  if (!res.ok) {
    const msg = body.detail || body.message || 'No se pudo cargar usuarios de la organización'
    throw new Error(typeof msg === 'string' ? msg : 'Error al cargar usuarios')
  }
  const users = (body.users || []).map((u) => ({
    id: u.id,
    email: u.email,
    full_name: u.full_name,
    role: u.role,
    is_verified: !!u.is_verified,
    created_at: u.created_at,
    email_confirmed_at: u.email_confirmed_at,
    last_sign_in_at: u.last_sign_in_at,
    org_role: u.org_role,
  }))
  const verifiedCount = body.verified_count ?? users.filter((u) => u.is_verified).length
  return {
    success: true,
    users,
    total: body.total ?? users.length,
    verifiedCount,
    pendingCount: body.pending_count ?? Math.max(0, users.length - verifiedCount),
    source: body.source || 'organization_scope',
    organizationName: body.organization_name || null,
    error: null,
  }
}

/** Asigna usuario a organización vía API (solo administrador autenticado). */
export async function assignUserToOrganizationAdmin({ userId, organizationId, orgRole = 'employee' }) {
  await tryRenewAccessToken()
  const token = localStorage.getItem('access_token')
  if (!token) {
    throw new Error('Sesión de administrador no válida')
  }
  const res = await fetch(`${API_URL}/api/auth/admin/assign-organization`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
      Authorization: `Bearer ${token}`,
      'X-Correlation-Id': createCorrelationId(),
    },
    body: JSON.stringify({
      user_id: userId,
      organization_id: organizationId,
      org_role: orgRole,
    }),
  })
  const body = await res.json().catch(() => ({}))
  if (!res.ok) {
    const msg = body.message || body.detail || 'No se pudo asignar el usuario a la organización'
    throw new Error(typeof msg === 'string' ? msg : 'Error al asignar organización')
  }
  return body
}

/** Marca cuenta recién creada para primer acceso (solo administrador autenticado). */
export async function markPasswordSetupRequired(userId) {
  await tryRenewAccessToken()
  const token = localStorage.getItem('access_token')
  if (!token) {
    throw new Error('Sesión de administrador no válida')
  }
  const res = await fetch(`${API_URL}/api/auth/first-access/mark`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
      Authorization: `Bearer ${token}`,
      'X-Correlation-Id': createCorrelationId(),
    },
    body: JSON.stringify({ user_id: userId }),
  })
  const body = await res.json().catch(() => ({}))
  if (!res.ok) {
    const msg = body.message || body.detail || 'No se pudo marcar el usuario para primer acceso'
    throw new Error(typeof msg === 'string' ? msg : 'Error al marcar usuario')
  }
  return body
}

/** Envía código OTP al correo (primer acceso sin contraseña conocida). */
export async function sendFirstAccessOtp(email) {
  if (!supabase) {
    throw new Error('Supabase no está configurado en el cliente')
  }
  const normalizedEmail = String(email || '').trim().toLowerCase()
  const { error } = await supabase.auth.signInWithOtp({
    email: normalizedEmail,
    options: { shouldCreateUser: false },
  })
  if (error) {
    throw new Error(error.message || 'No se pudo enviar el código al correo')
  }
}

/**
 * Verifica OTP, define contraseña en Supabase Auth y emite sesión JWT de la app.
 */
export async function completeFirstAccessWithOtp({ email, otp, password }) {
  if (!supabase) {
    throw new Error('Supabase no está configurado en el cliente')
  }
  const normalizedEmail = String(email || '').trim().toLowerCase()
  const code = String(otp || '').trim()
  if (!code) {
    throw new Error('Ingresa el código recibido en tu correo')
  }

  const { data, error } = await supabase.auth.verifyOtp({
    email: normalizedEmail,
    token: code,
    type: 'email',
  })
  if (error) {
    throw new Error(error.message || 'Código inválido o expirado')
  }

  const accessToken = data?.session?.access_token
  if (!accessToken) {
    throw new Error('No se pudo validar el código')
  }

  const { error: updateError } = await supabase.auth.updateUser({ password })
  if (updateError) {
    throw new Error(updateError.message || 'No se pudo guardar la nueva contraseña')
  }

  const { data: sessionData } = await supabase.auth.getSession()
  const freshToken = sessionData?.session?.access_token || accessToken
  return completePasswordSetupOnBackend(normalizedEmail, freshToken)
}

/**
 * Define contraseña cuando ya hay sesión Supabase (p. ej. contraseña temporal conocida).
 * currentPassword: contraseña con la que acaba de iniciar sesión (restaura sesión si se perdió).
 */
export async function completeFirstAccessWithSession(email, password, currentPassword) {
  if (!supabase) {
    throw new Error('Supabase no está configurado en el cliente')
  }
  const normalizedEmail = String(email || '').trim().toLowerCase()

  await ensureSupabaseSessionForPasswordChange(normalizedEmail, currentPassword)

  const { error: updateError } = await supabase.auth.updateUser({ password })
  if (updateError) {
    const raw = updateError.message || ''
    if (/auth session missing/i.test(raw)) {
      throw new Error('Sesión de Supabase expirada. Vuelve atrás e inicia sesión de nuevo.')
    }
    throw new Error(raw || 'No se pudo guardar la nueva contraseña')
  }

  const { data: sessionData } = await supabase.auth.getSession()
  const accessToken = sessionData?.session?.access_token
  if (!accessToken) {
    throw new Error('Sesión de Supabase no disponible. Vuelve a iniciar el proceso.')
  }

  const result = await completePasswordSetupOnBackend(normalizedEmail, accessToken)
  clearFirstAccessSupabaseSession()
  return result
}

async function loginViaBackendPassword(email, password) {
  const res = await fetch(`${API_URL}/api/auth/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
      'X-Correlation-Id': createCorrelationId(),
    },
    body: JSON.stringify({ email, password }),
  })
  const body = await res.json().catch(() => ({}))
  if (!res.ok) {
    appLogger.warn('Login fallido', { status: res.status, correlationId: res.headers.get('x-correlation-id') })
    const msg = body.message || body.detail || 'No se pudo iniciar sesión'
    throw new Error(typeof msg === 'string' ? msg : 'Credenciales inválidas')
  }
  return body
}

/**
 * 1) Supabase signInWithPassword (misma vía que al crear usuarios)
 * 2) Intercambio por JWT de la app en POST /api/auth/session
 * 3) Respaldo: POST /api/auth/login si Supabase no está configurado en el cliente
 */
export async function apiLogin(email, password) {
  const normalizedEmail = String(email || '').trim().toLowerCase()

  if (supabase) {
    const { data, error } = await supabase.auth.signInWithPassword({
      email: normalizedEmail,
      password,
    })
    if (error) {
      throw new Error(mapSupabaseLoginError(error.message))
    }
    const accessToken = data?.session?.access_token
    const refreshToken = data?.session?.refresh_token
    if (!accessToken) {
      throw new Error('No se pudo obtener la sesión de Supabase')
    }
    const session = await exchangeSupabaseSession(normalizedEmail, accessToken)
    if (session.requires_password_setup) {
      storeFirstAccessSupabaseSession(accessToken, refreshToken)
      return { requiresPasswordSetup: true, email: normalizedEmail }
    }
    clearFirstAccessSupabaseSession()
    return session
  }

  const session = await loginViaBackendPassword(normalizedEmail, password)
  if (session.requires_password_setup) {
    return { requiresPasswordSetup: true, email: normalizedEmail }
  }
  return session
}

/** Renueva access (y refresh rotado) usando el refresh token. */
export async function apiRefresh() {
  const refreshToken = localStorage.getItem('refresh_token')
  if (!refreshToken) return false
  const res = await fetch(`${API_URL}/api/auth/refresh`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    body: JSON.stringify({ refresh_token: refreshToken }),
  })
  if (!res.ok) return false
  const data = await res.json().catch(() => null)
  if (!data?.access_token || !data?.refresh_token) return false
  localStorage.setItem('access_token', data.access_token)
  localStorage.setItem('refresh_token', data.refresh_token)
  if (data.role) localStorage.setItem('userRole', data.role)
  if (data.email) localStorage.setItem('userEmail', data.email)
  persistOrganizationContext(data)
  return true
}

/** Cambia la organización activa (desarrolladores o usuarios multi-org). */
export async function switchOrganization(organizationId) {
  const token = localStorage.getItem('access_token')
  if (!token) throw new Error('Sesión no válida')

  const res = await fetch(`${API_URL}/api/auth/switch-organization`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ organization_id: organizationId }),
  })
  const body = await res.json().catch(() => ({}))
  if (!res.ok) {
    const msg = body.message || body.detail || 'No se pudo cambiar de organización'
    throw new Error(typeof msg === 'string' ? msg : 'Error al cambiar organización')
  }
  persistSession(body)
  notifyOrganizationChanged(organizationId)
  return body
}

/**
 * Garantiza un access token válido si el refresh sigue vigente.
 */
export async function tryRenewAccessToken() {
  if (isAccessTokenValid()) return true
  if (!isRefreshTokenValid()) return false
  return apiRefresh()
}

function sessionExpiredRedirect(reason) {
  clearSession()
  stopSessionIdleWatcher()
  if (reason === 'idle') {
    window.alert('Sesión cerrada por inactividad (30 minutos). Vuelve a iniciar sesión.')
  } else if (reason === 'token') {
    window.alert('Tu sesión ha expirado. Inicia sesión nuevamente.')
  }
  const r = routerRef
  if (r) {
    r.replace('/login').catch(() => {})
  } else {
    window.location.href = '/login'
  }
}

async function sessionTick() {
  if (localStorage.getItem('isAuthenticated') !== 'true') {
    return
  }

  const role = localStorage.getItem('userRole') || ''
  const idleMs = Date.now() - lastActivityAt

  if (isAdminRole(role) && idleMs >= IDLE_TIMEOUT_MS) {
    sessionExpiredRedirect('idle')
    return
  }

  if (!isRefreshTokenValid()) {
    if (!isAccessTokenValid()) {
      sessionExpiredRedirect('token')
    }
    return
  }

  const accessExp = getJwtExpMs(localStorage.getItem('access_token') || '')
  const needsRenew =
    !accessExp || accessExp <= Date.now() + ACCESS_RENEW_MARGIN_MS

  if (needsRenew) {
    const ok = await apiRefresh()
    if (!ok) {
      sessionExpiredRedirect('token')
    }
  }
}

export function startSessionIdleWatcher(router) {
  routerRef = router
  if (tickIntervalId != null) return

  lastActivityAt = Date.now()
  lastThrottleMark = Date.now()

  for (const ev of activityEvents) {
    window.addEventListener(ev, activityHandler, { passive: true, capture: true })
  }

  tickIntervalId = window.setInterval(() => {
    sessionTick().catch(() => {})
  }, TICK_MS)
}

export function stopSessionIdleWatcher() {
  if (tickIntervalId != null) {
    window.clearInterval(tickIntervalId)
    tickIntervalId = null
  }
  for (const ev of activityEvents) {
    window.removeEventListener(ev, activityHandler, { capture: true })
  }
  routerRef = null
}
