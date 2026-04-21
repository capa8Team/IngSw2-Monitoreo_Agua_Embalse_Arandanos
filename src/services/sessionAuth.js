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

export function persistSession(data) {
  localStorage.setItem('access_token', data.access_token)
  if (data.refresh_token) {
    localStorage.setItem('refresh_token', data.refresh_token)
  }
  localStorage.setItem('isAuthenticated', 'true')
  localStorage.setItem('userRole', data.role)
  localStorage.setItem('userEmail', data.email || '')
  lastActivityAt = Date.now()
  lastThrottleMark = Date.now()
}

export function clearSession() {
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
  localStorage.removeItem('isAuthenticated')
  localStorage.removeItem('userEmail')
  localStorage.removeItem('userRole')
}

export function isAdminRole(role) {
  const r = String(role || '').toLowerCase()
  return r === 'administrador' || r === 'admin'
}

export async function apiLogin(email, password) {
  const res = await fetch(`${API_URL}/api/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    body: JSON.stringify({ email, password }),
  })
  const body = await res.json().catch(() => ({}))
  if (!res.ok) {
    const msg = body.message || body.detail || 'No se pudo iniciar sesión'
    throw new Error(typeof msg === 'string' ? msg : 'Credenciales inválidas')
  }
  return body
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
  return true
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
