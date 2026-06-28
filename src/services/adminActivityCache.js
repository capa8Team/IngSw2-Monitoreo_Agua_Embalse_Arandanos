import { getActiveOrganizationId } from './apiContext.js'

const CACHE_PREFIX = 'orgActivityCache:'
const CACHE_TTL_MS = 45_000

function cacheKey(orgId, days) {
  const safeDays = Number(days) || 30
  return orgId ? `${CACHE_PREFIX}${orgId}:${safeDays}` : ''
}

export function readAccountsActivityCache(days = 30, orgId = getActiveOrganizationId()) {
  const key = cacheKey(orgId, days)
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

export function writeAccountsActivityCache(data, days = 30, orgId = getActiveOrganizationId()) {
  const key = cacheKey(orgId, days)
  if (!key || !data) return
  try {
    sessionStorage.setItem(key, JSON.stringify({ savedAt: Date.now(), data }))
  } catch {
    // almacenamiento lleno o no disponible
  }
}

export function invalidateAccountsActivityCache(orgId = getActiveOrganizationId()) {
  if (!orgId) return
  const prefix = `${CACHE_PREFIX}${orgId}:`
  try {
    const keysToRemove = []
    for (let i = 0; i < sessionStorage.length; i += 1) {
      const key = sessionStorage.key(i)
      if (key && key.startsWith(prefix)) keysToRemove.push(key)
    }
    keysToRemove.forEach((key) => sessionStorage.removeItem(key))
  } catch {
    // ignorar
  }
}
