import { getActiveOrganizationId } from './apiContext.js'

const CACHE_PREFIX = 'orgUsersCache:'
const CACHE_TTL_MS = 90_000

function cacheKey(orgId) {
  return orgId ? `${CACHE_PREFIX}${orgId}` : ''
}

export function readOrgUsersCache(orgId = getActiveOrganizationId()) {
  const key = cacheKey(orgId)
  if (!key) return null
  try {
    const raw = sessionStorage.getItem(key)
    if (!raw) return null
    const parsed = JSON.parse(raw)
    if (!parsed?.data || typeof parsed.savedAt !== 'number') return null
    if (Date.now() - parsed.savedAt > CACHE_TTL_MS) {
      sessionStorage.removeItem(key)
      return null
    }
    return parsed.data
  } catch {
    return null
  }
}

export function writeOrgUsersCache(data, orgId = getActiveOrganizationId()) {
  const key = cacheKey(orgId)
  if (!key || !data) return
  try {
    sessionStorage.setItem(key, JSON.stringify({ savedAt: Date.now(), data }))
  } catch {
    // almacenamiento lleno o no disponible
  }
}

export function invalidateOrgUsersCache(orgId = getActiveOrganizationId()) {
  const key = cacheKey(orgId)
  if (key) sessionStorage.removeItem(key)
}
