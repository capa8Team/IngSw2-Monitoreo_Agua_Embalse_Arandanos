<template>
  <router-view />
</template>

<script setup>
import { onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from './stores/authStore'
import { hasValidSessionToken, startSessionIdleWatcher, stopSessionIdleWatcher } from './services/sessionAuth.js'
import { initTheme } from './services/themePreference.js'

const authStore = useAuthStore()
const router = useRouter()

onMounted(async () => {
  initTheme()
  await authStore.initializeAuth()
  authStore.subscribeToAuthChanges()
  if (hasValidSessionToken()) {
    startSessionIdleWatcher(router)
  }
})

onBeforeUnmount(() => {
  stopSessionIdleWatcher()
})
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
  /* Fondo y color: style.css + theme-dark.css (evita pisar modo oscuro) */
}

html, body, #app {
  min-height: 100%;
  width: 100%;
}
</style>
