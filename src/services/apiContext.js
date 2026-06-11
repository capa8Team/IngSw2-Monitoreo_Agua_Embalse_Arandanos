/**
 * Headers de autenticación y organización activa para llamadas a la API.
 */

export function getStoredOrganizations() {
  try {
    const raw = localStorage.getItem('userOrganizations')
    if (!raw) return []
    const parsed = JSON.parse(raw)
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

function parseJwtPayload(token) {
  if (!token || typeof token !== 'string') return null
  try {
    const part = token.split('.')[1]
    if (!part) return null
    const b64 = part.replace(/-/g, '+').replace(/_/g, '/')
    const padded = b64 + '='.repeat((4 - (b64.length % 4)) % 4)
    return JSON.parse(atob(padded))
  } catch {
    return null
  }
}

/** Alinea localStorage con organization_id / organizations del JWT de acceso. */
export function syncOrganizationContextFromAccessToken() {
  const payload = parseJwtPayload(localStorage.getItem('access_token'))
  if (!payload) return

  const orgs = Array.isArray(payload.organizations) ? payload.organizations : []
  if (orgs.length) {
    localStorage.setItem('userOrganizations', JSON.stringify(orgs))
  }

  const tokenOrgId = payload.organization_id
  if (tokenOrgId && orgs.some((o) => o.id === tokenOrgId)) {
    localStorage.setItem('activeOrganizationId', tokenOrgId)
    return
  }
  if (orgs[0]?.id) {
    localStorage.setItem('activeOrganizationId', orgs[0].id)
  }
}

/** Organización activa del dashboard (validada contra las orgs de la sesión). */
export function getActiveOrganizationId() {
  const orgs = getStoredOrganizations()
  const stored = localStorage.getItem('activeOrganizationId')
  if (stored && orgs.some((o) => o.id === stored)) return stored
  if (orgs.length > 0) return orgs[0].id
  return ''
}

export function getActiveOrganizationSlug() {
  const orgs = getStoredOrganizations()
  const activeId = getActiveOrganizationId()
  const match = orgs.find((o) => o.id === activeId)
  return match?.slug || ''
}

export function getApiAuthHeaders(extra = {}) {
  const headers = {
    Accept: 'application/json',
    ...extra,
  }
  const token = localStorage.getItem('access_token')
  if (token) {
    headers.Authorization = `Bearer ${token}`
  }
  const orgId = getActiveOrganizationId()
  if (orgId) {
    headers['X-Organization-Id'] = orgId
  }
  return headers
}

export function shouldShowOrganizationSwitcher() {
  return getStoredOrganizations().length > 1
}

export function getActiveOrganizationName() {
  const orgs = getStoredOrganizations()
  const activeId = getActiveOrganizationId()
  const match = orgs.find((o) => o.id === activeId)
  return match?.name || orgs[0]?.name || ''
}

/** Clave de localStorage para límites de sensores, aislada por organización. */
export function getSensorLimitsStorageKey() {
  const orgId = getActiveOrganizationId()
  return orgId ? `sensorLimitsConfig:${orgId}` : 'sensorLimitsConfig'
}

export const ORGANIZATION_CHANGED_EVENT = 'app:organization-changed'

export function notifyOrganizationChanged(organizationId) {
  window.dispatchEvent(
    new CustomEvent(ORGANIZATION_CHANGED_EVENT, { detail: { organizationId } }),
  )
}
