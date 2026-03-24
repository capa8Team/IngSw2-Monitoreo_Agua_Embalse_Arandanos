<template>
  <div class="sensor-card">
    <div class="sensor-header">
      <h3 class="sensor-title">{{ sensorName }}</h3>
      <span class="sensor-status" :class="`status-${statusClass}`">
        {{ statusText }}
      </span>
    </div>
    
    <div class="gauge-wrapper">
      <DialGauge
        :value="value"
        :min="min"
        :max="max"
        :unit="unit"
        :size="240"
      />
    </div>

    <div class="sensor-info">
      <div class="info-row">
        <span class="info-label">Rango seguro:</span>
        <span class="info-value">{{ min.toFixed(1) }} - {{ safeMax.toFixed(1) }} {{ unit }}</span>
      </div>
      <div class="info-row">
        <span class="info-label">Última actualización:</span>
        <span class="info-value">{{ lastUpdated }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import DialGauge from './DialGauge.vue'

const props = defineProps({
  sensorName: {
    type: String,
    required: true
  },
  value: {
    type: Number,
    required: true
  },
  min: {
    type: Number,
    required: true
  },
  max: {
    type: Number,
    required: true
  },
  safeMax: {
    type: Number,
    required: true
  },
  unit: {
    type: String,
    required: true
  },
  lastUpdated: {
    type: String,
    default: 'ahora'
  }
})

const percentage = computed(() => {
  const clipped = Math.max(props.min, Math.min(props.max, props.value))
  return ((clipped - props.min) / (props.max - props.min)) * 100
})

const statusClass = computed(() => {
  const pct = percentage.value
  if (pct < 15 || pct > 85) return 'danger'
  if (pct < 35 || pct > 65) return 'warning'
  return 'safe'
})

const statusText = computed(() => {
  const pct = percentage.value
  if (pct < 15 || pct > 85) return 'Peligroso'
  if (pct < 35 || pct > 65) return 'Advertencia'
  return 'Estable'
})
</script>

<style scoped>
.sensor-card {
  background: #ffffff;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  border: 1px solid #e8e8e8;
  transition: all 0.3s ease;
}

.sensor-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border-color: #d0d0d0;
}

.sensor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid #f0f0f0;
}

.sensor-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #333;
  letter-spacing: 0.3px;
}

.sensor-status {
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.5px;
}

.status-safe {
  background-color: #e8f5e9;
  color: #2e7d32;
}

.status-warning {
  background-color: #fff3e0;
  color: #e65100;
}

.status-danger {
  background-color: #ffebee;
  color: #c62828;
}

.gauge-wrapper {
  display: flex;
  justify-content: center;
  margin: 24px 0;
}

.sensor-info {
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid #f0f0f0;
}

.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
  font-size: 13px;
}

.info-row:last-child {
  margin-bottom: 0;
}

.info-label {
  color: #888;
  font-weight: 500;
}

.info-value {
  color: #444;
  font-weight: 600;
}

@media (max-width: 768px) {
  .sensor-card {
    padding: 16px;
  }

  .sensor-title {
    font-size: 16px;
  }

  .sensor-header {
    margin-bottom: 16px;
  }
}
</style>
