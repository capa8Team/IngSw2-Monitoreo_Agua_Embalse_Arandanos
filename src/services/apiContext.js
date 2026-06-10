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

/** Organización activa del dashboard (localStorage o única org de la sesión). */
export function getActiveOrganizationId() {
  const stored = localStorage.getItem('activeOrganizationId')
  if (stored) return stored
  const orgs = getStoredOrganizations()
  if (orgs.length === 1) return orgs[0].id
  if (orgs.length > 1) return orgs[0].id
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
