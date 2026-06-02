<template>
  <Teleport to="body">
    <div
      v-if="show"
      class="dashboard-loading-overlay"
      role="status"
      aria-live="polite"
      aria-busy="true"
    >
      <div class="dashboard-loading-card">
        <div class="dashboard-loading-spinner" aria-hidden="true"></div>
        <p class="dashboard-loading-text">{{ message }}</p>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
defineProps({
  show: { type: Boolean, default: false },
  message: { type: String, default: 'Cargando...' },
})
</script>

<style scoped>
.dashboard-loading-overlay {
  position: fixed;
  inset: 0;
  z-index: 10000;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(245, 247, 250, 0.92);
  backdrop-filter: blur(3px);
}

.dashboard-loading-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 14px;
  padding: 28px 36px;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
}

.dashboard-loading-spinner {
  width: 44px;
  height: 44px;
  border: 3px solid #e8f5e9;
  border-top-color: #66bb6a;
  border-radius: 50%;
  animation: dashboard-loading-spin 0.85s linear infinite;
}

.dashboard-loading-text {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #2e7d32;
  letter-spacing: 0.02em;
}

@keyframes dashboard-loading-spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
