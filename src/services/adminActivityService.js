import { getApiAuthHeaders } from './apiContext.js'

function resolvePublicApiBase() {
  const raw = import.meta.env.VITE_API_URL
  if (raw === undefined || raw === null || String(raw).trim() === '') return ''
  return String(raw).replace(/\/$/, '')
}

const API_URL = resolvePublicApiBase()

export async function fetchAccountsActivity({ days = 30 } = {}) {
  const res = await fetch(`${API_URL}/api/admin/activity/users?days=${encodeURIComponent(days)}`, {
    headers: getApiAuthHeaders({ Accept: 'application/json' }),
  })

  const body = await res.json().catch(() => ({}))
  if (!res.ok) {
    const raw = body?.message ?? body?.detail
    const msg = typeof raw === 'string'
      ? raw
      : Array.isArray(raw)
        ? raw.map((x) => x?.msg || String(x)).join('. ')
        : 'No se pudo cargar la actividad de cuentas'
    throw new Error(msg)
  }
  return body
}

