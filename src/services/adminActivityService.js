function resolvePublicApiBase() {
  const raw = import.meta.env.VITE_API_URL
  if (raw === undefined || raw === null || String(raw).trim() === '') return ''
  return String(raw).replace(/\/$/, '')
}

const API_URL = resolvePublicApiBase()

export async function fetchAccountsActivity({ days = 30 } = {}) {
  const token = localStorage.getItem('access_token')
  if (!token) {
    throw new Error('No hay sesión activa (access_token faltante)')
  }

  const res = await fetch(`${API_URL}/api/admin/activity/users?days=${encodeURIComponent(days)}`, {
    headers: {
      Accept: 'application/json',
      Authorization: `Bearer ${token}`,
    },
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

