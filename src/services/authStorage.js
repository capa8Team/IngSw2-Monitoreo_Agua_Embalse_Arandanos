/**
 * Sesión en sessionStorage por defecto; localStorage solo con «Recordarme».
 */

export const AUTH_KEYS = [
  'access_token',
  'refresh_token',
  'isAuthenticated',
  'userRole',
  'userEmail',
  'userOrganizations',
  'activeOrganizationId',
]

const REMEMBER_KEY = 'embalse_remember_session'

export function isRememberMeEnabled() {
  return localStorage.getItem(REMEMBER_KEY) === 'true'
}

/** Lee de la pestaña actual; si no hay dato y «Recordarme» está activo, usa localStorage. */
export function getAuthItem(key) {
  const fromSession = sessionStorage.getItem(key)
  if (fromSession !== null) return fromSession
  if (isRememberMeEnabled()) return localStorage.getItem(key)
  return null
}

export function setAuthItem(key, value) {
  sessionStorage.setItem(key, value)
  if (isRememberMeEnabled()) {
    localStorage.setItem(key, value)
  }
}

export function removeAuthItem(key) {
  sessionStorage.removeItem(key)
  localStorage.removeItem(key)
}

export function clearAllAuthStorage() {
  for (const key of AUTH_KEYS) {
    sessionStorage.removeItem(key)
    localStorage.removeItem(key)
  }
  localStorage.removeItem(REMEMBER_KEY)
}

export function clearLegacyLocalAuthWithoutRememberMe() {
  if (isRememberMeEnabled()) return
  if (sessionStorage.getItem('isAuthenticated') === 'true') return
  for (const key of AUTH_KEYS) {
    localStorage.removeItem(key)
  }
}

/** Copia tokens recordados a sessionStorage al abrir el navegador de nuevo. */
export function hydrateSessionFromRememberMe() {
  clearLegacyLocalAuthWithoutRememberMe()
  if (sessionStorage.getItem('isAuthenticated') === 'true') return
  if (!isRememberMeEnabled()) return
  for (const key of AUTH_KEYS) {
    const value = localStorage.getItem(key)
    if (value !== null) sessionStorage.setItem(key, value)
  }
}

export function persistAuthFields(fields, rememberMe) {
  for (const key of AUTH_KEYS) {
    sessionStorage.removeItem(key)
    localStorage.removeItem(key)
  }
  localStorage.removeItem(REMEMBER_KEY)

  if (rememberMe) {
    localStorage.setItem(REMEMBER_KEY, 'true')
  }

  for (const [key, value] of Object.entries(fields)) {
    if (value === undefined || value === null) continue
    const serialized = typeof value === 'string' ? value : String(value)
    sessionStorage.setItem(key, serialized)
    if (rememberMe) {
      localStorage.setItem(key, serialized)
    }
  }
}

export function getAccessToken() {
  return getAuthItem('access_token')
}

export function getSessionRole() {
  return getAuthItem('userRole') || ''
}
