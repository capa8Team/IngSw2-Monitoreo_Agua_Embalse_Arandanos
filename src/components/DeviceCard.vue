<template>
  <div class="device-card" @click="$emit('select')" :class="{ 'is-selected': isSelected }">
    <div class="device-header">
      <div class="device-icon">
        <svg viewBox="0 0 24 24" width="32" height="32" fill="currentColor">
          <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm0 16H5V5h14v14zm-5.04-6.71l-2.75 3.54-1.3-1.54c-.3-.36-.77-.36-1.07 0-.3.36-.3.94 0 1.3l1.84 2.2c.3.36.77.36 1.07 0l3.29-4c.3-.36.3-.94 0-1.3-.3-.35-.77-.35-1.07 0z"/>
        </svg>
      </div>
      <div class="device-info">
        <h3 class="device-name">{{ device.name }}</h3>
        <p class="device-model">{{ device.model }}</p>
      </div>
      <div class="device-status">
        <span class="status-badge" :class="`status-${device.status}`">
          {{ device.status === 'connected' ? 'Conectado' : 'Desconectado' }}
        </span>
      </div>
    </div>

    <div class="device-body">
      <div class="sensor-list">
        <div
          v-for="sensor in normalizedSensors"
          :key="sensor.id"
          class="sensor-item"
        >
          <span class="sensor-name">{{ sensor.name }}</span>
          <span class="sensor-value">{{ formatSensorValue(sensor.value) }} {{ sensor.unit }}</span>
        </div>
      </div>
    </div>

    <div class="device-footer">
      <p class="last-update">Última actualización: {{ device.lastUpdate }}</p>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  device: {
    type: Object,
    required: true
  },
  isSelected: {
    type: Boolean,
    default: false
  }
})

defineEmits(['select'])

const formatSensorValue = (value) => {
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed.toFixed(2) : '--'
}

const normalizedSensors = computed(() => {
  const sensors = props.device?.sensors
  if (Array.isArray(sensors)) return sensors
  if (!sensors || typeof sensors !== 'object') return []

  return [
    { id: 'ph', name: 'pH', value: sensors.ph, unit: 'pH' },
    { id: 'temp', name: 'Temperatura', value: sensors.temperature, unit: '°C' },
    { id: 'cond', name: 'Conductividad', value: sensors.conductivity, unit: 'µS/cm' }
  ]
})
</script>

<style scoped>
.device-card {
  background: #ffffff;
  border-radius: 12px;
  padding: 20px;
  border: 2px solid #d0d0d0;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  flex-direction: column;
  gap: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}

.device-card:hover {
  border-color: #66bb6a;
  box-shadow: 0 4px 12px rgba(102, 187, 106, 0.25), 0 1px 3px rgba(0, 0, 0, 0.08);
  transform: translateY(-2px);
}

.device-card.is-selected {
  border-color: #66bb6a;
  border-width: 3px;
  background: #f1f8f5;
  box-shadow: 0 4px 16px rgba(102, 187, 106, 0.3), 0 1px 3px rgba(0, 0, 0, 0.08);
}

.device-header {
  display: flex;
  align-items: center;
  gap: 16px;
}

.device-icon {
  width: 48px;
  height: 48px;
  background: #f0f2f5;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #66bb6a;
  flex-shrink: 0;
}

.device-info {
  flex: 1;
}

.device-name {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.device-model {
  margin: 4px 0 0 0;
  font-size: 12px;
  color: #888;
}

.device-status {
  flex-shrink: 0;
}

.status-badge {
  display: inline-block;
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
}

.status-connected {
  background: #e8f5e9;
  color: #2e7d32;
}

.status-disconnected {
  background: #ffebee;
  color: #c62828;
}

.device-body {
  padding: 12px 0;
  border-top: 1px solid #f0f0f0;
  border-bottom: 1px solid #f0f0f0;
}

.sensor-list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 12px;
}

.sensor-item {
  background: #f8f9fa;
  padding: 10px;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.sensor-name {
  font-size: 11px;
  color: #888;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

.sensor-value {
  font-size: 14px;
  color: #333;
  font-weight: 600;
}

.device-footer {
  font-size: 12px;
  color: #999;
}

.last-update {
  margin: 0;
}

@media (max-width: 768px) {
  .device-card {
    padding: 16px;
    border: 2px solid #d0d0d0;
  }

  .device-header {
    flex-wrap: wrap;
    gap: 12px;
  }

  .device-icon {
    width: 40px;
    height: 40px;
  }

  .device-name {
    font-size: 15px;
  }

  .device-model {
    font-size: 11px;
  }

  .status-badge {
    padding: 5px 10px;
    font-size: 11px;
  }

  .sensor-list {
    grid-template-columns: repeat(2, 1fr);
    gap: 10px;
  }

  .sensor-item {
    padding: 8px;
  }

  .sensor-value {
    font-size: 13px;
  }
}

@media (max-width: 480px) {
  .device-card {
    padding: 12px;
    gap: 12px;
    border-radius: 10px;
  }

  .device-card.is-selected {
    border-width: 2px;
  }

  .device-header {
    gap: 10px;
  }

  .device-icon {
    width: 36px;
    height: 36px;
  }

  .device-name {
    font-size: 14px;
  }

  .device-model {
    font-size: 10px;
  }

  .status-badge {
    padding: 4px 8px;
    font-size: 10px;
  }

  .device-body {
    padding: 10px 0;
  }

  .sensor-list {
    grid-template-columns: 1fr;
    gap: 8px;
  }

  .sensor-item {
    padding: 8px;
  }

  .sensor-name {
    font-size: 10px;
  }

  .sensor-value {
    font-size: 12px;
  }

  .device-footer {
    font-size: 11px;
  }
}

/* Modo oscuro: reglas scoped para vencer estilos locales del componente */
html[data-theme='dark'] .device-card {
  background: #262a36;
  border-color: #3d4254;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.35);
}

html[data-theme='dark'] .device-card:hover {
  border-color: #4ade80;
  box-shadow: 0 4px 16px rgba(74, 222, 128, 0.2), 0 2px 8px rgba(0, 0, 0, 0.35);
}

html[data-theme='dark'] .device-card.is-selected {
  background: #1a2e24;
  border-color: #4ade80;
  box-shadow: 0 4px 20px rgba(74, 222, 128, 0.25), 0 2px 8px rgba(0, 0, 0, 0.35);
}

html[data-theme='dark'] .device-icon {
  background: #2e3240;
  color: #86efac;
}

html[data-theme='dark'] .device-name {
  color: #f1f5f9;
}

html[data-theme='dark'] .device-model {
  color: #94a3b8;
}

html[data-theme='dark'] .status-connected {
  background: #14532d;
  color: #bbf7d0;
}

html[data-theme='dark'] .status-disconnected {
  background: #450a0a;
  color: #fecaca;
}

html[data-theme='dark'] .device-body {
  border-top-color: #3d4254;
  border-bottom-color: #3d4254;
}

html[data-theme='dark'] .sensor-item {
  background: #1a1d26;
}

html[data-theme='dark'] .sensor-name {
  color: #94a3b8;
}

html[data-theme='dark'] .sensor-value {
  color: #e2e8f0;
}

html[data-theme='dark'] .device-footer,
html[data-theme='dark'] .last-update {
  color: #94a3b8;
}
</style>
