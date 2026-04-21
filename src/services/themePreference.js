const STORAGE_KEY = 'embalse_theme_mode'

export function getThemeMode() {
  return localStorage.getItem(STORAGE_KEY) === 'dark' ? 'dark' : 'light'
}

export function isDarkTheme() {
  return getThemeMode() === 'dark'
}

export function applyTheme(mode) {
  const m = mode === 'dark' ? 'dark' : 'light'
  document.documentElement.setAttribute('data-theme', m)
  document.documentElement.style.colorScheme = m === 'dark' ? 'dark' : 'light'
}

/** Carga preferencia guardada (persiste tras cerrar sesión o reiniciar). */
export function initTheme() {
  applyTheme(getThemeMode())
}

export function setThemeMode(mode) {
  localStorage.setItem(STORAGE_KEY, mode === 'dark' ? 'dark' : 'light')
  applyTheme(mode)
  window.dispatchEvent(new CustomEvent('embalse-theme-change'))
}

export function toggleThemeMode() {
  const next = isDarkTheme() ? 'light' : 'dark'
  setThemeMode(next)
  return next
}
