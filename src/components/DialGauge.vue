<template>
  <div class="dial-gauge-container">
    <svg
      :width="size"
      :height="size"
      :viewBox="`0 0 ${size} ${size}`"
      class="dial-gauge"
    >
      <!-- Background circle -->
      <circle
        :cx="center"
        :cy="center"
        :r="radius"
        fill="#f8f9fa"
        stroke="#e0e0e0"
        stroke-width="2"
      />

      <!-- Color zones background -->
      <defs>
        <linearGradient id="redZone" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" style="stop-color: #ff4444; stop-opacity: 0.2" />
          <stop offset="100%" style="stop-color: #ff4444; stop-opacity: 0" />
        </linearGradient>
        <linearGradient id="yellowZone" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" style="stop-color: #ffb84d; stop-opacity: 0.15" />
          <stop offset="100%" style="stop-color: #ffb84d; stop-opacity: 0.15" />
        </linearGradient>
        <linearGradient id="greenZone" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" style="stop-color: #66bb6a; stop-opacity: 0" />
          <stop offset="100%" style="stop-color: #66bb6a; stop-opacity: 0.2" />
        </linearGradient>
      </defs>

      <!-- Red zones (left and right) -->
      <circle
        :cx="center"
        :cy="center"
        :r="radius"
        fill="none"
        stroke="#ff4444"
        :stroke-width="radius * 0.15"
        :stroke-dasharray="`${arcLength * 0.15} ${arcLength}`"
        stroke-linecap="round"
        opacity="0.3"
      />
      <circle
        :cx="center"
        :cy="center"
        :r="radius"
        fill="none"
        stroke="#ff4444"
        :stroke-width="radius * 0.15"
        :stroke-dasharray="`${arcLength * 0.15} ${arcLength}`"
        :stroke-dashoffset="`${-arcLength * 0.85}`"
        stroke-linecap="round"
        opacity="0.3"
      />

      <!-- Yellow zones -->
      <circle
        :cx="center"
        :cy="center"
        :r="radius"
        fill="none"
        stroke="#ffb84d"
        :stroke-width="radius * 0.15"
        :stroke-dasharray="`${arcLength * 0.35} ${arcLength}`"
        :stroke-dashoffset="`${-arcLength * 0.15}`"
        stroke-linecap="round"
        opacity="0.3"
      />
      <circle
        :cx="center"
        :cy="center"
        :r="radius"
        fill="none"
        stroke="#ffb84d"
        :stroke-width="radius * 0.15"
        :stroke-dasharray="`${arcLength * 0.35} ${arcLength}`"
        :stroke-dashoffset="`${-arcLength * 0.5}`"
        stroke-linecap="round"
        opacity="0.3"
      />

      <!-- Green zone (center) -->
      <circle
        :cx="center"
        :cy="center"
        :r="radius"
        fill="none"
        stroke="#66bb6a"
        :stroke-width="radius * 0.15"
        :stroke-dasharray="`${arcLength * 0.3} ${arcLength}`"
        :stroke-dashoffset="`${-arcLength * 0.35}`"
        stroke-linecap="round"
        opacity="0.3"
      />

      <!-- Outer ring (progress indicator) -->
      <circle
        :cx="center"
        :cy="center"
        :r="radius"
        fill="none"
        :stroke="needleColor"
        :stroke-width="radius * 0.12"
        :stroke-dasharray="`${arcLength * (percentage / 100)} ${arcLength}`"
        stroke-linecap="round"
      />

      <!-- Center circle -->
      <circle
        :cx="center"
        :cy="center"
        :r="radius * 0.15"
        :fill="needleColor"
      />

      <!-- Needle -->
      <line
        :x1="center"
        :y1="center"
        :x2="needleX"
        :y2="needleY"
        :stroke="needleColor"
        :stroke-width="radius * 0.08"
        stroke-linecap="round"
      />

      <!-- Scale marks -->
      <g class="scale-marks" opacity="0.5">
        <line
          v-for="i in 9"
          :key="`mark-${i}`"
          :x1="getMarkX(i, 0.85)"
          :y1="getMarkY(i, 0.85)"
          :x2="getMarkX(i, 0.95)"
          :y2="getMarkY(i, 0.95)"
          stroke="#999"
          :stroke-width="radius * 0.04"
        />
      </g>
    </svg>

    <!-- Value display -->
    <div class="value-display">
      <div class="numeric-value">{{ value.toFixed(2) }}</div>
      <div class="unit">{{ unit }}</div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  value: {
    type: Number,
    required: true
  },
  min: {
    type: Number,
    default: 0
  },
  max: {
    type: Number,
    default: 100
  },
  unit: {
    type: String,
    default: ''
  },
  size: {
    type: Number,
    default: 200
  }
})

const center = computed(() => props.size / 2)
const radius = computed(() => props.size / 2.5)
const arcLength = computed(() => Math.PI * radius.value)

const percentage = computed(() => {
  const clipped = Math.max(props.min, Math.min(props.max, props.value))
  return ((clipped - props.min) / (props.max - props.min)) * 100
})

const needleColor = computed(() => {
  const pct = percentage.value
  if (pct < 15 || pct > 85) return '#ff4444' // Red - dangerous
  if (pct < 35 || pct > 65) return '#ffb84d' // Yellow - warning
  return '#66bb6a' // Green - stable
})

const angle = computed(() => {
  return (percentage.value / 100) * 180 - 90
})

const needleX = computed(() => {
  const rad = (angle.value * Math.PI) / 180
  return center.value + radius.value * 0.7 * Math.cos(rad)
})

const needleY = computed(() => {
  const rad = (angle.value * Math.PI) / 180
  return center.value + radius.value * 0.7 * Math.sin(rad)
})

const getMarkX = (index, distance) => {
  const angle = (index / 8) * 180 - 90
  const rad = (angle * Math.PI) / 180
  return center.value + radius.value * distance * Math.cos(rad)
}

const getMarkY = (index, distance) => {
  const angle = (index / 8) * 180 - 90
  const rad = (angle * Math.PI) / 180
  return center.value + radius.value * distance * Math.sin(rad)
}
</script>

<style scoped>
.dial-gauge-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 16px;
}

.dial-gauge {
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.08));
}

.value-display {
  text-align: center;
}

.numeric-value {
  font-size: 28px;
  font-weight: 600;
  color: #333;
  line-height: 1;
}

.unit {
  font-size: 13px;
  color: #888;
  margin-top: 4px;
  font-weight: 500;
}

.scale-marks line {
  transition: stroke-width 0.3s ease;
}
</style>
