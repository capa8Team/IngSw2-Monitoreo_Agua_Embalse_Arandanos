<template>
  <div class="zero-center-gauge-container">
    <svg
      :width="size"
      :height="size"
      :viewBox="`0 0 ${size} ${size}`"
      class="zero-center-gauge"
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

      <!-- Left danger zone (red) -->
      <path
        :d="getArcPath(center, radius, 'left', 'danger')"
        fill="none"
        stroke="#ff4444"
        :stroke-width="radius * 0.12"
        stroke-linecap="round"
        opacity="0.4"
      />

      <!-- Left warning zone (yellow) -->
      <path
        :d="getArcPath(center, radius, 'left', 'warning')"
        fill="none"
        stroke="#ffb84d"
        :stroke-width="radius * 0.12"
        stroke-linecap="round"
        opacity="0.4"
      />

      <!-- Right warning zone (yellow) -->
      <path
        :d="getArcPath(center, radius, 'right', 'warning')"
        fill="none"
        stroke="#ffb84d"
        :stroke-width="radius * 0.12"
        stroke-linecap="round"
        opacity="0.4"
      />

      <!-- Right danger zone (red) -->
      <path
        :d="getArcPath(center, radius, 'right', 'danger')"
        fill="none"
        stroke="#ff4444"
        :stroke-width="radius * 0.12"
        stroke-linecap="round"
        opacity="0.4"
      />

      <!-- Center safe zone (green) -->
      <path
        :d="getArcPath(center, radius, 'center', 'safe')"
        fill="none"
        stroke="#66bb6a"
        :stroke-width="radius * 0.12"
        stroke-linecap="round"
        opacity="0.4"
      />

      <!-- Center zero line -->
      <line
        :x1="center"
        :y1="center - radius * 0.15"
        :x2="center"
        :y2="center - radius"
        stroke="#333"
        :stroke-width="radius * 0.05"
        stroke-linecap="round"
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

      <!-- Center circle -->
      <circle
        :cx="center"
        :cy="center"
        :r="radius * 0.12"
        :fill="needleColor"
      />

      <!-- Scale marks -->
      <g class="scale-marks" opacity="0.6">
        <!-- Left side marks -->
        <line
          v-for="i in 5"
          :key="`left-mark-${i}`"
          :x1="getScaleMarkX('left', i, 0.85)"
          :y1="getScaleMarkY('left', i, 0.85)"
          :x2="getScaleMarkX('left', i, 0.95)"
          :y2="getScaleMarkY('left', i, 0.95)"
          stroke="#999"
          :stroke-width="radius * 0.04"
        />
        <!-- Right side marks -->
        <line
          v-for="i in 5"
          :key="`right-mark-${i}`"
          :x1="getScaleMarkX('right', i, 0.85)"
          :y1="getScaleMarkY('right', i, 0.85)"
          :x2="getScaleMarkX('right', i, 0.95)"
          :y2="getScaleMarkY('right', i, 0.95)"
          stroke="#999"
          :stroke-width="radius * 0.04"
        />
      </g>

      <!-- Scale numbers -->
      <g class="scale-numbers" opacity="0.7">
        <!-- Left side numbers -->
        <text
          v-for="i in 3"
          :key="`left-num-${i}`"
          :x="center - (radius * 0.7) - (i - 2) * (radius * 0.25)"
          :y="center - radius * 0.65"
          text-anchor="middle"
          dominant-baseline="middle"
          font-size="14"
          font-weight="600"
          fill="#666"
        >
          {{ (centerValue - (3 - i) * step).toFixed(1) }}
        </text>
        <!-- Center zero -->
        <text
          :x="center"
          :y="center - radius * 0.75"
          text-anchor="middle"
          dominant-baseline="middle"
          font-size="16"
          font-weight="700"
          fill="#333"
        >
          {{ centerValue.toFixed(1) }}
        </text>
        <!-- Right side numbers -->
        <text
          v-for="i in 3"
          :key="`right-num-${i}`"
          :x="center + (radius * 0.7) + (i - 1) * (radius * 0.25)"
          :y="center - radius * 0.65"
          text-anchor="middle"
          dominant-baseline="middle"
          font-size="14"
          font-weight="600"
          fill="#666"
        >
          {{ (centerValue + i * step).toFixed(1) }}
        </text>
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

// Calculate center value (midpoint of range)
const centerValue = computed(() => (props.min + props.max) / 2)
const step = computed(() => (props.max - props.min) / 6)

// Deviation from center (-1 to 1)
const deviation = computed(() => {
  const range = props.max - props.min
  const centerVal = centerValue.value
  const clipped = Math.max(props.min, Math.min(props.max, props.value))
  return (clipped - centerVal) / (range / 2)
})

// Angle for needle (-90 to 90 degrees, where 0 is center)
const needleAngle = computed(() => {
  return Math.max(-90, Math.min(90, deviation.value * 90))
})

// Needle position
const needleX = computed(() => {
  const angleRad = (needleAngle.value * Math.PI) / 180
  return center.value + radius.value * 0.8 * Math.cos(angleRad - Math.PI / 2)
})

const needleY = computed(() => {
  const angleRad = (needleAngle.value * Math.PI) / 180
  return center.value + radius.value * 0.8 * Math.sin(angleRad - Math.PI / 2)
})

// Needle color based on deviation
const needleColor = computed(() => {
  const dev = Math.abs(deviation.value)
  if (dev > 0.75) return '#ff4444' // Red - dangerous
  if (dev > 0.5) return '#ffb84d' // Yellow - warning
  return '#66bb6a' // Green - stable
})

// Arc path generator
const getArcPath = (cx, r, side, zone) => {
  const startAngle = side === 'center' ? -30 : side === 'left' ? -150 : 30
  const endAngle = side === 'center' ? 30 : side === 'left' ? -90 : 90
  
  const startRad = (startAngle * Math.PI) / 180
  const endRad = (endAngle * Math.PI) / 180
  
  const x1 = cx + r * Math.cos(startRad - Math.PI / 2)
  const y1 = cx + r * Math.sin(startRad - Math.PI / 2)
  const x2 = cx + r * Math.cos(endRad - Math.PI / 2)
  const y2 = cx + r * Math.sin(endRad - Math.PI / 2)
  
  const largeArc = Math.abs(endAngle - startAngle) > 180 ? 1 : 0
  
  return `M ${x1} ${y1} A ${r} ${r} 0 ${largeArc} 1 ${x2} ${y2}`
}

// Scale mark positions
const getScaleMarkX = (side, i, radiusPercent) => {
  const totalMarks = 5
  const baseAngle = side === 'left' ? -90 : 90
  const angle = baseAngle - (i - 1) * (60 / (totalMarks - 1))
  const angleRad = (angle * Math.PI) / 180
  return center.value + radius.value * radiusPercent * Math.cos(angleRad - Math.PI / 2)
}

const getScaleMarkY = (side, i, radiusPercent) => {
  const totalMarks = 5
  const baseAngle = side === 'left' ? -90 : 90
  const angle = baseAngle - (i - 1) * (60 / (totalMarks - 1))
  const angleRad = (angle * Math.PI) / 180
  return center.value + radius.value * radiusPercent * Math.sin(angleRad - Math.PI / 2)
}
</script>

<style scoped>
.zero-center-gauge-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.zero-center-gauge {
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.1));
}

.value-display {
  text-align: center;
}

.numeric-value {
  font-size: 32px;
  font-weight: 700;
  color: #333;
  line-height: 1;
}

.unit {
  font-size: 16px;
  color: #999;
  margin-top: 4px;
}
</style>
