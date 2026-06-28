import { createRouter, createWebHistory } from 'vue-router'
import {
  hasValidSessionToken,
  tryRenewAccessToken,
  clearSession,
  sanitizeSessionState,
  getSessionRole,
} from './services/sessionAuth.js'
import { syncOrganizationContextFromAccessToken } from './services/apiContext.js'

// Importación lazy de vistas
const Login = () => import('./views/Login.vue')
const DeviceDashboard = () => import('./components/DeviceDashboard.vue')

const routes = [
  {
    path: '/',
    name: 'Root',
    redirect: '/login',
  },
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: { title: 'Iniciar Sesión' },
  },

  // Dashboard unificado para usuario normal y admin
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: DeviceDashboard,
    meta: { title: 'Dashboard' },
  },

  // Catch-all para rutas no encontradas
  {
    path: '/:pathMatch(.*)*',
    redirect: '/',
  },
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
})

// Guard global de navegación
router.beforeEach(async (to, from, next) => {
  document.title = to.meta.title
    ? `${to.meta.title} - Monitoreo Embalse`
    : 'Monitoreo Embalse'

  sanitizeSessionState()

  if (to.path === '/' || to.name === 'Root') {
    if (hasValidSessionToken()) {
      const renewed = await tryRenewAccessToken()
      next(renewed ? '/dashboard' : '/login')
      if (!renewed) clearSession()
      return
    }
    clearSession()
    next('/login')
    return
  }

  if (to.path === '/login') {
    if (hasValidSessionToken()) {
      const renewed = await tryRenewAccessToken()
      if (renewed) {
        next('/dashboard')
        return
      }
      clearSession()
    }
    next()
    return
  }

  if (!hasValidSessionToken()) {
    clearSession()
    next('/login')
    return
  }

  if (to.path === '/dashboard') {
    void import('./components/DeviceDashboard.vue')
  }

  const renewed = await tryRenewAccessToken()
  if (!renewed) {
    clearSession()
    next('/login')
    return
  }
  syncOrganizationContextFromAccessToken()

  if (to.meta.roles && to.meta.roles.length > 0) {
    const userRole = getSessionRole()
    if (!userRole || !to.meta.roles.includes(userRole)) {
      console.warn(`Acceso denegado: rol requerido ${to.meta.roles.join(', ')}, rol actual: ${userRole}`)
      next('/dashboard')
      return
    }
  }

  next()
})

router.afterEach((to) => {
  window.scrollTo(0, 0)
})

export default router
