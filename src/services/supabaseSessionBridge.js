import { supabase, authService } from './supabaseClient'

/**
 * Tras el login JWT, abre sesión en Supabase con las mismas credenciales.
 * Necesario para que RLS permita listar/crear/editar users_roles como admin.
 */
export async function syncSupabaseSessionAfterLogin(email, password) {
  if (!supabase) {
    return { success: false, skipped: true, error: 'Supabase no configurado (revisa .env)' }
  }

  const normalizedEmail = String(email || '').trim().toLowerCase()
  if (!normalizedEmail || !password) {
    return { success: false, error: 'Correo o contraseña vacíos' }
  }

  try {
    const { data, error } = await supabase.auth.signInWithPassword({
      email: normalizedEmail,
      password,
    })

    if (error) {
      return {
        success: false,
        error:
          'No se pudo vincular la sesión con Supabase. El usuario debe existir en Supabase Auth con la misma contraseña que usaste para entrar.',
        detail: error.message,
      }
    }

    const userId = data?.user?.id
    let role = 'employee'
    if (userId) {
      try {
        role = await authService.getUserRole(userId)
      } catch {
        role = 'employee'
      }
    }

    return { success: true, userId, role }
  } catch (err) {
    return { success: false, error: err?.message || 'Error al conectar con Supabase' }
  }
}

export async function clearSupabaseSession() {
  if (!supabase) return
  try {
    await supabase.auth.signOut()
  } catch {
    /* ignorar */
  }
}

/**
 * Comprueba que hay sesión Supabase y rol admin en users_roles.
 */
export async function ensureSupabaseAdminSession() {
  if (!supabase) {
    return {
      ok: false,
      reason: 'not_configured',
      message: 'Faltan VITE_SUPABASE_URL y VITE_SUPABASE_ANON_KEY en el archivo .env de la raíz del proyecto.',
    }
  }

  const { data: { session }, error } = await supabase.auth.getSession()
  if (error) {
    return { ok: false, reason: 'session_error', message: error.message }
  }

  if (!session?.user) {
    return {
      ok: false,
      reason: 'no_session',
      message:
        'No hay sesión activa en Supabase. Cierra sesión e inicia de nuevo con un usuario que exista en Supabase Auth (mismo correo y contraseña).',
    }
  }

  let role = 'user'
  try {
    role = await authService.getUserRole(session.user.id)
  } catch {
    role = String(session.user.user_metadata?.role || 'user').toLowerCase()
  }

  const isAdmin = role === 'admin' || role === 'administrador'
  if (!isAdmin) {
    return {
      ok: false,
      reason: 'not_admin',
      message: `Tu cuenta en Supabase tiene rol "${role}". Solo un administrador puede gestionar usuarios.`,
    }
  }

  return { ok: true, userId: session.user.id, email: session.user.email }
}
