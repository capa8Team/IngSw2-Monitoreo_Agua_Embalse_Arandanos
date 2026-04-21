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
      <path
        fill="currentColor"
        d="M12 7c-2.76 0-5 2.24-5 5s2.24 5 5 5 5-2.24 5-5-2.24-5-5-5zM2 13h2c.55 0 1-.45 1-1s-.45-1-1-1H2c-.55 0-1 .45-1 1s.45 1 1 1zm18 0h2c.55 0 1-.45 1-1s-.45-1-1-1h-2c-.55 0-1 .45-1 1s.45 1 1 1zM11 2v2c0 .55.45 1 1 1s1-.45 1-1V2c0-.55-.45-1-1-1s-1 .45-1 1zm0 18v2c0 .55.45 1 1 1s1-.45 1-1v-2c0-.55-.45-1-1-1s-1 .45-1 1zM5.99 4.58a.996.996 0 0 0-1.41 0 .996.996 0 0 0 0 1.41l1.06 1.06c.39.39 1.03.39 1.41 0s.39-1.03 0-1.41L5.99 4.58zm12.37 12.37a.996.996 0 0 0-1.41 0 .996.996 0 0 0 0 1.41l1.06 1.06c.39.39 1.03.39 1.41 0 .39-.39.39-1.03 0-1.41l-1.06-1.06zM1.18 17.18l1.06 1.06c.39.39 1.03.39 1.41 0s.39-1.03 0-1.41l-1.06-1.06a.996.996 0 0 0-1.41 0c-.38.39-.39 1.03 0 1.41zM18.36 5.64l1.06-1.06c.39-.39.39-1.03 0-1.41s-1.03-.39-1.41 0l-1.06 1.06c-.39.39-.39 1.03 0 1.41.38.39 1.02.39 1.41 0z"
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
