<template>
  <div class="sensor-card">
    <div class="sensor-header">
      <h3 class="sensor-title">{{ sensorName }}</h3>
      <span class="sensor-status" :class="`status-${statusClass}`">
        {{ statusText }}
      </span>
    </div>

    <div class="sensor-display" :class="`status-bg-${statusClass}`">
      <div class="sensor-value">
        <span class="value-number">{{ value.toFixed(1) }}</span>
        <span class="value-unit">{{ unit }}</span>
      </div>
    </div>

    <div class="sensor-info">
      <div class="info-row">
        <span class="info-label">🔴 Zona roja:</span>
        <span class="info-value">
          {{ normalizedThresholds.dangerMin.toFixed(1) }} - {{ normalizedThresholds.dangerMax.toFixed(1) }}
          / {{ normalizedThresholds.dangerMinSup.toFixed(1) }} - {{ normalizedThresholds.dangerMaxSup.toFixed(1) }} {{ unit }}
        </span>
      </div>
      <div class="info-row">
        <span class="info-label">🟠 Zona amarilla:</span>
        <span class="info-value">
          {{ normalizedThresholds.warningMin.toFixed(1) }} - {{ normalizedThresholds.warningMax.toFixed(1) }}
          / {{ normalizedThresholds.warningMinSup.toFixed(1) }} - {{ normalizedThresholds.warningMaxSup.toFixed(1) }} {{ unit }}
        </span>
      </div>
      <div class="info-row">
        <span class="info-label">🟢 Rango verde:</span>
        <span class="info-value">{{ normalizedThresholds.safeMin.toFixed(1) }} - {{ normalizedThresholds.safeMax.toFixed(1) }} {{ unit }}</span>
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

const props = defineProps({
  sensorName: {
    type: String,
    required: true
  },
  sensorType: {
    type: String,
    default: 'temperature',
    validator: (value) => ['temperature', 'ph', 'conductivity'].includes(value)
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
  thresholds: {
    type: Object,
    default: null
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

const clamp = (value, min, max) => Math.min(max, Math.max(min, value))

const buildFallbackThresholds = () => {
  const range = props.max - props.min
  return {
    dangerMin: props.min,
    dangerMax: props.min + range * 0.15,
    warningMin: props.min + range * 0.15,
    warningMax: props.min + range * 0.35,
    safeMin: props.min + range * 0.35,
    safeMax: props.min + range * 0.65,
    warningMinSup: props.min + range * 0.65,
    warningMaxSup: props.min + range * 0.85,
    dangerMinSup: props.min + range * 0.85,
    dangerMaxSup: props.max
  }
}

const normalizedThresholds = computed(() => {
  const fallback = buildFallbackThresholds()

  const values = {
    dangerMin: Number(props.thresholds?.dangerMin ?? fallback.dangerMin),
    dangerMax: Number(props.thresholds?.dangerMax ?? fallback.dangerMax),
    warningMin: Number(props.thresholds?.warningMin ?? fallback.warningMin),
    warningMax: Number(props.thresholds?.warningMax ?? fallback.warningMax),
    safeMin: Number(props.thresholds?.safeMin ?? fallback.safeMin),
    safeMax: Number(props.thresholds?.safeMax ?? fallback.safeMax),
    warningMinSup: Number(props.thresholds?.warningMinSup ?? fallback.warningMinSup),
    warningMaxSup: Number(props.thresholds?.warningMaxSup ?? fallback.warningMaxSup),
    dangerMinSup: Number(props.thresholds?.dangerMinSup ?? fallback.dangerMinSup),
    dangerMaxSup: Number(props.thresholds?.dangerMaxSup ?? fallback.dangerMaxSup)
  }

  Object.keys(values).forEach((key) => {
    values[key] = Number.isFinite(values[key]) ? clamp(values[key], props.min, props.max) : props.min
  })

  return values
})

const statusClass = computed(() => {
  const currentValue = clamp(props.value, props.min, props.max)
  const t = normalizedThresholds.value

  if (currentValue <= t.dangerMax || currentValue >= t.dangerMinSup) return 'danger'
  if (currentValue <= t.warningMax || currentValue >= t.warningMinSup) return 'warning'
  return 'safe'
})

const statusText = computed(() => {
  const currentValue = clamp(props.value, props.min, props.max)
  const t = normalizedThresholds.value

  if (currentValue <= t.dangerMax || currentValue >= t.dangerMinSup) return 'Peligroso'
  if (currentValue <= t.warningMax || currentValue >= t.warningMinSup) return 'Advertencia'
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
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.sensor-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border-color: #d0d0d0;
}

.sensor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 12px;
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

.sensor-display {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 140px;
  border-radius: 8px;
  padding: 20px;
  transition: all 0.3s ease;
}

.status-bg-safe {
  background-color: rgba(76, 175, 80, 0.9);
}

.status-bg-warning {
  background-color: rgba(255, 193, 7, 0.9);
}

.status-bg-danger {
  background-color: rgba(244, 67, 54, 0.9);
}

.sensor-value {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  gap: 4px;
}

.value-number {
  font-size: 56px;
  font-weight: 700;
  color: #ffffff;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.value-unit {
  font-size: 18px;
  font-weight: 500;
  color: #ffffff;
  opacity: 0.95;
}

.sensor-info {
  padding-top: 12px;
  border-top: 1px solid #f0f0f0;
}

.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
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

  .value-number {
    font-size: 40px;
  }

  .value-unit {
    font-size: 14px;
  }

  .sensor-display {
    min-height: 100px;
  }
}

@media (max-width: 480px) {
  .sensor-card {
    padding: 12px;
  }

  .value-number {
    font-size: 32px;
  }

  .value-unit {
    font-size: 12px;
  }

  .sensor-display {
    min-height: 80px;
  }
}
</style>
