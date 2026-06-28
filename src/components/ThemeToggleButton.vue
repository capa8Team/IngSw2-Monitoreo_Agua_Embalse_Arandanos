<template>
  <button
    type="button"
    class="theme-toggle-btn"
    :title="isDark ? 'Cambiar a modo claro' : 'Cambiar a modo oscuro'"
    :aria-label="isDark ? 'Modo claro' : 'Modo oscuro'"
    @click="onToggle"
  >
    <!-- Modo oscuro activo: mostrar sol para volver a claro -->
    <svg v-if="isDark" class="theme-icon" viewBox="0 0 24 24" aria-hidden="true">
      <circle cx="12" cy="12" r="4.25" fill="currentColor" />
      <path
        fill="currentColor"
        d="M12 2.25a.75.75 0 0 1 .75.75v2.1a.75.75 0 0 1-1.5 0V3a.75.75 0 0 1 .75-.75zm0 16.65a.75.75 0 0 1 .75.75v2.1a.75.75 0 0 1-1.5 0V19.65a.75.75 0 0 1 .75-.75zM4.22 4.22a.75.75 0 0 1 1.06 0l1.49 1.49a.75.75 0 1 1-1.06 1.06L4.22 5.28a.75.75 0 0 1 0-1.06zm13.01 13.01a.75.75 0 0 1 1.06 0l1.49 1.49a.75.75 0 1 1-1.06 1.06l-1.49-1.49a.75.75 0 0 1 0-1.06zM2.25 12a.75.75 0 0 1 .75-.75h2.1a.75.75 0 0 1 0 1.5H3a.75.75 0 0 1-.75-.75zm16.65 0a.75.75 0 0 1 .75-.75h2.1a.75.75 0 0 1 0 1.5h-2.1a.75.75 0 0 1-.75-.75zM5.28 18.72a.75.75 0 0 1 0-1.06l1.49-1.49a.75.75 0 1 1 1.06 1.06l-1.49 1.49a.75.75 0 0 1-1.06 0zm12.16-12.16a.75.75 0 0 1 0-1.06l1.49-1.49a.75.75 0 1 1 1.06 1.06l-1.49 1.49a.75.75 0 0 1-1.06 0z"
      />
    </svg>
    <!-- Modo claro: mostrar luna para activar oscuro -->
    <svg v-else class="theme-icon" viewBox="0 0 24 24" aria-hidden="true">
      <path
        fill="currentColor"
        d="M12.34 2.02C6.59 1.82 2 6.57 2 12c0 5.52 4.48 10 10 10 3.71 0 6.93-2.02 8.66-5.02-7.51-.25-12.09-8.86-8.32-14.96z"
      />
    </svg>
  </button>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { isDarkTheme, toggleThemeMode } from '../services/themePreference.js'

const isDark = ref(false)

function sync() {
  isDark.value = isDarkTheme()
}

function onToggle() {
  toggleThemeMode()
  sync()
}

onMounted(() => {
  sync()
  window.addEventListener('embalse-theme-change', sync)
})

onBeforeUnmount(() => {
  window.removeEventListener('embalse-theme-change', sync)
})
</script>

<style scoped>
.theme-toggle-btn {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  border: 1px solid #cfd4dc;
  background: #ffffff;
  color: #374151;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: border-color 0.2s, color 0.2s, background 0.2s;
}

.theme-toggle-btn:hover {
  border-color: #66bb6a;
  color: #2e7d32;
  background: #f8fff8;
}

.theme-icon {
  width: 22px;
  height: 22px;
  display: block;
}
</style>

<style>
html[data-theme='dark'] .theme-toggle-btn {
  background: #2a2d38;
  border-color: #4a5064;
  color: #fcd34d;
}

html[data-theme='dark'] .theme-toggle-btn:hover {
  border-color: #fbbf24;
  color: #fef3c7;
  background: #343845;
}
</style>
